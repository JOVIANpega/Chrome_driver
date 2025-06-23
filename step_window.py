# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, font
import logging
import utils

class StepWindow:
    def __init__(self, parent: tk.Tk) -> None:
        """初始化步驟視窗"""
        self.window = tk.Toplevel(parent)
        self.window.title("執行步驟")
        self.window.geometry("600x400")
        self.window.protocol("WM_DELETE_WINDOW", self.hide_window)  # 關閉時隱藏而非銷毀
        
        # 載入設置
        self.settings = utils.load_settings()
        self.font_size = self.settings.get("font_size", utils.DEFAULT_FONT_SIZE)
        
        # 創建 UI
        self.create_ui()
        
        # 步驟列表
        self.steps = []
        self.current_step = -1
        self.failed_steps = set()
        
        # 顯示視窗
        self.window.update()
        self.window.deiconify()
    
    def create_ui(self) -> None:
        """創建使用者介面"""
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 工具列
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        # 字體大小調整
        ttk.Label(toolbar, text="字體大小:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.decrease_font = ttk.Button(toolbar, text="-", width=2, command=self.decrease_font_size)
        self.decrease_font.pack(side=tk.LEFT)
        
        self.font_size_var = tk.StringVar(value=str(self.font_size))
        font_size_label = ttk.Label(toolbar, textvariable=self.font_size_var, width=2)
        font_size_label.pack(side=tk.LEFT, padx=5)
        
        self.increase_font = ttk.Button(toolbar, text="+", width=2, command=self.increase_font_size)
        self.increase_font.pack(side=tk.LEFT)
        
        # 保存按鈕
        self.save_button = ttk.Button(toolbar, text="保存設置", command=self.save_settings)
        self.save_button.pack(side=tk.RIGHT, padx=5)

        # 狀態指示
        ttk.Label(toolbar, text="進度:").pack(side=tk.RIGHT, padx=5)
        self.progress_var = tk.StringVar(value="0/0")
        ttk.Label(toolbar, textvariable=self.progress_var).pack(side=tk.RIGHT)
        
        # 步驟列表
        self.step_list = tk.Listbox(main_frame, font=("Arial", self.font_size))
        self.step_list.pack(fill=tk.BOTH, expand=True)
        
        # 滾動條
        scrollbar = ttk.Scrollbar(self.step_list, orient=tk.VERTICAL, command=self.step_list.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.step_list.config(yscrollcommand=scrollbar.set)
        
        # 結果摘要
        self.summary_frame = ttk.LabelFrame(main_frame, text="測試結果摘要", padding="10")
        self.summary_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.summary_text = tk.Text(self.summary_frame, height=5, font=("Arial", self.font_size))
        self.summary_text.pack(fill=tk.BOTH, expand=True)
        self.summary_text.config(state=tk.DISABLED)
        
        # 更新UI
        self.update_font()
    
    def increase_font_size(self) -> None:
        """增加字體大小"""
        if self.font_size < utils.MAX_FONT_SIZE:
            self.font_size += 1
            self.font_size_var.set(str(self.font_size))
            self.update_font()
    
    def decrease_font_size(self) -> None:
        """減小字體大小"""
        if self.font_size > utils.MIN_FONT_SIZE:
            self.font_size -= 1
            self.font_size_var.set(str(self.font_size))
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
    
    def destroy(self) -> None:
        """銷毀視窗"""
        self.window.destroy() 