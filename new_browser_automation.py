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
    def __init__(self, script_lines=None, callback=None):
        """初始化瀏覽器自動化
        
        Args:
            script_lines: 腳本行的列表
            callback: 進度回調函數，用於更新UI
        """
        self.script_lines = script_lines or []
        self.callback = callback
        self.browser = None
        self.context = None
        self.page = None
        self.pages = []
        
        # 錄製相關
        self.recording = False
        self.recorder_page = None
        self.recorded_actions = []
        self.is_paused = False
        
    async def start_browser(self, headless=False):
        """啟動瀏覽器
        
        Args:
            headless: 是否使用無頭模式
        """
        self.log("啟動瀏覽器...")
        try:
            playwright = await async_playwright().start()
            self.browser = await getattr(playwright, DEFAULT_BROWSER).launch(headless=headless)
            self.context = await self.browser.new_context(viewport={'width': 1280, 'height': 800})
            self.page = await self.context.new_page()
            self.pages = [self.page]
            
            # 記錄頁面打開時的URL
            await self.page.goto("about:blank")
            
            self.log("瀏覽器已啟動")
            return self.page
        except Exception as e:
            self.log(f"啟動瀏覽器時發生錯誤: {e}")
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
            
    async def execute_script(self, script_text):
        """執行腳本文本
        
        Args:
            script_text: 腳本文本
        """
        self.script_lines = [line.strip() for line in script_text.split('\n') if line.strip() and not line.strip().startswith('#')]
        
        try:
            await self.start_browser(headless=False)
            await self.run_script()
        except Exception as e:
            self.log(f"執行腳本時發生錯誤: {e}")
        finally:
            await self.close_browser()
            
    async def run_script(self):
        """執行腳本行"""
        line_index = 0
        total_lines = len(self.script_lines)
        
        while line_index < total_lines:
            line = self.script_lines[line_index]
            
            # 跳過註釋行
            if line.startswith('#'):
                line_index += 1
                continue
                
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
        
        # 根據指令類型執行對應操作
        if cmd == "OPEN_URL":
            if param.startswith('file://'):
                # 處理本地文件路徑
                file_path = param.replace('file://', '')
                await self.page.goto(f"file://{file_path}")
                self.log(f"已打開本地文件: {file_path}")
            else:
                await self.page.goto(param)
                self.log(f"已打開URL: {param}")
            
        elif cmd == "CLICK_BY":
            await self.page.click(param)
            self.log(f"已點擊: {param}")
            
        elif cmd == "ASSERT_TEXT":
            content = await self.page.content()
            if param not in content:
                raise AssertionError(f"文字驗證失敗: 未找到 '{param}'")
            self.log(f"文字驗證通過: {param}")
            
        elif cmd == "WAIT":
            seconds = int(param)
            self.log(f"等待 {seconds} 秒")
            await asyncio.sleep(seconds)
            
        elif cmd == "WAIT_FOR_TEXT":
            try:
                await self.page.wait_for_function(
                    f"document.body.innerText.includes('{param}')",
                    timeout=DEFAULT_TIMEOUT
                )
                self.log(f"已等到文字: {param}")
            except PlaywrightTimeoutError:
                raise TimeoutError(f"等待文字超時: {param}")
    
    # 錄製相關方法
    async def start_recording(self, start_url="about:blank"):
        """開始錄製瀏覽器操作
        
        Args:
            start_url: 開始錄製時打開的URL
        """
        if self.recording:
            self.log("已經在錄製中")
            return
        
        try:
            # 如果瀏覽器未啟動，則啟動瀏覽器
            if not self.browser:
                await self.start_browser(headless=False)
            
            self.recorder_page = self.page
            self.recording = True
            self.is_paused = False
            self.recorded_actions = []
            
            # 設置事件監聽器以捕獲用戶操作
            await self.setup_recording_events()
            
            # 打開起始URL
            if start_url != "about:blank":
                await self.recorder_page.goto(start_url)
                self.record_action(f"OPEN_URL = {start_url}")
            
            self.log("錄製已開始，請在瀏覽器中進行操作")
            
        except Exception as e:
            self.log(f"開始錄製時發生錯誤: {e}")
            self.recording = False
            raise
    
    async def setup_recording_events(self):
        """設置錄製事件監聽器"""
        page = self.recorder_page
        
        # 監聽頁面導航
        page.on("framenavigated", self.on_frame_navigated)
        
        # 監聽點擊事件
        await page.evaluate("""
        () => {
            window.addEventListener('click', (event) => {
                const target = event.target;
                let selector = '';
                
                // 嘗試使用ID
                if (target.id) {
                    selector = `#${target.id}`;
                    window.reportClick(selector);
                    return;
                }
                
                // 嘗試使用類名
                if (target.className && typeof target.className === 'string') {
                    const classes = target.className.split(' ').filter(c => c);
                    if (classes.length > 0) {
                        selector = `.${classes.join('.')}`;
                        window.reportClick(selector);
                        return;
                    }
                }
                
                // 嘗試使用標籤名稱和文本內容
                if (target.textContent && target.textContent.trim()) {
                    const text = target.textContent.trim();
                    if (text.length < 50) {  // 避免選擇太長的文本
                        selector = `text=${text}`;
                        window.reportClick(selector);
                        return;
                    }
                }
                
                // 回退到 CSS 路徑
                let path = [];
                let element = target;
                while (element && element.nodeType === Node.ELEMENT_NODE) {
                    let selector = element.tagName.toLowerCase();
                    if (element.id) {
                        selector = `#${element.id}`;
                        path.unshift(selector);
                        break;
                    }
                    
                    let sibling = element;
                    let nth = 1;
                    while (sibling = sibling.previousElementSibling) {
                        if (sibling.tagName === element.tagName) nth++;
                    }
                    
                    if (nth > 1) selector += `:nth-child(${nth})`;
                    path.unshift(selector);
                    element = element.parentNode;
                }
                
                window.reportClick(path.join(' > '));
            });
        }
        """)
        
        # 添加回調函數以報告點擊
        await page.expose_function("reportClick", self.on_click_reported)
        
        # 監聽表單輸入
        await page.evaluate("""
        () => {
            const inputs = document.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                input.addEventListener('change', (event) => {
                    const target = event.target;
                    let selector = '';
                    
                    if (target.id) {
                        selector = `#${target.id}`;
                    } else if (target.name) {
                        selector = `[name="${target.name}"]`;
                    } else {
                        // 回退到標籤和索引
                        const elements = document.querySelectorAll(target.tagName);
                        for (let i = 0; i < elements.length; i++) {
                            if (elements[i] === target) {
                                selector = `${target.tagName.toLowerCase()}:nth-child(${i+1})`;
                                break;
                            }
                        }
                    }
                    
                    if (selector) {
                        let value = '';
                        if (target.type === 'checkbox' || target.type === 'radio') {
                            value = target.checked ? 'true' : 'false';
                        } else {
                            value = target.value;
                        }
                        
                        window.reportInput(selector, value);
                    }
                });
            });
        }
        """)
        
        # 添加回調函數以報告輸入
        await page.expose_function("reportInput", self.on_input_reported)
    
    def on_frame_navigated(self, frame):
        """頁面導航事件處理"""
        if frame.is_main_frame() and not self.is_paused and self.recording:
            url = frame.url
            if url != "about:blank":
                self.record_action(f"OPEN_URL = {url}")
    
    def on_click_reported(self, selector):
        """點擊事件處理"""
        if not self.is_paused and self.recording:
            self.record_action(f"CLICK_BY = {selector}")
    
    def on_input_reported(self, selector, value):
        """輸入事件處理"""
        if not self.is_paused and self.recording:
            self.record_action(f"FILL = {selector} || {value}")
    
    def record_action(self, action):
        """記錄一個操作"""
        self.recorded_actions.append(action)
        self.log(f"錄製: {action}")
        
        # 通知UI更新
        if self.callback:
            self.callback(0, f"錄製: {action}")
    
    def pause_recording(self):
        """暫停錄製"""
        if self.recording:
            self.is_paused = True
            self.log("錄製已暫停")
    
    def resume_recording(self):
        """繼續錄製"""
        if self.recording:
            self.is_paused = False
            self.log("錄製已繼續")
    
    async def stop_recording(self):
        """停止錄製"""
        if not self.recording:
            return []
        
        self.recording = False
        self.is_paused = False
        
        self.log(f"錄製已停止，共記錄了 {len(self.recorded_actions)} 個操作")
        
        # 返回記錄的操作列表
        return self.recorded_actions
    
    def log(self, message):
        """記錄日誌
        
        Args:
            message: 日誌消息
        """
        log_message = f"[{datetime.now().strftime('%H:%M:%S')}] {message}"
        print(log_message)
        
        if self.callback:
            self.callback(0, message)
