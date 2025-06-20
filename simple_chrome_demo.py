import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os
import sys
import time
import threading
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("log.txt", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

class SimpleChromeDemo:
    def __init__(self, root):
        self.root = root
        self.root.title("Chrome 自動化示範")
        self.root.geometry("800x600")
        
        # 設定變數
        self.driver = None
        self.is_running = False
        
        # 建立 UI
        self.create_ui()
    
    def create_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 標題
        title_label = ttk.Label(main_frame, text="Chrome 自動化示範", font=("Arial", 16))
        title_label.pack(pady=10)
        
        # 說明
        desc_label = ttk.Label(main_frame, text="此程式將示範自動操作網頁元素，展示自動化功能")
        desc_label.pack(pady=5)
        
        # 按鈕
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(pady=10)
        
        self.start_button = ttk.Button(buttons_frame, text="開始示範", command=self.start_demo)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(buttons_frame, text="停止", command=self.stop_demo, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # 進度顯示
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(progress_frame, text="目前步驟:").pack(side=tk.LEFT)
        self.current_step = tk.StringVar(value="未開始")
        ttk.Label(progress_frame, textvariable=self.current_step).pack(side=tk.LEFT, padx=5)
        
        # 進度條
        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=700, mode='determinate')
        self.progress.pack(pady=10)
        
        # 日誌區域
        log_frame = ttk.LabelFrame(main_frame, text="執行日誌")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 初始訊息
        self.log("歡迎使用 Chrome 自動化示範程式")
        self.log("點擊「開始示範」按鈕開始自動化測試")
    
    def log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        # 顯示在 UI 上
        self.log_text.insert(tk.END, f"{log_message}\n")
        self.log_text.see(tk.END)
        
        # 更新 UI
        self.root.update_idletasks()
        
        # 寫入日誌檔
        logging.info(message)
    
    def update_step(self, step, progress_value):
        self.current_step.set(step)
        self.progress['value'] = progress_value
        self.log(f"執行: {step}")
        self.root.update_idletasks()
    
    def start_demo(self):
        # 更新 UI 狀態
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.is_running = True
        
        # 啟動執行緒
        self.demo_thread = threading.Thread(target=self.run_demo)
        self.demo_thread.daemon = True
        self.demo_thread.start()
    
    def stop_demo(self):
        self.is_running = False
        self.log("正在停止示範...")
    
    def run_demo(self):
        try:
            # 步驟 1: 初始化 WebDriver
            self.update_step("初始化 Chrome WebDriver", 10)
            
            # 尋找 chromedriver.exe
            chromedriver_path = self.find_chromedriver()
            if not chromedriver_path:
                self.log("錯誤: 未找到 chromedriver.exe")
                messagebox.showerror("錯誤", "未找到 chromedriver.exe，請確保它與程式在同一目錄")
                self.reset_ui()
                return
            
            self.log(f"找到 ChromeDriver: {chromedriver_path}")
            
            # 初始化 WebDriver
            options = webdriver.ChromeOptions()
            options.add_argument("--start-maximized")
            options.add_argument("--disable-notifications")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            
            service = Service(executable_path=chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
            self.log("Chrome WebDriver 初始化成功")
            
            # 設定等待時間
            wait = WebDriverWait(self.driver, 5)
            
            # 步驟 2: 創建並打開本地 HTML 頁面
            self.update_step("創建並打開測試頁面", 20)
            html_path = self.create_test_html()
            self.log(f"創建測試頁面: {html_path}")
            
            file_url = f"file:///{html_path.replace('\\', '/')}"
            self.driver.get(file_url)
            time.sleep(1)
            
            # 步驟 3: 填寫表單
            self.update_step("填寫表單", 30)
            self.log("填寫使用者名稱和密碼")
            
            # 輸入使用者名稱
            username_input = wait.until(EC.element_to_be_clickable((By.ID, "username")))
            username_input.click()
            username_input.clear()
            username_input.send_keys("測試使用者")
            time.sleep(0.5)
            
            # 輸入密碼
            password_input = wait.until(EC.element_to_be_clickable((By.ID, "password")))
            password_input.click()
            password_input.clear()
            password_input.send_keys("password123")
            time.sleep(0.5)
            
            # 點擊登入按鈕
            self.log("點擊登入按鈕")
            login_button = wait.until(EC.element_to_be_clickable((By.ID, "login-btn")))
            login_button.click()
            time.sleep(1)
            
            # 步驟 4: 新增項目
            self.update_step("新增項目", 50)
            self.log("新增項目")
            
            # 輸入項目名稱
            item_input = wait.until(EC.element_to_be_clickable((By.ID, "item-name")))
            item_input.click()
            item_input.clear()
            item_input.send_keys("筆記型電腦")
            time.sleep(0.5)
            
            # 輸入項目價格
            price_input = wait.until(EC.element_to_be_clickable((By.ID, "item-price")))
            price_input.click()
            price_input.clear()
            price_input.send_keys("25000")
            time.sleep(0.5)
            
            # 點擊新增按鈕
            add_button = wait.until(EC.element_to_be_clickable((By.ID, "add-btn")))
            add_button.click()
            time.sleep(1)
            
            # 步驟 5: 搜尋項目
            self.update_step("搜尋項目", 70)
            self.log("搜尋項目")
            
            # 輸入搜尋關鍵字
            search_input = wait.until(EC.element_to_be_clickable((By.ID, "search-input")))
            search_input.click()
            search_input.clear()
            search_input.send_keys("筆記型")
            time.sleep(0.5)
            
            # 點擊搜尋按鈕
            search_button = wait.until(EC.element_to_be_clickable((By.ID, "search-btn")))
            search_button.click()
            time.sleep(1)
            
            # 步驟 6: 刪除項目
            self.update_step("刪除項目", 90)
            self.log("刪除項目")
            
            # 點擊刪除按鈕
            delete_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "delete-btn")))
            delete_button.click()
            time.sleep(1)
            
            # 完成
            self.update_step("示範完成", 100)
            self.log("自動化示範完成！")
            self.log("您可以看到頁面上的操作結果")
            
            # 等待用戶觀察結果
            time.sleep(5)
            
        except Exception as e:
            self.log(f"執行過程中發生錯誤: {str(e)}")
        
        finally:
            # 關閉 WebDriver
            if self.driver:
                self.log("關閉 Chrome WebDriver...")
                try:
                    time.sleep(3)  # 給用戶時間觀察結果
                    self.driver.quit()
                except Exception:
                    pass
                self.driver = None
            
            # 重置 UI 狀態
            self.reset_ui()
    
    def reset_ui(self):
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.current_step.set("未開始")
        self.progress['value'] = 0
    
    def find_chromedriver(self):
        """尋找 ChromeDriver"""
        locations = [
            "chromedriver.exe",  # 當前目錄
            os.path.join(os.path.dirname(sys.executable), "chromedriver.exe"),  # 執行檔目錄
            os.path.join(os.getcwd(), "chromedriver.exe"),  # 工作目錄
        ]
        
        for location in locations:
            if os.path.exists(location):
                return location
        
        return None
    
    def create_test_html(self):
        """創建測試用的 HTML 頁面"""
        html_dir = "web"
        if not os.path.exists(html_dir):
            os.makedirs(html_dir)
        
        html_path = os.path.join(html_dir, "demo.html")
        
        html_content = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>自動化測試頁面</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .container {
            border: 1px solid #ddd;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 5px;
        }
        .hidden {
            display: none;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        table, th, td {
            border: 1px solid #ddd;
        }
        th, td {
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
        .success {
            color: green;
            font-weight: bold;
        }
        .highlight {
            background-color: yellow;
        }
        .delete-btn {
            background-color: #ff4d4d;
            color: white;
            border: none;
            padding: 5px 10px;
            cursor: pointer;
            border-radius: 3px;
        }
        input, button {
            padding: 8px;
            margin: 5px 0;
        }
    </style>
</head>
<body>
    <h1>自動化測試頁面</h1>
    
    <!-- 登入表單 -->
    <div id="login-container" class="container">
        <h2>登入系統</h2>
        <div>
            <label for="username">使用者名稱:</label>
            <input type="text" id="username" placeholder="請輸入使用者名稱">
        </div>
        <div>
            <label for="password">密碼:</label>
            <input type="password" id="password" placeholder="請輸入密碼">
        </div>
        <button id="login-btn">登入</button>
        <p id="login-message"></p>
    </div>
    
    <!-- 主要內容 (登入後顯示) -->
    <div id="main-content" class="container hidden">
        <h2>項目管理</h2>
        
        <!-- 新增項目 -->
        <div>
            <h3>新增項目</h3>
            <div>
                <label for="item-name">項目名稱:</label>
                <input type="text" id="item-name" placeholder="請輸入項目名稱">
            </div>
            <div>
                <label for="item-price">價格:</label>
                <input type="number" id="item-price" placeholder="請輸入價格">
            </div>
            <button id="add-btn">新增項目</button>
        </div>
        
        <!-- 搜尋項目 -->
        <div>
            <h3>搜尋項目</h3>
            <div>
                <input type="text" id="search-input" placeholder="請輸入關鍵字">
                <button id="search-btn">搜尋</button>
            </div>
        </div>
        
        <!-- 項目列表 -->
        <div>
            <h3>項目列表</h3>
            <table id="item-table">
                <thead>
                    <tr>
                        <th>項目名稱</th>
                        <th>價格</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody id="item-list">
                    <!-- 項目會在這裡動態新增 -->
                </tbody>
            </table>
            <p id="no-items">目前沒有項目</p>
        </div>
    </div>

    <script>
        // 項目資料
        let items = [];
        
        // DOM 元素
        const loginContainer = document.getElementById('login-container');
        const mainContent = document.getElementById('main-content');
        const loginBtn = document.getElementById('login-btn');
        const loginMessage = document.getElementById('login-message');
        const addBtn = document.getElementById('add-btn');
        const searchBtn = document.getElementById('search-btn');
        const itemList = document.getElementById('item-list');
        const noItemsMsg = document.getElementById('no-items');
        
        // 登入功能
        loginBtn.addEventListener('click', () => {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            if (username && password) {
                loginMessage.textContent = `登入成功！歡迎 ${username}`;
                loginMessage.className = 'success';
                
                // 切換顯示內容
                setTimeout(() => {
                    loginContainer.classList.add('hidden');
                    mainContent.classList.remove('hidden');
                }, 500);
            } else {
                loginMessage.textContent = '請輸入使用者名稱和密碼';
                loginMessage.className = '';
            }
        });
        
        // 新增項目功能
        addBtn.addEventListener('click', () => {
            const name = document.getElementById('item-name').value;
            const price = document.getElementById('item-price').value;
            
            if (name && price) {
                const newItem = { name, price };
                items.push(newItem);
                
                // 清空輸入
                document.getElementById('item-name').value = '';
                document.getElementById('item-price').value = '';
                
                // 更新顯示
                updateItemList();
            }
        });
        
        // 搜尋功能
        searchBtn.addEventListener('click', () => {
            const keyword = document.getElementById('search-input').value.toLowerCase();
            
            // 清除所有高亮
            const highlightedElements = document.querySelectorAll('.highlight');
            highlightedElements.forEach(el => el.classList.remove('highlight'));
            
            if (keyword) {
                // 搜尋並高亮顯示
                const rows = itemList.querySelectorAll('tr');
                rows.forEach(row => {
                    const nameCell = row.querySelector('td:first-child');
                    if (nameCell && nameCell.textContent.toLowerCase().includes(keyword)) {
                        nameCell.classList.add('highlight');
                    }
                });
            }
        });
        
        // 更新項目列表
        function updateItemList() {
            // 清空列表
            itemList.innerHTML = '';
            
            // 顯示或隱藏無項目訊息
            if (items.length === 0) {
                noItemsMsg.style.display = 'block';
            } else {
                noItemsMsg.style.display = 'none';
                
                // 新增項目到列表
                items.forEach((item, index) => {
                    const row = document.createElement('tr');
                    
                    // 名稱
                    const nameCell = document.createElement('td');
                    nameCell.textContent = item.name;
                    row.appendChild(nameCell);
                    
                    // 價格
                    const priceCell = document.createElement('td');
                    priceCell.textContent = `${item.price} 元`;
                    row.appendChild(priceCell);
                    
                    // 操作按鈕
                    const actionCell = document.createElement('td');
                    const deleteBtn = document.createElement('button');
                    deleteBtn.textContent = '刪除';
                    deleteBtn.className = 'delete-btn';
                    deleteBtn.addEventListener('click', () => {
                        items.splice(index, 1);
                        updateItemList();
                    });
                    actionCell.appendChild(deleteBtn);
                    row.appendChild(actionCell);
                    
                    itemList.appendChild(row);
                });
            }
        }
        
        // 初始化
        updateItemList();
    </script>
</body>
</html>
"""
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return os.path.abspath(html_path)

def main():
    root = tk.Tk()
    app = SimpleChromeDemo(root)
    root.mainloop()

if __name__ == "__main__":
    main()
