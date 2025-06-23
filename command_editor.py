# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import os
from typing import List, Tuple, Dict, Any, Optional
import logging

import utils

class CommandEditor:
    def __init__(self, parent: tk.Tk, on_execute_commands=None) -> None:
        """初始化命令编辑器"""
        self.window = tk.Toplevel(parent)
        self.window.title("命令编辑器")
        self.window.geometry("800x600")
        self.window.protocol("WM_DELETE_WINDOW", self.hide_window)  # 关闭时隐藏而非销毁
        
        # 当前命令列表
        self.commands = []
        
        # 回调函数 - 当用户点击"执行这些命令"时调用
        self.on_execute_commands = on_execute_commands
        
        # 创建 UI
        self.create_ui()
        
        # 加载现有命令
        self.load_commands_from_file()
        
        # 显示窗口
        self.window.update()
        self.window.deiconify()
    
    def create_ui(self) -> None:
        """创建用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 命令输入区域
        input_frame = ttk.LabelFrame(main_frame, text="添加命令", padding="10")
        input_frame.pack(fill=tk.X, pady=5)
        
        # 命令类型选择
        cmd_frame = ttk.Frame(input_frame)
        cmd_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(cmd_frame, text="命令类型:").pack(side=tk.LEFT, padx=(0, 5))
        
        # 将命令按类型分组
        self.cmd_categories = {}
        for cmd, cmd_type in utils.COMMANDS.items():
            if cmd_type not in self.cmd_categories:
                self.cmd_categories[cmd_type] = []
            self.cmd_categories[cmd_type].append(cmd)
        
        # 命令类型下拉菜单
        self.cmd_type_var = tk.StringVar()
        self.cmd_type_combobox = ttk.Combobox(cmd_frame, textvariable=self.cmd_type_var, width=20)
        self.cmd_type_combobox["values"] = list(self.cmd_categories.keys())
        self.cmd_type_combobox.pack(side=tk.LEFT, padx=5)
        self.cmd_type_combobox.bind("<<ComboboxSelected>>", self.on_cmd_type_selected)
        
        # 命令下拉菜单
        ttk.Label(cmd_frame, text="命令:").pack(side=tk.LEFT, padx=(10, 5))
        self.cmd_var = tk.StringVar()
        self.cmd_combobox = ttk.Combobox(cmd_frame, textvariable=self.cmd_var, width=25)
        self.cmd_combobox.pack(side=tk.LEFT, padx=5)
        
        # 参数输入
        param_frame = ttk.Frame(input_frame)
        param_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(param_frame, text="参数:").pack(side=tk.LEFT, padx=(0, 5))
        self.param_entry = ttk.Entry(param_frame, width=50)
        self.param_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 多参数区分说明
        ttk.Label(param_frame, text="(多个参数用 || 分隔)").pack(side=tk.LEFT, padx=5)
        
        # 按钮区域
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        self.add_cmd_button = ttk.Button(button_frame, text="添加命令", command=self.add_command)
        self.add_cmd_button.pack(side=tk.LEFT, padx=5)
        
        self.add_test_case_button = ttk.Button(button_frame, text="添加TEST_CASE分隔线", command=self.add_test_case)
        self.add_test_case_button.pack(side=tk.LEFT, padx=5)
        
        self.add_nav_start_button = ttk.Button(button_frame, text="添加导航序列开始", command=self.add_nav_sequence_start)
        self.add_nav_start_button.pack(side=tk.LEFT, padx=5)
        
        self.add_nav_end_button = ttk.Button(button_frame, text="添加导航序列结束", command=self.add_nav_sequence_end)
        self.add_nav_end_button.pack(side=tk.LEFT, padx=5)
        
        self.add_comment_button = ttk.Button(button_frame, text="添加注释", command=self.add_comment)
        self.add_comment_button.pack(side=tk.LEFT, padx=5)
        
        # 模板下拉菜单
        template_frame = ttk.Frame(input_frame)
        template_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(template_frame, text="常用模板:").pack(side=tk.LEFT, padx=(0, 5))
        self.template_var = tk.StringVar()
        self.template_combobox = ttk.Combobox(template_frame, textvariable=self.template_var, width=30)
        self.template_combobox["values"] = ["登录流程", "表单填写", "页面导航", "搜索测试"]
        self.template_combobox.pack(side=tk.LEFT, padx=5)
        
        self.apply_template_button = ttk.Button(template_frame, text="应用模板", command=self.apply_template)
        self.apply_template_button.pack(side=tk.LEFT, padx=5)
        
        # 命令列表区域
        cmd_list_frame = ttk.LabelFrame(main_frame, text="当前命令列表", padding="10")
        cmd_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 命令列表框 - 修改为支持多选
        self.cmd_listbox = tk.Listbox(cmd_list_frame, font=("Courier New", 10), selectmode=tk.EXTENDED)
        self.cmd_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(cmd_list_frame, orient=tk.VERTICAL, command=self.cmd_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.cmd_listbox.config(yscrollcommand=scrollbar.set)
        
        # 命令操作按钮
        cmd_op_frame = ttk.Frame(main_frame)
        cmd_op_frame.pack(fill=tk.X, pady=5)
        
        self.move_up_button = ttk.Button(cmd_op_frame, text="上移", command=self.move_command_up)
        self.move_up_button.pack(side=tk.LEFT, padx=5)
        
        self.move_down_button = ttk.Button(cmd_op_frame, text="下移", command=self.move_command_down)
        self.move_down_button.pack(side=tk.LEFT, padx=5)
        
        self.move_to_top_button = ttk.Button(cmd_op_frame, text="移至顶部", command=self.move_command_to_top)
        self.move_to_top_button.pack(side=tk.LEFT, padx=5)
        
        self.move_to_bottom_button = ttk.Button(cmd_op_frame, text="移至底部", command=self.move_command_to_bottom)
        self.move_to_bottom_button.pack(side=tk.LEFT, padx=5)
        
        self.edit_button = ttk.Button(cmd_op_frame, text="编辑", command=self.edit_command)
        self.edit_button.pack(side=tk.LEFT, padx=5)
        
        self.delete_button = ttk.Button(cmd_op_frame, text="删除", command=self.delete_command)
        self.delete_button.pack(side=tk.LEFT, padx=5)
        
        self.clear_button = ttk.Button(cmd_op_frame, text="清空所有", command=self.clear_commands)
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        # 添加帮助按钮
        self.help_button = ttk.Button(cmd_op_frame, text="帮助", command=self.show_help)
        self.help_button.pack(side=tk.RIGHT, padx=5)
        
        # 底部按钮区域
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=10)
        
        self.save_button = ttk.Button(bottom_frame, text="保存到command.txt", command=self.save_commands)
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        self.load_button = ttk.Button(bottom_frame, text="从文件加载", command=self.load_commands_from_file)
        self.load_button.pack(side=tk.LEFT, padx=5)
        
        self.execute_button = ttk.Button(bottom_frame, text="执行这些命令", command=self.execute_commands)
        self.execute_button.pack(side=tk.RIGHT, padx=5)
        
        # 键盘快捷键
        self.window.bind("<Control-s>", lambda event: self.save_commands())
        self.window.bind("<Control-o>", lambda event: self.load_commands_from_file())
        self.window.bind("<Control-e>", lambda event: self.execute_commands())
        self.window.bind("<Delete>", lambda event: self.delete_command())
        
        # 初始化类型选择
        if self.cmd_categories:
            first_type = list(self.cmd_categories.keys())[0]
            self.cmd_type_var.set(first_type)
            self.cmd_combobox["values"] = sorted(self.cmd_categories[first_type])
            if self.cmd_categories[first_type]:
                self.cmd_combobox.current(0)
    
    def on_cmd_type_selected(self, event) -> None:
        """命令类型被选择时更新命令下拉菜单"""
        cmd_type = self.cmd_type_var.get()
        if cmd_type in self.cmd_categories:
            self.cmd_combobox["values"] = sorted(self.cmd_categories[cmd_type])
            if self.cmd_categories[cmd_type]:
                self.cmd_combobox.current(0)
    
    def add_command(self) -> None:
        """添加命令到列表"""
        cmd = self.cmd_var.get()
        params = self.param_entry.get()
        
        if not cmd:
            messagebox.showwarning("警告", "请选择命令类型和命令")
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
    
    def add_test_case(self) -> None:
        """添加TEST_CASE分隔线"""
        params = self.param_entry.get()
        cmd = "TEST_CASE"
        
        if not params:
            messagebox.showwarning("警告", "请输入测试案例名称")
            return
        
        # 格式化显示
        display_text = f"{len(self.commands) + 1}. {cmd} = {params}"
        
        # 添加到列表框
        self.cmd_listbox.insert(tk.END, display_text)
        
        # 保存命令
        self.commands.append((cmd, params))
        
        # 清空参数输入框
        self.param_entry.delete(0, tk.END)
    
    def add_nav_sequence_start(self) -> None:
        """添加导航序列开始标记"""
        params = self.param_entry.get()
        cmd = "NAV_SEQUENCE_START"
        
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
    
    def add_nav_sequence_end(self) -> None:
        """添加导航序列结束标记"""
        cmd = "NAV_SEQUENCE_END"
        
        # 格式化显示
        display_text = f"{len(self.commands) + 1}. {cmd}"
        
        # 添加到列表框
        self.cmd_listbox.insert(tk.END, display_text)
        
        # 保存命令
        self.commands.append((cmd, ""))
    
    def add_comment(self) -> None:
        """添加注释"""
        comment = self.param_entry.get()
        
        if not comment:
            messagebox.showwarning("警告", "请输入注释内容")
            return
        
        # 格式化显示
        display_text = f"{len(self.commands) + 1}. # {comment}"
        
        # 添加到列表框
        self.cmd_listbox.insert(tk.END, display_text)
        
        # 保存命令 (使用特殊标记 "#" 表示注释)
        self.commands.append(("#", comment))
        
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
    
    def move_command_to_top(self) -> None:
        """将选中命令移至顶部"""
        selected_indices = self.cmd_listbox.curselection()
        if not selected_indices:
            return
        
        # 转换为列表并排序
        indices = sorted(list(selected_indices))
        selected_commands = [self.commands[idx] for idx in indices]
        
        # 从列表中删除选择的命令
        for idx in reversed(indices):
            del self.commands[idx]
        
        # 将选择的命令插入到顶部
        for i, cmd in enumerate(selected_commands):
            self.commands.insert(i, cmd)
        
        # 更新显示
        self.refresh_command_list()
        
        # 选中移动后的项
        for i in range(len(selected_commands)):
            self.cmd_listbox.selection_set(i)
    
    def move_command_to_bottom(self) -> None:
        """将选中命令移至底部"""
        selected_indices = self.cmd_listbox.curselection()
        if not selected_indices:
            return
        
        # 转换为列表并排序
        indices = sorted(list(selected_indices), reverse=True)
        selected_commands = [self.commands[idx] for idx in reversed(indices)]
        
        # 从列表中删除选择的命令
        for idx in indices:
            del self.commands[idx]
        
        # 将选择的命令添加到底部
        self.commands.extend(selected_commands)
        
        # 更新显示
        self.refresh_command_list()
        
        # 选中移动后的项
        start_idx = len(self.commands) - len(selected_commands)
        for i in range(len(selected_commands)):
            self.cmd_listbox.selection_set(start_idx + i)
    
    def edit_command(self) -> None:
        """编辑选中命令"""
        selected = self.cmd_listbox.curselection()
        if not selected or len(selected) > 1:
            messagebox.showinfo("提示", "请选择单个命令进行编辑")
            return
        
        index = selected[0]
        cmd, params = self.commands[index]
        
        # 如果是注释
        if cmd == "#":
            self.param_entry.delete(0, tk.END)
            self.param_entry.insert(0, params)
            self.delete_command()
            return
        
        # 设置UI状态
        if cmd in utils.COMMANDS:
            for cmd_type, cmds in self.cmd_categories.items():
                if cmd in cmds:
                    self.cmd_type_var.set(cmd_type)
                    self.cmd_combobox["values"] = sorted(cmds)
                    self.cmd_var.set(cmd)
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
            if cmd == "#":
                display_text = f"{i+1}. # {params}"
            else:
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
                    if cmd == "#":
                        f.write(f"# {params}\n")
                    else:
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
                        if not line:
                            continue
                        
                        # 处理注释
                        if line.startswith("#"):
                            self.commands.append(("#", line[1:].strip()))
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
                messagebox.showinfo("成功", f"已从 {utils.COMMAND_FILE} 加载 {len(self.commands)} 个命令")
                logging.info(f"已从 {utils.COMMAND_FILE} 加载 {len(self.commands)} 个命令")
            else:
                messagebox.showinfo("提示", f"找不到 {utils.COMMAND_FILE} 文件")
                logging.info(f"找不到 {utils.COMMAND_FILE} 文件")
        except Exception as e:
            messagebox.showerror("错误", f"加载命令时发生错误: {str(e)}")
            logging.error(f"加载命令时发生错误: {str(e)}")
    
    def apply_template(self) -> None:
        """应用预设模板"""
        template = self.template_var.get()
        
        if not template:
            return
        
        if template == "登录流程":
            self.apply_login_template()
        elif template == "表单填写":
            self.apply_form_template()
        elif template == "页面导航":
            self.apply_navigation_template()
        elif template == "搜索测试":
            self.apply_search_template()
    
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
        
        if messagebox.askyesno("确认", "是否添加登录流程模板？这将在当前命令列表末尾添加10条新命令。"):
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
        
        if messagebox.askyesno("确认", "是否添加表单填写模板？这将在当前命令列表末尾添加12条新命令。"):
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
        
        if messagebox.askyesno("确认", "是否添加页面导航模板？这将在当前命令列表末尾添加12条新命令。"):
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
        
        if messagebox.askyesno("确认", "是否添加搜索测试模板？这将在当前命令列表末尾添加8条新命令。"):
            self.commands.extend(new_commands)
            self.refresh_command_list()
    
    def execute_commands(self) -> None:
        """执行当前命令列表"""
        if not self.commands:
            messagebox.showwarning("警告", "命令列表为空，无法执行")
            return
        
        if self.on_execute_commands:
            # 先保存命令
            self.save_commands()
            # 调用回调函数
            self.on_execute_commands()
        else:
            messagebox.showinfo("提示", "已保存命令，但未设置执行回调函数")
    
    def hide_window(self) -> None:
        """隐藏窗口"""
        self.window.withdraw()
    
    def show_window(self) -> None:
        """显示窗口"""
        self.window.deiconify()
        self.window.lift()
    
    def destroy(self) -> None:
        """销毁窗口"""
        self.window.destroy()
    
    def show_help(self) -> None:
        """显示帮助信息"""
        help_text = """命令编辑器使用帮助：
        
1. 添加命令：
   - 选择命令类型和具体命令
   - 输入参数（多个参数用 || 分隔）
   - 点击"添加命令"按钮

2. 编辑命令：
   - 选择要编辑的命令（单个）
   - 点击"编辑"按钮
   - 修改参数后重新添加

3. 移动命令：
   - 可以选择多个命令（按住Ctrl或Shift选择）
   - 使用"上移"、"下移"、"移至顶部"或"移至底部"按钮

4. 删除命令：
   - 选择要删除的命令（可多选）
   - 点击"删除"按钮或按Delete键

5. 使用模板：
   - 从下拉菜单选择模板
   - 点击"应用模板"按钮

6. 快捷键：
   - Ctrl+S：保存命令
   - Ctrl+O：加载命令
   - Ctrl+E：执行命令
   - Delete：删除选中命令
"""
        messagebox.showinfo("命令编辑器帮助", help_text)


if __name__ == "__main__":
    # 测试代码
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    editor = CommandEditor(root)
    
    root.mainloop() 