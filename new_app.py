import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import os
import sys
import traceback
from datetime import datetime
import json
from recorder_template import get_recorder_script_template
import subprocess
import time
import signal

# 常數定義
APP_TITLE = "Playwright E2E助手"
APP_VERSION = "2.0.0"
DEFAULT_FONT_SIZE = 11
CONFIG_FILE = "config.json"
DEFAULT_WINDOW_SIZE = "1200x800"  # 增大預設窗口大小

class PlaywrightGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_TITLE} v{APP_VERSION}")
        self.root.geometry(DEFAULT_WINDOW_SIZE)
        self.root.minsize(1000, 700)  # 設置最小窗口大小以確保所有元素都可見
        
        # 設定變數
        self.font_size = tk.IntVar(value=DEFAULT_FONT_SIZE)
        self.headless_mode = tk.BooleanVar(value=False)
        self.running = False
        
        # 录制相关变量
        self.recording = False
        self.recorder_process = None
        self.recorded_code = []
        
        # 讀取配置文件
        self.load_config()
        
        # 建立UI
        self.create_ui()
        
        # 設置關閉窗口的處理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def load_config(self):
        """載入配置文件"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    
                    # 載入字體大小設定
                    if "font_size" in config:
                        self.font_size.set(config["font_size"])
                    
                    # 載入窗口大小設定
                    if "window_size" in config:
                        self.root.geometry(config["window_size"])
                    
                    # 載入無頭模式設定
                    if "headless_mode" in config:
                        self.headless_mode.set(config["headless_mode"])
        except Exception as e:
            print(f"載入配置文件失敗: {e}")
    
    def save_config(self):
        """保存配置文件"""
        try:
            config = {
                "font_size": self.font_size.get(),
                "window_size": self.root.geometry(),
                "headless_mode": self.headless_mode.get()
            }
            
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"保存配置文件失敗: {e}")
    
    def create_ui(self):
        """創建使用者介面"""
        # 設置字體
        font_family = "Microsoft JhengHei UI" if sys.platform == "win32" else "TkDefaultFont"
        default_font = (font_family, self.font_size.get())
        
        # 主框架 - 使用PanedWindow實現左右分割
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左側框架 - 腳本編輯區
        left_frame = ttk.LabelFrame(main_paned, text="Playwright 腳本")
        main_paned.add(left_frame, weight=50)
        
        # 右側框架 - 日誌區
        right_frame = ttk.LabelFrame(main_paned, text="執行日誌")
        main_paned.add(right_frame, weight=50)
        
        # 腳本編輯區域
        script_frame = ttk.Frame(left_frame)
        script_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 使用Text而非ScrolledText，以便自定義行號顯示
        self.script_text = tk.Text(script_frame, wrap=tk.NONE, undo=True, font=default_font)
        self.script_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # 為腳本文本框添加滾動條
        script_scrolly = ttk.Scrollbar(script_frame, orient=tk.VERTICAL, command=self.script_text.yview)
        script_scrolly.pack(fill=tk.Y, side=tk.RIGHT)
        self.script_text.config(yscrollcommand=script_scrolly.set)
        
        script_scrollx = ttk.Scrollbar(script_frame, orient=tk.HORIZONTAL, command=self.script_text.xview)
        script_scrollx.pack(fill=tk.X, side=tk.BOTTOM)
        self.script_text.config(xscrollcommand=script_scrollx.set)
        
        # 添加一些預設腳本作為示例
        self.script_text.insert(tk.END, """# Playwright 腳本示例
# 這裡貼上您的 Playwright 代碼（不需要 sync_playwright 包裝）
# 範例:

