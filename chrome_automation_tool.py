# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import os
import sys
import time
import threading
import logging
from typing import List, Optional, Tuple, Dict, Any, Union, Callable
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# 常量定義
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
STEP_WINDOW_WIDTH = 250
STEP_WINDOW_HEIGHT = 500
DEFAULT_WAIT_TIME = 5
LOG_FILE = "log.txt"
COMMAND_FILE = "command.txt"

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

class StepWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk) -> None:
        super().__init__(parent)
        self.title("執行步驟")
        
        # 設定視窗大小和位置（靠右側中間）
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_position = screen_width - STEP_WINDOW_WIDTH - 20  # 距離右邊 20 像素
        y_position = (screen_height - STEP_WINDOW_HEIGHT) // 2  # 垂直置中
        self.geometry(f"{STEP_WINDOW_WIDTH}x{STEP_WINDOW_HEIGHT}+{x_position}+{y_position}")
        
        # 設定視窗樣式
        self.attributes("-topmost", True)  # 保持在最上層
        self.protocol("WM_DELETE_WINDOW", lambda: None)  # 禁用關閉按鈕
        
        # 建立標題列框架
        title_frame = ttk.Frame(self)
        title_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # 標題
        title_label = ttk.Label(title_frame, text="執行步驟", font=("微軟正黑體", 10, "bold"))
        title_label.pack(side=tk.LEFT, padx=5)
        
        # 最小化按鈕
        minimize_button = ttk.Button(title_frame, text="─", width=2, command=self.iconify)
        minimize_button.pack(side=tk.RIGHT, padx=2)
        
        # 建立主要內容框架（可滾動）
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 建立Canvas和Scrollbar
        self.canvas = tk.Canvas(self.main_frame)
        self.scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", 
                                      command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        # 設定Canvas的滾動區域
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # 在Canvas中創建視窗
        self.canvas_frame = self.canvas.create_window((0, 0), 
                                                    window=self.scrollable_frame, 
                                                    anchor="nw")
        
        # 配置Canvas和Scrollbar
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 設定樣式
        style = ttk.Style()
        style.configure("Current.TLabel", 
                       foreground="blue", 
                       font=("微軟正黑體", 10, "bold"))
        style.configure("Done.TLabel", 
                       foreground="green", 
                       font=("微軟正黑體", 10))
        style.configure("Pending.TLabel", 
                       foreground="gray", 
                       font=("微軟正黑體", 10))
        
        # 初始化步驟列表
        self.steps: List[str] = []
        self.current_step: int = -1
        self.step_labels: List[ttk.Label] = []
        
        # 加入拖曳功能
        self.bind('<Button-1>', self.start_move)
        self.bind('<B1-Motion>', self.on_move)
        
        # 加入滾輪滾動功能
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # 拖曳變數
        self.x: int = 0
        self.y: int = 0
    
    def _on_mousewheel(self, event: tk.Event) -> None:
        """處理滾輪事件"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def set_steps(self, steps: List[str]) -> None:
        """設定步驟列表"""
        self.steps = steps
        self.current_step = -1
        self.update_steps()
    
    def update_steps(self) -> None:
        """更新步驟顯示"""
        # 清除現有的標籤
        for label in self.step_labels:
            label.destroy()
        self.step_labels.clear()
        
        # 重新創建所有步驟標籤
        for i, step in enumerate(self.steps):
            if i < self.current_step:
                style = "Done.TLabel"
                prefix = "✓ "
            elif i == self.current_step:
                style = "Current.TLabel"
                prefix = "➤ "
            else:
                style = "Pending.TLabel"
                prefix = "○ "
            
            label = ttk.Label(self.scrollable_frame, 
                            text=f"{prefix}{step}", 
                            style=style,
                            wraplength=200)  # 允許文字換行
            label.pack(pady=2, padx=5, anchor="w")
            self.step_labels.append(label)
        
        # 更新滾動區域
        self.scrollable_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        # 如果是當前步驟，確保它可見
        if self.current_step >= 0 and self.scrollable_frame.winfo_height() > 0:
            self.canvas.yview_moveto(
                (self.current_step * 30) / max(1, self.scrollable_frame.winfo_height())
            )
    
    def set_current_step(self, step_index: int) -> None:
        """設定當前步驟"""
        if 0 <= step_index < len(self.steps):
            self.current_step = step_index
            self.update_steps()
    
    def add_step(self, step_text: str) -> int:
        """新增步驟"""
        self.steps.append(step_text)
        self.update_steps()
        return len(self.steps) - 1  # 返回新步驟的索引
    
    def start_move(self, event: tk.Event) -> None:
        """開始拖曳視窗"""
        self.x = event.x
        self.y = event.y

    def on_move(self, event: tk.Event) -> None:
        """處理視窗拖曳"""
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")

class SimpleChromeAutomation:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("簡易 Chrome 自動化工具")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        
        # 設定變數
        self.driver: Optional[webdriver.Chrome] = None
        self.is_running: bool = False
        self.current_task: Optional[threading.Thread] = None
        self.step_window: Optional[StepWindow] = None
        self.chromedriver_path: Optional[str] = None
        self.keywords: List[str] = []
        
        # 建立 UI
        self.create_ui()
        
        # 自動尋找 chromedriver.exe
        self.find_chromedriver()
        
    def create_ui(self) -> None:
        """建立簡化的使用者介面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ChromeDriver 狀態
        driver_frame = ttk.LabelFrame(main_frame, text="ChromeDriver 狀態", padding="10")
        driver_frame.pack(fill=tk.X, pady=5)
        
        self.driver_status = tk.StringVar(value="尋找中...")
        ttk.Label(driver_frame, textvariable=self.driver_status).pack(side=tk.LEFT)
        
        # 操作按鈕
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        self.start_button = ttk.Button(buttons_frame, text="開始自動化測試", command=self.start_automation)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(buttons_frame, text="停止", command=self.stop_automation, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(buttons_frame, text="清除日誌", command=lambda: self.log_text.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=5)
        
        # 日誌區塊
        log_frame = ttk.LabelFrame(main_frame, text="執行日誌", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 目前執行的命令
        self.current_action = tk.StringVar(value="")
        current_frame = ttk.Frame(main_frame)
        current_frame.pack(fill=tk.X, pady=5)
        ttk.Label(current_frame, text="目前執行:").pack(side=tk.LEFT)
        ttk.Label(current_frame, textvariable=self.current_action).pack(side=tk.LEFT, padx=5)
        
        # 狀態列
        self.status = tk.StringVar(value="就緒")
        status_bar = ttk.Label(self.root, textvariable=self.status, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 顯示初始說明
        self.add_log("歡迎使用簡易 Chrome 自動化工具")
        self.add_log("此工具將自動操作本地 HTML 頁面，展示自動化功能")
    
    def show_step_window(self) -> None:
        """顯示步驟視窗"""
        if not self.step_window:
            self.step_window = StepWindow(self.root)
        else:
            self.step_window.deiconify()  # 如果已經存在，則重新顯示
            self.step_window.lift()  # 將視窗提升到最上層
    
    def update_step(self, step_index: int) -> None:
        """更新當前步驟"""
        if self.step_window:
            self.step_window.set_current_step(step_index)
    
    def add_step(self, step_text: str) -> int:
        """新增步驟"""
        if self.step_window:
            return self.step_window.add_step(step_text)
        return -1
    
    def initialize_steps(self) -> None:
        """初始化步驟列表"""
        # 顯示步驟視窗
        self.show_step_window()
        
        # 讀取關鍵字
        self.load_keywords_from_command()
        
        # 基本步驟
        basic_steps = [
            "初始化 Chrome WebDriver",
            "打開本地 HTML 頁面",
            "登入表單測試",
            "資料管理測試",
            "搜尋功能測試",
            "互動按鈕測試"
        ]
        
        # 關鍵字搜尋步驟
        keyword_steps = []
        for keyword in self.keywords:
            keyword_steps.append(f"搜尋關鍵字: {keyword}")
        
        # 合併所有步驟
        all_steps = basic_steps + keyword_steps + ["測試完成"]
        
        # 設定步驟列表
        if self.step_window:
            self.step_window.set_steps(all_steps)
    
    def load_keywords_from_command(self) -> None:
        """從 command.txt 讀取關鍵字"""
        self.keywords = []
        try:
            if os.path.exists(COMMAND_FILE):
                with open(COMMAND_FILE, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        # 跳過空行、註解行和指令行
                        if (not line or line.startswith("#") or 
                            "=" in line or "||" in line):
                            continue
                        self.keywords.append(line)
                
                self.add_log(f"已載入 {len(self.keywords)} 個關鍵字")
            else:
                self.add_log(f"找不到 {COMMAND_FILE} 檔案")
        except Exception as e:
            self.add_log(f"讀取關鍵字時發生錯誤: {str(e)}")
    
    def find_chromedriver(self) -> None:
        """尋找 chromedriver.exe"""
        # 檢查當前目錄
        chromedriver_path = os.path.join(os.getcwd(), "chromedriver.exe")
        if os.path.exists(chromedriver_path):
            self.chromedriver_path = chromedriver_path
            self.driver_status.set(f"已找到 ChromeDriver: {os.path.basename(chromedriver_path)}")
            self.add_log(f"已找到 ChromeDriver: {chromedriver_path}")
            return
        
        # 如果找不到，顯示錯誤訊息
        self.driver_status.set("未找到 chromedriver.exe")
        self.add_log("錯誤: 未找到 chromedriver.exe，請確保它與程式在同一目錄")
        messagebox.showerror("錯誤", "未找到 chromedriver.exe，請確保它與程式在同一目錄")
    
    def add_log(self, message: str) -> None:
        """新增日誌訊息"""
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        # 顯示在 UI 上
        self.log_text.insert(tk.END, f"{log_message}\n")
        self.log_text.see(tk.END)
        
        # 更新 UI
        self.root.update_idletasks()
        
        # 寫入日誌檔
        logging.info(message)
    
    def start_automation(self) -> None:
        """開始自動化測試"""
        if self.is_running:
            return
        
        # 更新 UI 狀態
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.is_running = True
        self.status.set("執行中...")
        
        # 初始化步驟
        self.initialize_steps()
        
        # 啟動執行緒
        self.current_task = threading.Thread(target=self.run_automation)
        self.current_task.daemon = True
        self.current_task.start()
    
    def stop_automation(self) -> None:
        """停止自動化測試"""
        self.is_running = False
        self.status.set("停止中...")
        self.add_log("正在停止自動化測試...")
    
    def search_keywords(self, keyword: str) -> bool:
        """搜尋關鍵字"""
        try:
            # 尋找自訂文字區域
            custom_text_element = self.driver.find_element(By.ID, "customText")
            
            # 獲取文字內容
            text_content = custom_text_element.text
            
            # 檢查關鍵字是否存在
            if keyword in text_content:
                # 使用 JavaScript 高亮顯示關鍵字
                script = """
                var element = arguments[0];
                var keyword = arguments[1];
                var text = element.innerHTML;
                
                // 移除之前的高亮
                text = text.replace(/<span class="highlight">(.*?)<\/span>/g, '$1');
                
                // 高亮新的關鍵字
                var regex = new RegExp(keyword, 'g');
                var newText = text.replace(regex, '<span class="highlight">$&</span>');
                
                element.innerHTML = newText;
                
                // 滾動到第一個高亮處
                var highlightElement = element.querySelector('.highlight');
                if (highlightElement) {
                    highlightElement.scrollIntoView({behavior: "smooth", block: "center"});
                    return true;
                }
                return false;
                """
                result = self.driver.execute_script(script, custom_text_element, keyword)
                
                if result:
                    self.add_log(f"找到關鍵字: {keyword}")
                    return True
                else:
                    self.add_log(f"找到關鍵字但無法高亮顯示: {keyword}")
                    return True
            else:
                self.add_log(f"未找到關鍵字: {keyword}")
                return False
                
        except NoSuchElementException:
            self.add_log(f"錯誤: 找不到自訂文字區域，無法搜尋關鍵字: {keyword}")
            return False
        except WebDriverException as e:
            self.add_log(f"搜尋關鍵字時發生錯誤: {str(e)}")
            return False
        except Exception as e:
            self.add_log(f"搜尋關鍵字時發生未知錯誤: {str(e)}")
            return False
    
    def run_automation(self) -> None:
        """執行自動化測試"""
        try:
            # 步驟 1: 初始化 WebDriver
            self.update_action("初始化 Chrome WebDriver")
            self.update_step(0)
            
            if not self.chromedriver_path or not os.path.exists(self.chromedriver_path):
                self.add_log("錯誤: 未找到 chromedriver.exe")
                messagebox.showerror("錯誤", "未找到 chromedriver.exe，請確保它與程式在同一目錄")
                self.reset_ui()
                return
            
            # 初始化 WebDriver
            options = webdriver.ChromeOptions()
            options.add_argument("--start-maximized")
            options.add_argument("--disable-notifications")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            
            try:
                service = Service(executable_path=self.chromedriver_path)
                self.driver = webdriver.Chrome(service=service, options=options)
                self.add_log("Chrome WebDriver 初始化成功")
            except WebDriverException as e:
                self.add_log(f"初始化 Chrome WebDriver 失敗: {str(e)}")
                messagebox.showerror("錯誤", f"初始化 Chrome WebDriver 失敗: {str(e)}")
                self.reset_ui()
                return
            
            # 設定等待時間
            wait = WebDriverWait(self.driver, DEFAULT_WAIT_TIME)
            
            # 讀取命令檔案
            commands = self.read_commands()
            if not commands:
                self.add_log("警告: 命令檔案為空或不存在")
            
            # 步驟 2: 打開本地 HTML 頁面
            self.update_action("打開本地 HTML 頁面")
            self.update_step(1)
            
            # 從命令中獲取 URL
            url_path = "web/index.html"  # 預設值
            for cmd, params in commands:
                if cmd == "OPEN_URL":
                    url_path = params[0]
                    break
            
            # 確保 URL 路徑存在
            html_path = os.path.abspath(url_path)
            if not os.path.exists(html_path):
                self.add_log(f"錯誤: 找不到 HTML 檔案: {html_path}")
                messagebox.showerror("錯誤", f"找不到 HTML 檔案: {html_path}")
                self.reset_ui()
                return
            
            # 打開 HTML 頁面
            file_url = f"file:///{html_path.replace(os.sep, '/')}"
            self.driver.get(file_url)
            self.add_log(f"已打開頁面: {file_url}")
            
            # 等待頁面載入
            try:
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                time.sleep(1)  # 額外等待確保頁面完全載入
            except TimeoutException:
                self.add_log("警告: 頁面載入超時")
            
            # 步驟 3: 登入表單測試
            self.update_step(2)
            self.update_action("登入表單測試")
            self.add_log("測試登入表單")
            
            # 步驟 4: 資料管理測試
            self.update_step(3)
            self.update_action("資料管理測試")
            self.add_log("測試資料管理功能")
            
            # 步驟 5: 搜尋功能測試
            self.update_step(4)
            self.update_action("搜尋功能測試")
            self.add_log("測試搜尋功能")
            
            # 步驟 6: 互動按鈕測試
            self.update_step(5)
            self.update_action("互動按鈕測試")
            self.add_log("測試互動按鈕")
            
            # 步驟 7: 搜尋關鍵字
            base_step_index = 6  # 關鍵字搜尋的起始步驟索引
            
            # 搜尋每個關鍵字
            for i, keyword in enumerate(self.keywords):
                if not self.is_running:
                    self.add_log("使用者停止了自動化測試")
                    break
                
                step_index = base_step_index + i
                self.update_step(step_index)
                self.update_action(f"搜尋關鍵字: {keyword}")
                
                try:
                    found = self.search_keywords(keyword)
                    if found:
                        self.add_log(f"✓ 找到關鍵字: {keyword}")
                    else:
                        self.add_log(f"✗ 未找到關鍵字: {keyword}")
                    
                    # 給使用者時間觀察結果
                    time.sleep(2)
                except Exception as e:
                    self.add_log(f"搜尋關鍵字 '{keyword}' 時發生錯誤: {str(e)}")
            
            # 完成測試
            final_step = base_step_index + len(self.keywords)
            self.update_step(final_step)
            self.update_action("測試完成")
            self.add_log("自動化測試完成！")
            
        except Exception as e:
            self.add_log(f"執行過程中發生錯誤: {str(e)}")
            import traceback
            self.add_log(traceback.format_exc())
        
        finally:
            # 關閉 WebDriver
            if self.driver:
                try:
                    time.sleep(3)  # 給使用者時間觀察結果
                    self.driver.quit()
                except Exception:
                    pass
                self.driver = None
            
            # 重置 UI 狀態
            self.reset_ui()
            self.status.set("就緒")
    
    def update_action(self, action: str) -> None:
        """更新目前執行的動作"""
        self.current_action.set(action)
        self.status.set(f"執行中: {action}")
        self.root.update_idletasks()

    def reset_ui(self) -> None:
        """重置 UI 狀態"""
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.is_running = False
        self.status.set("就緒")
        
        # 關閉 WebDriver
        if self.driver:
            try:
                self.driver.quit()
            except WebDriverException:
                pass
            finally:
                self.driver = None
    
    def read_commands(self) -> List[Tuple[str, List[str]]]:
        """讀取命令檔案"""
        commands = []
        try:
            if os.path.exists(COMMAND_FILE):
                with open(COMMAND_FILE, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        
                        if "=" in line:
                            cmd, params_str = line.split("=", 1)
                            cmd = cmd.strip()
                            params = [p.strip() for p in params_str.split("||")]
                            commands.append((cmd, params))
                
                self.add_log(f"已載入 {len(commands)} 個命令")
            else:
                self.add_log(f"找不到 {COMMAND_FILE} 檔案")
        except Exception as e:
            self.add_log(f"讀取命令檔案時發生錯誤: {str(e)}")
        
        return commands

def main() -> None:
    # 建立主視窗
    root = tk.Tk()
    root.title("Chrome 自動化工具")
    
    # 設定圖示
    icon_path = "icon.ico"
    if os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
        except Exception:
            pass
    
    # 創建應用程式
    app = SimpleChromeAutomation(root)
    
    # 設定關閉視窗事件處理
    def on_closing() -> None:
        if app.is_running:
            if messagebox.askokcancel("確認", "程式正在執行中，確定要關閉嗎？"):
                app.stop_automation()
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # 啟動主循環
    root.mainloop()

if __name__ == "__main__":
    main()
