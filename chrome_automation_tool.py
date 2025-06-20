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
        self.add_log("歡迎使用 Chrome 自動化工具")
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
    
    def mark_step_failed(self, step_index: int) -> None:
        """標記步驟為失敗"""
        if self.step_window:
            self.step_window.mark_step_failed(step_index)
    
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
            
            # 步驟 2: 打開本地 HTML 頁面
            self.update_action("打開本地 HTML 頁面")
            self.update_step(1)
            
            # 從命令中獲取 URL
            url_path = "web/index.html"  # 預設值
            for cmd, params in commands:
                if cmd == "OPEN_URL":
                    url_path = params[0]
                    break
            
            if not self.selenium_handler.open_html_page(url_path):
                self.add_log(f"錯誤: 打開頁面失敗: {url_path}")
                self.mark_step_failed(1)
                self.reset_ui()
                return
            
            # 步驟 3: 登入表單測試
            self.update_step(2)
            self.update_action("登入表單測試")
            self.add_log("測試登入表單")
            
            if not self.selenium_handler.test_login_form():
                self.add_log("錯誤: 登入表單測試失敗")
                self.mark_step_failed(2)
            else:
                self.add_log("登入表單測試成功")
            
            # 步驟 4: 資料管理測試
            self.update_step(3)
            self.update_action("資料管理測試")
            self.add_log("測試資料管理功能")
            
            if not self.selenium_handler.test_data_management():
                self.add_log("錯誤: 資料管理測試失敗")
                self.mark_step_failed(3)
            else:
                self.add_log("資料管理測試成功")
            
            # 步驟 5: 搜尋功能測試
            self.update_step(4)
            self.update_action("搜尋功能測試")
            self.add_log("測試搜尋功能")
            
            if not self.selenium_handler.test_search_function():
                self.add_log("錯誤: 搜尋功能測試失敗")
                self.mark_step_failed(4)
            else:
                self.add_log("搜尋功能測試成功")
            
            # 步驟 6: 互動按鈕測試
            self.update_step(5)
            self.update_action("互動按鈕測試")
            self.add_log("測試互動按鈕")
            
            if not self.selenium_handler.test_interactive_buttons():
                self.add_log("錯誤: 互動按鈕測試失敗")
                self.mark_step_failed(5)
            else:
                self.add_log("互動按鈕測試成功")
            
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
                    found = self.selenium_handler.search_keyword(keyword)
                    if found:
                        self.add_log(f"✓ 找到關鍵字: {keyword}")
                    else:
                        self.add_log(f"✗ 未找到關鍵字: {keyword}")
                        self.mark_step_failed(step_index)
                    
                    # 給使用者時間觀察結果
                    time.sleep(2)
                except Exception as e:
                    self.add_log(f"搜尋關鍵字 '{keyword}' 時發生錯誤: {str(e)}")
                    self.mark_step_failed(step_index)
            
            # 完成測試
            final_step = base_step_index + len(self.keywords)
            self.update_step(final_step)
            self.update_action("測試完成")
            self.add_log("自動化測試完成！")
            
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