browser = playwright.chromium.launch(headless=False)
page = browser.new_page()
page.goto("https://example.com")
page.fill("input[name='username']", "testuser")
page.click("text=Login")
assert "Welcome" in page.content()
browser.close()
""")
        
        # 日誌區域
        log_frame = ttk.Frame(right_frame)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, font=default_font)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
        
        # 控制區域 - 底部按鈕和選項
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 無頭模式複選框
        headless_check = ttk.Checkbutton(
            control_frame, 
            text="無頭模式 (Headless)",
            variable=self.headless_mode
        )
        headless_check.pack(side=tk.LEFT, padx=5)
        
        # 字體大小控制
        font_frame = ttk.Frame(control_frame)
        font_frame.pack(side=tk.LEFT, padx=15)
        
        ttk.Label(font_frame, text="字體大小:").pack(side=tk.LEFT)
        ttk.Button(font_frame, text="A-", width=3, command=lambda: self.change_font_size(-1)).pack(side=tk.LEFT, padx=2)
        ttk.Label(font_frame, textvariable=self.font_size).pack(side=tk.LEFT, padx=3)
        ttk.Button(font_frame, text="A+", width=3, command=lambda: self.change_font_size(1)).pack(side=tk.LEFT, padx=2)
        
        # 右側按鈕
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(side=tk.RIGHT)
        
        # 載入和保存按鈕
        ttk.Button(btn_frame, text="載入腳本", width=10, command=self.load_script).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="保存腳本", width=10, command=self.save_script).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="清空日誌", width=10, command=self.clear_log).pack(side=tk.LEFT, padx=5)
        
        # 執行按鈕 - 使用特殊樣式
        style = ttk.Style()
        style.configure("Execute.TButton", font=(font_family, self.font_size.get() + 2, "bold"))
        
        self.execute_btn = ttk.Button(
            btn_frame, 
            text="執行腳本", 
            width=15, 
            command=self.execute_script,
            style="Execute.TButton"
        )
        self.execute_btn.pack(side=tk.LEFT, padx=5)
        
        # 添加錄製按鈕區域
        record_frame = ttk.LabelFrame(self.root, text="腳本錄製")
        record_frame.pack(fill=tk.X, padx=10, pady=5)
        
        record_btn_frame = ttk.Frame(record_frame)
        record_btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 錄製說明
        ttk.Label(
            record_btn_frame, 
            text="錄製功能將打開瀏覽器並記錄您的操作，生成原生 Playwright 腳本。您可以錄製基本的點擊、填寫表單等操作。"
        ).pack(side=tk.TOP, anchor=tk.W, pady=5)
        
        # 錄製URL輸入框
        url_frame = ttk.Frame(record_btn_frame)
        url_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(url_frame, text="起始URL:").pack(side=tk.LEFT, padx=(0, 5))
        self.url_var = tk.StringVar(value="https://example.com")
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=50)
        url_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 錄製控制按鈕
        btn_control_frame = ttk.Frame(record_btn_frame)
        btn_control_frame.pack(fill=tk.X, pady=5)
        
        # 創建錄製按鈕
        self.record_btn = ttk.Button(
            btn_control_frame, 
            text="開始錄製", 
            width=15, 
            command=self.start_recording
        )
        self.record_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(
            btn_control_frame, 
            text="停止錄製", 
            width=15, 
            command=self.stop_recording,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # 本地文件測試按鈕
        self.test_page_btn = ttk.Button(
            btn_control_frame, 
            text="錄製測試頁面", 
            width=15, 
            command=self.record_test_page
        )
        self.test_page_btn.pack(side=tk.LEFT, padx=5)
        
        # 錄製狀態顯示
        self.record_status_var = tk.StringVar(value="未錄製")
        record_status = ttk.Label(
            btn_control_frame, 
            textvariable=self.record_status_var,
            font=(font_family, self.font_size.get(), "bold"),
            foreground="gray"
        )
        record_status.pack(side=tk.LEFT, padx=15)
        
        # 狀態欄
        self.status_var = tk.StringVar(value="就緒")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=2)
        
        # 初始化日誌
        self.log("Playwright E2E助手已啟動")
        self.log(f"請在左側輸入 Playwright 腳本，然後點擊「執行腳本」按鈕")
    
    def change_font_size(self, delta):
        """變更字體大小"""
        new_size = self.font_size.get() + delta
        if 8 <= new_size <= 24:  # 限制字體大小範圍
            self.font_size.set(new_size)
            font_family = "Microsoft JhengHei UI" if sys.platform == "win32" else "TkDefaultFont"
            
            # 更新腳本文本框字體
            self.script_text.configure(font=(font_family, new_size))
            
            # 更新日誌文本框字體
            self.log_text.configure(font=(font_family, new_size))
            
            # 更新執行按鈕字體
            style = ttk.Style()
            style.configure("Execute.TButton", font=(font_family, new_size + 2, "bold"))
    
    def load_script(self):
        """載入腳本文件"""
        file_path = filedialog.askopenfilename(
            title="選擇腳本文件",
            filetypes=[("Python 文件", "*.py"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # 清空當前內容並插入新腳本
                self.script_text.delete(1.0, tk.END)
                self.script_text.insert(tk.END, content)
                
                self.status_var.set(f"已載入腳本: {os.path.basename(file_path)}")
                self.log(f"已載入腳本文件: {file_path}")
            except Exception as e:
                self.status_var.set("載入腳本失敗")
                self.log(f"載入腳本失敗: {e}")
                messagebox.showerror("錯誤", f"載入腳本失敗: {e}")
    
    def save_script(self):
        """保存腳本到文件"""
        file_path = filedialog.asksaveasfilename(
            title="保存腳本文件",
            defaultextension=".py",
            filetypes=[("Python 文件", "*.py"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                content = self.script_text.get(1.0, tk.END)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                
                self.status_var.set(f"已保存腳本: {os.path.basename(file_path)}")
                self.log(f"已保存腳本到文件: {file_path}")
            except Exception as e:
                self.status_var.set("保存腳本失敗")
                self.log(f"保存腳本失敗: {e}")
                messagebox.showerror("錯誤", f"保存腳本失敗: {e}")
    
    def clear_log(self):
        """清空日誌"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.log("日誌已清空")
    
    def execute_script(self):
        """執行腳本"""
        if self.running:
            messagebox.showinfo("提示", "腳本正在執行中，請等待完成")
            return
        
        # 獲取腳本內容
        script_content = self.script_text.get(1.0, tk.END).strip()
        
        if not script_content:
            messagebox.showinfo("提示", "請先輸入腳本內容")
            return
        
        # 標記為正在執行
        self.running = True
        self.execute_btn.config(state=tk.DISABLED)
        self.status_var.set("正在執行腳本...")
        
        # 清空先前日誌
        self.clear_log()
        self.log("開始執行腳本...")
        
        # 在新線程中執行，避免UI凍結
        threading.Thread(target=self._execute_in_thread, args=(script_content,), daemon=True).start()
    
    def _execute_in_thread(self, script_content):
        """在單獨線程中執行腳本"""
        try:
            from playwright.sync_api import sync_playwright
            
            # 準備要執行的完整腳本
            indent_script = "\n    ".join(script_content.split("\n"))
            
            complete_script = f"""
from playwright.sync_api import sync_playwright
import traceback

def run(playwright):
    try:
        # 用戶腳本開始
        {indent_script}
        # 用戶腳本結束
        return True, "腳本執行成功"
    except Exception as e:
        error_info = traceback.format_exc()
        return False, error_info

# 執行腳本
with sync_playwright() as playwright:
    success, message = run(playwright)
    print("SCRIPT_RESULT:" + ("SUCCESS" if success else "ERROR"))
    print("SCRIPT_MESSAGE:" + message)
"""
            # 創建臨時腳本文件
            temp_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_script.py")
            with open(temp_script_path, "w", encoding="utf-8") as f:
                f.write(complete_script)
            
            # 執行腳本
            self.log(f"正在使用{'無頭模式' if self.headless_mode.get() else '有頭模式'}執行腳本...")
            
            # 設置環境變數控制無頭模式
            env = os.environ.copy()
            env["PLAYWRIGHT_HEADLESS"] = str(self.headless_mode.get()).lower()
            
            # 執行臨時腳本
            import subprocess
            process = subprocess.Popen(
                [sys.executable, temp_script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True
            )
            
            # 讀取輸出
            stdout, stderr = process.communicate()
            
            # 處理結果
            if process.returncode == 0:
                # 從輸出中提取結果
                result = "SUCCESS" in stdout
                if result:
                    self.log("✅ 腳本執行成功!")
                else:
                    # 提取錯誤訊息
                    error_lines = stdout.split("\n")
                    error_message = None
                    for line in error_lines:
                        if line.startswith("SCRIPT_MESSAGE:"):
                            error_message = line.replace("SCRIPT_MESSAGE:", "")
                            break
                    
                    if error_message:
                        self.log("❌ 腳本執行失敗:")
                        self.log(error_message)
                    else:
                        self.log("❌ 腳本執行失敗，但未找到錯誤詳情")
            else:
                self.log("❌ 腳本執行過程中發生錯誤:")
                self.log(stderr)
            
            # 刪除臨時腳本
            try:
                os.remove(temp_script_path)
            except:
                pass
        
        except Exception as e:
            self.log(f"❌ 執行腳本時發生錯誤: {e}")
            self.log(traceback.format_exc())
        
        finally:
            # 更新UI（回到主線程）
            self.root.after(0, self._finish_execution)
    
    def _finish_execution(self):
        """執行完成後的UI更新（在主線程中）"""
        self.running = False
        self.execute_btn.config(state=tk.NORMAL)
        self.status_var.set("腳本執行完成")
        self.log("腳本執行完成")
    
    def log(self, message):
        """添加日誌訊息"""
        # 使用after方法確保在主線程更新UI
        def _update_log():
            self.log_text.config(state=tk.NORMAL)
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_text.see(tk.END)  # 自動滾動到底部
            self.log_text.config(state=tk.DISABLED)
        
        # 如果在主線程，直接執行；否則使用after方法
        if threading.current_thread() is threading.main_thread():
            _update_log()
        else:
            self.root.after(0, _update_log)
    
    def on_closing(self):
        """關閉窗口時的處理"""
        if self.running:
            if not messagebox.askyesno("警告", "腳本正在執行中，確定要關閉嗎？"):
                return
        
        # 保存配置
        self.save_config()
        
        # 關閉窗口
        self.root.destroy()

    def start_recording(self):
        """开始录制浏览器操作"""
        if self.recording or self.running:
            messagebox.showinfo("提示", "已有正在进行的录制或执行任务")
            return
            
        url = self.url_var.get().strip()
        if not url:
            messagebox.showinfo("提示", "请输入起始URL")
            return
            
        # 确保URL格式正确
        if not url.startswith(("http://", "https://", "file://")):
            if os.path.exists(url):
                url = f"file://{os.path.abspath(url)}"
            else:
                url = f"https://{url}"
                
        # 清空之前的录制内容
        self.recorded_code = []
        
        # 更新状态
        self.recording = True
        self.record_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.test_page_btn.config(state=tk.DISABLED)
        self.execute_btn.config(state=tk.DISABLED)
        self.record_status_var.set("录制中...")
        
        # 在新线程中启动录制，避免UI冻结
        threading.Thread(target=self._start_recording_process, args=(url,), daemon=True).start()
        
    def _start_recording_process(self, url):
        """在单独线程中启动录制进程"""
        try:
            self.log("開始錄製瀏覽器操作...")
            self.log(f"打開URL: {url}")
            self.log("請在操作完成後關閉瀏覽器窗口以結束錄製")
            
            # 创建临时Python文件用于记录操作
            recorder_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recorder_temp.py")
            
            # 使用模板生成录制脚本
            with open(recorder_script, "w", encoding="utf-8") as f:
                f.write(get_recorder_script_template(url))
            
            # 执行录制脚本
            import subprocess
            
            self.log("啟動錄製進程...")
            
            # 使用新的方式启动录制进程，以确保正确处理输出和子进程
            # 在Windows上使用CREATE_NEW_CONSOLE确保进程在单独的控制台窗口中运行
            # 这样即使主程序关闭，录制进程也能继续运行
            self.recorder_process = subprocess.Popen(
                [sys.executable, recorder_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
            )
            
            # 创建一个线程来监控录制进程的输出
            def monitor_output():
                for line in iter(self.recorder_process.stdout.readline, ''):
                    if line.strip():
                        self.log(f"錄製: {line.strip()}")
                        
                        # 检查是否有生成的代码
                        if "生成的 Playwright Python 腳本:" in line:
                            # 接下来的行是生成的代码
                            in_code_section = True
                            continue
                            
                        if in_code_section and line.strip() and not line.startswith("沒有生成"):
                            self.recorded_code.append(line.strip())
                        
                        # 检查是否录制已结束
                        if "頁面已關閉，結束錄製..." in line or "瀏覽器已關閉" in line:
                            self.log("瀏覽器已關閉，錄製結束")
                            # 当进程结束时，检查是否有生成的脚本文件
                            self.root.after(0, self._check_recorded_script)
                
                # 无论如何，当进程输出结束时，检查是否有生成的脚本文件
                self.root.after(0, self._check_recorded_script)
            
            # 启动监控线程
            in_code_section = False
            monitor_thread = threading.Thread(target=monitor_output, daemon=True)
            monitor_thread.start()
            
            # 显示录制状态提示
            self.log("錄製已開始，請在瀏覽器中操作...")
            self.log("當您完成操作，請手動關閉瀏覽器窗口來結束錄製")
                
        except Exception as e:
            self.log(f"錄製過程中發生錯誤: {e}")
            self.log(traceback.format_exc())
            # 更新UI
            self.root.after(0, self._finish_recording)
    
    def _check_recorded_script(self):
        """检查是否有生成的脚本文件"""
        generated_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated_script.py")
        if os.path.exists(generated_script):
            try:
                with open(generated_script, "r", encoding="utf-8") as f:
                    # 只读取非注释行和非空行
                    self.recorded_code = [
                        line.strip() for line in f 
                        if line.strip() and not line.strip().startswith("#") and not "browser" in line
                    ]
                
                self.log(f"已從生成的腳本文件中讀取 {len(self.recorded_code)} 行代碼")
            except Exception as e:
                self.log(f"讀取生成的腳本文件時出錯: {e}")
        
        # 清理临时文件
        try:
            recorder_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recorder_temp.py")
            if os.path.exists(recorder_script):
                os.remove(recorder_script)
                
            # 清理临时JSON文件
            recorded_actions = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recorded_actions.json")
            if os.path.exists(recorded_actions):
                os.remove(recorded_actions)
        except Exception as e:
            self.log(f"清理臨時文件時出錯: {e}")
            
        # 完成录制
        self._finish_recording()
    
    def _finish_recording(self):
        """完成录制并更新UI"""
        self.recording = False
        self.record_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.test_page_btn.config(state=tk.NORMAL)
        self.execute_btn.config(state=tk.NORMAL)
        self.record_status_var.set("录制完成")
        
        # 将录制的代码添加到编辑区
        if self.recorded_code:
            # 备份当前编辑区内容
            current_content = self.script_text.get(1.0, tk.END).strip()
            
            # 添加录制的代码
            if current_content:
                # 添加到现有内容
                separator = "\n\n# --- 新录制内容 ---\n"
                self.script_text.insert(tk.END, separator)
                for line in self.recorded_code:
                    self.script_text.insert(tk.END, f"\n{line}")
            else:
                # 设置为录制的代码
                self.script_text.delete(1.0, tk.END)
                
                # 添加标准模板
                template = """# Playwright 脚本 - 由录制功能生成
# 可以编辑此脚本，然后点击"执行脚本"按钮运行

browser = playwright.chromium.launch(headless=False)
page = browser.new_page()

# 录制的操作:
"""
                self.script_text.insert(tk.END, template)
                
                # 添加录制的操作
                for line in self.recorded_code:
                    self.script_text.insert(tk.END, f"{line}\n")
                    
                # 添加关闭浏览器
                self.script_text.insert(tk.END, "\n# 关闭浏览器\nbrowser.close()")
            
            self.log(f"已将录制的 {len(self.recorded_code)} 行代码添加到脚本编辑区")
        else:
            self.log("未录制到任何操作")
            
    def stop_recording(self):
        """停止录制"""
        if not self.recording:
            return
            
        self.log("正在停止錄製...")
        
        # 尝试终止录制进程
        if self.recorder_process:
            try:
                # 在Windows上使用taskkill强制关闭进程树
                if sys.platform == "win32":
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(self.recorder_process.pid)],
                        stderr=subprocess.PIPE,
                        stdout=subprocess.PIPE
                    )
                else:
                    # 在Unix系统上终止进程
                    os.kill(self.recorder_process.pid, signal.SIGTERM)
                
                self.log("已終止錄製進程")
            except Exception as e:
                self.log(f"終止錄製進程時出錯: {e}")
            
            # 给进程一些时间来清理
            time.sleep(0.5)
            
            # 检查生成的脚本文件
            self.root.after(100, self._check_recorded_script)
    
    def record_test_page(self):
        """录制测试页面"""
        # 获取测试页面路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        test_page_path = os.path.join(current_dir, "web", "test_page.html")
        
        if os.path.exists(test_page_path):
            # 设置URL为测试页面
            self.url_var.set(f"file://{test_page_path}")
            self.log(f"已设置测试页面: {test_page_path}")
            
            # 开始录制
            self.start_recording()
        else:
            self.log(f"找不到测试页面: {test_page_path}")
            messagebox.showinfo("提示", f"找不到测试页面: {test_page_path}\n请确保web目录中存在test_page.html文件")

def main():
    """程式入口點"""
    root = tk.Tk()
    app = PlaywrightGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
