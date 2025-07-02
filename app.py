import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import os
import sys
import threading
from datetime import datetime
import asyncio
from browser_automation import BrowserAutomation

# 常數定義
APP_TITLE = "Chrome E2E助手"
APP_VERSION = "1.0.0"
DEFAULT_FONT_SIZE = 12
CONFIG_FILE = "config.json"
DEFAULT_WINDOW_SIZE = "900x700"  # 增大預設窗口大小

class BrowserAutomationApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_TITLE} v{APP_VERSION}")
        self.root.geometry(DEFAULT_WINDOW_SIZE)
        self.root.minsize(900, 700)  # 設置最小窗口大小以確保所有元素都可見
        
        # 設定變數
        self.font_size = tk.IntVar(value=DEFAULT_FONT_SIZE)
        self.is_recording = False
        self.current_script = []
        self.recording = False
        self.executing = False
        self.script_content = ""
        
        # 設置事件循環
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self._run_event_loop, daemon=True).start()
        
        # 建立UI
        self.create_ui()
    
    def _run_event_loop(self):
        """在單獨的線程中運行事件循環"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
    
    def create_ui(self):
        """創建使用者介面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 狀態欄
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # 腳本驗證狀態指示器
        self.validation_status_var = tk.StringVar(value="")
        validation_status = ttk.Label(status_frame, textvariable=self.validation_status_var, 
                                     width=20, anchor=tk.CENTER)
        validation_status.pack(side=tk.RIGHT, padx=5, pady=2)
        
        # 一般狀態欄
        self.status_var = tk.StringVar(value="就緒")
        status_bar = ttk.Label(status_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.LEFT, expand=True, pady=2)

        # 創建字體和樣式設定
        default_font = ("Microsoft JhengHei UI", self.font_size.get())
        big_font = ("Microsoft JhengHei UI", self.font_size.get() + 2, "bold")
        
        # 創建自定義樣式
        style = ttk.Style()
        style.configure("TButton", font=default_font)
        style.configure("Bold.TButton", font=big_font)
        style.configure("Action.TButton", font=big_font, padding=10)
        style.configure("Execute.TButton", font=big_font, foreground="blue", padding=10)
        style.map("Execute.TButton", background=[("active", "#e1e1ff")])

        # ===== 顯眼的操作按鈕區域 =====
        # 將操作按鈕移到最上方，確保它們始終可見
        operation_frame = ttk.LabelFrame(main_frame, text="腳本操作", padding=10)
        operation_frame.pack(fill=tk.X, pady=(0, 10), ipady=5)
        
        # 底部功能按鈕 - 使用更明顯的方式放置
        button_frame = ttk.Frame(operation_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        # 建立底部按鈕，使用大尺寸確保可見性
        button_texts = [
            ("載入腳本", self.on_load_script_click),
            ("儲存腳本", self.on_save_script_click),
            ("執行腳本", self.on_execute_click),
            ("清空腳本", self.on_clear_script_click)
        ]
        
        for i, (text, cmd) in enumerate(button_texts):
            if text == "執行腳本":
                # 特別強調執行按鈕
                btn = ttk.Button(button_frame, text=text, width=20, 
                              command=cmd, style="Execute.TButton")
            else:
                btn = ttk.Button(button_frame, text=text, width=20, 
                              command=cmd, style="Action.TButton")
                
            btn.grid(row=i//2, column=i%2, padx=20, pady=10, sticky="ew")
            
            # 設置按鈕的變數名稱
            if text == "載入腳本":
                self.載入_btn = btn
                # 確保載入按鈕總是可用
                self.載入_btn.configure(state=tk.NORMAL)
                print("載入腳本按鈕已設置為可用狀態")
            elif text == "儲存腳本":
                self.儲存_btn = btn
            elif text == "執行腳本":
                self.執行_btn = btn
            elif text == "清空腳本":
                self.清空_btn = btn
        
        # 均勻分配按鈕網格列/行權重
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        # 頂部控制區
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 錄製控制按鈕
        record_frame = ttk.Frame(control_frame)
        record_frame.pack(side=tk.LEFT)
        
        self.record_btn = ttk.Button(record_frame, text="開始錄製", width=15, 
                                    command=self.on_record_click)
        self.record_btn.pack(side=tk.LEFT, padx=5)
        
        self.record_local_btn = ttk.Button(record_frame, text="錄製本地頁面", width=15,
                                         command=self.on_record_local_click)
        self.record_local_btn.pack(side=tk.LEFT, padx=5)
        
        self.record_test_btn = ttk.Button(record_frame, text="錄製測試頁面", width=15,
                                       command=self.on_record_test_click)
        self.record_test_btn.pack(side=tk.LEFT, padx=5)
        
        self.pause_btn = ttk.Button(record_frame, text="暫停錄製", width=15, 
                                    command=self.on_pause_click, state=tk.DISABLED)
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(record_frame, text="停止錄製", width=15, 
                                   command=self.on_stop_click, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # 驗證點插入按鈕
        verify_frame = ttk.Frame(main_frame)
        verify_frame.pack(fill=tk.X, pady=5)
        
        verify_label = ttk.Label(verify_frame, text="插入驗證點:")
        verify_label.pack(side=tk.LEFT, padx=(0, 5))
        
        for text, cmd in [
            ("文字驗證", self.on_text_verify_click),
            ("網址驗證", self.on_url_verify_click),
            ("截圖驗證", self.on_screenshot_verify_click),
            ("OCR驗證", self.on_ocr_verify_click)
        ]:
            btn = ttk.Button(verify_frame, text=text, width=10, command=cmd, state=tk.DISABLED)
            btn.pack(side=tk.LEFT, padx=5)
            setattr(self, f"{text.replace('驗證', '')}_btn", btn)
        
        # 分頁控制
        tab_frame = ttk.Frame(main_frame)
        tab_frame.pack(fill=tk.X, pady=5)
        
        tab_label = ttk.Label(tab_frame, text="分頁操作:")
        tab_label.pack(side=tk.LEFT, padx=(0, 5))
        
        for text, cmd in [
            ("切換分頁", self.on_switch_tab_click),
            ("關閉分頁", self.on_close_tab_click)
        ]:
            btn = ttk.Button(tab_frame, text=text, width=10, command=cmd, state=tk.DISABLED)
            btn.pack(side=tk.LEFT, padx=5)
            setattr(self, f"{text.replace('分頁', '')}_btn", btn)
        
        # 條件控制
        condition_frame = ttk.Frame(main_frame)
        condition_frame.pack(fill=tk.X, pady=5)
        
        condition_label = ttk.Label(condition_frame, text="條件控制:")
        condition_label.pack(side=tk.LEFT, padx=(0, 5))
        
        for text, cmd in [
            ("IF文字存在", self.on_if_text_exists_click),
            ("IF網址包含", self.on_if_url_contains_click),
            ("ELSE", self.on_else_click),
            ("ENDIF", self.on_endif_click),
        ]:
            btn = ttk.Button(condition_frame, text=text, width=10, command=cmd, state=tk.DISABLED)
            btn.pack(side=tk.LEFT, padx=5)
            setattr(self, f"{text.lower().replace(' ', '_')}_btn", btn)
        
        # 等待控制
        wait_frame = ttk.Frame(main_frame)
        wait_frame.pack(fill=tk.X, pady=5)
        
        wait_label = ttk.Label(wait_frame, text="等待控制:")
        wait_label.pack(side=tk.LEFT, padx=(0, 5))
        
        for text, cmd in [
            ("等待秒數", self.on_wait_seconds_click),
            ("等待文字", self.on_wait_for_text_click),
            ("等待網址", self.on_wait_for_url_click)
        ]:
            btn = ttk.Button(wait_frame, text=text, width=10, command=cmd, state=tk.DISABLED)
            btn.pack(side=tk.LEFT, padx=5)
            setattr(self, f"{text.replace('等待', '')}_btn", btn)
        
        # 字體大小控制
        font_frame = ttk.Frame(main_frame)
        font_frame.pack(fill=tk.X, pady=5)
        
        font_label = ttk.Label(font_frame, text="字體大小:")
        font_label.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(font_frame, text="A+", width=5, 
                  command=lambda: self.change_font_size(1)).pack(side=tk.LEFT, padx=5)
        ttk.Button(font_frame, text="A-", width=5, 
                  command=lambda: self.change_font_size(-1)).pack(side=tk.LEFT, padx=5)
        
        # 建立分割面板
        paned = ttk.PanedWindow(main_frame, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 腳本編輯區域
        script_frame = ttk.LabelFrame(paned, text="腳本編輯")
        paned.add(script_frame, weight=3)
        
        self.script_text = scrolledtext.ScrolledText(script_frame, wrap=tk.WORD, 
                                                  font=("TkDefaultFont", self.font_size.get()))
        self.script_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 輸出區域
        output_frame = ttk.LabelFrame(paned, text="執行輸出")
        paned.add(output_frame, weight=1)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, 
                                                  font=("TkDefaultFont", self.font_size.get()))
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 再次強調，在底部也添加操作按鈕
        bottom_button_frame = ttk.Frame(main_frame)
        bottom_button_frame.pack(fill=tk.X, pady=10)
        
        # 在底部添加執行腳本按鈕，確保用戶能找到它
        execute_btn_bottom = ttk.Button(bottom_button_frame, text="執行腳本", 
                                     command=self.on_execute_click, style="Execute.TButton",
                                     width=30)
        execute_btn_bottom.pack(side=tk.BOTTOM, pady=10)
    
    def change_font_size(self, delta):
        """更改字體大小"""
        new_size = self.font_size.get() + delta
        if 8 <= new_size <= 24:  # 限制字體大小範圍
            self.font_size.set(new_size)
            self.script_text.configure(font=("Microsoft JhengHei UI", new_size))
            self.output_text.configure(font=("Microsoft JhengHei UI", new_size))
            
            # 更新所有按鈕的字體大小
            style = ttk.Style()
            style.configure("TButton", font=("Microsoft JhengHei UI", new_size))
            style.configure("Bold.TButton", font=("Microsoft JhengHei UI", new_size + 2, "bold"))
            style.configure("Action.TButton", font=("Microsoft JhengHei UI", new_size + 2, "bold"), padding=10)
            style.configure("Execute.TButton", font=("Microsoft JhengHei UI", new_size + 2, "bold"), foreground="blue", padding=10)
            
            # 更新對話框的提示
            for dialog in self.root.winfo_children():
                if isinstance(dialog, tk.Toplevel):
                    for widget in dialog.winfo_children():
                        try:
                            widget.configure(font=("Microsoft JhengHei UI", new_size))
                        except:
                            pass
    
    # 錄製控制函數
    def on_record_click(self):
        """開始錄製"""
        self.is_recording = True
        self.record_btn.configure(state=tk.DISABLED)
        self.record_local_btn.configure(state=tk.DISABLED)
        self.pause_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.NORMAL)
        
        # 啟用驗證點按鈕
        self.enable_recording_buttons()
        
        self.status_var.set("正在錄製中...")
        
        # 啟動瀏覽器並開始錄製 (此處將在main.py中替換為真實實現)
        self.append_script("# 錄製開始: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # 啟動錄製瀏覽器的功能會在main.py中實現
        url = self.show_input_dialog("輸入網址", "請輸入要錄製的網址:")
        if url:
            self.start_recording(url)
        else:
            self.start_recording()
    
    def on_record_local_click(self):
        """錄製本地頁面"""
        # 顯示檔案選擇對話框
        initial_dir = os.path.join(os.getcwd(), "web")
        if not os.path.exists(initial_dir):
            initial_dir = os.getcwd()
        
        file_path = filedialog.askopenfilename(
            title="選擇本地HTML檔案",
            initialdir=initial_dir,
            filetypes=[("HTML檔案", "*.html"), ("所有檔案", "*.*")]
        )
        
        if not file_path:
            return
        
        # 設置錄製狀態
        self.is_recording = True
        self.record_btn.configure(state=tk.DISABLED)
        self.record_local_btn.configure(state=tk.DISABLED)
        self.pause_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.NORMAL)
        
        # 啟用驗證點按鈕
        self.enable_recording_buttons()
        
        self.status_var.set("正在錄製本地頁面...")
        
        # 添加錄製開始標記
        self.append_script("# 錄製開始 (本地頁面): " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # 將檔案路徑轉換為file://URL格式
        file_url = f"file://{file_path}"
        
        # 啟動錄製瀏覽器功能 (會在main.py中實現)
        self.start_recording(file_url)
    
    def start_recording(self, url=None):
        """開始錄製"""
        if self.recording or self.executing:
            messagebox.showinfo("提示", "已有錄製或執行任務在進行中")
            return
        
        self.recording = True
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, "正在準備錄製環境...\n")
        
        # 更新按鈕狀態
        self.執行_btn.configure(state=tk.DISABLED)
        self.載入_btn.configure(state=tk.DISABLED)
        self.record_btn.configure(state=tk.DISABLED)
        self.record_local_btn.configure(state=tk.DISABLED)
        self.record_test_btn.configure(state=tk.DISABLED)
        self.pause_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.NORMAL)
        
        # 啟動瀏覽器自動化進行錄製
        asyncio.run_coroutine_threadsafe(self._start_recording_async(url), self.loop)
    
    async def _start_recording_async(self, url=None):
        """非同步啟動錄製"""
        try:
            # 創建瀏覽器自動化實例
            self.browser = BrowserAutomation(
                log_callback=self.log_message,
                on_script_generated=self.on_script_generated,
                on_recording_stopped=self.on_recording_stopped
            )
            
            # 啟動瀏覽器
            await self.browser.start_browser(headless=False)
            
            # 開始錄製
            await self.browser.start_recording(url)
            
        except Exception as e:
            self.log_message(f"啟動錄製時出錯: {str(e)}")
            self.root.after(0, self.on_recording_stopped)
    
    def on_script_generated(self, script_content, script_filename):
        """腳本生成的回調"""
        self.script_content = script_content
        self.script_text.delete(1.0, tk.END)
        self.script_text.insert(tk.END, script_content)
        self.log_message(f"已生成腳本: {script_filename}")
        
        # 更新驗證狀態
        self.validation_status_var.set("🔄 腳本驗證中...")
        self.root.update_idletasks()
    
    def update_validation_status(self, success):
        """更新驗證狀態指示器"""
        if success:
            self.validation_status_var.set("✅ 腳本驗證通過")
        else:
            self.validation_status_var.set("❌ 腳本驗證失敗")
        self.root.update_idletasks()
    
    def on_recording_stopped(self, validation_success=None):
        """錄製停止的回調"""
        self.recording = False
        
        # 更新按鈕狀態
        self.執行_btn.configure(state=tk.NORMAL)
        self.載入_btn.configure(state=tk.NORMAL)
        self.record_btn.configure(state=tk.NORMAL)
        self.record_local_btn.configure(state=tk.NORMAL)
        self.record_test_btn.configure(state=tk.NORMAL)
        self.pause_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.DISABLED)
        
        # 關閉瀏覽器
        if hasattr(self, 'browser') and self.browser:
            asyncio.run_coroutine_threadsafe(self.browser.close_browser(), self.loop)
            self.browser = None
        
        self.log_message("錄製已停止")
        
        # 更新驗證狀態
        if validation_success is not None:
            self.update_validation_status(validation_success)
            
            # 如果腳本驗證通過，彈出對話框詢問是否要立即執行腳本
            if validation_success and self.script_content:
                if messagebox.askyesno("腳本已生成", "腳本已生成並驗證通過。是否要立即執行此腳本？"):
                    self.root.after(500, self.execute_script)  # 使用短延遲確保UI更新完成
    
    def on_pause_click(self):
        """暫停錄製"""
        if self.is_recording:
            self.is_recording = False
            self.pause_btn.configure(text="繼續錄製")
            self.status_var.set("已暫停錄製")
            self.append_script("# 錄製暫停: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            # 暫停錄製的功能會在main.py中實現
            self.pause_recording()
        else:
            self.is_recording = True
            self.pause_btn.configure(text="暫停錄製")
            self.status_var.set("正在錄製中...")
            self.append_script("# 錄製繼續: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            # 繼續錄製的功能會在main.py中實現
            self.resume_recording()
    
    def pause_recording(self):
        """暫停錄製 (此函數將在main.py中被替換)"""
        pass
    
    def resume_recording(self):
        """繼續錄製 (此函數將在main.py中被替換)"""
        pass
    
    def on_stop_click(self):
        """停止錄製"""
        self.is_recording = False
        self.record_btn.configure(state=tk.NORMAL)
        self.record_local_btn.configure(state=tk.NORMAL)
        self.record_test_btn.configure(state=tk.NORMAL)
        self.pause_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.DISABLED)
        
        # 禁用驗證點按鈕
        self.disable_recording_buttons()
        
        self.status_var.set("錄製已停止")
        self.append_script("# 錄製結束: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # 停止錄製的功能會在main.py中實現
        self.stop_recording()
    
    def stop_recording(self):
        """停止錄製 (此函數將在main.py中被替換)"""
        pass
    
    def enable_recording_buttons(self):
        """啟用錄製過程中需要的按鈕"""
        for btn_name in [
            "文字_btn", "網址_btn", "截圖_btn", "OCR_btn",
            "切換_btn", "關閉_btn",
            "if_文字存在_btn", "if_網址包含_btn", "else_btn", "endif_btn",
            "秒數_btn", "文字_btn", "網址_btn"
        ]:
            if hasattr(self, btn_name):
                getattr(self, btn_name).configure(state=tk.NORMAL)
    
    def disable_recording_buttons(self):
        """禁用錄製過程中需要的按鈕"""
        for btn_name in [
            "文字_btn", "網址_btn", "截圖_btn", "OCR_btn",
            "切換_btn", "關閉_btn",
            "if_文字存在_btn", "if_網址包含_btn", "else_btn", "endif_btn",
            "秒數_btn", "文字_btn", "網址_btn"
        ]:
            if hasattr(self, btn_name):
                getattr(self, btn_name).configure(state=tk.DISABLED)
    
    # 驗證點插入函數
    def on_text_verify_click(self):
        """插入文字驗證點"""
        if not self.is_recording:
            return
        text = self.show_input_dialog("文字驗證", "請輸入要驗證的文字:")
        if text:
            self.append_script(f"ASSERT_TEXT = {text}")
    
    def on_url_verify_click(self):
        """插入網址驗證點"""
        if not self.is_recording:
            return
        url = self.show_input_dialog("網址驗證", "請輸入要驗證的網址部分:")
        if url:
            self.append_script(f"ASSERT_URL = {url}")
    
    def on_screenshot_verify_click(self):
        """插入截圖驗證點"""
        if not self.is_recording:
            return
        coords = self.show_input_dialog("截圖驗證", "請輸入截圖區域座標 (x1,y1,x2,y2):")
        if coords:
            self.append_script(f"SCREENSHOT_ASSERT = {coords}")
    
    def on_ocr_verify_click(self):
        """插入OCR驗證點"""
        if not self.is_recording:
            return
        coords = self.show_input_dialog("OCR區域", "請輸入OCR區域座標 (x1,y1,x2,y2):")
        if not coords:
            return
        
        text = self.show_input_dialog("OCR驗證", "請輸入預期的OCR文字:")
        if text:
            self.append_script(f"OCR_ASSERT = {coords}||{text}")
    
    # 分頁操作函數
    def on_switch_tab_click(self):
        """切換分頁"""
        if not self.is_recording:
            return
        tab_index = self.show_input_dialog("切換分頁", "請輸入分頁索引 (從0開始):")
        if tab_index:
            self.append_script(f"SWITCH_TAB = {tab_index}")
    
    def on_close_tab_click(self):
        """關閉分頁"""
        if not self.is_recording:
            return
        self.append_script("CLOSE_TAB")
    
    # 條件控制函數
    def on_if_text_exists_click(self):
        """IF文字存在"""
        if not self.is_recording:
            return
        text = self.show_input_dialog("IF文字存在", "請輸入要檢查的文字:")
        if text:
            self.append_script(f"IF_TEXT_EXISTS = {text}")
    
    def on_if_url_contains_click(self):
        """IF網址包含"""
        if not self.is_recording:
            return
        url = self.show_input_dialog("IF網址包含", "請輸入要檢查的網址部分:")
        if url:
            self.append_script(f"IF_URL_CONTAINS = {url}")
    
    def on_else_click(self):
        """ELSE"""
        if not self.is_recording:
            return
        self.append_script("ELSE")
    
    def on_endif_click(self):
        """ENDIF"""
        if not self.is_recording:
            return
        self.append_script("ENDIF")
    
    # 等待控制函數
    def on_wait_seconds_click(self):
        """等待秒數"""
        if not self.is_recording:
            return
        seconds = self.show_input_dialog("等待秒數", "請輸入等待秒數:")
        if seconds:
            self.append_script(f"WAIT = {seconds}")
    
    def on_wait_for_text_click(self):
        """等待文字出現"""
        if not self.is_recording:
            return
        text = self.show_input_dialog("等待文字", "請輸入要等待的文字:")
        if text:
            self.append_script(f"WAIT_FOR_TEXT = {text}")
    
    def on_wait_for_url_click(self):
        """等待網址"""
        if not self.is_recording:
            return
        url = self.show_input_dialog("等待網址", "請輸入要等待的網址部分:")
        if url:
            self.append_script(f"WAIT_FOR_URL = {url}")
    
    # 腳本操作函數
    def on_load_script_click(self):
        """載入腳本"""
        print("===載入腳本按鈕被點擊===")  # 添加調試輸出
        self.log_message("嘗試載入腳本...")
        
        file_path = filedialog.askopenfilename(
            title="選擇腳本檔案",
            filetypes=[("文本檔案", "*.txt"), ("所有檔案", "*.*")],
            initialdir=os.path.dirname(os.path.abspath(__file__))  # 從當前目錄開始
        )
        
        if not file_path:
            self.log_message("未選擇文件")
            print("使用者取消選擇文件")
            return
        
        try:
            # 讀取文件內容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"讀取到的腳本內容長度: {len(content)}")
            
            if not content.strip():
                self.log_message(f"載入的腳本文件為空: {os.path.basename(file_path)}")
                print(f"警告: 載入的腳本文件為空")
                messagebox.showwarning("警告", "載入的腳本文件是空的")
                return
            
            # 更新UI和內部狀態
            self.script_text.delete(1.0, tk.END)
            self.script_text.insert(tk.END, content)
            
            # 確保更新script_content屬性，這樣執行腳本時能正確取得內容
            self.script_content = content
            
            # 檢查腳本內容是否被正確設置
            text_content = self.script_text.get(1.0, tk.END).strip()
            print(f"腳本載入後文本區域內容長度: {len(text_content)}")
            print(f"腳本載入後script_content長度: {len(self.script_content)}")
            
            # 更新狀態
            self.status_var.set(f"已載入腳本: {os.path.basename(file_path)}")
            self.log_message(f"已成功載入腳本: {os.path.basename(file_path)}")
            print(f"成功載入腳本: {file_path}")
            
            # 載入腳本後啟用執行按鈕
            self.執行_btn.configure(state=tk.NORMAL)
            
        except UnicodeDecodeError:
            self.log_message(f"載入腳本失敗: 文件編碼不兼容")
            print(f"載入腳本錯誤: 文件編碼不兼容")
            messagebox.showerror("錯誤", f"載入腳本失敗: 文件編碼不兼容，請使用UTF-8編碼")
        except Exception as e:
            self.log_message(f"載入腳本失敗: {e}")
            print(f"載入腳本錯誤: {e}")
            messagebox.showerror("錯誤", f"載入腳本失敗: {e}")
    
    def on_save_script_click(self):
        """儲存腳本"""
        file_path = filedialog.asksaveasfilename(
            title="儲存腳本檔案",
            defaultextension=".txt",
            filetypes=[("文本檔案", "*.txt"), ("所有檔案", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            content = self.script_text.get(1.0, tk.END)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                self.status_var.set(f"已儲存腳本: {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("錯誤", f"儲存腳本失敗: {e}")
    
    def on_execute_click(self):
        """執行腳本按鈕點擊事件"""
        print("===執行腳本按鈕被點擊===")
        self.log_message("嘗試執行腳本...")
        self.execute_script()
    
    def execute_script(self, script_file=None):
        """執行腳本"""
        print("===execute_script 方法被調用===")
        
        # 獲取腳本內容（先從文字區域獲取，如果為空再從script_content屬性獲取）
        script_content = self.script_text.get(1.0, tk.END).strip()
        print(f"從文本區域獲取的腳本內容長度: {len(script_content)}")
        
        if not script_content:
            script_content = self.script_content.strip() if hasattr(self, 'script_content') and self.script_content else ""
            print(f"從script_content屬性獲取的腳本內容長度: {len(script_content)}")
            
        if not script_content:
            # 嘗試從temp_script.txt載入，如果存在的話
            temp_script = "temp_script.txt"
            if os.path.exists(temp_script):
                try:
                    with open(temp_script, "r", encoding="utf-8") as f:
                        script_content = f.read().strip()
                    print(f"從臨時腳本文件載入的內容長度: {len(script_content)}")
                except Exception as e:
                    print(f"讀取臨時腳本文件失敗: {e}")
        
        if not script_content:
            print("沒有找到腳本內容")
            messagebox.showerror("錯誤", "請先載入或輸入腳本內容")
            return
            
        if self.executing:
            print("腳本正在執行中")
            messagebox.showinfo("提示", "腳本正在執行中，請等待完成")
            return
        
        self.executing = True
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, "正在執行腳本...\n")
        
        # 更新script_content屬性，確保保存了當前要執行的腳本
        self.script_content = script_content
        print(f"已更新script_content屬性，當前長度: {len(self.script_content)}")
        
        # 確保script_text中也有相同的內容
        if self.script_text.get(1.0, tk.END).strip() != script_content:
            self.script_text.delete(1.0, tk.END)
            self.script_text.insert(tk.END, script_content)
            print("已更新script_text內容")
        
        # 保存臨時腳本文件
        if script_file is None:
            script_file = "temp_script.txt"
            try:
                with open(script_file, "w", encoding="utf-8") as f:
                    f.write(script_content)
                    print(f"成功寫入臨時腳本文件: {script_file}，內容長度: {len(script_content)}")
            except Exception as e:
                print(f"保存臨時腳本失敗: {e}")
                messagebox.showerror("錯誤", f"保存臨時腳本失敗: {str(e)}")
                self.executing = False
                return
        
        # 更新按鈕狀態
        self.執行_btn.configure(state=tk.DISABLED)
        self.載入_btn.configure(state=tk.DISABLED)
        self.record_btn.configure(state=tk.DISABLED)
        self.record_local_btn.configure(state=tk.DISABLED)
        self.record_test_btn.configure(state=tk.DISABLED)
        
        # 這裡將由main.py中設置的實現取代
        # 啟動瀏覽器自動化
        try:
            # 如果已經由main.py替換了execute_script方法
            if hasattr(self, '_execute_script_replaced') and self._execute_script_replaced:
                print("使用main.py提供的execute_script替換實現")
                # 執行由main.py提供的實現
                # 這部分代碼不會被執行，因為函數會被替換
                pass
            else:
                print("使用app.py原始的execute_script實現")
                # 如果沒有被替換，則使用原始的實現
                asyncio.run_coroutine_threadsafe(self._execute_script_async(script_file), self.loop)
        except Exception as e:
            print(f"執行腳本時發生異常: {e}")
            self.log_message(f"執行腳本時出錯: {str(e)}")
            self.executing = False
            # 恢復按鈕狀態
            self.執行_btn.configure(state=tk.NORMAL)
            self.載入_btn.configure(state=tk.NORMAL)
            self.record_btn.configure(state=tk.NORMAL)
            self.record_local_btn.configure(state=tk.NORMAL)
            self.record_test_btn.configure(state=tk.NORMAL)
    
    async def _execute_script_async(self, script_file):
        """非同步執行腳本"""
        try:
            # 創建瀏覽器自動化實例
            self.browser = BrowserAutomation(
                log_callback=self.log_message,
                on_script_end=self.on_script_execution_end
            )
            
            # 啟動瀏覽器
            await self.browser.start_browser(headless=False)
            
            # 執行腳本
            await self.browser.execute_script(script_file)
            
        except Exception as e:
            self.log_message(f"執行腳本時出錯: {str(e)}")
            self.root.after(0, self.on_script_execution_end)
            
    def on_script_execution_end(self):
        """腳本執行完成的回調"""
        self.executing = False
        
        # 更新按鈕狀態
        self.執行_btn.configure(state=tk.NORMAL)
        self.載入_btn.configure(state=tk.NORMAL)
        self.record_btn.configure(state=tk.NORMAL)
        self.record_local_btn.configure(state=tk.NORMAL)
        self.record_test_btn.configure(state=tk.NORMAL)
        
        # 關閉瀏覽器
        if hasattr(self, 'browser') and self.browser:
            asyncio.run_coroutine_threadsafe(self.browser.close_browser(), self.loop)
            self.browser = None
        
        self.log_message("腳本執行完成")
    
    def on_clear_script_click(self):
        """清空腳本"""
        if messagebox.askyesno("確認", "確定要清空當前腳本內容嗎?"):
            self.script_text.delete(1.0, tk.END)
            self.status_var.set("腳本已清空")
    
    # 輔助函數
    def append_script(self, line):
        """向腳本中添加一行"""
        current_text = self.script_text.get(1.0, tk.END).rstrip()
        if current_text:
            self.script_text.insert(tk.END, f"\n{line}")
        else:
            self.script_text.insert(tk.END, line)
        self.script_text.see(tk.END)
    
    def enable_after_execution(self):
        """執行完成後調用"""
        self.status_var.set("腳本執行完成")
    
    def show_input_dialog(self, title, prompt):
        """顯示輸入對話框"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x150")
        dialog.transient(self.root)
        dialog.resizable(False, False)
        
        ttk.Label(dialog, text=prompt).pack(pady=(20, 10))
        
        input_var = tk.StringVar()
        entry = ttk.Entry(dialog, textvariable=input_var, width=40)
        entry.pack(pady=10)
        entry.focus_set()
        
        result = [None]
        
        def on_ok():
            result[0] = input_var.get()
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="確定", command=on_ok, width=10).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="取消", command=on_cancel, width=10).pack(side=tk.LEFT, padx=10)
        
        # 按Enter鍵確認
        dialog.bind("<Return>", lambda e: on_ok())
        
        dialog.wait_window()
        return result[0]

    def on_record_test_click(self):
        """錄製測試頁面"""
        # 設置錄製狀態
        self.is_recording = True
        self.record_btn.configure(state=tk.DISABLED)
        self.record_local_btn.configure(state=tk.DISABLED)
        self.record_test_btn.configure(state=tk.DISABLED)
        self.pause_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.NORMAL)
        
        # 啟用驗證點按鈕
        self.enable_recording_buttons()
        
        self.status_var.set("正在錄製測試頁面...")
        
        # 添加錄製開始標記
        self.append_script("# 錄製開始 (測試頁面): " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # 使用預設的測試頁面
        file_path = os.path.join(os.getcwd(), "web", "test_page.html")
        if not os.path.exists(file_path):
            messagebox.showerror("錯誤", f"找不到測試頁面: {file_path}")
            self.on_stop_click()
            return
            
        # 將檔案路徑轉換為file://URL格式
        file_url = f"file://{file_path}"
        
        # 啟動錄製瀏覽器功能 (會在main.py中實現)
        self.start_recording(file_url)

    def log_message(self, message):
        """記錄消息到輸出區域"""
        if hasattr(self, 'output_text'):
            self.output_text.insert(tk.END, f"{message}\n")
            self.output_text.see(tk.END)
            self.status_var.set(message if len(message) < 50 else message[:47] + "...")
            self.root.update_idletasks()
        print(message)

def main():
    """主函數"""
    root = tk.Tk()
    app = BrowserAutomationApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
