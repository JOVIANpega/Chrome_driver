import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import os
import sys
import threading
from datetime import datetime

# 常數定義
APP_TITLE = "Chrome E2E助手"
APP_VERSION = "1.0.0"
DEFAULT_FONT_SIZE = 12
CONFIG_FILE = "config.json"
DEFAULT_WINDOW_SIZE = "800x600"

class BrowserAutomationApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_TITLE} v{APP_VERSION}")
        self.root.geometry(DEFAULT_WINDOW_SIZE)
        
        # 設定變數
        self.font_size = tk.IntVar(value=DEFAULT_FONT_SIZE)
        self.is_recording = False
        self.current_script = []
        
        # 建立UI
        self.create_ui()
    
    def create_ui(self):
        """創建使用者介面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 狀態欄
        self.status_var = tk.StringVar(value="就緒")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=2)
        
        # 頂部控制區
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 錄製控制按鈕
        record_frame = ttk.Frame(control_frame)
        record_frame.pack(side=tk.LEFT)
        
        self.record_btn = ttk.Button(record_frame, text="開始錄製", width=15, 
                                    command=self.on_record_click)
        self.record_btn.pack(side=tk.LEFT, padx=5)
        
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
        
        # 腳本編輯區域
        script_frame = ttk.LabelFrame(main_frame, text="腳本編輯")
        script_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.script_text = scrolledtext.ScrolledText(script_frame, wrap=tk.WORD)
        self.script_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 底部功能按鈕
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        for text, cmd in [
            ("載入腳本", self.on_load_script_click),
            ("儲存腳本", self.on_save_script_click),
            ("執行腳本", self.on_run_script_click),
            ("清空腳本", self.on_clear_script_click)
        ]:
            btn = ttk.Button(button_frame, text=text, width=15, command=cmd)
            btn.pack(side=tk.LEFT, padx=5)
    
    # 錄製控制函數
    def on_record_click(self):
        """開始錄製"""
        self.is_recording = True
        self.record_btn.configure(state=tk.DISABLED)
        self.pause_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.NORMAL)
        
        # 啟用驗證點按鈕
        self.enable_recording_buttons()
        
        self.status_var.set("正在錄製中...")
        
        # 啟動瀏覽器並開始錄製 (此處將在main.py中替換為真實實現)
        self.append_script("# 錄製開始: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # 啟動錄製瀏覽器的功能會在main.py中實現
        self.start_recording()
    
    def start_recording(self):
        """啟動錄製 (此函數將在main.py中被替換)"""
        self.status_var.set("錄製功能已啟動 (此為預設實現，將被main.py替換)")
    
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
        file_path = filedialog.askopenfilename(
            title="選擇腳本檔案",
            filetypes=[("文本檔案", "*.txt"), ("所有檔案", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.script_text.delete(1.0, tk.END)
                self.script_text.insert(tk.END, content)
                self.status_var.set(f"已載入腳本: {os.path.basename(file_path)}")
        except Exception as e:
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
    
    def on_run_script_click(self):
        """執行腳本"""
        script_content = self.script_text.get(1.0, tk.END).strip()
        if not script_content:
            messagebox.showinfo("提示", "腳本內容為空，無法執行")
            return
        
        self.status_var.set("正在執行腳本...")
        self.execute_script(script_content)
    
    def execute_script(self, script_content):
        """執行腳本的方法 (會被main.py替換)"""
        self.status_var.set("執行腳本 (此為預設實現，會被main.py替換)")
    
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

def main():
    """主函數"""
    root = tk.Tk()
    app = BrowserAutomationApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
