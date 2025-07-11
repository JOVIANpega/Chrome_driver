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
from command_editor import CommandEditor

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
        self.command_editor = None
        self.selenium_handler = SeleniumHandler()
        self.keywords: List[str] = []
        self.test_results: Dict[str, bool] = {}
        
        # 載入設置
        self.settings = utils.load_settings()
        self.font_size = self.settings.get("font_size", utils.DEFAULT_FONT_SIZE)
        
        # 建立 UI
        self.create_ui()
        
        # 自動尋找 chromedriver.exe
        self.find_chromedriver()
        
        # 綁定關閉事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_ui(self) -> None:
        """建立使用者介面"""
        # 設置自定義主題和顏色
        self.style = ttk.Style()
        
        # 設置整體顏色方案
        bg_color = "#ffffff"  # 白色背景
        selected_tab_bg = "#000080"  # 深藍色選中標籤
        active_tab_bg = "#000066"  # 活動標籤背景色
        tab_bg = "#e0e0e0"  # 未選中標籤背景色
        
        # 確保所有小部件都使用自定義樣式
        self.style.theme_use('default')  # 使用默認主題作為基礎
        
        # 配置根窗口背景色
        self.root.configure(background=bg_color)
        
        # 配置選項卡樣式
        self.style.configure("TNotebook", background=bg_color)
        self.style.configure("TNotebook.Tab", background=tab_bg, padding=[12, 4], font=('Arial', self.font_size))
        
        # 設置選中和活動標籤顏色 - 加強對比度
        self.style.map("TNotebook.Tab", 
                      background=[("selected", selected_tab_bg), ("active", active_tab_bg)],
                      foreground=[("selected", "#ffffff"), ("active", "#ffffff")])
        
        # 設置標籤頁頂部區域背景顏色
        self.style.configure("TNotebook", background=bg_color, tabmargins=[0, 0, 0, 0])
        
        # 設置按鈕和標籤樣式
        self.style.configure("TButton", font=('Arial', self.font_size))
        self.style.configure("TLabel", font=('Arial', self.font_size))
        self.style.configure("TLabelframe.Label", font=('Arial', self.font_size))
        
        # 創建標籤頁控件
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 主標籤頁
        self.main_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.main_tab, text="主界面")
        
        # 命令編輯標籤頁
        self.cmd_editor_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.cmd_editor_tab, text="命令編輯器")
        
        # 綁定標籤切換事件
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
        # 初始化命令編輯器
        self.command_editor = CommandEditor(self.cmd_editor_tab, on_execute_commands=self.start_automation)
        
        # 主框架（在主標籤頁中）
        main_frame = ttk.Frame(self.main_tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ChromeDriver 狀態
        driver_frame = ttk.LabelFrame(main_frame, text="ChromeDriver 狀態", padding="10")
        driver_frame.pack(fill=tk.X, pady=5)
        
        self.driver_status = tk.StringVar(value="尋找中...")
        ttk.Label(driver_frame, textvariable=self.driver_status, font=("Arial", self.font_size)).pack(side=tk.LEFT)
        
        # 顯示版本信息
        version_label = ttk.Label(driver_frame, text=f"版本: v{utils.VERSION}", font=("Arial", self.font_size))
        version_label.pack(side=tk.RIGHT, padx=5)
        
        # 操作按鈕
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        self.start_button = ttk.Button(buttons_frame, text="開始自動化測試", command=self.start_automation)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(buttons_frame, text="停止", command=self.stop_automation, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # 添加測試按鈕
        test_button = ttk.Button(buttons_frame, text="測試按鈕", command=lambda: self.add_log("測試按鈕點擊正常"))
        test_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(buttons_frame, text="清除日誌", command=lambda: self.log_text.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=5)
        
        # 新增顯示步驟窗口按鈕
        self.show_steps_button = ttk.Button(buttons_frame, text="顯示步驟窗口", command=self.show_step_window)
        self.show_steps_button.pack(side=tk.LEFT, padx=5)
        
        # 切換到命令編輯器標籤頁按鈕
        self.switch_to_editor_button = ttk.Button(buttons_frame, text="命令編輯器", command=self.switch_to_command_editor)
        self.switch_to_editor_button.pack(side=tk.LEFT, padx=5)
        
        # 新增全螢幕命令編輯器按鈕
        self.fullscreen_editor_button = ttk.Button(buttons_frame, text="全螢幕編輯器", command=self.show_fullscreen_editor)
        self.fullscreen_editor_button.pack(side=tk.LEFT, padx=5)
        
        # 字體大小控制區域
        font_control_frame = ttk.LabelFrame(main_frame, text="文字大小", padding="5")
        font_control_frame.pack(fill=tk.X, pady=5)
        
        self.font_size_var = tk.StringVar(value=str(self.font_size))
        
        # 文字大小標籤和按鈕
        ttk.Label(font_control_frame, text="字體大小:", font=("Arial", self.font_size), style="TLabel").pack(side=tk.LEFT, padx=(10, 5))
        
        self.decrease_font = ttk.Button(font_control_frame, text="-", width=2, command=self.decrease_font_size)
        self.decrease_font.pack(side=tk.LEFT, padx=2)
        
        font_size_label = ttk.Label(font_control_frame, textvariable=self.font_size_var, width=2, font=("Arial", self.font_size), style="TLabel")
        font_size_label.pack(side=tk.LEFT, padx=5)
        
        self.increase_font = ttk.Button(font_control_frame, text="+", width=2, command=self.increase_font_size)
        self.increase_font.pack(side=tk.LEFT, padx=2)
        
        # 保存設置按鈕
        self.save_settings_button = ttk.Button(font_control_frame, text="保存設置", command=self.save_settings)
        self.save_settings_button.pack(side=tk.RIGHT, padx=5)
        
        # 日誌區塊
        log_frame = ttk.LabelFrame(main_frame, text="執行日誌", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, wrap=tk.WORD, font=("Arial", self.font_size), bg="#ffffff")
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 新增結果摘要區域
        summary_frame = ttk.LabelFrame(main_frame, text="測試結果摘要", padding="10")
        summary_frame.pack(fill=tk.X, pady=5)
        
        self.summary_text = scrolledtext.ScrolledText(summary_frame, height=5, wrap=tk.WORD, font=("Arial", self.font_size), bg="#ffffff")
        self.summary_text.pack(fill=tk.BOTH, expand=True)
        self.summary_text.config(state=tk.DISABLED)
        
        # 目前執行的命令
        self.current_action = tk.StringVar(value="")
        current_frame = ttk.Frame(main_frame)
        current_frame.pack(fill=tk.X, pady=5)
        ttk.Label(current_frame, text="目前執行:", font=("Arial", self.font_size)).pack(side=tk.LEFT)
        ttk.Label(current_frame, textvariable=self.current_action, font=("Arial", self.font_size)).pack(side=tk.LEFT, padx=5)
        
        # 狀態列
        self.status = tk.StringVar(value="就緒")
        status_bar = ttk.Label(self.root, textvariable=self.status, relief=tk.SUNKEN, anchor=tk.W, font=("Arial", self.font_size))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 顯示初始說明
        self.add_log("歡迎使用 Chrome 自動化工具")
        self.add_log("此工具將自動操作本地 HTML 頁面，展示自動化功能")
    
    def on_tab_changed(self, event) -> None:
        """當標籤頁切換時更新樣式"""
        # 如果切換到命令編輯器標籤頁，更新命令編輯器的字體大小
        if self.notebook.index("current") == 1 and self.command_editor:
            self.command_editor.set_font_size(self.font_size)
        
        # 更新當前標籤頁樣式
        self.root.update_idletasks()
    
    def increase_font_size(self) -> None:
        """增加字體大小"""
        if self.font_size < utils.MAX_FONT_SIZE:
            self.font_size += 1
            self.font_size_var.set(str(self.font_size))
            self.update_font()
            self.save_settings()
    
    def decrease_font_size(self) -> None:
        """減小字體大小"""
        if self.font_size > utils.MIN_FONT_SIZE:
            self.font_size -= 1
            self.font_size_var.set(str(self.font_size))
            self.update_font()
            self.save_settings()
    
    def update_font(self) -> None:
        """更新所有 UI 元素的字體大小"""
        # 更新所有文本元素的字體大小
        self.log_text.config(font=("Arial", self.font_size))
        self.summary_text.config(font=("Arial", self.font_size))
        
        # 更新標籤頁字體
        self.style.configure("TNotebook.Tab", font=('Arial', self.font_size))
        
        # 更新按鈕和標籤樣式
        self.style.configure("TButton", font=('Arial', self.font_size))
        self.style.configure("TLabel", font=('Arial', self.font_size))
        self.style.configure("TLabelframe.Label", font=('Arial', self.font_size))
        
        # 更新步驟窗口字體大小
        if self.step_window:
            self.step_window.set_font_size(self.font_size)
        
        # 更新命令編輯器字體大小
        if self.command_editor:
            self.command_editor.set_font_size(self.font_size)
        
        # 更新所有子部件的字體
        self._update_widget_fonts(self.root)
        
        # 重新繪製界面
        self.root.update_idletasks()
    
    def _update_widget_fonts(self, widget: tk.Widget) -> None:
        """遞迴更新所有子部件的字體"""
        try:
            # 更新當前部件的字體
            if isinstance(widget, (tk.Label, tk.Button, tk.Entry, tk.Text)):
                widget.configure(font=("Arial", self.font_size))
            elif isinstance(widget, ttk.Widget):
                style_name = widget.winfo_class()
                if style_name in ["TLabel", "TButton", "TEntry"]:
                    self.style.configure(style_name, font=("Arial", self.font_size))
        except (tk.TclError, AttributeError):
            pass
        
        # 遞迴更新子部件
        for child in widget.winfo_children():
            self._update_widget_fonts(child)
    
    def show_step_window(self) -> None:
        """顯示步驟視窗"""
        if not self.step_window:
            self.step_window = StepWindow(self.root, self.font_size)
            # 設置窗口位置在屏幕最右側
            self.position_step_window()
        else:
            self.step_window.show_window()
            self.position_step_window()
    
    def position_step_window(self) -> None:
        """將步驟窗口定位到屏幕最右側"""
        if not self.step_window:
            return
            
        # 獲取屏幕寬度和高度
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 獲取步驟窗口寬度
        step_window_width = 350  # 設置一個固定寬度
        
        # 計算步驟窗口的 x 坐標 (屏幕最右側)
        x_position = screen_width - step_window_width - 10  # 10 像素的邊距
        
        # 設置窗口位置和大小
        self.step_window.set_position(x_position, 50, step_window_width, screen_height - 100)
    
    def switch_to_command_editor(self) -> None:
        """切換到命令編輯器標籤頁"""
        self.notebook.select(1)  # 切換到命令編輯器標籤頁（索引1）
    
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
        self.settings["font_size"] = self.font_size
        utils.save_settings(self.settings)
        
        if self.step_window:
            self.step_window.set_font_size(self.font_size)
        
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
        # 添加調試日誌
        print("開始自動化測試函數被調用")
        logging.info("開始自動化測試函數被調用")
        self.add_log("開始自動化測試...")
        
        if self.is_running:
            logging.info("自動化測試已在運行中，忽略此次調用")
            return
        
        # 更新 UI 狀態
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.is_running = True
        self.status.set("執行中...")
        
        # 初始化步驟
        self.initialize_steps()
        self.position_step_window()  # 確保步驟窗口在正確位置
        
        # 清空測試結果
        self.test_results = {}
        
        # 檢查必要檔案
        if not os.path.exists("assets/icon.ico"):
            logging.error("找不到圖示檔案")
            self.add_log("錯誤: 找不到圖示檔案")
            self.reset_ui()
            return
            
        if not os.path.exists("web/360_TEST_WEBFILE.html"):
            logging.error("找不到測試頁面")
            self.add_log("錯誤: 找不到測試頁面")
            self.reset_ui()
            return
            
        # 初始化 Selenium
        if not self.selenium_handler:
            logging.info("創建新的 SeleniumHandler 實例")
            self.selenium_handler = SeleniumHandler()
        
        # 確保 chromedriver 路徑正確
        if not self.selenium_handler.find_chromedriver():
            logging.error("找不到 chromedriver.exe")
            self.add_log("錯誤: 找不到 chromedriver.exe")
            self.reset_ui()
            return
            
        if not self.selenium_handler.initialize_driver():
            logging.error("初始化 WebDriver 失敗")
            self.add_log("錯誤: 初始化 WebDriver 失敗")
            self.reset_ui()
            return
            
        if not self.selenium_handler.open_html_page("web/360_TEST_WEBFILE.html"):
            logging.error("開啟測試頁面失敗")
            self.add_log("錯誤: 開啟測試頁面失敗")
            self.reset_ui()
            return
        
        # 添加調試日誌
        logging.info("準備啟動自動化執行線程")
        self.add_log("準備啟動自動化執行...")
        
        # 啟動執行緒
        self.current_task = threading.Thread(target=self.run_automation)
        self.current_task.daemon = True
        
        try:
            self.current_task.start()
            logging.info("自動化執行線程已啟動")
            self.add_log("自動化執行已啟動")
        except Exception as e:
            logging.error(f"啟動執行線程時發生錯誤: {str(e)}")
            self.add_log(f"錯誤: 啟動執行失敗 - {str(e)}")
            self.reset_ui()
    
    def stop_automation(self) -> None:
        """停止自動化測試"""
        self.is_running = False
        self.status.set("停止中...")
        self.add_log("正在停止自動化測試...")
    
    def run_automation(self) -> None:
        """執行自動化測試"""
        try:
            # 初始化 WebDriver
            if not self.selenium_handler.initialize_driver():
                self.add_log("錯誤: 無法初始化 WebDriver")
                self.reset_ui()
                return
            
            # 讀取命令
            commands = utils.read_commands()
            if not commands:
                self.add_log("錯誤: 沒有可執行的命令")
                self.reset_ui()
                return
            
            # 初始化步驟視窗
            if not self.step_window:
                self.step_window = StepWindow(self.root, self.font_size)
            else:
                self.step_window.show_window()
            
            # 設置步驟
            steps = [f"{cmd}: {', '.join(params)}" for cmd, params in commands]
            self.step_window.set_steps(steps)
            
            # 執行命令
            for i, (cmd, params) in enumerate(commands):
                if not self.is_running:
                    break
                
                try:
                    self.step_window.set_current_step(i)
                    self.update_action(f"執行: {cmd}")
                    
                    # 執行命令
                    success = self._execute_command(cmd, params)
                    
                    # 更新步驟狀態
                    if success:
                        self.step_window.mark_step_passed(i)
                        self.add_log(f"✓ {cmd}: {', '.join(params)}")
                    else:
                        self.step_window.mark_step_failed(i)
                        self.add_log(f"✗ {cmd}: {', '.join(params)}")
                    
                    # 更新測試結果摘要
                    self.step_window.update_summary()
                    self.update_summary()
                    
                except Exception as e:
                    self.step_window.mark_step_failed(i)
                    self.add_log(f"錯誤: {cmd} 執行失敗 - {str(e)}")
                    logging.error(f"命令執行錯誤: {str(e)}")
                    continue
            
        except Exception as e:
            self.add_log(f"自動化執行過程中發生錯誤: {str(e)}")
            logging.error(f"自動化執行錯誤: {str(e)}")
        finally:
            self.reset_ui()
            self.selenium_handler.close_driver()
    
    def update_action(self, action: str) -> None:
        """更新當前動作"""
        self.current_action.set(action)
        self.add_log(f"執行: {action}")
    
    def reset_ui(self) -> None:
        """重置 UI 狀態"""
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status.set("就緒")
    
    def on_closing(self) -> None:
        """處理視窗關閉事件"""
        try:
            # 停止自動化任務
            if self.is_running:
                self.stop_automation()
            
            # 關閉 step_window
            if self.step_window:
                self.step_window.destroy()
            
            # 關閉 selenium driver
            if self.selenium_handler:
                self.selenium_handler.close_driver()
            
            # 保存設置
            self.save_settings()
            
            # 關閉主視窗
            self.root.destroy()
            
        except Exception as e:
            logging.error(f"關閉程式時發生錯誤: {str(e)}")
            self.root.destroy()
    
    def _execute_command(self, cmd: str, params: List[str]) -> bool:
        """執行單一命令"""
        if not self.selenium_handler:
            logging.error("Selenium Handler 未初始化")
            return False
            
        try:
            # 特殊處理 WAIT 命令
            if cmd == "WAIT":
                try:
                    import time
                    seconds = int(params[0]) if params else 1
                    time.sleep(seconds)
                    logging.info(f"已等待 {seconds} 秒")
                    return True
                except Exception as e:
                    logging.error(f"等待時發生錯誤: {str(e)}")
                    return False
            else:
                # 其他命令轉發給 selenium_handler 執行
                result = self.selenium_handler._execute_command(cmd, params)
                return result
        except Exception as e:
            logging.error(f"執行命令 {cmd} 時發生錯誤: {str(e)}")
            return False
    
    def show_fullscreen_editor(self) -> None:
        """顯示全螢幕命令編輯器視窗"""
        # 創建新的頂層視窗
        editor_window = tk.Toplevel(self.root)
        editor_window.title("全螢幕命令編輯器")
        
        # 獲取螢幕尺寸
        screen_width = editor_window.winfo_screenwidth()
        screen_height = editor_window.winfo_screenheight()
        
        # 設置視窗大小為全螢幕
        editor_window.geometry(f"{screen_width}x{screen_height}+0+0")
        
        # 創建命令編輯器實例
        fullscreen_editor = CommandEditor(editor_window, on_execute_commands=self.start_automation)
        fullscreen_editor.set_font_size(self.font_size)
        
        # 添加關閉按鈕
        close_button = ttk.Button(editor_window, text="關閉全螢幕編輯器", 
                                command=lambda: self.close_fullscreen_editor(editor_window))
        close_button.pack(side=tk.BOTTOM, pady=10)
        
        # 設置視窗置頂
        editor_window.lift()
        editor_window.focus_force()
        
        # 綁定Escape鍵關閉視窗
        editor_window.bind('<Escape>', lambda e: self.close_fullscreen_editor(editor_window))
    
    def close_fullscreen_editor(self, editor_window: tk.Toplevel) -> None:
        """關閉全螢幕編輯器視窗"""
        editor_window.destroy()

def main() -> None:
    # 建立主視窗
    root = tk.Tk()
    app = ChromeAutomationTool(root)
    
    # 設定圖標
    try:
        icon_path = utils.get_resource_path(os.path.join("assets", "icon.ico"))
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
        else:
            icon_path = "icon.ico"
            if os.path.exists(icon_path):
                root.iconbitmap(icon_path)
    except Exception as e:
        logging.warning(f"載入圖標時發生錯誤: {str(e)}")
    
    # 視窗關閉處理
    def on_closing() -> None:
        if app.step_window:
            app.step_window.destroy()
        if app.selenium_handler.driver:
            app.selenium_handler.close_driver()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # 啟動主循環
    root.mainloop()

if __name__ == "__main__":
    main()
