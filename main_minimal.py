import os
import sys
import asyncio
import tkinter as tk
from app_minimal import BrowserAutomationApp
from browser_automation import BrowserAutomation

def main():
    """主程序入口點"""
    # 確保資源目錄存在
    os.makedirs("assets", exist_ok=True)
    
    # 創建GUI
    root = tk.Tk()
    app = BrowserAutomationApp(root)
    
    # 使用異步自動化替換
    def execute_script_with_automation(script_content):
        async def run_script():
            try:
                app.status_var.set("正在啟動瀏覽器...")
                automation = BrowserAutomation(callback=lambda progress, msg: app.root.after(0, lambda: app.status_var.set(msg)))
                await automation.execute_script(script_content)
                app.root.after(0, lambda: app.status_var.set("腳本執行完成"))
            except Exception as e:
                app.root.after(0, lambda: app.status_var.set(f"執行錯誤: {e}"))
            finally:
                app.root.after(0, app.enable_after_execution)
        
        # 建立新線程執行異步代碼
        try:
            asyncio.run(run_script())
        except Exception as e:
            app.status_var.set(f"執行錯誤: {e}")
            app.enable_after_execution()
    
    # 替換原始方法
    app.execute_script = execute_script_with_automation
    
    # 啟動GUI主循環
    root.mainloop()

if __name__ == "__main__":
    main() 