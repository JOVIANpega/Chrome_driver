# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import os
from typing import List, Tuple, Dict, Any, Optional
import logging

import utils

class CommandEditor:
    def __init__(self, parent_frame, on_execute_commands=None) -> None:
        """初始化命令编辑器（作为框架而非窗口）"""
        # 主框架
        self.frame = parent_frame
        
        # 当前命令列表
        self.commands = []
        
        # 回调函数 - 当用户点击"执行这些命令"时调用
        self.on_execute_commands = on_execute_commands
        
        # 创建 UI
        self.create_ui()
        
        # 加载现有命令
        self.load_commands_from_file()
    
    def create_ui(self) -> None:
        """创建用户界面"""
        # 清空框架中的所有小部件
        for widget in self.frame.winfo_children():
            widget.destroy()
        
        # 创建顶部区域
        top_frame = ttk.Frame(self.frame)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 左侧简化控制区域
        control_frame = ttk.LabelFrame(top_frame, text="添加命令")
        control_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 命令类型和命令选择 - 简化布局
        cmd_select_frame = ttk.Frame(control_frame)
        cmd_select_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 将命令按类型分组
        self.cmd_categories = {}
        for cmd, cmd_type in utils.COMMANDS.items():
            if cmd_type not in self.cmd_categories:
                self.cmd_categories[cmd_type] = []
            self.cmd_categories[cmd_type].append(cmd)
        
        # 命令类型下拉菜单 - 使用更直观的标签
        ttk.Label(cmd_select_frame, text="选择命令类型:").grid(row=0, column=0, sticky=tk.W, columnspan=2, pady=(0, 5))
        
        self.cmd_type_var = tk.StringVar()
        self.cmd_type_combobox = ttk.Combobox(cmd_select_frame, textvariable=self.cmd_type_var, width=20)
        self.cmd_type_combobox["values"] = [
            "basic - 基本操作",
            "verify - 验证",
            "wait - 等待",
            "navigation - 导航",
            "test - 测试",
            "fuzzy - 模糊匹配"
        ]
        self.cmd_type_combobox.grid(row=1, column=0, columnspan=2, sticky=tk.W+tk.E, pady=(0, 10))
        self.cmd_type_combobox.bind("<<ComboboxSelected>>", self.on_cmd_type_selected)
        
        # 命令下拉菜单 - 使用更直观的标签
        ttk.Label(cmd_select_frame, text="选择具体命令:").grid(row=2, column=0, sticky=tk.W, columnspan=2, pady=(0, 5))
        
        self.cmd_var = tk.StringVar()
        self.cmd_combobox = ttk.Combobox(cmd_select_frame, textvariable=self.cmd_var, width=20)
        self.cmd_combobox.grid(row=3, column=0, columnspan=2, sticky=tk.W+tk.E, pady=(0, 10))
        
        # 参数输入 - 简化布局，添加示例
        ttk.Label(cmd_select_frame, text="输入参数:").grid(row=4, column=0, sticky=tk.W, columnspan=2, pady=(0, 5))
        
        self.param_entry = ttk.Entry(cmd_select_frame, width=40)
        self.param_entry.grid(row=5, column=0, columnspan=2, sticky=tk.W+tk.E, pady=(0, 5))
        
        # 示例文本标签 - 用于显示所选命令的参数示例
        self.example_var = tk.StringVar(value="示例: 选择命令后显示参数格式")
        example_label = ttk.Label(cmd_select_frame, textvariable=self.example_var, font=("Arial", 9, "italic"), foreground="blue")
        example_label.grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # 命令描述标签 - 显示当前选择命令的用途
        self.desc_var = tk.StringVar(value="请选择一个命令类型和具体命令")
        desc_label = ttk.Label(cmd_select_frame, textvariable=self.desc_var, wraplength=300, font=("Arial", 9))
        desc_label.grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # 添加命令按钮 - 使用更醒目的样式
        self.add_cmd_button = ttk.Button(cmd_select_frame, text="添加到命令列表", command=self.add_command, width=20)
        self.add_cmd_button.grid(row=8, column=0, columnspan=2, pady=(5, 0))
        
        # 右侧模板区域
        template_frame = ttk.LabelFrame(top_frame, text="快速模板")
        template_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        
        # 添加模板说明标签
        template_desc = "点击下方按钮快速添加预设测试模板"
        template_label = ttk.Label(template_frame, text=template_desc, font=("Arial", 9, "italic"))
        template_label.pack(padx=10, pady=(5, 2))
        
        # 模板按钮
        templates_grid = ttk.Frame(template_frame)
        templates_grid.pack(padx=10, pady=5)
        
        # 第一行模板
        self.create_template_button(templates_grid, "登录流程", self.apply_login_template, 0, 0)
        self.create_template_button(templates_grid, "表单填写", self.apply_form_template, 0, 1)
        self.create_template_button(templates_grid, "页面导航", self.apply_navigation_template, 0, 2)
        
        # 第二行模板
        self.create_template_button(templates_grid, "搜索测试", self.apply_search_template, 1, 0)
        self.create_template_button(templates_grid, "数据验证", self.apply_data_validation_template, 1, 1)
        self.create_template_button(templates_grid, "弹窗测试", self.apply_popup_template, 1, 2)
        
        # 第三行模板
        self.create_template_button(templates_grid, "响应性测试", self.apply_responsive_template, 2, 0)
        self.create_template_button(templates_grid, "分页测试", self.apply_pagination_template, 2, 1)
        self.create_template_button(templates_grid, "性能测试", self.apply_performance_template, 2, 2)
        
        # 命令列表区域
        list_frame = ttk.LabelFrame(self.frame, text="命令列表")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))
        
        # 命令列表框和滚动条
        list_container = ttk.Frame(list_frame)
        list_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.cmd_listbox = tk.Listbox(list_container, font=("Courier New", 10), selectmode=tk.EXTENDED, bg="white")
        self.cmd_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.cmd_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.cmd_listbox.config(yscrollcommand=scrollbar.set)
        
        # 命令操作按钮区域
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # 文件操作按钮
        file_frame = ttk.Frame(button_frame)
        file_frame.pack(side=tk.LEFT)
        
        self.save_button = ttk.Button(file_frame, text="保存", command=self.save_commands)
        self.save_button.pack(side=tk.LEFT, padx=2)
        
        self.load_button = ttk.Button(file_frame, text="加载", command=self.load_commands_from_file)
        self.load_button.pack(side=tk.LEFT, padx=2)
        
        self.execute_button = ttk.Button(file_frame, text="执行", command=self.execute_commands)
        self.execute_button.pack(side=tk.LEFT, padx=2)
        
        # 命令操作按钮
        cmd_button_frame = ttk.Frame(button_frame)
        cmd_button_frame.pack(side=tk.RIGHT)
        
        self.move_up_button = ttk.Button(cmd_button_frame, text="上移", command=self.move_command_up)
        self.move_up_button.pack(side=tk.LEFT, padx=2)
        
        self.move_down_button = ttk.Button(cmd_button_frame, text="下移", command=self.move_command_down)
        self.move_down_button.pack(side=tk.LEFT, padx=2)
        
        self.edit_button = ttk.Button(cmd_button_frame, text="编辑", command=self.edit_command)
        self.edit_button.pack(side=tk.LEFT, padx=2)
        
        self.delete_button = ttk.Button(cmd_button_frame, text="删除", command=self.delete_command)
        self.delete_button.pack(side=tk.LEFT, padx=2)
        
        self.clear_button = ttk.Button(cmd_button_frame, text="清空", command=self.clear_commands)
        self.clear_button.pack(side=tk.LEFT, padx=2)
        
        # 初始化类型选择
        if self.cmd_categories:
            self.cmd_type_combobox.current(0)
            self.on_cmd_type_selected(None)
        
        # 绑定命令选择事件，更新示例和描述
        self.cmd_combobox.bind("<<ComboboxSelected>>", self.on_command_selected)
        
        # 键盘快捷键
        self.frame.bind("<Control-s>", lambda event: self.save_commands())
        self.frame.bind("<Control-o>", lambda event: self.load_commands_from_file())
        self.frame.bind("<Control-e>", lambda event: self.execute_commands())
        self.frame.bind("<Delete>", lambda event: self.delete_command())
    
    def on_command_selected(self, event) -> None:
        """当命令被选择时更新示例和描述"""
        cmd = self.cmd_var.get()
        if not cmd:
            return
            
        # 根据命令类型设置示例和描述
        examples = {
            # 基本操作命令示例
            "OPEN_URL": ("网址", "示例: web/index.html"),
            "WAIT": ("等待秒数", "示例: 2"),
            "CLICK_BY_TEXT": ("文本内容", "示例: 登录"),
            "CLICK_BY_ID": ("元素ID", "示例: login-button"),
            "TYPE": ("要输入的文本", "示例: admin"),
            
            # 验证命令示例
            "VERIFY_TEXT_EXISTS": ("要验证的文本", "示例: 登录成功"),
            "VERIFY_ELEMENT_EXISTS": ("元素ID或选择器", "示例: login-form"),
            "VERIFY_COUNT": ("选择器||预期数量", "示例: .item||5"),
            
            # 等待命令示例
            "WAIT_FOR_TEXT": ("要等待的文本||最长等待秒数", "示例: 加载完成||10"),
            "WAIT_FOR_ELEMENT": ("元素选择器||最长等待秒数", "示例: #submit-button||5"),
            "WAIT_FOR_PAGE_LOAD": ("无需参数", ""),
            
            # 测试命令示例
            "TEST_CASE": ("测试用例名称", "示例: 登录功能测试"),
            
            # 模糊匹配命令示例
            "VERIFY_TEXT_CONTAINS": ("部分文本", "示例: 成功"),
            "VERIFY_TEXT_PATTERN": ("正则表达式", "示例: 用户\\d+"),
            "VERIFY_TEXT_SIMILAR": ("相似文本||相似度阈值", "示例: 登录成功||0.8"),
            
            # 导航命令示例
            "SCROLL_TO_ELEMENT": ("元素ID或选择器", "示例: footer"),
            "SCROLL_TO_BOTTOM": ("无需参数", ""),
        }
        
        descriptions = {
            # 基本操作命令描述
            "OPEN_URL": "打开指定网址",
            "WAIT": "等待指定秒数",
            "CLICK_BY_TEXT": "点击包含指定文本的元素",
            "CLICK_BY_ID": "点击指定ID的元素",
            "TYPE": "在当前焦点元素中输入文本",
            
            # 验证命令描述
            "VERIFY_TEXT_EXISTS": "验证页面中存在指定文本",
            "VERIFY_ELEMENT_EXISTS": "验证页面中存在指定元素",
            "VERIFY_COUNT": "验证页面中符合选择器的元素数量",
            
            # 等待命令描述
            "WAIT_FOR_TEXT": "等待指定文本出现，最长等待时间为指定秒数",
            "WAIT_FOR_ELEMENT": "等待指定元素出现，最长等待时间为指定秒数",
            "WAIT_FOR_PAGE_LOAD": "等待页面完全加载",
            
            # 测试命令描述
            "TEST_CASE": "开始一个新的测试用例，需要提供测试用例名称",
            
            # 模糊匹配命令描述
            "VERIFY_TEXT_CONTAINS": "验证页面中包含指定的部分文本",
            "VERIFY_TEXT_PATTERN": "使用正则表达式验证页面文本",
            "VERIFY_TEXT_SIMILAR": "验证页面中有与指定文本相似的内容，可设置相似度阈值(0.0-1.0)",
            
            # 导航命令描述
            "SCROLL_TO_ELEMENT": "滚动页面直到指定元素可见",
            "SCROLL_TO_BOTTOM": "滚动到页面底部",
        }
        
        # 更新示例和描述
        if cmd in examples:
            param_name, example = examples[cmd]
            if example:
                self.example_var.set(f"参数格式: {param_name}\n{example}")
            else:
                self.example_var.set("此命令不需要参数")
        else:
            self.example_var.set("示例: 选择命令后显示参数格式")
            
        if cmd in descriptions:
            self.desc_var.set(descriptions[cmd])
        else:
            self.desc_var.set("请选择一个命令")
    
    def create_template_button(self, parent, text, command, row, column) -> None:
        """创建模板按钮"""
        btn = ttk.Button(parent, text=text, command=command, width=12)
        btn.grid(row=row, column=column, padx=3, pady=3)
    
    def on_cmd_type_selected(self, event) -> None:
        """命令类型被选择时更新命令下拉菜单"""
        cmd_type_full = self.cmd_type_var.get()
        # 从显示文本中提取命令类型
        cmd_type = cmd_type_full.split(" - ")[0] if " - " in cmd_type_full else cmd_type_full
        
        if cmd_type in self.cmd_categories:
            self.cmd_combobox["values"] = sorted(self.cmd_categories[cmd_type])
            if self.cmd_categories[cmd_type]:
                self.cmd_combobox.current(0)
                # 触发命令选择事件更新示例
                self.on_command_selected(None)
    
    def add_command(self) -> None:
        """添加命令到列表"""
        cmd = self.cmd_var.get()
        params = self.param_entry.get()
        
        if not cmd:
            messagebox.showwarning("提示", "请选择命令")
            return
        
        # 特殊处理TEST_CASE
        if cmd == "TEST_CASE" and not params:
            messagebox.showwarning("提示", "TEST_CASE命令需要提供测试案例名称")
            return
        
        # 格式化显示
        display_text = f"{len(self.commands) + 1}. {cmd}"
        if params:
            display_text += f" = {params}"
        
        # 添加到列表框
        self.cmd_listbox.insert(tk.END, display_text)
        
        # 保存命令
        self.commands.append((cmd, params))
        
        # 清空参数输入框
        self.param_entry.delete(0, tk.END)
    
    def move_command_up(self) -> None:
        """上移选中命令"""
        selected_indices = self.cmd_listbox.curselection()
        if not selected_indices:
            return
        
        # 转换为列表并排序，确保从上到下处理
        indices = sorted(list(selected_indices))
        
        # 检查第一个选择的项是否已经在顶部
        if indices[0] == 0:
            return
        
        # 移动每个选择的项
        for idx in indices:
            # 交换命令
            self.commands[idx], self.commands[idx-1] = self.commands[idx-1], self.commands[idx]
        
        # 更新显示
        self.refresh_command_list()
        
        # 选中移动后的项
        for i, idx in enumerate(indices):
            self.cmd_listbox.selection_set(idx-1)
    
    def move_command_down(self) -> None:
        """下移选中命令"""
        selected_indices = self.cmd_listbox.curselection()
        if not selected_indices:
            return
        
        # 转换为列表并反向排序，确保从下到上处理
        indices = sorted(list(selected_indices), reverse=True)
        
        # 检查最后一个选择的项是否已经在底部
        if indices[0] >= len(self.commands) - 1:
            return
        
        # 移动每个选择的项
        for idx in indices:
            if idx < len(self.commands) - 1:
                # 交换命令
                self.commands[idx], self.commands[idx+1] = self.commands[idx+1], self.commands[idx]
        
        # 更新显示
        self.refresh_command_list()
        
        # 选中移动后的项
        for i, idx in enumerate(indices):
            if idx < len(self.commands) - 1:
                self.cmd_listbox.selection_set(idx+1)
    
    def edit_command(self) -> None:
        """编辑选中命令"""
        selected = self.cmd_listbox.curselection()
        if not selected or len(selected) > 1:
            messagebox.showinfo("提示", "请选择单个命令进行编辑")
            return
        
        index = selected[0]
        cmd, params = self.commands[index]
        
        # 设置UI状态
        if cmd in utils.COMMANDS:
            for cmd_type, cmds in self.cmd_categories.items():
                if cmd in cmds:
                    # 找到对应的显示文本
                    for display_text in self.cmd_type_combobox["values"]:
                        if display_text.startswith(cmd_type + " - "):
                            self.cmd_type_var.set(display_text)
                            break
                    else:
                        self.cmd_type_var.set(cmd_type)
                    
                    self.cmd_combobox["values"] = sorted(cmds)
                    self.cmd_var.set(cmd)
                    self.on_command_selected(None)  # 更新命令描述和示例
                    break
        else:
            self.cmd_var.set(cmd)
        
        self.param_entry.delete(0, tk.END)
        self.param_entry.insert(0, params)
        
        # 删除原命令
        self.delete_command()
    
    def delete_command(self) -> None:
        """删除选中命令"""
        selected_indices = self.cmd_listbox.curselection()
        if not selected_indices:
            return
        
        # 转换为列表并反向排序，确保从下到上删除
        indices = sorted(list(selected_indices), reverse=True)
        
        # 从列表中删除
        for idx in indices:
            del self.commands[idx]
        
        # 更新显示
        self.refresh_command_list()
        
        # 如果还有命令，选中删除位置的下一个命令（或者最后一个）
        if self.commands and indices:
            next_idx = min(indices[0], len(self.commands) - 1)
            self.cmd_listbox.selection_set(next_idx)
    
    def clear_commands(self) -> None:
        """清空所有命令"""
        if messagebox.askyesno("确认", "确定要清空所有命令吗？"):
            self.commands = []
            self.refresh_command_list()
    
    def refresh_command_list(self) -> None:
        """刷新命令列表显示"""
        self.cmd_listbox.delete(0, tk.END)
        
        for i, (cmd, params) in enumerate(self.commands):
            display_text = f"{i+1}. {cmd}"
            if params:
                display_text += f" = {params}"
            
            self.cmd_listbox.insert(tk.END, display_text)
    
    def save_commands(self) -> None:
        """保存命令到文件"""
        try:
            with open(utils.COMMAND_FILE, "w", encoding="utf-8") as f:
                f.write("# 自动化命令，每行一个指令，格式为: 指令名 = 参数\n")
                f.write("# 若参数有多个栏位，用两个直线符号（||）区隔\n\n")
                
                for cmd, params in self.commands:
                    if params:
                        f.write(f"{cmd} = {params}\n")
                    else:
                        f.write(f"{cmd}\n")
            
            messagebox.showinfo("成功", f"命令已保存到 {utils.COMMAND_FILE}")
            logging.info(f"命令已保存到 {utils.COMMAND_FILE}")
        except Exception as e:
            messagebox.showerror("错误", f"保存命令时发生错误: {str(e)}")
            logging.error(f"保存命令时发生错误: {str(e)}")
    
    def load_commands_from_file(self) -> None:
        """从文件加载命令"""
        try:
            self.commands = []
            
            if os.path.exists(utils.COMMAND_FILE):
                with open(utils.COMMAND_FILE, "r", encoding="utf-8") as f:
                    in_nav_sequence = False
                    
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        
                        # 处理命令
                        if "=" in line:
                            cmd, params_str = line.split("=", 1)
                            cmd = cmd.strip()
                            params = params_str.strip()
                            self.commands.append((cmd, params))
                        else:
                            self.commands.append((line.strip(), ""))
                
                self.refresh_command_list()
                logging.info(f"已从 {utils.COMMAND_FILE} 加载 {len(self.commands)} 个命令")
            else:
                messagebox.showinfo("提示", f"找不到 {utils.COMMAND_FILE} 文件")
                logging.info(f"找不到 {utils.COMMAND_FILE} 文件")
        except Exception as e:
            messagebox.showerror("错误", f"加载命令时发生错误: {str(e)}")
            logging.error(f"加载命令时发生错误: {str(e)}")
    
    def execute_commands(self) -> None:
        """执行当前命令列表"""
        if not self.commands:
            messagebox.showwarning("提示", "命令列表为空，无法执行")
            return
        
        if self.on_execute_commands:
            # 先保存命令
            self.save_commands()
            # 调用回调函数
            self.on_execute_commands()
        else:
            messagebox.showinfo("提示", "已保存命令，但未设置执行回调函数")
    
    def apply_login_template(self) -> None:
        """应用登录流程模板"""
        new_commands = [
            ("TEST_CASE", "登录功能测试"),
            ("OPEN_URL", "web/integrated.html"),
            ("WAIT_FOR_PAGE_LOAD", ""),
            ("CLICK_BY_ID", "username"),
            ("TYPE", "admin"),
            ("CLICK_BY_ID", "password"),
            ("TYPE", "admin123"),
            ("CLICK_BY_ID", "login-button"),
            ("WAIT_FOR_TEXT", "登录成功||5"),
            ("VERIFY_TEXT_EXISTS", "欢迎 admin")
        ]
        
        if messagebox.askyesno("确认", "是否添加登录流程模板？"):
            self.commands.extend(new_commands)
            self.refresh_command_list()
    
    def apply_form_template(self) -> None:
        """应用表单填写模板"""
        new_commands = [
            ("TEST_CASE", "表单填写测试"),
            ("OPEN_URL", "web/index.html"),
            ("WAIT_FOR_PAGE_LOAD", ""),
            ("CLICK_BY_ID", "item-name"),
            ("TYPE", "测试商品"),
            ("CLICK_BY_ID", "item-category"),
            ("CLICK_BY_TEXT", "电子"),
            ("CLICK_BY_ID", "item-price"),
            ("TYPE", "1500"),
            ("CLICK_BY_ID", "add-item"),
            ("WAIT", "1"),
            ("VERIFY_TEXT_EXISTS", "测试商品")
        ]
        
        if messagebox.askyesno("确认", "是否添加表单填写模板？"):
            self.commands.extend(new_commands)
            self.refresh_command_list()
    
    def apply_navigation_template(self) -> None:
        """应用页面导航模板"""
        new_commands = [
            ("TEST_CASE", "页面导航测试"),
            ("OPEN_URL", "web/advanced.html"),
            ("WAIT_FOR_PAGE_LOAD", ""),
            ("NAV_SEQUENCE_START", "产品导航"),
            ("CLICK_BY_ID", "electronics-link"),
            ("WAIT_FOR_ELEMENT", "#product-grid||5"),
            ("CLICK_BY_ID", "laptops-link"),
            ("WAIT", "2"),
            ("NAV_SEQUENCE_END", ""),
            ("CLICK_BY_TEXT", "查看详情"),
            ("WAIT_FOR_ELEMENT", "#product-title||5"),
            ("VERIFY_TEXT_EXISTS", "ROG Strix G15")
        ]
        
        if messagebox.askyesno("确认", "是否添加页面导航模板？"):
            self.commands.extend(new_commands)
            self.refresh_command_list()
    
    def apply_search_template(self) -> None:
        """应用搜索测试模板"""
        new_commands = [
            ("TEST_CASE", "搜索功能测试"),
            ("OPEN_URL", "web/index.html"),
            ("WAIT_FOR_PAGE_LOAD", ""),
            ("CLICK_BY_ID", "search-text"),
            ("TYPE", "测试关键字"),
            ("CLICK_BY_ID", "search-button"),
            ("WAIT", "1"),
            ("VERIFY_TEXT_EXISTS", "找到关键字")
        ]
        
        if messagebox.askyesno("确认", "是否添加搜索测试模板？"):
            self.commands.extend(new_commands)
            self.refresh_command_list()
    
    def apply_data_validation_template(self) -> None:
        """应用数据验证模板"""
        new_commands = [
            ("TEST_CASE", "数据验证测试"),
            ("OPEN_URL", "web/index.html"),
            ("WAIT_FOR_PAGE_LOAD", ""),
            ("CLICK_BY_ID", "validation-form"),
            ("CLICK_BY_ID", "email-field"),
            ("TYPE", "invalid-email"),
            ("CLICK_BY_ID", "submit-button"),
            ("WAIT", "1"),
            ("VERIFY_TEXT_EXISTS", "请输入有效的电子邮件地址"),
            ("CLICK_BY_ID", "email-field"),
            ("TYPE", "valid@example.com"),
            ("CLICK_BY_ID", "submit-button"),
            ("WAIT", "1"),
            ("VERIFY_TEXT_EXISTS", "表单提交成功")
        ]
        
        if messagebox.askyesno("确认", "是否添加数据验证模板？"):
            self.commands.extend(new_commands)
            self.refresh_command_list()
    
    def apply_popup_template(self) -> None:
        """应用弹窗测试模板"""
        new_commands = [
            ("TEST_CASE", "弹窗测试"),
            ("OPEN_URL", "web/advanced.html"),
            ("WAIT_FOR_PAGE_LOAD", ""),
            ("CLICK_BY_ID", "show-popup-button"),
            ("WAIT", "1"),
            ("VERIFY_TEXT_EXISTS", "确认操作"),
            ("CLICK_BY_TEXT", "确认"),
            ("WAIT", "1"),
            ("VERIFY_TEXT_EXISTS", "操作已确认")
        ]
        
        if messagebox.askyesno("确认", "是否添加弹窗测试模板？"):
            self.commands.extend(new_commands)
            self.refresh_command_list()
    
    def apply_responsive_template(self) -> None:
        """应用响应性测试模板"""
        new_commands = [
            ("TEST_CASE", "响应性测试"),
            ("OPEN_URL", "web/index.html"),
            ("WAIT_FOR_PAGE_LOAD", ""),
            ("VERIFY_ELEMENT_EXISTS", "header-nav"),
            ("WAIT", "1"),
            ("SCROLL_TO_BOTTOM", ""),
            ("WAIT", "1"),
            ("VERIFY_ELEMENT_EXISTS", "footer-links")
        ]
        
        if messagebox.askyesno("确认", "是否添加响应性测试模板？"):
            self.commands.extend(new_commands)
            self.refresh_command_list()
    
    def apply_pagination_template(self) -> None:
        """应用分页测试模板"""
        new_commands = [
            ("TEST_CASE", "分页测试"),
            ("OPEN_URL", "web/advanced.html"),
            ("WAIT_FOR_PAGE_LOAD", ""),
            ("VERIFY_TEXT_EXISTS", "第1页"),
            ("CLICK_BY_ID", "next-page"),
            ("WAIT", "1"),
            ("VERIFY_TEXT_EXISTS", "第2页"),
            ("CLICK_BY_ID", "next-page"),
            ("WAIT", "1"),
            ("VERIFY_TEXT_EXISTS", "第3页"),
            ("CLICK_BY_ID", "prev-page"),
            ("WAIT", "1"),
            ("VERIFY_TEXT_EXISTS", "第2页")
        ]
        
        if messagebox.askyesno("确认", "是否添加分页测试模板？"):
            self.commands.extend(new_commands)
            self.refresh_command_list()
    
    def apply_performance_template(self) -> None:
        """应用性能测试模板"""
        new_commands = [
            ("TEST_CASE", "性能测试"),
            ("OPEN_URL", "web/index.html"),
            ("WAIT_FOR_PAGE_LOAD", ""),
            ("CLICK_BY_ID", "load-data-button"),
            ("WAIT_FOR_TEXT", "数据加载完成||10"),
            ("VERIFY_COUNT", "data-item||5")
        ]
        
        if messagebox.askyesno("确认", "是否添加性能测试模板？"):
            self.commands.extend(new_commands)
            self.refresh_command_list()


if __name__ == "__main__":
    # 测试代码
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    editor = CommandEditor(root)
    
    root.mainloop() 