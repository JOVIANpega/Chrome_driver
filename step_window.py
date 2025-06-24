# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, font
import logging
import utils

class StepWindow:
    def __init__(self, parent: tk.Tk, font_size=None) -> None:
        """初始化步驟視窗"""
        self.window = tk.Toplevel(parent)
        self.window.title("執行步驟")
        self.window.geometry("350x600")
        self.window.protocol("WM_DELETE_WINDOW", self.hide_window)  # 關閉時隱藏而非銷毀
        
        # 載入設置
        self.settings = utils.load_settings()
        self.font_size = font_size if font_size is not None else self.settings.get("font_size", utils.DEFAULT_FONT_SIZE)
        
        # 創建 UI
        self.create_ui()
        
        # 步驟列表
        self.steps = []
        self.current_step = -1
        self.failed_steps = set()
        
        # 初始位置設定為右側
        self.set_default_position()
        
        # 使窗口始終置頂
        self.window.attributes("-topmost", True)
        
        # 顯示視窗
        self.window.update()
        self.window.deiconify()
    
    def create_ui(self) -> None:
        """創建使用者介面"""
        # 設置窗口背景色，使其更易區分
        self.window.configure(background="#f0f8ff")  # 淺藍色背景
        
        main_frame = ttk.Frame(self.window, padding="5")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 步驟列表標題（添加樣式）
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 5))
        
        title_label = ttk.Label(title_frame, text="執行步驟", font=("Arial", self.font_size + 2, "bold"))
        title_label.pack(side=tk.LEFT)
        
        # 工具列
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        # 進度指示
        self.progress_var = tk.StringVar(value="0/0")
        progress_frame = ttk.Frame(toolbar)
        progress_frame.pack(side=tk.LEFT)
        
        ttk.Label(progress_frame, text="進度:").pack(side=tk.LEFT)
        ttk.Label(progress_frame, textvariable=self.progress_var, font=("Arial", self.font_size, "bold")).pack(side=tk.LEFT, padx=5)
        
        # 步驟列表
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 添加邊框和背景色
        self.step_list = tk.Listbox(list_frame, font=("Arial", self.font_size), 
                                   background="white", selectbackground="#d0e0ff", 
                                   relief=tk.SUNKEN, borderwidth=2)
        self.step_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 滾動條
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.step_list.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.step_list.config(yscrollcommand=scrollbar.set)
        
        # 結果摘要
        self.summary_frame = ttk.LabelFrame(main_frame, text="測試結果摘要")
        self.summary_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.summary_text = tk.Text(self.summary_frame, height=4, font=("Arial", self.font_size),
                                   background="#f8f8f8", relief=tk.SUNKEN, borderwidth=2)
        self.summary_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.summary_text.config(state=tk.DISABLED)
    
    def set_default_position(self) -> None:
        """設置默認位置在螢幕右側"""
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        window_width = 350
        window_height = min(600, screen_height - 100)
        
        x_position = screen_width - window_width - 10
        y_position = 50
        
        self.window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
    
    def set_position(self, x, y, width=None, height=None) -> None:
        """設置窗口位置和大小"""
        if width is None:
            width = 350
        if height is None:
            height = 600
        
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def set_font_size(self, size) -> None:
        """設置字體大小"""
        self.font_size = size
        self.settings["font_size"] = size
        self.update_font()
    
    def update_font(self) -> None:
        """更新字體大小"""
        self.step_list.config(font=("Arial", self.font_size))
        self.summary_text.config(font=("Arial", self.font_size))
    
    def save_settings(self) -> None:
        """保存設置"""
        self.settings["font_size"] = self.font_size
        utils.save_settings(self.settings)
    
    def set_steps(self, steps: list) -> None:
        """設定步驟列表"""
        self.steps = steps
        self.step_list.delete(0, tk.END)
        
        for i, step in enumerate(steps):
            self.step_list.insert(tk.END, f"{i+1}. {step}")
        
        self.current_step = -1
        self.failed_steps = set()
        self.update_progress()
    
    def add_step(self, step_text: str) -> int:
        """新增步驟，返回步驟索引"""
        step_index = len(self.steps)
        self.steps.append(step_text)
        self.step_list.insert(tk.END, f"{step_index+1}. {step_text}")
        self.update_progress()
        return step_index
    
    def set_current_step(self, step_index: int) -> None:
        """設定當前步驟"""
        if 0 <= step_index < len(self.steps):
            # 恢復前一個步驟的顏色
            if 0 <= self.current_step < len(self.steps):
                self.step_list.itemconfig(
                    self.current_step,
                    background="",
                    foreground="red" if self.current_step in self.failed_steps else "black"
                )
            
            # 設定當前步驟
            self.current_step = step_index
            
            # 設定當前步驟的顏色
            self.step_list.itemconfig(
                step_index,
                background="#e0f0ff",
                foreground="red" if step_index in self.failed_steps else "black"
            )
            
            # 確保當前步驟可見
            self.step_list.see(step_index)
            
            # 更新進度
            self.update_progress()
    
    def mark_step_failed(self, step_index: int) -> None:
        """標記步驟為失敗"""
        if 0 <= step_index < len(self.steps):
            self.failed_steps.add(step_index)
            
            # 更新步驟顏色
            bg_color = "#e0f0ff" if step_index == self.current_step else ""
            self.step_list.itemconfig(step_index, foreground="red", background=bg_color)
            
            # 更新測試結果
            step_text = self.steps[step_index]
            utils.update_test_results(step_text, False)
    
    def mark_step_passed(self, step_index: int) -> None:
        """標記步驟為成功"""
        if 0 <= step_index < len(self.steps):
            if step_index in self.failed_steps:
                self.failed_steps.remove(step_index)
            
            # 更新步驟顏色
            bg_color = "#e0f0ff" if step_index == self.current_step else ""
            self.step_list.itemconfig(step_index, foreground="green", background=bg_color)
            
            # 更新測試結果
            step_text = self.steps[step_index]
            utils.update_test_results(step_text, True)
    
    def update_progress(self) -> None:
        """更新進度顯示"""
        if self.current_step >= 0 and len(self.steps) > 0:
            self.progress_var.set(f"{self.current_step+1}/{len(self.steps)}")
        else:
            self.progress_var.set("0/0")
    
    def update_summary(self) -> None:
        """更新測試結果摘要"""
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        
        total_steps = len(self.steps)
        failed_count = len(self.failed_steps)
        passed_count = total_steps - failed_count
        
        summary = f"測試結果摘要:\n"
        summary += f"總步驟數: {total_steps}\n"
        summary += f"通過數: {passed_count} (通過率: {passed_count/total_steps*100:.1f}%)\n"
        summary += f"失敗數: {failed_count}\n\n"
        
        if failed_count > 0:
            summary += "失敗的步驟:\n"
            for index in sorted(self.failed_steps):
                if index < len(self.steps):
                    summary += f"- {self.steps[index]}\n"
        
        self.summary_text.insert(tk.END, summary)
        self.summary_text.config(state=tk.DISABLED)
    
    def hide_window(self) -> None:
        """隱藏視窗"""
        self.window.withdraw()
    
    def show_window(self) -> None:
        """顯示視窗"""
        self.window.deiconify()
        self.window.lift()
        self.window.attributes("-topmost", True)  # 確保窗口在最前面
    
    def destroy(self) -> None:
        """銷毀視窗"""
        self.window.destroy() 