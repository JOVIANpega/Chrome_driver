# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk
from typing import List, Optional
import utils

class StepWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk) -> None:
        super().__init__(parent)
        self.title("執行步驟")
        
        # 字體大小控制
        self.font_size = utils.DEFAULT_FONT_SIZE
        
        # 設定視窗大小和位置（靠右側中間）
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_position = screen_width - utils.STEP_WINDOW_WIDTH - 20  # 距離右邊 20 像素
        y_position = (screen_height - utils.STEP_WINDOW_HEIGHT) // 2  # 垂直置中
        self.geometry(f"{utils.STEP_WINDOW_WIDTH}x{utils.STEP_WINDOW_HEIGHT}+{x_position}+{y_position}")
        
        # 設定視窗樣式
        self.attributes("-topmost", True)  # 保持在最上層
        self.protocol("WM_DELETE_WINDOW", lambda: None)  # 禁用關閉按鈕
        
        # 建立標題列框架
        title_frame = ttk.Frame(self)
        title_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # 標題
        title_label = ttk.Label(title_frame, text="執行步驟", font=("微軟正黑體", 10, "bold"))
        title_label.pack(side=tk.LEFT, padx=5)
        
        # 字體大小控制按鈕
        font_control_frame = ttk.Frame(title_frame)
        font_control_frame.pack(side=tk.LEFT, padx=10)
        
        decrease_button = ttk.Button(font_control_frame, text="-", width=2, 
                                   command=self.decrease_font_size)
        decrease_button.pack(side=tk.LEFT)
        
        increase_button = ttk.Button(font_control_frame, text="+", width=2, 
                                   command=self.increase_font_size)
        increase_button.pack(side=tk.LEFT)
        
        # 最小化按鈕
        minimize_button = ttk.Button(title_frame, text="─", width=2, command=self.iconify)
        minimize_button.pack(side=tk.RIGHT, padx=2)
        
        # 建立主要內容框架（可滾動）
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 建立Canvas和Scrollbar
        self.canvas = tk.Canvas(self.main_frame)
        self.scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", 
                                      command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        # 設定Canvas的滾動區域
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # 在Canvas中創建視窗
        self.canvas_frame = self.canvas.create_window((0, 0), 
                                                    window=self.scrollable_frame, 
                                                    anchor="nw")
        
        # 配置Canvas和Scrollbar
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 設定樣式
        self.setup_styles()
        
        # 初始化步驟列表
        self.steps: List[str] = []
        self.step_status: List[str] = []  # 用於存儲每個步驟的狀態: "done", "current", "pending", "failed"
        self.current_step: int = -1
        self.step_labels: List[ttk.Label] = []
        
        # 加入拖曳功能
        self.bind('<Button-1>', self.start_move)
        self.bind('<B1-Motion>', self.on_move)
        
        # 加入滾輪滾動功能
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # 拖曳變數
        self.x: int = 0
        self.y: int = 0
    
    def setup_styles(self) -> None:
        """設定樣式"""
        style = ttk.Style()
        style.configure("Current.TLabel", 
                       foreground="blue", 
                       font=("微軟正黑體", self.font_size, "bold"))
        style.configure("Done.TLabel", 
                       foreground="green", 
                       font=("微軟正黑體", self.font_size))
        style.configure("Pending.TLabel", 
                       foreground="gray", 
                       font=("微軟正黑體", self.font_size))
        style.configure("Failed.TLabel", 
                       foreground="red", 
                       font=("微軟正黑體", self.font_size))
    
    def increase_font_size(self) -> None:
        """增加字體大小"""
        if self.font_size < 20:  # 設定最大字體大小
            self.font_size += 1
            self.setup_styles()
            self.update_steps()
    
    def decrease_font_size(self) -> None:
        """減小字體大小"""
        if self.font_size > 6:  # 設定最小字體大小
            self.font_size -= 1
            self.setup_styles()
            self.update_steps()
    
    def _on_mousewheel(self, event: tk.Event) -> None:
        """處理滾輪事件"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def set_steps(self, steps: List[str]) -> None:
        """設定步驟列表"""
        self.steps = steps
        self.step_status = ["pending"] * len(steps)  # 初始化所有步驟為待處理
        self.current_step = -1
        self.update_steps()
    
    def update_steps(self) -> None:
        """更新步驟顯示"""
        # 清除現有的標籤
        for label in self.step_labels:
            label.destroy()
        self.step_labels.clear()
        
        # 重新創建所有步驟標籤
        for i, step in enumerate(self.steps):
            status = self.step_status[i]
            
            if status == "done":
                style = "Done.TLabel"
                prefix = "✓ "
            elif status == "current":
                style = "Current.TLabel"
                prefix = "➤ "
            elif status == "failed":
                style = "Failed.TLabel"
                prefix = "✗ "
            else:  # pending
                style = "Pending.TLabel"
                prefix = "○ "
            
            label = ttk.Label(self.scrollable_frame, 
                            text=f"{prefix}{step}", 
                            style=style,
                            wraplength=200)  # 允許文字換行
            label.pack(pady=2, padx=5, anchor="w")
            self.step_labels.append(label)
        
        # 更新滾動區域
        self.scrollable_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
        # 如果是當前步驟，確保它可見
        if self.current_step >= 0 and self.scrollable_frame.winfo_height() > 0:
            self.canvas.yview_moveto(
                (self.current_step * 30) / max(1, self.scrollable_frame.winfo_height())
            )
    
    def set_current_step(self, step_index: int) -> None:
        """設定當前步驟"""
        if 0 <= step_index < len(self.steps):
            # 將前一個當前步驟標記為完成
            if self.current_step >= 0 and self.current_step < len(self.step_status):
                if self.step_status[self.current_step] == "current":
                    self.step_status[self.current_step] = "done"
            
            self.current_step = step_index
            self.step_status[step_index] = "current"
            self.update_steps()
    
    def mark_step_failed(self, step_index: int) -> None:
        """標記步驟為失敗"""
        if 0 <= step_index < len(self.steps):
            self.step_status[step_index] = "failed"
            self.update_steps()
    
    def add_step(self, step_text: str) -> int:
        """新增步驟"""
        self.steps.append(step_text)
        self.step_status.append("pending")
        self.update_steps()
        return len(self.steps) - 1  # 返回新步驟的索引
    
    def start_move(self, event: tk.Event) -> None:
        """開始拖曳視窗"""
        self.x = event.x
        self.y = event.y

    def on_move(self, event: tk.Event) -> None:
        """處理視窗拖曳"""
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}") 