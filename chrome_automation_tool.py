# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import os
import sys
import time
import threading
import logging
import traceback
from typing import List, Optional, Tuple, Dict, Any
from selenium.webdriver.common.by import By

# 導入自定義模塊
import utils
from step_window import StepWindow
from selenium_handler import SeleniumHandler

# 初始化日誌
utils.setup_logging()

class ChromeAutomationTool:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Chrome 自動化工具")
        self.root.geometry(f"{utils.WINDOW_WIDTH}x{utils.WINDOW_HEIGHT}")
        
        # 設定變數
        self.is_running: bool = False
        self.current_task: Optional[threading.Thread] = None
        self.step_window: Optional[StepWindow] = None
        self.selenium_handler = SeleniumHandler()
        self.keywords: List[str] = []
        self.test_results: Dict[str, bool] = {}
        
        # 載入設置
        self.settings = utils.load_settings()
        
        # 建立 UI
        self.create_ui()
        
        # 自動尋找 chromedriver.exe
        self.find_chromedriver()
        
    def create_ui(self) -> None:
        """建立使用者介面"""
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
        
        # 新增顯示步驟窗口按鈕
        self.show_steps_button = ttk.Button(buttons_frame, text="顯示步驟窗口", command=self.show_step_window)
        self.show_steps_button.pack(side=tk.LEFT, padx=5)
        
        # 新增保存設置按鈕
        self.save_settings_button = ttk.Button(buttons_frame, text="保存設置", command=self.save_settings)
        self.save_settings_button.pack(side=tk.RIGHT, padx=5)
        
        # 日誌區塊
        log_frame = ttk.LabelFrame(main_frame, text="執行日誌", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 新增結果摘要區域
        summary_frame = ttk.LabelFrame(main_frame, text="測試結果摘要", padding="10")
        summary_frame.pack(fill=tk.X, pady=5)
        
        self.summary_text = scrolledtext.ScrolledText(summary_frame, height=5, wrap=tk.WORD)
        self.summary_text.pack(fill=tk.BOTH, expand=True)
        self.summary_text.config(state=tk.DISABLED)
        
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
        self.add_log("歡迎使用 Chrome 自動化工具")
        self.add_log("此工具將自動操作本地 HTML 頁面，展示自動化功能")
    
    def show_step_window(self) -> None:
        """顯示步驟視窗"""
        if not self.step_window:
            self.step_window = StepWindow(self.root)
        else:
            self.step_window.show_window()
    
    def update_step(self, step_index: int) -> None:
        """更新當前步驟"""
        if self.step_window:
            self.step_window.set_current_step(step_index)
            # 標記步驟為通過
            self.step_window.mark_step_passed(step_index)
    
    def mark_step_failed(self, step_index: int) -> None:
        """標記步驟為失敗"""
        if self.step_window:
            self.step_window.mark_step_failed(step_index)
            
            # 記錄失敗結果
            if 0 <= step_index < len(self.step_window.steps):
                step_text = self.step_window.steps[step_index]
                self.test_results[step_text] = False
    
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
        self.keywords = utils.load_keywords_from_command()
        
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
    
    def find_chromedriver(self) -> None:
        """尋找 chromedriver.exe"""
        if self.selenium_handler.find_chromedriver():
            self.driver_status.set(f"已找到 ChromeDriver: {os.path.basename(self.selenium_handler.chromedriver_path)}")
        else:
            self.driver_status.set("未找到 chromedriver.exe")
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
    
    def save_settings(self) -> None:
        """保存設置"""
        if self.step_window:
            self.step_window.save_settings()
        messagebox.showinfo("設置", "設置已保存")
    
    def update_summary(self) -> None:
        """更新測試結果摘要"""
        if self.step_window:
            self.step_window.update_summary()
            
            # 同時更新主窗口的摘要
            self.summary_text.config(state=tk.NORMAL)
            self.summary_text.delete(1.0, tk.END)
            
            # 獲取步驟窗口的摘要內容
            self.step_window.summary_text.config(state=tk.NORMAL)
            summary_content = self.step_window.summary_text.get(1.0, tk.END)
            self.step_window.summary_text.config(state=tk.DISABLED)
            
            # 在主窗口顯示
            self.summary_text.insert(tk.END, summary_content)
            self.summary_text.config(state=tk.DISABLED)
    
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
        
        # 清空測試結果
        self.test_results = {}
        
        # 啟動執行緒
        self.current_task = threading.Thread(target=self.run_automation)
        self.current_task.daemon = True
        self.current_task.start()
    
    def stop_automation(self) -> None:
        """停止自動化測試"""
        self.is_running = False
        self.status.set("停止中...")
        self.add_log("正在停止自動化測試...")
    
    def run_automation(self) -> None:
        """執行自動化測試"""
        try:
            # 步驟 1: 初始化 WebDriver
            self.update_action("初始化 Chrome WebDriver")
            self.update_step(0)
            
            if not self.selenium_handler.initialize_driver():
                self.add_log("錯誤: 初始化 Chrome WebDriver 失敗")
                self.mark_step_failed(0)
                messagebox.showerror("錯誤", "初始化 Chrome WebDriver 失敗")
                self.reset_ui()
                return
            
            # 讀取命令檔案
            commands = utils.read_commands()
            if not commands:
                self.add_log("警告: 命令檔案為空或不存在")
            
            # 執行命令
            current_step_index = 1
            in_test_case = False
            test_case_name = ""
            nav_sequence_name = ""
            
            for cmd, params in commands:
                if not self.is_running:
                    self.add_log("使用者停止了自動化測試")
                    break
            
                # 處理測試案例
                if cmd == "TEST_CASE":
                    in_test_case = True
                    test_case_name = params[0] if params else "未命名測試案例"
                    self.add_log(f"開始執行測試案例: {test_case_name}")
                    self.update_action(f"測試案例: {test_case_name}")
                    step_text = f"測試案例: {test_case_name}"
                    step_index = self.add_step(step_text) if self.step_window else current_step_index
                    self.update_step(step_index)
                    current_step_index += 1
                    continue
                
                # 處理命令
                self.update_action(f"執行: {cmd}")
                step_text = f"{cmd}: {params[0] if params else ''}"
                step_index = current_step_index
                
                if self.step_window and cmd != "NAV_SEQUENCE":
                    step_index = self.add_step(step_text)
                
                self.update_step(step_index)
                self.add_log(f"執行命令: {cmd} {params}")
            
                result = False
                
                # 執行不同類型的命令
                if cmd == "OPEN_URL":
                    url_path = params[0] if params else "web/index.html"
                    result = self.selenium_handler.open_html_page(url_path)
                
                elif cmd == "WAIT":
                    seconds = int(params[0]) if params and params[0].isdigit() else 1
                    result = self.selenium_handler.wait(seconds)
                
                elif cmd == "REFRESH":
                    result = self.selenium_handler.refresh_page()
                
                elif cmd == "BACK":
                    result = self.selenium_handler.go_back()
                
                elif cmd == "CLICK_BY_TEXT":
                    text = params[0] if params else ""
                    result = self.selenium_handler.click_by_text(text)
                
                elif cmd == "CLICK_BY_ID":
                    element_id = params[0] if params else ""
                    result = self.selenium_handler.click_by_id(element_id)
                
                elif cmd == "TYPE":
                    text = params[0] if params else ""
                    result = self.selenium_handler.type_text(text)
                
                elif cmd == "LOGIN":
                    username = params[0] if len(params) > 0 else ""
                    password = params[1] if len(params) > 1 else ""
                    
                    # 找到用戶名輸入框
                    username_input = self.selenium_handler.driver.find_element(By.ID, "username")
                    username_input.clear()
                    username_input.send_keys(username)
                    
                    # 找到密碼輸入框
                    password_input = self.selenium_handler.driver.find_element(By.ID, "password")
                    password_input.clear()
                    password_input.send_keys(password)
                    
                    result = True
                
                # 驗證指令
                elif cmd == "VERIFY_TEXT_EXISTS":
                    text = params[0] if params else ""
                    result = self.selenium_handler.verify_text_exists(text)
                
                elif cmd == "VERIFY_TEXT_NOT_EXISTS":
                    text = params[0] if params else ""
                    result = self.selenium_handler.verify_text_not_exists(text)
                
                elif cmd == "VERIFY_ELEMENT_EXISTS":
                    selector = params[0] if params else ""
                    result = self.selenium_handler.verify_element_exists(selector)
                
                elif cmd == "VERIFY_ELEMENT_VALUE":
                    selector = params[0] if len(params) > 0 else ""
                    expected_value = params[1] if len(params) > 1 else ""
                    result = self.selenium_handler.verify_element_value(selector, expected_value)
                
                elif cmd == "VERIFY_COUNT":
                    selector = params[0] if len(params) > 0 else ""
                    expected_count = int(params[1]) if len(params) > 1 and params[1].isdigit() else 0
                    result = self.selenium_handler.verify_count(selector, expected_count)
            
                # 等待指令
                elif cmd == "WAIT_FOR_TEXT":
                    text = params[0] if len(params) > 0 else ""
                    max_wait_time = int(params[1]) if len(params) > 1 and params[1].isdigit() else None
                    result = self.selenium_handler.wait_for_text(text, max_wait_time)
                
                elif cmd == "WAIT_FOR_ELEMENT":
                    selector = params[0] if len(params) > 0 else ""
                    max_wait_time = int(params[1]) if len(params) > 1 and params[1].isdigit() else None
                    result = self.selenium_handler.wait_for_element(selector, max_wait_time)
                
                elif cmd == "WAIT_FOR_PAGE_LOAD":
                    max_wait_time = int(params[0]) if params and params[0].isdigit() else None
                    result = self.selenium_handler.wait_for_page_load(max_wait_time)
                
                # 頁面導航與互動
                elif cmd == "SCROLL_TO_ELEMENT":
                    selector = params[0] if params else ""
                    result = self.selenium_handler.scroll_to_element(selector)
                
                elif cmd == "SCROLL_TO_BOTTOM":
                    result = self.selenium_handler.scroll_to_bottom()
                
                elif cmd == "EXPAND":
                    selector = params[0] if params else ""
                    result = self.selenium_handler.expand(selector)
                
                # 導航序列
                elif cmd == "NAV_SEQUENCE":
                    nav_sequence_name = params[0] if params else "導航序列"
                    nav_commands = params[1:] if len(params) > 1 else []
                    
                    self.add_log(f"執行導航序列: {nav_sequence_name}")
                    step_text = f"導航序列: {nav_sequence_name}"
                    
                    if self.step_window:
                        step_index = self.add_step(step_text)
                    
                    self.update_step(step_index)
                    result = self.selenium_handler.execute_nav_sequence(nav_commands)
                
                # 基本測試功能
                elif cmd == "test_login_form":
                    result = self.selenium_handler.test_login_form()
                
                elif cmd == "test_data_management":
                    result = self.selenium_handler.test_data_management()
                
                elif cmd == "test_search_function":
                    result = self.selenium_handler.test_search_function()
                
                elif cmd == "test_interactive_buttons":
                    result = self.selenium_handler.test_interactive_buttons()
                
                # 處理結果
                if result:
                    self.add_log(f"命令執行成功: {cmd}")
                    # 記錄成功結果
                    self.test_results[step_text] = True
                else:
                    self.add_log(f"命令執行失敗: {cmd}")
                    self.mark_step_failed(step_index)
                    # 記錄失敗結果
                    self.test_results[step_text] = False
                
                current_step_index += 1
            
            # 搜尋關鍵字
            if self.keywords:
                base_step_index = current_step_index
                self.add_log("開始搜尋關鍵字")
            
                # 搜尋每個關鍵字
                for i, keyword in enumerate(self.keywords):
                    if not self.is_running:
                        self.add_log("使用者停止了自動化測試")
                        break
                    
                    step_index = base_step_index + i
                    step_text = f"搜尋關鍵字: {keyword}"
                    
                    if self.step_window:
                        step_index = self.add_step(step_text)
                    
                    self.update_step(step_index)
                    self.update_action(f"搜尋關鍵字: {keyword}")
                    
                    try:
                        found = self.selenium_handler.search_keyword(keyword)
                        if found:
                            self.add_log(f"✓ 找到關鍵字: {keyword}")
                            # 記錄成功結果
                            self.test_results[step_text] = True
                        else:
                            self.add_log(f"✗ 未找到關鍵字: {keyword}")
                            self.mark_step_failed(step_index)
                            # 記錄失敗結果
                            self.test_results[step_text] = False
                        
                        # 給使用者時間觀察結果
                        time.sleep(2)
                    except Exception as e:
                        self.add_log(f"搜尋關鍵字 '{keyword}' 時發生錯誤: {str(e)}")
                        self.mark_step_failed(step_index)
                        # 記錄失敗結果
                        self.test_results[step_text] = False
                
                current_step_index = base_step_index + len(self.keywords)
            
            # 完成測試
            final_step_text = "測試完成"
            final_step_index = current_step_index
            
            if self.step_window:
                final_step_index = self.add_step(final_step_text)
            
            self.update_step(final_step_index)
            self.update_action("測試完成")
            self.add_log("自動化測試完成！")
            
            # 更新測試結果摘要
            self.update_summary()
            
        except Exception as e:
            self.add_log(f"執行過程中發生錯誤: {str(e)}")
            self.add_log(traceback.format_exc())
        
        finally:
            # 關閉 WebDriver
            self.selenium_handler.close_driver()
            
            # 給使用者時間觀察結果
            time.sleep(3)
            
            # 重置 UI 狀態
            self.reset_ui()
            self.status.set("就緒")
    
    def update_action(self, action: str) -> None:
        """更新目前執行的動作"""
        self.current_action.set(action)
        self.root.update_idletasks()
    
    def reset_ui(self) -> None:
        """重置 UI 狀態"""
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.is_running = False
        self.current_action.set("")

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
    app = ChromeAutomationTool(root)
    
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
