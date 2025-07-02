import asyncio
import re
import time
import os
import sys
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# 常數定義
DEFAULT_TIMEOUT = 10000  # 預設等待超時時間 (毫秒)
DEFAULT_BROWSER = 'chromium'  # 預設瀏覽器

class BrowserAutomation:
    def __init__(self, script_lines=None, callback=None, log_callback=None, on_script_generated=None, on_recording_stopped=None, on_script_end=None):
        """初始化瀏覽器自動化
        
        Args:
            script_lines: 腳本行的列表
            callback: 進度回調函數，用於更新UI
            log_callback: 日誌回調函數，用於顯示日誌
            on_script_generated: 腳本生成回調函數
            on_recording_stopped: 錄製停止回調函數
            on_script_end: 腳本執行結束回調函數
        """
        self.script_lines = script_lines or []
        self.callback = callback
        self.log_callback = log_callback
        self.on_script_generated = on_script_generated
        self.on_recording_stopped = on_recording_stopped
        self.on_script_end = on_script_end
        
        self.browser = None
        self.context = None
        self.page = None
        self.browser_page = None
        self.pages = []
        
        # 錄製相關
        self.recording = False
        self.recorder_page = None
        self.recorded_actions = []
        self.is_paused = False  # 使用統一的命名
        self.initial_url = None
        self.executing = False
        self._polling_task = None
        
    async def start_browser(self, headless=False):
        """啟動瀏覽器
        
        Args:
            headless: 是否使用無頭模式
        """
        self.log_message("啟動瀏覽器...")
        try:
            playwright = await async_playwright().start()
            self.browser = await getattr(playwright, DEFAULT_BROWSER).launch(headless=headless)
            self.context = await self.browser.new_context(viewport={'width': 1280, 'height': 800})
            self.page = await self.context.new_page()
            self.browser_page = self.page  # 設置browser_page與page相同
            self.pages = [self.page]
            
            # 記錄頁面打開時的URL
            await self.page.goto("about:blank")
            
            self.log_message("瀏覽器已啟動")
            return self.page
        except Exception as e:
            self.log_message(f"啟動瀏覽器時發生錯誤: {str(e)}")
            raise
        
    async def close_browser(self):
        """關閉瀏覽器"""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.context = None
            self.page = None
            self.pages = []
            self.log("瀏覽器已關閉")
            
    async def execute_script(self, script_path):
        """執行給定的腳本檔案"""
        self.executing = True
        success = True
        
        try:
            with open(script_path, 'r', encoding='utf-8') as file:
                script_lines = file.readlines()
            
            # 移除空行和註釋行
            script_lines = [line.strip() for line in script_lines if line.strip() and not line.strip().startswith('#')]
            
            # 處理條件語句
            condition_stack = []
            skip_until = None
            
            for i, line in enumerate(script_lines):
                # 處理條件控制流
                if skip_until is not None:
                    if line == skip_until:
                        skip_until = None
                    continue
                
                if line.startswith('IF '):
                    result = await self._evaluate_condition(line[3:])
                    condition_stack.append(result)
                    if not result:  # 如果條件為假，跳過到ELSE或ENDIF
                        skip_until = 'ELSE' if 'ELSE' in script_lines[i+1:] else 'ENDIF'
                    continue
                elif line == 'ELSE':
                    if not condition_stack:
                        self.log_message("錯誤：在IF之前遇到ELSE")
                        continue
                    if condition_stack[-1]:  # 如果之前的IF為真，現在應該跳過
                        skip_until = 'ENDIF'
                    continue
                elif line == 'ENDIF':
                    if condition_stack:
                        condition_stack.pop()
                    continue
                
                # 執行指令
                try:
                    await self._execute_command(line)
                except Exception as e:
                    self.log_message(f"執行命令 '{line}' 時出錯: {str(e)}")
                    success = False
                    if "驗證失敗" in str(e):
                        self.log_message(f"❌ 驗證失敗: {str(e)}")
                
                # 在每個命令之後添加延遲
                await asyncio.sleep(0.5)
                
            self.log_message("腳本執行完成")
        except Exception as e:
            self.log_message(f"執行腳本時出錯: {str(e)}")
            success = False
        
        self.executing = False
        if self.on_script_end:
            self.on_script_end()
            
        return success
            
    async def run_script(self):
        """執行腳本行"""
        line_index = 0
        total_lines = len(self.script_lines)
        
        # 條件執行相關
        condition_stack = []  # 存儲條件狀態的堆疊
        skip_mode = False     # 當前是否處於跳過模式
        
        while line_index < total_lines:
            line = self.script_lines[line_index]
            
            # 跳過註釋行
            if line.startswith('#'):
                line_index += 1
                continue
            
            # 條件語句處理
            cmd = line.split('=', 1)[0].strip()
            
            # 處理條件語句
            if cmd in ["IF_TEXT_EXISTS", "IF_URL_CONTAINS"]:
                # 處理IF語句
                if not skip_mode:
                    try:
                        result = await self.execute_command(line)
                        condition_stack.append(result)
                        skip_mode = not result  # 如果條件不滿足，則跳過後續語句
                    except Exception as e:
                        self.log(f"執行條件'{line}'時出錯: {e}")
                        condition_stack.append(False)
                        skip_mode = True
                else:
                    # 已經在跳過模式，繼續跳過
                    condition_stack.append(False)
                
                line_index += 1
                continue
                
            elif cmd == "ELSE":
                # 處理ELSE語句
                if condition_stack:
                    skip_mode = condition_stack[-1]  # 反轉跳過模式
                line_index += 1
                continue
                
            elif cmd == "ENDIF":
                # 處理ENDIF語句
                if condition_stack:
                    condition_stack.pop()  # 彈出最後一個條件
                    if not condition_stack:
                        skip_mode = False  # 如果條件堆疊為空，則停止跳過
                    elif condition_stack[-1] == False:
                        skip_mode = True   # 如果還有未滿足的條件，繼續跳過
                line_index += 1
                continue
            
            # 如果當前處於跳過模式，則跳過當前行
            if skip_mode:
                line_index += 1
                continue
                
            # 執行常規命令
            try:
                self.log(f"執行: {line}")
                await self.execute_command(line)
                
                # 成功後更新進度
                if self.callback:
                    progress = int((line_index + 1) / total_lines * 100)
                    self.callback(progress, f"已執行: {line}")
            except Exception as e:
                self.log(f"執行行 '{line}' 時出錯: {e}")
            
            line_index += 1
            
        self.log("腳本執行完成")
        
    async def execute_command(self, line):
        """執行單行命令
        
        Args:
            line: 命令行
        """
        # 將命令分解為指令和參數
        parts = line.split('=', 1)
        cmd = parts[0].strip()
        param = parts[1].strip() if len(parts) > 1 else ""
        
        # 如果沒有使用"="分割，可能使用空格分割
        if len(parts) == 1 and ' ' in line:
            parts = line.split(' ', 1)
            cmd = parts[0].strip()
            param = parts[1].strip() if len(parts) > 1 else ""
        
        # 處理引號包裹的參數
        if param and ((param.startswith('"') and param.endswith('"')) or 
                      (param.startswith("'") and param.endswith("'"))):
            param = param[1:-1]  # 移除引號
        
        # 根據指令類型執行對應操作
        if cmd == "OPEN_URL" or cmd == "OPEN":
            # 判断是否是本地文件路径（没有http前缀且包含常见文件扩展名或路径分隔符）
            if (not param.startswith(('http://', 'https://', 'file://'))) and \
               (os.path.sep in param or param.endswith(('.html', '.htm'))):
                # 处理本地文件路径
                file_path = param
                if not os.path.exists(file_path):
                    # 嘗試轉換為絕對路徑
                    if not os.path.isabs(file_path):
                        web_dir = os.path.join(os.getcwd(), "web")
                        abs_path = os.path.join(web_dir, os.path.basename(file_path))
                        if os.path.exists(abs_path):
                            file_path = abs_path
                        else:
                            raise FileNotFoundError(f"本地文件不存在: {file_path}")
                
                self.log(f"打開本地文件: {file_path}")
                # 确保使用file://前缀和绝对路径
                absolute_path = os.path.abspath(file_path)
                await self.page.goto(f"file://{absolute_path}")
            elif param.startswith('file://'):
                # 處理已有file://前缀的本地文件路徑
                file_path = param.replace('file://', '')
                if not os.path.exists(file_path):
                    # 嘗試轉換為絕對路徑
                    if not os.path.isabs(file_path):
                        web_dir = os.path.join(os.getcwd(), "web")
                        abs_path = os.path.join(web_dir, os.path.basename(file_path))
                        if os.path.exists(abs_path):
                            file_path = abs_path
                        else:
                            raise FileNotFoundError(f"本地文件不存在: {file_path}")
                
                self.log(f"打開本地文件: {file_path}")
                absolute_path = os.path.abspath(file_path)
                await self.page.goto(f"file://{absolute_path}")
            else:
                # 處理網絡URL
                if not param.startswith(('http://', 'https://')):
                    param = 'https://' + param
                self.log(f"打開URL: {param}")
                await self.page.goto(param)
            
        elif cmd == "CLICK_BY":
            await self.page.click(param)
            self.log(f"已點擊: {param}")
            
        elif cmd == "FILL":
            # 處理填充表單的情況
            if "||" in param:
                selector, value = param.split("||", 1)
                await self.page.fill(selector.strip(), value.strip())
                self.log(f"已填充表單: {selector} = {value}")
            else:
                self.log(f"填充格式錯誤: {param}")
                
        elif cmd == "SUBMIT_FORM":
            # 處理表單提交
            try:
                # 先找到表單
                form = await self.page.query_selector(param)
                if form:
                    # 找到表單的提交按鈕
                    submit_btn = await form.query_selector("button[type='submit']")
                    if submit_btn:
                        await submit_btn.click()
                        self.log(f"已提交表單: {param}")
                    else:
                        # 嘗試找一個普通按鈕
                        any_btn = await form.query_selector("button")
                        if any_btn:
                            await any_btn.click()
                            self.log(f"已點擊表單按鈕: {param}")
                        else:
                            # 直接使用JavaScript提交表單
                            await self.page.evaluate(f"document.querySelector('{param}').submit()")
                            self.log(f"已使用JavaScript提交表單: {param}")
                else:
                    self.log(f"找不到表單: {param}")
            except Exception as e:
                self.log(f"提交表單時出錯: {e}")
            
        elif cmd == "ASSERT_TEXT":
            content = await self.page.content()
            if param not in content:
                raise AssertionError(f"文字驗證失敗: 未找到 '{param}'")
            self.log(f"文字驗證通過: {param}")
            
        elif cmd == "WAIT":
            try:
                seconds = float(param)
                self.log(f"等待 {seconds} 秒")
                await asyncio.sleep(seconds)
            except ValueError:
                self.log(f"等待時間格式錯誤: {param}")
            
        elif cmd == "WAIT_FOR_TEXT":
            try:
                await self.page.wait_for_function(
                    f"document.body.innerText.includes('{param}')",
                    timeout=DEFAULT_TIMEOUT
                )
                self.log(f"已等到文字: {param}")
            except PlaywrightTimeoutError:
                raise TimeoutError(f"等待文字超時: {param}")
                
        elif cmd == "WAIT_FOR_URL":
            try:
                # 等待URL包含指定內容
                check_url = lambda url: param in url
                await self.page.wait_for_url(check_url, timeout=DEFAULT_TIMEOUT)
                self.log(f"已等到URL包含: {param}")
            except PlaywrightTimeoutError:
                raise TimeoutError(f"等待URL超時: {param}")
                
        elif cmd == "IF_TEXT_EXISTS":
            # 檢查文字是否存在
            content = await self.page.content()
            exists = param in content
            self.log(f"條件: 文字'{param}'{'存在' if exists else '不存在'}")
            return exists
            
        elif cmd == "IF_URL_CONTAINS":
            # 檢查URL是否包含特定字符串
            url = self.page.url
            exists = param in url
            self.log(f"條件: URL{'包含' if exists else '不包含'}'{param}'")
            return exists
            
        elif cmd == "SWITCH_TAB":
            # 切換到指定的標籤頁
            index = int(param)
            if 0 <= index < len(self.pages):
                self.page = self.pages[index]
                self.log(f"已切換到標籤頁 {index}")
            else:
                raise IndexError(f"標籤頁索引超出範圍: {index}")
                
        elif cmd == "CLOSE_TAB":
            # 關閉當前標籤頁
            if len(self.pages) > 1:
                await self.page.close()
                self.pages.remove(self.page)
                self.page = self.pages[0]
                self.log("已關閉當前標籤頁")
            else:
                self.log("無法關閉: 只有一個標籤頁")

        elif cmd == "SCREENSHOT" or cmd == "SCREENSHOT_ASSERT":
            # 處理截圖命令
            try:
                # 如果沒有指定檔名，使用預設命名
                if not param:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    param = f"screenshot_{timestamp}.png"
                
                # 確保檔案名稱有.png副檔名
                if not param.lower().endswith('.png'):
                    param += '.png'
                
                # 確保截圖目錄存在
                screenshots_dir = os.path.join(os.getcwd(), "screenshots")
                os.makedirs(screenshots_dir, exist_ok=True)
                
                # 完整的截圖路徑
                screenshot_path = os.path.join(screenshots_dir, param)
                
                # 執行截圖
                await self._take_screenshot(screenshot_path)
                
                if cmd == "SCREENSHOT_ASSERT":
                    self.log(f"截圖驗證: {param}")
                    # TODO: 實現截圖比對功能
            except Exception as e:
                self.log(f"截圖時出錯: {str(e)}")
                
        else:
            self.log(f"未知命令: {cmd}")
        
        return True  # 默認返回True用於條件執行
    
    # 錄製相關方法
    async def start_recording(self, initial_url=None):
        """開始錄製網頁操作"""
        if self.recording:
            self.log_message("已經在錄製中")
            return
        
        self.recording = True
        self.is_paused = False
        self.recorded_actions = []
        self.initial_url = initial_url
        
        # 啟動一個新的頁面用於錄製
        try:
            if not self.browser:
                await self.start_browser(headless=False)
            
            self.recorder_page = await self.browser.new_page()
            
            # 如果有初始URL，導航到該URL
            if initial_url:
                try:
                    if initial_url.lower().startswith('file://'):
                        # 處理本地文件路徑
                        file_path = initial_url[7:]
                        
                        # 檢查文件是否存在
                        if not os.path.exists(file_path):
                            # 嘗試在web目錄中查找
                            web_dir = os.path.join(os.getcwd(), "web")
                            test_path = os.path.join(web_dir, os.path.basename(file_path))
                            
                            if os.path.exists(test_path):
                                file_path = test_path
                            else:
                                raise FileNotFoundError(f"找不到本地文件: {file_path}")
                        
                        # 使用絕對路徑
                        abs_path = os.path.abspath(file_path)
                        initial_url = f"file://{abs_path}"
                    
                    self.log_message(f"導航到: {initial_url}")
                    await self.recorder_page.goto(initial_url)
                    
                    # 記錄導航操作
                    self.recorded_actions.append({
                        "type": "navigation",
                        "url": initial_url,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    self.log_message(f"導航到初始URL時出錯: {str(e)}")
            
            # 設置錄製事件
            await self.setup_recording_events()
            
            # 添加錄製狀態指示器
            await self.recorder_page.evaluate("""
            () => {
                // 創建錄製狀態指示器
                const statusEl = document.createElement('div');
                statusEl.id = '__recording_status';
                statusEl.style.position = 'fixed';
                statusEl.style.top = '10px';
                statusEl.style.right = '10px';
                statusEl.style.backgroundColor = 'red';
                statusEl.style.color = 'white';
                statusEl.style.padding = '5px 10px';
                statusEl.style.borderRadius = '5px';
                statusEl.style.zIndex = '9999';
                statusEl.style.fontFamily = 'Arial, sans-serif';
                statusEl.style.fontSize = '14px';
                statusEl.style.display = 'flex';
                statusEl.style.alignItems = 'center';
                statusEl.style.gap = '5px';
                
                // 添加錄製圖標
                const recordIcon = document.createElement('span');
                recordIcon.innerHTML = '⚫';
                recordIcon.style.color = 'red';
                recordIcon.style.animation = 'blink 1s infinite';
                statusEl.appendChild(recordIcon);
                
                // 添加文字
                const text = document.createElement('span');
                text.textContent = '錄製中 (0 個操作)';
                statusEl.appendChild(text);
                
                // 添加閃爍動畫
                const style = document.createElement('style');
                style.textContent = `
                    @keyframes blink {
                        0% { opacity: 1; }
                        50% { opacity: 0.5; }
                        100% { opacity: 1; }
                    }
                `;
                document.head.appendChild(style);
                
                // 添加到頁面
                document.body.appendChild(statusEl);
                
                // 計數器，用於顯示錄製的操作數
                window._recordedActionsCount = 0;
                
                // 更新操作計數
                window.updateActionCount = (count) => {
                    const text = statusEl.querySelector('span:last-child');
                    if (text) {
                        text.textContent = `錄製中 (${count} 個操作)`;
                    }
                };
            }
            """)
            
            self.log_message("錄製已開始")
            
        except Exception as e:
            self.recording = False
            self.log_message(f"啟動錄製時出錯: {str(e)}")
            raise
    
    async def setup_recording_events(self):
        """設置錄製事件監聽器"""
        page = self.recorder_page
        
        # 監聽頁面導航
        page.on("framenavigated", self.on_frame_navigated)
        
        # 監聽點擊事件
        await page.evaluate("""
        () => {
            window._recordedClicks = [];
            
            // 獲取更穩定的選擇器
            function getOptimalSelector(element) {
                // 嘗試使用ID
                if (element.id) {
                    return `#${element.id}`;
                }
                
                // 嘗試使用特殊屬性
                if (element.getAttribute('data-testid')) {
                    return `[data-testid="${element.getAttribute('data-testid')}"]`;
                }
                
                if (element.getAttribute('name')) {
                    return `[name="${element.getAttribute('name')}"]`;
                }
                
                // 嘗試使用標籤名+索引組合
                const tag = element.tagName.toLowerCase();
                if (tag === 'button' || tag === 'a' || tag === 'input' || tag === 'select' || tag === 'textarea') {
                    // 嘗試使用文本內容
                    let textContent = element.textContent?.trim();
                    if (textContent && textContent.length < 50) {
                        return `${tag}:has-text("${textContent}")`;
                    }
                    
                    // 嘗試使用placeholder
                    if (element.getAttribute('placeholder')) {
                        return `${tag}[placeholder="${element.getAttribute('placeholder')}"]`;
                    }
                    
                    // 對於按鈕，嘗試使用類型
                    if (tag === 'button' && element.getAttribute('type')) {
                        return `button[type="${element.getAttribute('type')}"]`;
                    }
                    
                    // 使用CSS類
                    if (element.className && typeof element.className === 'string') {
                        const classes = element.className.split(' ').filter(c => c);
                        if (classes.length > 0) {
                            const className = classes.join('.');
                            return `.${className}`;
                        }
                    }
                }
                
                // 生成CSS路徑
                let path = [];
                let currElement = element;
                let maxDepth = 3; // 限制路徑深度
                
                while (currElement && currElement.nodeType === Node.ELEMENT_NODE && maxDepth > 0) {
                    let selector = currElement.tagName.toLowerCase();
                    
                    // 如果有ID，優先使用
                    if (currElement.id) {
                        selector = `#${currElement.id}`;
                        path.unshift(selector);
                        break;
                    }
                    
                    // 如果是唯一的標籤，直接使用標籤名
                    if (document.querySelectorAll(selector).length === 1) {
                        path.unshift(selector);
                        break;
                    }
                    
                    // 添加類名
                    if (currElement.className && typeof currElement.className === 'string') {
                        const classes = currElement.className.split(' ').filter(c => c);
                        if (classes.length > 0) {
                            selector += `.${classes.join('.')}`;
                            // 檢查是否唯一
                            if (document.querySelectorAll(selector).length === 1) {
                                path.unshift(selector);
                                break;
                            }
                        }
                    }
                    
                    // 添加:nth-child
                    let siblings = 0;
                    let nth = 0;
                    
                    for (let node = currElement; node; node = node.previousElementSibling) {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            siblings++;
                            if (node === currElement) nth = siblings;
                        }
                    }
                    
                    if (siblings > 1) {
                        selector += `:nth-child(${nth})`;
                    }
                    
                    path.unshift(selector);
                    currElement = currElement.parentNode;
                    maxDepth--;
                }
                
                return path.join(' > ');
            }
            
            // 添加點擊事件監聽器
            document.addEventListener('click', (event) => {
                const target = event.target;
                
                // 獲取最佳選擇器
                const selector = getOptimalSelector(target);
                
                // 記錄選擇器
                window._recordedClicks.push(selector);
                window.reportClick(selector);
            }, true);
        }
        """)
        
        # 添加回調函數以報告點擊
        await page.expose_function("reportClick", self.on_click_reported)
        
        # 監聽表單輸入
        await page.evaluate("""
        () => {
            window._recordedInputs = [];
            
            // 使用與點擊事件相同的選擇器邏輯
            function getOptimalSelector(element) {
                // 嘗試使用ID
                if (element.id) {
                    return `#${element.id}`;
                }
                
                // 嘗試使用特殊屬性
                if (element.getAttribute('data-testid')) {
                    return `[data-testid="${element.getAttribute('data-testid')}"]`;
                }
                
                if (element.getAttribute('name')) {
                    return `[name="${element.getAttribute('name')}"]`;
                }
                
                // 嘗試使用標籤名+索引組合
                const tag = element.tagName.toLowerCase();
                if (tag === 'input' || tag === 'select' || tag === 'textarea') {
                    // 嘗試使用placeholder
                    if (element.getAttribute('placeholder')) {
                        return `${tag}[placeholder="${element.getAttribute('placeholder')}"]`;
                    }
                    
                    // 使用CSS類
                    if (element.className && typeof element.className === 'string') {
                        const classes = element.className.split(' ').filter(c => c);
                        if (classes.length > 0) {
                            const className = classes.join('.');
                            return `.${className}`;
                        }
                    }
                }
                
                // 生成CSS路徑
                let path = [];
                let currElement = element;
                let maxDepth = 3; // 限制路徑深度
                
                while (currElement && currElement.nodeType === Node.ELEMENT_NODE && maxDepth > 0) {
                    let selector = currElement.tagName.toLowerCase();
                    
                    // 如果有ID，優先使用
                    if (currElement.id) {
                        selector = `#${currElement.id}`;
                        path.unshift(selector);
                        break;
                    }
                    
                    // 如果是唯一的標籤，直接使用標籤名
                    if (document.querySelectorAll(selector).length === 1) {
                        path.unshift(selector);
                        break;
                    }
                    
                    // 添加類名
                    if (currElement.className && typeof currElement.className === 'string') {
                        const classes = currElement.className.split(' ').filter(c => c);
                        if (classes.length > 0) {
                            selector += `.${classes.join('.')}`;
                            // 檢查是否唯一
                            if (document.querySelectorAll(selector).length === 1) {
                                path.unshift(selector);
                                break;
                            }
                        }
                    }
                    
                    // 添加:nth-child
                    let siblings = 0;
                    let nth = 0;
                    
                    for (let node = currElement; node; node = node.previousElementSibling) {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            siblings++;
                            if (node === currElement) nth = siblings;
                        }
                    }
                    
                    if (siblings > 1) {
                        selector += `:nth-child(${nth})`;
                    }
                    
                    path.unshift(selector);
                    currElement = currElement.parentNode;
                    maxDepth--;
                }
                
                return path.join(' > ');
            }
            
            const inputHandler = (event) => {
                const target = event.target;
                // 只處理input, textarea和select元素
                if (!['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName)) {
                    return;
                }
                
                // 獲取最佳選擇器
                const selector = getOptimalSelector(target);
                
                let value = '';
                if (target.type === 'checkbox' || target.type === 'radio') {
                    value = target.checked ? 'true' : 'false';
                } else {
                    value = target.value;
                }
                
                // 避免每次按鍵都觸發，使用 debounce 技術
                if (window._inputTimeout) {
                    clearTimeout(window._inputTimeout);
                }
                
                window._inputTimeout = setTimeout(() => {
                    window._recordedInputs.push({ selector, value });
                    window.reportInput(selector, value);
                }, 500);  // 500毫秒延遲
            };
            
            // 使用事件委託
            document.addEventListener('input', inputHandler, true);
            document.addEventListener('change', inputHandler, true);
            
            // 監聽表單提交
            document.addEventListener('submit', (event) => {
                const form = event.target;
                let formSelector = getOptimalSelector(form);
                
                if (formSelector) {
                    window.reportFormSubmit(formSelector);
                }
            }, true);
            
            // 設置JavaScript端的輪詢，每秒檢查記錄的操作
            window._recordingInterval = setInterval(() => {
                window.pollRecordedActions();
            }, 1000);
        }
        """)
        
        # 添加回調函數以報告輸入
        await page.expose_function("reportInput", self.on_input_reported)
        
        # 添加回調函數以報告表單提交
        await page.expose_function("reportFormSubmit", self.on_form_submit_reported)
        
        # 添加輪詢函數
        await page.expose_function("pollRecordedActions", self._poll_recorded_actions_js)
        
        # 設置Python端的輪詢
        self._polling_task = asyncio.create_task(self._poll_recorded_actions_periodic())
    
    async def _poll_recorded_actions_periodic(self):
        """定期輪詢記錄的操作"""
        try:
            while self.recording:
                # 檢查並安全訪問is_paused屬性
                try:
                    is_paused = getattr(self, "is_paused", False)  # 如果屬性不存在，默認為False
                    if is_paused:
                        # 如果暫停了，則等待一段時間後再檢查
                        await asyncio.sleep(1)
                        continue
                        
                    # 檢查recorder_page是否已關閉
                    if not self.recorder_page or self.recorder_page.is_closed():
                        # 如果頁面已關閉，停止輪詢
                        print("頁面已關閉，停止輪詢")
                        break
                    
                    # 輪詢記錄的操作
                    await self._poll_recorded_actions()
                    
                except AttributeError as e:
                    # 處理屬性錯誤，例如self.is_paused不存在
                    print(f"屬性錯誤: {e}")
                    # 確保設置is_paused屬性
                    self.is_paused = False
                    
                except Exception as e:
                    if "Target page, context or browser has been closed" in str(e):
                        # 如果瀏覽器已關閉，停止輪詢
                        print("瀏覽器已關閉，停止輪詢")
                        break
                    else:
                        print(f"輪詢記錄操作時出錯: {e}")
                
                # 無論如何都等待一段時間
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"輪詢任務出錯: {e}")
        finally:
            print("輪詢任務已結束")
    
    async def _poll_recorded_actions_js(self):
        """JavaScript調用的輪詢函數"""
        if not self.recording:
            return
            
        try:
            # 安全檢查is_paused屬性
            is_paused = getattr(self, "is_paused", False)  # 如果屬性不存在，默認為False
            if not is_paused:
                await self._poll_recorded_actions()
        except Exception as e:
            print(f"JavaScript輪詢時出錯: {e}")
    
    async def _poll_recorded_actions(self):
        """獲取瀏覽器記錄的操作"""
        if not self.recorder_page:
            return
            
        try:
            # 獲取記錄的點擊
            clicks = await self.recorder_page.evaluate("window._recordedClicks || []")
            if clicks and len(clicks) > 0:
                await self.recorder_page.evaluate("window._recordedClicks = []")
                for selector in clicks:
                    self.record_action(f"CLICK_BY = {selector}")
            
            # 獲取記錄的輸入
            inputs = await self.recorder_page.evaluate("window._recordedInputs || []")
            if inputs and len(inputs) > 0:
                await self.recorder_page.evaluate("window._recordedInputs = []")
                for input_data in inputs:
                    selector = input_data.get("selector", "")
                    value = input_data.get("value", "")
                    if selector and value:
                        self.record_action(f"FILL = {selector} || {value}")
        except Exception as e:
            print(f"輪詢記錄操作時出錯: {e}")
    
    def on_form_submit_reported(self, form_selector):
        """表單提交事件處理"""
        if not hasattr(self, "is_paused"):
            self.is_paused = False
            
        if self.recording and not getattr(self, "is_paused", False):
            self.record_action(f"SUBMIT_FORM = {form_selector}")
    
    def on_frame_navigated(self, frame):
        """頁面導航事件處理"""
        if not hasattr(self, "is_paused"):
            self.is_paused = False
            
        if frame.parent_frame is None and self.recording and not getattr(self, "is_paused", False):
            url = frame.url
            if url != "about:blank":
                self.record_action(f"OPEN_URL = {url}")
    
    def on_click_reported(self, selector):
        """點擊事件處理"""
        if not hasattr(self, "is_paused"):
            self.is_paused = False
            
        if self.recording and not getattr(self, "is_paused", False):
            self.record_action(f"CLICK_BY = {selector}")
    
    def on_input_reported(self, selector, value):
        """輸入事件處理"""
        if not hasattr(self, "is_paused"):
            self.is_paused = False
            
        if self.recording and not getattr(self, "is_paused", False):
            self.record_action(f"FILL = {selector} || {value}")
    
    def record_action(self, action):
        """記錄一個操作"""
        # 確保is_paused屬性存在
        if not hasattr(self, "is_paused"):
            self.is_paused = False
            
        # 如果暫停了，不記錄操作
        if getattr(self, "is_paused", False):
            return
            
        self.recorded_actions.append(action)
        self.log(f"錄製: {action}")
        
        # 更新瀏覽器中的操作計數
        if self.recorder_page and self.recording:
            try:
                # 非阻塞方式調用
                asyncio.create_task(self.recorder_page.evaluate(f"window.updateActionCount({len(self.recorded_actions)})"))
            except Exception as e:
                print(f"更新操作計數時出錯: {e}")
        
        # 通知UI更新
        if self.callback:
            self.callback(0, f"錄製: {action}")
    
    def pause_recording(self):
        """暫停錄製"""
        if not hasattr(self, "is_paused"):
            self.is_paused = False  # 如果屬性不存在，先添加它
            
        if self.recording:
            self.is_paused = True
            
            # 更新錄製狀態指示器
            if self.recorder_page:
                try:
                    # 非阻塞方式調用
                    asyncio.create_task(self.recorder_page.evaluate("""
                    () => {
                        const indicator = document.getElementById('recording-indicator');
                        if (indicator) {
                            indicator.style.backgroundColor = 'rgba(255, 165, 0, 0.7)';
                            indicator.textContent = '⏸️ 已暫停';
                        }
                    }
                    """))
                except Exception as e:
                    print(f"更新暫停指示器時出錯: {e}")
            
            self.log("錄製已暫停")
    
    def resume_recording(self):
        """繼續錄製"""
        if not hasattr(self, "is_paused"):
            self.is_paused = True  # 如果屬性不存在，先添加它
            
        if self.recording:
            self.is_paused = False
            
            # 更新錄製狀態指示器
            if self.recorder_page:
                try:
                    # 非阻塞方式調用
                    asyncio.create_task(self.recorder_page.evaluate("""
                    () => {
                        const indicator = document.getElementById('recording-indicator');
                        if (indicator) {
                            indicator.style.backgroundColor = 'rgba(255, 0, 0, 0.7)';
                            indicator.textContent = '🔴 錄製中';
                        }
                    }
                    """))
                except Exception as e:
                    print(f"更新錄製指示器時出錯: {e}")
            
            self.log("錄製已繼續")
    
    async def stop_recording(self):
        """停止錄製並生成腳本"""
        self.recording = False
        
        # 移除錄製提示
        try:
            if self.recorder_page and not self.recorder_page.is_closed():
                await self.recorder_page.evaluate("""
                () => {
                    const statusEl = document.getElementById('__recording_status');
                    if (statusEl) {
                        statusEl.remove();
                    }
                    
                    // 清除輪詢任務
                    if (window._recordingInterval) {
                        clearInterval(window._recordingInterval);
                    }
                }
                """)
        except Exception as e:
            self.log_message(f"移除錄製提示時出錯: {str(e)}")
        
        # 如果沒有錄製任何操作，添加一個默認操作
        if not self.recorded_actions:
            if self.initial_url:
                self.record_action(f"OPEN_URL = {self.initial_url}")
            self.record_action("WAIT = 1")
        
        # 生成腳本內容
        script_content = self._generate_script_from_actions()
        
        # 記錄腳本到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        script_filename = f"recorded_script_{timestamp}.txt"
        
        try:
            with open(script_filename, "w", encoding="utf-8") as f:
                f.write(script_content)
            
            self.log_message(f"已生成腳本: {script_filename}")
            
            # 將腳本內容設置到輸出回調
            if self.on_script_generated:
                self.on_script_generated(script_content, script_filename)
                
            # 關閉錄製頁面
            try:
                if self.recorder_page and not self.recorder_page.is_closed():
                    await self.recorder_page.close()
                    self.recorder_page = None
            except Exception as e:
                self.log_message(f"關閉錄製頁面時出錯: {str(e)}")
            
            self.recorder_page = None
            
            # 自動執行一次生成的腳本進行驗證
            self.log_message("開始驗證腳本...")
            validation_success = await self.verify_script(script_filename)
            
            # 返回腳本內容和文件名，確保返回的是元組格式
            return (script_content, script_filename)
            
        except Exception as e:
            self.log_message(f"保存腳本時出錯: {str(e)}")
            
            # 在錯誤情況下調用回調
            if self.on_recording_stopped:
                self.on_recording_stopped(False)
            
            return None
        finally:
            self.recorded_actions = []
    
    async def verify_script(self, script_filename):
        """驗證生成的腳本"""
        self.log_message("開始自動驗證錄製的腳本...")
        success = True
        verify_browser = None
        verify_page = None
        
        try:
            # 創建新的瀏覽器實例進行驗證
            playwright = await async_playwright().start()
            verify_browser = await getattr(playwright, DEFAULT_BROWSER).launch(headless=False)
            verify_context = await verify_browser.new_context(viewport={'width': 1280, 'height': 800})
            verify_page = await verify_context.new_page()
            
            # 保存當前的瀏覽器和頁面
            original_browser = self.browser
            original_page = self.page
            
            # 設置驗證使用的瀏覽器和頁面
            self.browser = verify_browser
            self.page = verify_page
            
            # 讀取腳本內容
            with open(script_filename, 'r', encoding='utf-8') as f:
                script_lines = f.readlines()
            
            # 移除空行和註釋
            script_lines = [line.strip() for line in script_lines if line.strip() and not line.strip().startswith('#')]
            
            # 逐行執行命令驗證
            for line in script_lines:
                try:
                    # 使用與執行腳本相同的命令執行函數
                    await self.execute_command(line)
                except Exception as e:
                    self.log_message(f"執行命令 '{line}' 時出錯: {str(e)}")
                    success = False
            
            self.log_message("腳本執行完成")
            
            # 返回驗證結果
            if success:
                self.log_message("✅ 腳本驗證通過！可以順利重新執行。")
            else:
                self.log_message("❌ 腳本驗證失敗！部分操作無法順利執行。")
            
            # 恢復原始瀏覽器和頁面
            self.browser = original_browser
            self.page = original_page
            
            return success
            
        except Exception as e:
            self.log_message(f"驗證腳本時出錯: {str(e)}")
            return False
        finally:
            # 確保關閉驗證用的瀏覽器
            if verify_browser:
                await verify_browser.close()

    def _generate_script_from_actions(self):
        """從記錄的操作生成腳本內容"""
        lines = [
            "# 自動生成的腳本",
            f"# 生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]
        
        # 初始URL記錄
        if self.initial_url:
            if self.initial_url.startswith("file://"):
                local_path = self.initial_url[7:].replace("\\", "/")
                lines.append(f"OPEN {local_path}")
            else:
                lines.append(f"OPEN {self.initial_url}")
            lines.append("WAIT 1")
        
        # 設置一個字典，用於跟踪最近一次輸入的值
        last_input_values = {}
        
        # 遍歷所有記錄的操作
        for action in self.recorded_actions:
            action_type = action.get("type")
            
            if action_type == "navigation":
                url = action.get("url", "")
                if url.startswith("file://"):
                    local_path = url[7:].replace("\\", "/")
                    lines.append(f"OPEN {local_path}")
                else:
                    lines.append(f"OPEN {url}")
            
            elif action_type == "click":
                selector = action.get("selector", "")
                lines.append(f'CLICK "{selector}"')
                lines.append("WAIT 0.5")
            
            elif action_type == "input":
                selector = action.get("selector", "")
                value = action.get("value", "")
                
                # 如果相同的選擇器有新的值，用新值替換舊值
                if selector in last_input_values and last_input_values[selector] == value:
                    continue  # 跳過重複的輸入
                
                last_input_values[selector] = value
                lines.append(f'FILL "{selector}" "{value}"')
            
            elif action_type == "form_submit":
                selector = action.get("selector", "")
                lines.append(f'SUBMIT_FORM "{selector}"')
                lines.append("WAIT 1")  # 表單提交後需要多等一會
            
            elif action_type == "verify_text":
                selector = action.get("selector", "")
                text = action.get("text", "")
                lines.append(f'VERIFY_TEXT "{selector}" "{text}"')
            
            elif action_type == "verify_url":
                url = action.get("url", "")
                lines.append(f'VERIFY_URL "{url}"')
            
            elif action_type == "screenshot":
                filename = action.get("filename", "screenshot.png")
                lines.append(f'SCREENSHOT "{filename}"')
            
            elif action_type == "wait":
                seconds = action.get("seconds", 1)
                lines.append(f"WAIT {seconds}")
        
        # 添加最後的等待
        lines.append("WAIT 1")
        lines.append("# 腳本結束")
        
        return "\n".join(lines)
    
    def log_message(self, message):
        """記錄訊息"""
        print(message)
        if self.log_callback:
            self.log_callback(message)
    
    def log(self, message):
        """兼容舊的log方法"""
        self.log_message(message)

    async def _evaluate_condition(self, condition):
        """評估條件語句"""
        page = self.browser_page
        
        # 簡單的文本存在檢查
        if condition.startswith("TEXT_EXISTS "):
            text = condition[len("TEXT_EXISTS "):].strip()
            # 處理引號
            if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
                text = text[1:-1]
            
            try:
                result = await page.evaluate(f'''() => {{
                    return document.body.innerText.includes("{text}");
                }}''')
                return result
            except Exception as e:
                self.log_message(f"評估文字存在條件時出錯: {str(e)}")
                return False
        
        # URL包含檢查
        elif condition.startswith("URL_CONTAINS "):
            url_part = condition[len("URL_CONTAINS "):].strip()
            # 處理引號
            if (url_part.startswith('"') and url_part.endswith('"')) or (url_part.startswith("'") and url_part.endswith("'")):
                url_part = url_part[1:-1]
            
            current_url = page.url
            return url_part in current_url
        
        # 元素存在檢查
        elif condition.startswith("ELEMENT_EXISTS "):
            selector = condition[len("ELEMENT_EXISTS "):].strip()
            # 處理引號
            if (selector.startswith('"') and selector.endswith('"')) or (selector.startswith("'") and selector.endswith("'")):
                selector = selector[1:-1]
            
            try:
                element = await page.query_selector(selector)
                return element is not None
            except Exception as e:
                self.log_message(f"評估元素存在條件時出錯: {str(e)}")
                return False
        
        # 默認返回False
        self.log_message(f"無法評估條件: {condition}")
        return False

    async def _verify_text(self, selector, expected_text):
        """驗證元素中的文本"""
        try:
            page = self.browser_page
            
            # 嘗試查找元素
            try:
                element = await page.wait_for_selector(selector, state="visible", timeout=5000)
                if not element:
                    error_msg = f"找不到元素: {selector}"
                    self.log_message(error_msg)
                    raise Exception(error_msg)
            except Exception as e:
                self.log_message(f"等待元素可見時出錯: {str(e)}")
                
                # 嘗試不同的選擇器策略
                element = None
                alt_selectors = self._generate_alternative_selectors(selector)
                for alt_selector in alt_selectors:
                    try:
                        element = await page.wait_for_selector(alt_selector, state="visible", timeout=2000)
                        if element:
                            selector = alt_selector
                            break
                    except Exception:
                        continue
                
                if not element:
                    error_msg = f"找不到元素: {selector}"
                    self.log_message(error_msg)
                    raise Exception(error_msg)
            
            # 獲取元素文本
            text = await page.evaluate(f'''(selector) => {{
                const el = document.querySelector(selector);
                return el ? el.innerText : "";
            }}''', selector)
            
            # 檢查文本是否符合預期
            if expected_text in text:
                self.log_message(f"✅ 驗證通過: 找到文字 '{expected_text}'")
                return True
            else:
                error_msg = f"驗證失敗: 未找到文字 '{expected_text}'，實際文字: '{text}'"
                self.log_message(f"❌ {error_msg}")
                raise Exception(error_msg)
        
        except Exception as e:
            if "驗證失敗" not in str(e):
                self.log_message(f"驗證文字時出錯: {str(e)}")
            raise

    async def _verify_url(self, expected_url):
        """驗證當前URL"""
        try:
            page = self.browser_page
            current_url = page.url
            
            # 檢查URL是否符合預期
            if expected_url in current_url:
                self.log_message(f"✅ URL驗證通過: URL包含 '{expected_url}'")
                return True
            else:
                error_msg = f"URL驗證失敗: URL不包含 '{expected_url}'，實際URL: '{current_url}'"
                self.log_message(f"❌ {error_msg}")
                raise Exception(error_msg)
        
        except Exception as e:
            if "驗證失敗" not in str(e):
                self.log_message(f"驗證URL時出錯: {str(e)}")
            raise
            
    async def _open_url(self, url):
        """打開URL"""
        try:
            page = self.browser_page
            self.log_message(f"正在打開: {url}")
            await page.goto(url)
            self.log_message(f"已成功打開: {url}")
        except Exception as e:
            self.log_message(f"打開URL時出錯: {str(e)}")
            
    async def _take_screenshot(self, filename):
        """截圖"""
        try:
            page = self.browser_page
            self.log_message(f"正在截圖: {filename}")
            await page.screenshot(path=filename)
            self.log_message(f"已保存截圖: {filename}")
        except Exception as e:
            self.log_message(f"截圖時出錯: {str(e)}")
