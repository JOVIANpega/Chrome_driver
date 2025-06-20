# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import os
import sys
import time
import threading
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("log.txt", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

class StepWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("執行步驟")
        
        # 設定視窗大小和位置（靠右側中間）
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = 250
        window_height = 500
        x_position = screen_width - window_width - 20  # 距離右邊 20 像素
        y_position = (screen_height - window_height) // 2  # 垂直置中
        self.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        
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
        self.steps = []
        self.current_step = -1
        self.step_labels = []
        
        # 加入拖曳功能
        self.bind('<Button-1>', self.start_move)
        self.bind('<B1-Motion>', self.on_move)
        
        # 加入滾輪滾動功能
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
    
    def _on_mousewheel(self, event):
        """處理滾輪事件"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def set_steps(self, steps):
        """設定步驟列表"""
        self.steps = steps
        self.current_step = -1
        self.update_steps()
    
    def update_steps(self):
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
    
    def set_current_step(self, step_index):
        """設定當前步驟"""
        if 0 <= step_index < len(self.steps):
            self.current_step = step_index
            self.update_steps()
    
    def add_step(self, step_text):
        """新增步驟"""
        self.steps.append(step_text)
        self.update_steps()
        return len(self.steps) - 1  # 返回新步驟的索引
    
    def start_move(self, event):
        """開始拖曳視窗"""
        self.x = event.x
        self.y = event.y

    def on_move(self, event):
        """處理視窗拖曳"""
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")

class SimpleChromeAutomation:
    def __init__(self, root):
        self.root = root
        self.root.title("簡易 Chrome 自動化工具")
        self.root.geometry("800x600")
        
        # 設定變數
        self.driver = None
        self.is_running = False
        self.current_task = None
        self.step_window = None
        
        # 建立 UI
        self.create_ui()
        
        # 自動尋找 chromedriver.exe
        self.find_chromedriver()
        
    def create_ui(self):
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
    
    def show_step_window(self):
        """顯示步驟視窗"""
        if not self.step_window:
            self.step_window = StepWindow(self.root)
        else:
            self.step_window.deiconify()  # 如果已經存在，則重新顯示
            self.step_window.lift()  # 將視窗提升到最上層
    
    def update_step(self, step_index):
        """更新步驟視窗的當前步驟"""
        if self.step_window and self.step_window.winfo_exists():
            self.step_window.set_current_step(step_index)
    
    def add_step(self, step_text):
        """新增步驟到步驟視窗"""
        if self.step_window and self.step_window.winfo_exists():
            return self.step_window.add_step(step_text)
        return -1
    
    def initialize_steps(self):
        """初始化步驟清單"""
        if not self.step_window:
            return
            
        # 基本步驟
        basic_steps = [
            "準備開始自動化測試",
            "打開本地 HTML 頁面",
            "填寫登入表單",
            "輸入使用者名稱",
            "輸入密碼",
            "點擊登入按鈕",
            "新增項目",
            "輸入項目名稱",
            "輸入價格",
            "點擊新增按鈕",
            "搜尋功能測試",
            "輸入搜尋文字",
            "點擊搜尋按鈕",
            "互動按鈕測試",
            "點擊顯示訊息按鈕",
            "點擊改變顏色按鈕",
            "點擊計數按鈕",
            "刪除項目"
        ]
        
        # 讀取 command.txt 尋找關鍵字
        keywords = self.load_keywords_from_command()
        
        # 設定步驟清單
        steps = basic_steps.copy()
        
        # 添加關鍵字搜尋步驟
        for keyword in keywords:
            steps.append(f"搜尋關鍵字：{keyword}")
        
        # 添加完成步驟
        steps.append("完成測試")
        
        # 設定步驟視窗
        self.step_window.set_steps(steps)
        
        return steps
    
    def load_keywords_from_command(self):
        """從 command.txt 讀取關鍵字"""
        keywords = []
        command_file = "command.txt"
        
        if os.path.exists(command_file):
            try:
                with open(command_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    
                # 尋找不是指令的行，可能是關鍵字
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" not in line:
                        keywords.append(line)
                        
                self.add_log(f"從 command.txt 讀取到 {len(keywords)} 個關鍵字")
            except Exception as e:
                self.add_log(f"讀取 command.txt 時發生錯誤: {str(e)}")
        
        # 如果沒有找到關鍵字，使用預設值
        if not keywords:
            keywords = ["挪威國家廣播公司", "台灣的戰貓", "記者洛特", "需要有8條命才能存活", "有違挪威的一中政策"]
            self.add_log("使用預設關鍵字")
            
        return keywords
    
    def find_chromedriver(self):
        """尋找 ChromeDriver"""
        # 可能的位置
        locations = [
            "chromedriver.exe",  # 當前目錄
            os.path.join(os.path.dirname(sys.executable), "chromedriver.exe"),  # 執行檔目錄
            os.path.join(os.getcwd(), "chromedriver.exe"),  # 工作目錄
        ]
        
        for location in locations:
            if os.path.exists(location):
                self.driver_path = location
                self.driver_status.set(f"已找到: {location}")
                self.add_log(f"已找到 ChromeDriver: {location}")
                return
        
        self.driver_status.set("未找到 ChromeDriver")
        self.add_log("警告: 未找到 ChromeDriver，請確保 chromedriver.exe 與程式在同一目錄")
    
    def add_log(self, message):
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
    
    def start_automation(self):
        """開始自動化測試"""
        if hasattr(self, 'driver_path') and os.path.exists(self.driver_path):
            # 更新 UI 狀態
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.is_running = True
            
            # 顯示步驟視窗
            self.show_step_window()
            
            # 初始化步驟清單
            self.initialize_steps()
            
            # 啟動執行緒
            self.current_task = threading.Thread(target=self.run_automation)
            self.current_task.daemon = True
            self.current_task.start()
        else:
            messagebox.showerror("錯誤", "未找到 ChromeDriver，請確保 chromedriver.exe 與程式在同一目錄")
    
    def stop_automation(self):
        """停止自動化測試"""
        self.is_running = False
        self.add_log("正在停止執行...")
        self.status.set("正在停止...")
    
    def search_keywords(self, keyword):
        """在頁面中搜尋關鍵字"""
        self.update_action(f"搜尋關鍵字: {keyword}")
        self.add_log(f"搜尋關鍵字: {keyword}")
        
        try:
            # 先清除之前的高亮
            try:
                self.driver.execute_script("""
                try {
                    var elements = document.querySelectorAll('*');
                    for (var i = 0; i < elements.length; i++) {
                        var element = elements[i];
                        if (element.style && element.style.backgroundColor === 'yellow') {
                            element.style.backgroundColor = '';
                        }
                    }
                    
                    // 移除可能存在的提示元素
                    var indicators = ['search-indicator', 'search-result', 'search-not-found'];
                    for (var i = 0; i < indicators.length; i++) {
                        var elem = document.getElementById(indicators[i]);
                        if (elem && elem.parentNode) {
                            elem.parentNode.removeChild(elem);
                        }
                    }
                } catch (e) {
                    console.error('清除高亮時發生錯誤:', e);
                }
                """)
            except Exception as e:
                self.add_log(f"清除高亮時發生錯誤: {str(e)}")
            
            # 顯示搜尋動畫 - 使用更簡單的方式
            try:
                self.driver.execute_script("""
                try {
                    var div = document.createElement('div');
                    div.id = 'search-indicator';
                    div.style.position = 'fixed';
                    div.style.top = '10px';
                    div.style.right = '10px';
                    div.style.backgroundColor = 'blue';
                    div.style.color = 'white';
                    div.style.padding = '10px';
                    div.style.zIndex = '9999';
                    div.textContent = '正在搜尋...';
                    document.body.appendChild(div);
                } catch (e) {
                    console.error('創建搜尋提示時發生錯誤:', e);
                }
                """)
            except Exception as e:
                self.add_log(f"創建搜尋提示時發生錯誤: {str(e)}")
            
            # 等待一下讓用戶看到搜尋動畫
            time.sleep(0.5)
            
            # 使用更簡單的 JavaScript 在頁面中搜尋關鍵字
            found = False
            try:
                result = self.driver.execute_script(f"""
                try {{
                    // 移除搜尋提示
                    var indicator = document.getElementById('search-indicator');
                    if (indicator && indicator.parentNode) {{
                        indicator.parentNode.removeChild(indicator);
                    }}
                    
                    var found = false;
                    var elements = document.getElementsByTagName('*');
                    
                    for (var i = 0; i < elements.length; i++) {{
                        var element = elements[i];
                        if (element.innerText && element.innerText.indexOf('{keyword}') !== -1) {{
                            found = true;
                            element.scrollIntoView(true);
                            element.style.backgroundColor = 'yellow';
                            break;
                        }}
                    }}
                    
                    // 創建結果提示
                    var resultDiv = document.createElement('div');
                    resultDiv.id = found ? 'search-result' : 'search-not-found';
                    resultDiv.style.position = 'fixed';
                    resultDiv.style.top = '10px';
                    resultDiv.style.right = '10px';
                    resultDiv.style.backgroundColor = found ? 'green' : 'red';
                    resultDiv.style.color = 'white';
                    resultDiv.style.padding = '10px';
                    resultDiv.style.zIndex = '9999';
                    resultDiv.textContent = found ? '找到關鍵字' : '未找到關鍵字';
                    document.body.appendChild(resultDiv);
                    
                    return found;
                }} catch (e) {{
                    console.error('搜尋關鍵字時發生錯誤:', e);
                    return false;
                }}
                """)
                
                found = bool(result)
            except Exception as e:
                self.add_log(f"執行搜尋腳本時發生錯誤: {str(e)}")
                found = False
            
            if found:
                self.add_log(f"✓ 找到關鍵字: {keyword}")
            else:
                self.add_log(f"✗ 未找到關鍵字: {keyword}")
            
            return found
            
        except Exception as e:
            self.add_log(f"搜尋關鍵字時發生錯誤: {str(e)}")
            return False
    
    def run_automation(self):
        """執行自動化測試"""
        self.status.set("執行中...")
        self.add_log("開始自動化測試")
        
        # 重置步驟視窗
        if self.step_window:
            self.step_window.current_step = 0
            self.step_window.update_steps()
        
        try:
            # 初始化 WebDriver
            self.update_step(0)
            self.add_log("初始化 Chrome WebDriver...")
            
            options = webdriver.ChromeOptions()
            options.add_argument("--start-maximized")
            options.add_argument("--disable-notifications")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            
            service = Service(executable_path=self.driver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
            self.add_log("Chrome WebDriver 初始化成功")
            
            # 設定等待時間
            wait = WebDriverWait(self.driver, 5)
            
            # 步驟 1: 打開本地 HTML 頁面
            self.update_step(1)
            self.update_action("打開本地 HTML 頁面")
            html_path = os.path.abspath("web/index.html")
            html_path = html_path.replace('\\', '/')  # 先轉換路徑
            file_url = f"file:///{html_path}"
            self.add_log(f"打開頁面: {file_url}")
            self.driver.get(file_url)
            time.sleep(1)
            
            # 步驟 2: 填寫登入表單
            self.update_step(2)
            self.update_action("填寫登入表單")
            self.add_log("填寫使用者名稱和密碼")
            
            # 點擊使用者名稱輸入框
            self.update_step(3)
            username_input = wait.until(EC.presence_of_element_located((By.ID, "username")))
            username_input.click()
            username_input.clear()
            username_input.send_keys("測試使用者")
            
            # 點擊密碼輸入框
            self.update_step(4)
            password_input = wait.until(EC.presence_of_element_located((By.ID, "password")))
            password_input.click()
            password_input.clear()
            password_input.send_keys("密碼123")
            
            # 點擊登入按鈕
            self.update_step(5)
            self.add_log("點擊登入按鈕")
            login_button = wait.until(EC.presence_of_element_located((By.ID, "login-button")))
            login_button.click()
            time.sleep(1)
            
            # 步驟 3: 新增項目
            self.update_step(6)
            self.update_action("新增項目")
            self.add_log("填寫項目資訊")
            
            # 點擊項目名稱輸入框
            self.update_step(7)
            name_input = wait.until(EC.presence_of_element_located((By.ID, "item-name")))
            name_input.click()
            name_input.clear()
            name_input.send_keys("筆記型電腦")
            
            # 點擊價格輸入框
            self.update_step(8)
            price_input = wait.until(EC.presence_of_element_located((By.ID, "item-price")))
            price_input.click()
            price_input.clear()
            price_input.send_keys("25000")
            
            # 點擊新增項目按鈕
            self.update_step(9)
            self.add_log("點擊新增項目按鈕")
            add_button = wait.until(EC.presence_of_element_located((By.ID, "add-item")))
            add_button.click()
            time.sleep(1)
            
            # 步驟 4: 搜尋功能測試
            self.update_step(10)
            self.update_action("搜尋功能測試")
            self.add_log("測試搜尋功能")
            
            # 點擊搜尋輸入框
            self.update_step(11)
            search_input = wait.until(EC.presence_of_element_located((By.ID, "search-text")))
            search_input.click()
            search_input.clear()
            search_input.send_keys("筆記型電腦")
            
            # 點擊搜尋按鈕
            self.update_step(12)
            search_button = wait.until(EC.presence_of_element_located((By.ID, "search-button")))
            search_button.click()
            time.sleep(1)
            
            # 步驟 5: 互動按鈕測試
            self.update_step(13)
            self.update_action("互動按鈕測試")
            self.add_log("測試互動按鈕")
            
            # 點擊顯示訊息按鈕
            self.update_step(14)
            message_button = wait.until(EC.presence_of_element_located((By.ID, "show-message")))
            message_button.click()
            time.sleep(1)
            
            # 點擊改變顏色按鈕
            self.update_step(15)
            color_button = wait.until(EC.presence_of_element_located((By.ID, "change-color")))
            color_button.click()
            time.sleep(1)
            
            # 點擊計數按鈕
            self.update_step(16)
            count_button = wait.until(EC.presence_of_element_located((By.ID, "count-button")))
            count_button.click()
            time.sleep(1)
            
            # 步驟 6: 刪除項目
            self.update_step(17)
            self.update_action("刪除項目")
            self.add_log("刪除項目")
            
            # 點擊刪除按鈕
            delete_button = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "delete-item")))
            delete_button.click()
            time.sleep(1)
            
            # 步驟 7: 執行關鍵字搜尋
            self.update_action("執行關鍵字搜尋")
            self.add_log("執行關鍵字搜尋")
            
            # 搜尋關鍵字
            keywords = self.load_keywords_from_command()
            found_count = 0
            not_found_count = 0
            
            for i, keyword in enumerate(keywords):
                if not self.is_running:
                    break
                    
                step_index = 18 + i  # 從步驟18開始
                self.update_step(step_index)
                self.add_log(f"搜尋第 {i+1} 個關鍵字: {keyword}")
                
                try:
                    # 執行搜尋
                    found = self.search_keywords(keyword)
                    if found:
                        found_count += 1
                    else:
                        not_found_count += 1
                    
                    # 顯示搜尋結果
                    time.sleep(2)  # 給使用者更多時間觀察
                    
                    # 清除搜尋提示
                    try:
                        self.driver.execute_script("""
                        try {
                            var indicators = ['search-indicator', 'search-result', 'search-not-found'];
                            for (var i = 0; i < indicators.length; i++) {
                                var elem = document.getElementById(indicators[i]);
                                if (elem && elem.parentNode) {
                                    elem.parentNode.removeChild(elem);
                                }
                            }
                        } catch (e) {
                            console.error('清除提示時發生錯誤:', e);
                        }
                        """)
                    except Exception as e:
                        self.add_log(f"清除提示時發生錯誤: {str(e)}")
                        
                except Exception as e:
                    self.add_log(f"搜尋關鍵字 '{keyword}' 時發生錯誤: {str(e)}")
                    not_found_count += 1
            
            # 顯示搜尋總結
            self.add_log(f"關鍵字搜尋完成: 找到 {found_count} 個，未找到 {not_found_count} 個")
            
            # 完成測試
            if self.is_running:
                self.update_step(18 + len(keywords))  # 最後一個步驟的索引
                self.update_action("測試完成")
                self.add_log("自動化測試完成！")
            
        except Exception as e:
            self.add_log(f"執行過程中發生錯誤: {str(e)}")
        finally:
            # 關閉 WebDriver
            if self.driver:
                self.add_log("關閉 Chrome WebDriver...")
                try:
                    time.sleep(3)  # 等待一下，讓使用者能看到最後的結果
                    self.driver.quit()
                except Exception:
                    pass
                self.driver = None
            
            # 重置 UI 狀態
            self.is_running = False
            self.current_action.set("")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.status.set("就緒")
    
    def update_action(self, action):
        """更新目前執行的動作"""
        self.current_action.set(action)
        self.status.set(f"執行中: {action}")
        self.root.update_idletasks()

def main():
    # 建立主視窗
    root = tk.Tk()
    
    try:
        # 設定應用程式圖示
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'icon.ico')
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except Exception:
        pass  # 如果無法設定圖示，就略過
    
    # 建立應用程式實例
    app = SimpleChromeAutomation(root)
    
    # 設定關閉視窗的處理
    def on_closing():
        if app.is_running:
            if messagebox.askokcancel("確認", "自動化測試正在執行中，確定要關閉嗎？"):
                app.stop_automation()
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # 啟動主迴圈
    root.mainloop()

if __name__ == "__main__":
    main()
