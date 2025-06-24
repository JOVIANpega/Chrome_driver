# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import os
import threading
import time
import logging

import utils

class CommandEditor:
    def __init__(self, parent, on_execute_commands=None):
        self.parent = parent
        self.on_execute_commands = on_execute_commands
        self.commands = []
        self.font_size = utils.DEFAULT_FONT_SIZE
        
        # 顏色方案 - 與主程式保持一致
        self.bg_color = "#ffffff"  # 白色背景
        self.content_bg = "#ffffff"  # 內容區域背景色
        
        # 建立 UI
        self.create_ui()
        
        # 載入現有命令
        self.load_commands()
    
    def create_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 標題
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(title_frame, text="Chrome 自動化命令編輯器", 
                 font=("Arial", self.font_size + 2, "bold")).pack(side=tk.LEFT)
        
        # 說明
        help_text = """此編輯器用於管理自動化測試命令。您可以新增、編輯和刪除命令，並保存到命令檔案中。"""
        help_frame = ttk.LabelFrame(main_frame, text="說明", padding="10")
        help_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(help_frame, text=help_text, wraplength=utils.WINDOW_WIDTH - 50, 
                 font=("Arial", self.font_size)).pack(fill=tk.X)
        
        # 命令編輯區域
        edit_frame = ttk.LabelFrame(main_frame, text="命令編輯", padding="10")
        edit_frame.pack(fill=tk.X, pady=5)
        
        # 命令輸入
        input_frame = ttk.Frame(edit_frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(input_frame, text="命令:", font=("Arial", self.font_size)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.command_entry = ttk.Entry(input_frame, width=50, font=("Arial", self.font_size))
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(input_frame, text="新增", command=self.add_command,
                  width=8).pack(side=tk.LEFT, padx=2)
        
        # 範例命令按鈕區域
        examples_frame = ttk.LabelFrame(main_frame, text="範例命令", padding="10")
        examples_frame.pack(fill=tk.X, pady=5)
        
        examples_button_frame = ttk.Frame(examples_frame)
        examples_button_frame.pack(fill=tk.X, pady=5)
        
        # 新增範例命令按鈕
        ttk.Button(examples_button_frame, text="測試字串", 
                  command=lambda: self.add_example_command("測試字串")).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(examples_button_frame, text="測試登入登出", 
                  command=lambda: self.add_example_command("測試登入登出")).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(examples_button_frame, text="測試表單填寫", 
                  command=lambda: self.add_example_command("測試表單填寫")).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(examples_button_frame, text="測試搜尋功能", 
                  command=lambda: self.add_example_command("測試搜尋功能")).pack(side=tk.LEFT, padx=5)
        
        # 命令列表
        list_frame = ttk.LabelFrame(main_frame, text="命令列表", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.command_text = scrolledtext.ScrolledText(list_frame, height=15, width=70, 
                                                    wrap=tk.WORD, font=("Arial", self.font_size), bg="#ffffff")
        self.command_text.pack(fill=tk.BOTH, expand=True)
        
        # 按鈕區域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="載入命令", command=self.load_commands, 
                  width=15).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="保存命令", command=self.save_commands, 
                  width=15).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="清除所有", command=self.clear_commands, 
                  width=15).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="執行命令", command=self.execute_commands, 
                  width=15).pack(side=tk.RIGHT, padx=5)
    
    def set_font_size(self, size):
        """設定字體大小"""
        self.font_size = size
        
        # 更新 UI 元素的字體大小
        for widget in self.parent.winfo_children():
            self.update_widget_font(widget)
    
    def update_widget_font(self, widget):
        """遞迴更新小部件的字體大小"""
        try:
            widget_class = widget.winfo_class()
            if widget_class in ('TLabel', 'Label'):
                widget.configure(font=('Arial', self.font_size))
            elif widget_class in ('TButton', 'Button'):
                widget.configure(font=('Arial', self.font_size))
            elif widget_class in ('TEntry', 'Entry'):
                widget.configure(font=('Arial', self.font_size))
            elif widget_class == 'Text':
                widget.configure(font=('Arial', self.font_size))
            elif widget_class == 'Scrolledtext':
                widget.configure(font=('Arial', self.font_size))
        except (tk.TclError, AttributeError):
            pass
        
        # 遞迴處理子部件
        try:
            for child in widget.winfo_children():
                self.update_widget_font(child)
        except (AttributeError, tk.TclError):
            pass
    
    def add_command(self):
        """新增命令"""
        command = self.command_entry.get().strip()
        if not command:
            messagebox.showwarning("警告", "請輸入命令")
            return
        
        # 新增命令到列表
        self.commands.append(command)
        self.update_command_display()
        
        # 清空輸入
        self.command_entry.delete(0, tk.END)
    
    def update_command_display(self):
        """更新命令顯示"""
        self.command_text.delete(1.0, tk.END)
        for i, cmd in enumerate(self.commands, 1):
            self.command_text.insert(tk.END, f"{i}. {cmd}\n")
    
    def load_commands(self):
        """載入命令"""
        try:
            commands_data = utils.read_commands()
            # 將命令數據轉換為純文本命令列表
            self.commands = []
            for cmd, params in commands_data:
                if cmd == "NAV_SEQUENCE":
                    # 處理導航序列
                    sequence_name = params[0]
                    sequence_commands = params[1:]
                    self.commands.append(f"NAV_SEQUENCE_START={sequence_name}")
                    for seq_cmd in sequence_commands:
                        self.commands.append(seq_cmd)
                    self.commands.append("NAV_SEQUENCE_END")
                else:
                    # 處理一般命令
                    param_text = " || ".join(params)
                    self.commands.append(f"{cmd}={param_text}")
            
            self.update_command_display()
            logging.info(f"已從 command.txt 加載 {len(self.commands)} 個命令")
        except Exception as e:
            messagebox.showerror("錯誤", f"載入命令時發生錯誤: {str(e)}")
            logging.error(f"載入命令時發生錯誤: {str(e)}")
    
    def save_commands(self):
        """保存命令"""
        try:
            with open(utils.COMMAND_FILE, 'w', encoding='utf-8') as f:
                for cmd in self.commands:
                        f.write(f"{cmd}\n")
            messagebox.showinfo("保存", "命令已成功保存")
            logging.info(f"已保存 {len(self.commands)} 個命令到 command.txt")
        except Exception as e:
            messagebox.showerror("錯誤", f"保存命令時發生錯誤: {str(e)}")
            logging.error(f"保存命令時發生錯誤: {str(e)}")
    
    def clear_commands(self):
        """清除所有命令"""
        if messagebox.askyesno("確認", "確定要清除所有命令嗎？"):
            self.commands = []
            self.update_command_display()
    
    def execute_commands(self):
        """執行命令"""
        if not self.commands:
            messagebox.showwarning("警告", "沒有命令可執行")
            return
        
        if self.on_execute_commands:
            self.on_execute_commands()
        else:
            messagebox.showinfo("執行", "命令執行功能尚未實現")
    
    def add_example_command(self, example_type):
        """新增範例命令"""
        if example_type == "測試字串":
            commands = [
                "VERIFY_TEXT_EXISTS=歡迎使用 Chrome 自動化測試",
                "VERIFY_TEXT_CONTAINS=自動化 || 測試",
                "VERIFY_TEXT_NOT_EXISTS=錯誤訊息",
                "VERIFY_TEXT_SIMILAR=歡迎使用自動化測試 || 0.8"
            ]
            for cmd in commands:
                self.commands.append(cmd)
            
        elif example_type == "測試登入登出":
            commands = [
                "LOGIN=admin || password123",
                "VERIFY_TEXT_EXISTS=登入成功",
                "CLICK_BY_ID=logout-button",
                "VERIFY_TEXT_EXISTS=您已登出系統"
            ]
            for cmd in commands:
                self.commands.append(cmd)
            
        elif example_type == "測試表單填寫":
            commands = [
                "TYPE=username-field || test_user",
                "TYPE=email-field || test@example.com",
                "TYPE=password-field || secure_password",
                "CLICK_BY_ID=submit-button",
                "VERIFY_TEXT_EXISTS=表單提交成功"
            ]
            for cmd in commands:
                self.commands.append(cmd)
            
        elif example_type == "測試搜尋功能":
            commands = [
                "TYPE=search-box || 測試關鍵字",
                "CLICK_BY_ID=search-button",
                "WAIT=2",
                "VERIFY_TEXT_EXISTS=搜尋結果",
                "VERIFY_COUNT=result-item || 5"
            ]
            for cmd in commands:
                self.commands.append(cmd)
        
        # 更新顯示
        self.update_command_display()
        messagebox.showinfo("範例命令", f"已新增 {example_type} 範例命令")


if __name__ == "__main__":
    # 測試代碼
    root = tk.Tk()
    root.withdraw()  # 隱藏主窗口
    
    editor = CommandEditor(root)
    
    root.mainloop() 