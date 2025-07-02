import os
import sys
import asyncio
import tkinter as tk
from new_app import BrowserAutomationApp
from new_browser_automation import BrowserAutomation

def main():
    """主程序入口點"""
    # 確保資源目錄存在
    os.makedirs("assets", exist_ok=True)
    
    # 創建GUI
    root = tk.Tk()
    app = BrowserAutomationApp(root)
    
    # 創建共享的自動化實例
    automation = None
    
    # 替換錄製相關函數
    async def start_recording_async():
        """開始錄製的異步方法"""
        nonlocal automation
        try:
            automation = BrowserAutomation(callback=lambda progress, msg: app.root.after(0, lambda: app.status_var.set(msg)))
            await automation.start_recording()
        except Exception as e:
            app.root.after(0, lambda: app.status_var.set(f"錄製啟動失敗: {e}"))
    
    def start_recording():
        """啟動錄製"""
        asyncio.run(start_recording_async())
    
    async def pause_recording_async():
        """暫停錄製的異步方法"""
        nonlocal automation
        if automation:
            automation.pause_recording()
    
    def pause_recording():
        """暫停錄製"""
        asyncio.run(pause_recording_async())
    
    async def resume_recording_async():
        """繼續錄製的異步方法"""
        nonlocal automation
        if automation:
            automation.resume_recording()
    
    def resume_recording():
        """繼續錄製"""
        asyncio.run(resume_recording_async())
    
    async def stop_recording_async():
        """停止錄製的異步方法"""
        nonlocal automation
        if automation:
            actions = await automation.stop_recording()
            for action in actions:
                app.root.after(0, lambda a=action: app.append_script(a))
            await automation.close_browser()
            automation = None
    
    def stop_recording():
        """停止錄製"""
        asyncio.run(stop_recording_async())
    
    # 替換執行腳本的方法
    def execute_script_with_automation(script_content):
        """使用自動化執行腳本"""
        async def run_script():
            nonlocal automation
            try:
                app.status_var.set("正在啟動瀏覽器...")
                automation = BrowserAutomation(callback=lambda progress, msg: app.root.after(0, lambda: app.status_var.set(msg)))
                await automation.execute_script(script_content)
                app.root.after(0, lambda: app.status_var.set("腳本執行完成"))
            except Exception as e:
                app.root.after(0, lambda: app.status_var.set(f"執行錯誤: {e}"))
            finally:
                automation = None
                app.root.after(0, app.enable_after_execution)
        
        # 建立新線程執行異步代碼
        try:
            asyncio.run(run_script())
        except Exception as e:
            app.status_var.set(f"執行錯誤: {e}")
            app.enable_after_execution()
    
    # 替換原始方法
    app.execute_script = execute_script_with_automation
    app.start_recording = start_recording
    app.pause_recording = pause_recording
    app.resume_recording = resume_recording
    app.stop_recording = stop_recording
    
    # 啟動GUI主循環
    root.mainloop()

if __name__ == "__main__":
    main()
