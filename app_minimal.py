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
        
        # 腳本區域
        script_frame = ttk.LabelFrame(main_frame, text="腳本編輯")
        script_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.script_text = scrolledtext.ScrolledText(script_frame, wrap=tk.WORD)
        self.script_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 按鈕區域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="載入腳本", 
                 command=self.on_load_script_click).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="執行腳本", 
                 command=self.on_run_script_click).pack(side=tk.LEFT, padx=5)
    
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
        
    def enable_after_execution(self):
        """執行完成後調用"""
        self.status_var.set("腳本執行完成")

def main():
    """主函數"""
    root = tk.Tk()
    app = BrowserAutomationApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 