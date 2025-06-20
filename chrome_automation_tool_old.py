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

class SimpleChromeAutomation:
    def __init__(self, root):
        self.root = root
        self.root.title("簡易 Chrome 自動化工具")
        self.root.geometry("800x600")
        
        # 設定變數
        self.driver = None
        self.is_running = False
        self.current_task = None
        
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
    
    def run_automation(self):
        """執行自動化測試"""
        self.status.set("執行中...")
        self.add_log("開始自動化測試")
        
        try:
            # 初始化 WebDriver
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
            self.update_action("打開本地 HTML 頁面")
            html_path = os.path.abspath("web/index.html")
            file_url = f"file:///{html_path.replace('\\', '/')}"
            self.add_log(f"打開頁面: {file_url}")
            self.driver.get(file_url)
            time.sleep(1)
            
            # 步驟 2: 填寫登入表單
            self.update_action("填寫登入表單")
            self.add_log("填寫使用者名稱和密碼")
            
            # 點擊使用者名稱輸入框
            username_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input#username")))
            username_input.click()
            username_input.clear()
            username_input.send_keys("測試使用者")
            
            # 點擊密碼輸入框
            password_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input#password")))
            password_input.click()
            password_input.clear()
            password_input.send_keys("密碼123")
            
            # 點擊登入按鈕
            self.add_log("點擊登入按鈕")
            login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button#login-button")))
            login_button.click()
            time.sleep(1)
            
            # 步驟 3: 新增項目
            self.update_action("新增項目")
            self.add_log("填寫項目資訊")
            
            # 點擊項目名稱輸入框
            name_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input#item-name")))
            name_input.click()
            name_input.clear()
            name_input.send_keys("筆記型電腦")
            
            # 點擊價格輸入框
            price_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input#item-price")))
            price_input.click()
            price_input.clear()
            price_input.send_keys("25000")
            
            # 點擊新增項目按鈕
            self.add_log("點擊新增項目按鈕")
            add_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button#add-item")))
            add_button.click()
            time.sleep(1)
            
            # 步驟 4: 搜尋功能測試
            self.update_action("搜尋功能測試")
            self.add_log("測試搜尋功能")
            
            # 點擊搜尋輸入框
            search_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input#search-text")))
            search_input.click()
            search_input.clear()
            search_input.send_keys("筆記型電腦")
            
            # 點擊搜尋按鈕
            search_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button#search-button")))
            search_button.click()
            time.sleep(1)
            
            # 步驟 5: 互動按鈕測試
            self.update_action("互動按鈕測試")
            self.add_log("測試互動按鈕")
            
            # 點擊顯示訊息按鈕
            message_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button#show-message")))
            message_button.click()
            time.sleep(1)
            
            # 點擊改變顏色按鈕
            color_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button#change-color")))
            color_button.click()
            time.sleep(1)
            
            # 點擊計數按鈕
            count_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button#count-button")))
            count_button.click()
            time.sleep(1)
            
            # 步驟 6: 刪除項目
            self.update_action("刪除項目")
            self.add_log("刪除項目")
            
            # 點擊刪除按鈕
            delete_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button.delete-item")
            if delete_buttons:
                delete_buttons[0].click()
                time.sleep(1)
            
            # 完成
            self.add_log("自動化測試完成！")
            self.add_log("您可以看到頁面上的變化：新增了筆記型電腦項目、執行了搜尋、顯示了訊息、改變了顏色、增加了計數、刪除了一個項目")
            
            # 等待用戶觀察結果
            self.update_action("測試完成，請觀察頁面結果")
            time.sleep(5)
            
        except Exception as e:
            self.add_log(f"執行過程中發生錯誤: {str(e)}")
        
        finally:
            # 關閉 WebDriver
            if self.driver:
                self.add_log("關閉 Chrome WebDriver...")
                try:
                    # 不要立即關閉，讓用戶有時間查看結果
                    time.sleep(3)
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
        """更新當前執行的動作"""
        self.current_action.set(action)
        self.add_log(f"執行: {action}")
        self.root.update_idletasks()

def main():
    # 啟動 GUI
    root = tk.Tk()
    app = SimpleChromeAutomation(root)
    root.mainloop()

if __name__ == "__main__":
    main() 