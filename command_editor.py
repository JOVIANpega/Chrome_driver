# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import os
import threading
import time
import logging
import re

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
        self.highlight_color = "#FFFF99"  # 反黃色，用於高亮可編輯部分
        self.editing_border_color = "#0078D7"  # 藍色邊框，用於標示正在編輯的項目
        
        # 命令類型中英文對照表
        self.cmd_type_mapping = {
            "開啟網址": "NAVIGATE",
            "點擊元素（ID）": "CLICK_BY_ID",
            "點擊元素（CSS）": "CLICK_BY_CSS",
            "輸入文字": "TYPE",
            "等待時間（秒）": "WAIT",
            "驗證文字存在": "VERIFY_TEXT_EXISTS",
            "驗證文字不存在": "VERIFY_TEXT_NOT_EXISTS",
            "驗證文字包含": "VERIFY_TEXT_CONTAINS",
            "驗證文字相似度": "VERIFY_TEXT_SIMILAR",
            "登入帳號密碼": "LOGIN",
            "測試案例名稱": "TEST_CASE",
            "測試案例描述": "DESCRIPTION"
        }
        
        # 反向映射表 (英文 -> 中文)
        self.reverse_cmd_mapping = {v: k for k, v in self.cmd_type_mapping.items()}
        
        # 範例命令模板
        self.example_templates = {
            "請選擇範例...": None,
            "開啟本地HTML檔案": [
                "TEST_CASE=開啟本地HTML檔案測試",
                "DESCRIPTION=測試開啟本地HTML檔案功能",
                "NAVIGATE=web/360_TEST_WEBFILE.html",
                "WAIT=2",
                "VERIFY_TEXT_EXISTS=測試頁面"
            ],
            "開啟網路URL": [
                "TEST_CASE=開啟網路URL測試",
                "DESCRIPTION=測試開啟外部網站功能",
                "NAVIGATE=https://www.example.com",
                "WAIT=2",
                "VERIFY_TEXT_EXISTS=Example Domain"
            ],
            "基本登入測試": [
                "TEST_CASE=登入功能測試",
                "DESCRIPTION=測試使用者登入功能",
                "NAVIGATE=web/360_TEST_WEBFILE.html",
                "CLICK_BY_ID=username",
                "TYPE=admin",
                "CLICK_BY_ID=password",
                "TYPE=password123",
                "CLICK_BY_CSS=.login-button",
                "VERIFY_TEXT_EXISTS=登入成功"
            ],
            "表單填寫測試": [
                "TEST_CASE=表單填寫測試",
                "DESCRIPTION=測試表單自動填寫功能",
                "NAVIGATE=web/360_TEST_WEBFILE.html",
                "CLICK_BY_ID=name",
                "TYPE=測試使用者",
                "CLICK_BY_ID=email",
                "TYPE=test@example.com",
                "CLICK_BY_ID=phone",
                "TYPE=0912345678",
                "CLICK_BY_ID=submit-button",
                "VERIFY_TEXT_EXISTS=表單提交成功"
            ],
            "多欄位驗證測試": [
                "TEST_CASE=多欄位驗證測試",
                "DESCRIPTION=測試多個欄位的驗證功能",
                "NAVIGATE=web/360_TEST_WEBFILE.html",
                "CLICK_BY_ID=submit-button",
                "VERIFY_TEXT_EXISTS=請填寫必要欄位",
                "CLICK_BY_ID=username",
                "TYPE=test_user",
                "CLICK_BY_ID=email",
                "TYPE=test@example.com",
                "CLICK_BY_ID=submit-button",
                "VERIFY_TEXT_NOT_EXISTS=請填寫必要欄位",
                "VERIFY_TEXT_EXISTS=驗證成功"
            ],
            "搜尋功能測試": [
                "TEST_CASE=搜尋功能測試",
                "DESCRIPTION=測試網站搜尋功能",
                "NAVIGATE=web/360_TEST_WEBFILE.html",
                "CLICK_BY_ID=search-box",
                "TYPE=測試關鍵字",
                "CLICK_BY_ID=search-button",
                "WAIT=2",
                "VERIFY_TEXT_EXISTS=搜尋結果",
                "VERIFY_TEXT_CONTAINS=找到 || 筆結果"
            ],
            "等待與驗證測試": [
                "TEST_CASE=等待與驗證測試",
                "DESCRIPTION=測試等待和多重驗證功能",
                "NAVIGATE=web/360_TEST_WEBFILE.html",
                "CLICK_BY_ID=load-data",
                "WAIT=3",
                "VERIFY_TEXT_EXISTS=數據載入完成",
                "VERIFY_TEXT_CONTAINS=共載入",
                "VERIFY_TEXT_CONTAINS=筆數據"
            ],
            "元素點擊測試": [
                "TEST_CASE=元素點擊測試",
                "DESCRIPTION=測試不同方式的元素點擊",
                "NAVIGATE=web/360_TEST_WEBFILE.html",
                "CLICK_BY_ID=button1",
                "VERIFY_TEXT_EXISTS=按鈕1已點擊",
                "CLICK_BY_CSS=.button2",
                "VERIFY_TEXT_EXISTS=按鈕2已點擊",
                "WAIT=1",
                "CLICK_BY_CSS=#button3",
                "VERIFY_TEXT_EXISTS=按鈕3已點擊"
            ]
        }
        
        # 建立 UI
        self.create_ui()
        
        # 載入現有命令
        self.load_commands()
        
        # 選中的命令索引
        self.selected_command_index = None
        
        # 當前編輯的命令框架
        self.editing_frame = None
    
    def create_ui(self):
        # 設置樣式
        self.style = ttk.Style()
        
        # 設定黃色背景的輸入欄位樣式
        self.style.configure("Yellow.TEntry", fieldbackground=self.highlight_color)
        
        # 設定編輯中的框架樣式
        self.style.configure("Editing.TFrame", borderwidth=2, relief="solid")
        self.style.map("Editing.TFrame", background=[("active", self.editing_border_color)])
        
        # 主框架
        main_frame = ttk.Frame(self.parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 標題
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(title_frame, text="Chrome 自動化命令編輯器", 
                 font=("Arial", self.font_size + 2, "bold")).pack(side=tk.LEFT)
        
        # 說明
        help_text = """此編輯器用於管理自動化測試命令。黃色背景標示的欄位為可編輯的參數值。命令格式為「命令類型=參數值」，多參數以「||」分隔。"""
        help_frame = ttk.LabelFrame(main_frame, text="說明", padding="10")
        help_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(help_frame, text=help_text, wraplength=utils.WINDOW_WIDTH - 50, 
                 font=("Arial", self.font_size)).pack(fill=tk.X)
        
        # 範例命令選擇區
        examples_frame = ttk.LabelFrame(main_frame, text="範例命令模板", padding="10")
        examples_frame.pack(fill=tk.X, pady=5)
        
        examples_select_frame = ttk.Frame(examples_frame)
        examples_select_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(examples_select_frame, text="選擇範例:", 
                 font=("Arial", self.font_size)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.example_var = tk.StringVar()
        self.example_combo = ttk.Combobox(examples_select_frame, textvariable=self.example_var,
                                         values=list(self.example_templates.keys()),
                                         font=("Arial", self.font_size), width=30, state="readonly")
        self.example_combo.current(0)  # 設置默認值
        self.example_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.example_combo.bind("<<ComboboxSelected>>", self.on_example_selected)
        
        # 命令編輯區域
        self.edit_frame = ttk.LabelFrame(main_frame, text="命令編輯", padding="10")
        self.edit_frame.pack(fill=tk.X, pady=5)
        
        # 命令類型選擇
        cmd_type_frame = ttk.Frame(self.edit_frame)
        cmd_type_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(cmd_type_frame, text="命令類型:", font=("Arial", self.font_size)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.cmd_type_var = tk.StringVar()
        self.cmd_type_combo = ttk.Combobox(cmd_type_frame, textvariable=self.cmd_type_var, 
                                          values=list(self.cmd_type_mapping.keys()),
                                          font=("Arial", self.font_size), width=20, state="readonly")
        self.cmd_type_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.cmd_type_combo.bind("<<ComboboxSelected>>", self.on_cmd_type_selected)
        
        # 命令參數 (使用黃色背景標示)
        param_frame = ttk.Frame(self.edit_frame)
        param_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(param_frame, text="參數值:", font=("Arial", self.font_size)).pack(side=tk.LEFT, padx=(0, 5))
        
        # 使用自定義樣式的Entry，背景為黃色
        self.param_entry = ttk.Entry(param_frame, width=50, font=("Arial", self.font_size), style="Yellow.TEntry")
        self.param_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # 命令輸入 (完整命令)
        input_frame = ttk.Frame(self.edit_frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(input_frame, text="完整命令:", font=("Arial", self.font_size)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.command_entry = ttk.Entry(input_frame, width=50, font=("Arial", self.font_size))
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # 按鈕區域 (新增/更新/刪除)
        cmd_buttons_frame = ttk.Frame(self.edit_frame)
        cmd_buttons_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(cmd_buttons_frame, text="新增", command=self.add_command,
                  width=8).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(cmd_buttons_frame, text="更新", command=self.update_command,
                  width=8).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(cmd_buttons_frame, text="刪除", command=self.delete_command,
                  width=8).pack(side=tk.LEFT, padx=2)
        
        # 命令列表
        list_frame = ttk.LabelFrame(main_frame, text="命令列表", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 使用Listbox
        list_container = ttk.Frame(list_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        self.command_listbox = tk.Listbox(list_container, height=15, width=70, 
                                         font=("Arial", self.font_size), bg="#ffffff",
                                         selectbackground="#4a6984", selectforeground="#ffffff")
        self.command_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 添加滾動條
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.command_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.command_listbox.config(yscrollcommand=scrollbar.set)
        
        # 綁定選擇事件
        self.command_listbox.bind('<<ListboxSelect>>', self.on_command_selected)
        
        # 命令列表按鈕區域
        list_buttons_frame = ttk.Frame(list_frame)
        list_buttons_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(list_buttons_frame, text="清除全部命令", command=self.clear_commands, 
                  width=15).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(list_buttons_frame, text="儲存命令", command=self.save_commands, 
                  width=15).pack(side=tk.RIGHT, padx=5)
        
        # 按鈕區域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="載入命令", command=self.load_commands, 
                  width=15).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="執行命令", command=self.execute_commands, 
                  width=15).pack(side=tk.RIGHT, padx=5)
        
        # 命令上下移動按鈕
        move_frame = ttk.Frame(main_frame)
        move_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(move_frame, text="上移", command=self.move_command_up,
                  width=15).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(move_frame, text="下移", command=self.move_command_down,
                  width=15).pack(side=tk.LEFT, padx=5)
    
    def on_example_selected(self, event):
        """當選擇範例命令時"""
        selected = self.example_var.get()
        if selected in self.example_templates and self.example_templates[selected]:
            # 確認是否要清除現有命令
            if self.commands and messagebox.askyesno("確認", "要用範例命令替換現有命令嗎？"):
                self.commands = self.example_templates[selected].copy()
                self.update_command_display()
            elif not self.commands:
                self.commands = self.example_templates[selected].copy()
                self.update_command_display()
            
            # 重置下拉選單
            self.example_combo.current(0)
    
    def on_cmd_type_selected(self, event):
        """當選擇命令類型時，更新完整命令"""
        cmd_type_zh = self.cmd_type_var.get()
        if cmd_type_zh in self.cmd_type_mapping:
            cmd_type_en = self.cmd_type_mapping[cmd_type_zh]
            param = self.param_entry.get()
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, f"{cmd_type_en}={param}")
    
    def on_command_selected(self, event):
        """當從列表中選擇命令時"""
        selection = self.command_listbox.curselection()
        if selection:
            # 標記選中的命令
            self.selected_command_index = selection[0]
            command = self.commands[self.selected_command_index]
            
            # 更新命令編輯區域
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, command)
            
            # 解析命令類型和參數
            if "=" in command:
                cmd_type_en, param = command.split("=", 1)
                if cmd_type_en in self.reverse_cmd_mapping:
                    self.cmd_type_var.set(self.reverse_cmd_mapping[cmd_type_en])
                self.param_entry.delete(0, tk.END)
                self.param_entry.insert(0, param)
            
            # 高亮顯示編輯區域
            self.highlight_editing_frame()
    
    def highlight_editing_frame(self):
        """高亮顯示正在編輯的命令框架"""
        # 將編輯框架設為藍色邊框
        self.edit_frame.configure(style="Editing.TFrame")
        
        # 設置定時器，3秒後恢復正常顯示
        self.parent.after(3000, self.reset_editing_highlight)
    
    def reset_editing_highlight(self):
        """重置編輯框架的高亮顯示"""
        self.edit_frame.configure(style="")
    
    def validate_command_format(self, command):
        """驗證命令格式是否正確"""
        # 基本格式驗證：命令=參數
        pattern = r'^[A-Z_]+=.+$'
        if not re.match(pattern, command):
            return False, "命令格式錯誤，應為「命令=參數」格式"
        
        # 命令類型驗證
        cmd_type = command.split("=")[0]
        valid_cmd_types = list(self.reverse_cmd_mapping.keys())
        if cmd_type not in valid_cmd_types:
            return False, f"無效的命令類型：{cmd_type}"
        
        return True, ""
    
    def add_command(self):
        """新增命令"""
        command = self.command_entry.get().strip()
        if not command:
            messagebox.showwarning("警告", "請輸入命令")
            return
        
        # 驗證命令格式
        is_valid, error_msg = self.validate_command_format(command)
        if not is_valid:
            messagebox.showerror("格式錯誤", error_msg)
            return
        
        # 新增命令到列表
        self.commands.append(command)
        self.update_command_display()
        
        # 清空輸入
        self.command_entry.delete(0, tk.END)
        self.param_entry.delete(0, tk.END)
        self.cmd_type_var.set("")
    
    def update_command(self):
        """更新選中的命令"""
        if self.selected_command_index is not None:
            new_command = self.command_entry.get().strip()
            if not new_command:
                messagebox.showwarning("警告", "請輸入命令")
                return
            
            # 驗證命令格式
            is_valid, error_msg = self.validate_command_format(new_command)
            if not is_valid:
                messagebox.showerror("格式錯誤", error_msg)
                return
            
            self.commands[self.selected_command_index] = new_command
            self.update_command_display()
            self.command_entry.delete(0, tk.END)
            self.param_entry.delete(0, tk.END)
            self.cmd_type_var.set("")
            self.selected_command_index = None
    
    def delete_command(self):
        """刪除選中的命令"""
        if self.selected_command_index is not None:
            del self.commands[self.selected_command_index]
            self.update_command_display()
            self.command_entry.delete(0, tk.END)
            self.param_entry.delete(0, tk.END)
            self.cmd_type_var.set("")
            self.selected_command_index = None
    
    def move_command_up(self):
        """將選中的命令向上移動"""
        if self.selected_command_index is not None and self.selected_command_index > 0:
            self.commands[self.selected_command_index], self.commands[self.selected_command_index - 1] = \
                self.commands[self.selected_command_index - 1], self.commands[self.selected_command_index]
            self.update_command_display()
            self.command_listbox.selection_clear(0, tk.END)
            self.command_listbox.selection_set(self.selected_command_index - 1)
            self.selected_command_index -= 1
    
    def move_command_down(self):
        """將選中的命令向下移動"""
        if self.selected_command_index is not None and self.selected_command_index < len(self.commands) - 1:
            self.commands[self.selected_command_index], self.commands[self.selected_command_index + 1] = \
                self.commands[self.selected_command_index + 1], self.commands[self.selected_command_index]
            self.update_command_display()
            self.command_listbox.selection_clear(0, tk.END)
            self.command_listbox.selection_set(self.selected_command_index + 1)
            self.selected_command_index += 1
    
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
            elif widget_class == 'Listbox':
                widget.configure(font=('Arial', self.font_size))
            elif widget_class == 'TCombobox':
                widget.configure(font=('Arial', self.font_size))
        except (tk.TclError, AttributeError):
            pass
        
        # 遞迴處理子部件
        try:
            for child in widget.winfo_children():
                self.update_widget_font(child)
        except (AttributeError, tk.TclError):
            pass
    
    def update_command_display(self):
        """更新命令顯示"""
        self.command_listbox.delete(0, tk.END)
        for i, cmd in enumerate(self.commands, 1):
            self.command_listbox.insert(tk.END, f"{i}. {cmd}")
    
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
            messagebox.showinfo("保存", "命令已成功保存到 command.txt")
            logging.info(f"已保存 {len(self.commands)} 個命令到 command.txt")
        except Exception as e:
            messagebox.showerror("錯誤", f"保存命令時發生錯誤: {str(e)}")
            logging.error(f"保存命令時發生錯誤: {str(e)}")
    
    def clear_commands(self):
        """清除所有命令"""
        if messagebox.askyesno("確認", "確定要清除所有命令嗎？"):
            self.commands = []
            self.update_command_display()
            self.command_entry.delete(0, tk.END)
            self.param_entry.delete(0, tk.END)
            self.cmd_type_var.set("")
            self.selected_command_index = None
    
    def execute_commands(self):
        """執行命令"""
        if not self.commands:
            messagebox.showwarning("警告", "沒有命令可執行")
            return
        
        if self.on_execute_commands:
            self.on_execute_commands()
        else:
            messagebox.showinfo("執行", "命令執行功能尚未實現")


if __name__ == "__main__":
    # 測試代碼
    root = tk.Tk()
    root.withdraw()  # 隱藏主窗口
    
    editor = CommandEditor(root)
    
    root.mainloop() 