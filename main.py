import os
import sys
import asyncio
import tkinter as tk
import threading
from app import BrowserAutomationApp
from browser_automation import BrowserAutomation

# 創建一個全局的執行器，用於處理所有的異步操作
class AsyncExecutor:
    def __init__(self):
        self.loop = None
        self.thread = None
        self.running = False
        self.automation = None
    
    def start(self):
        """啟動執行器"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.thread.start()
    
    def _run_event_loop(self):
        """運行事件循環"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_forever()
        finally:
            self.loop.close()
            self.loop = None
    
    def stop(self):
        """停止執行器"""
        if not self.running:
            return
        
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)
    
    def run_task(self, coroutine):
        """執行異步任務
        
        Args:
            coroutine: 要執行的協程
        
        Returns:
            返回Future對象
        """
        if not self.running or not self.loop:
            return None
        
        future = asyncio.run_coroutine_threadsafe(coroutine, self.loop)
        return future

# 全局執行器
executor = AsyncExecutor()

def main():
    """主程序入口點"""
    # 啟動異步執行器
    executor.start()
    
    # 確保資源目錄存在
    os.makedirs("assets", exist_ok=True)
    
    # 創建GUI
    root = tk.Tk()
    app = BrowserAutomationApp(root)
    
    # 替換錄製相關函數
    async def start_recording_async(url=None):
        """開始錄製的異步方法"""
        try:
            if executor.automation:
                # 如果已經有一個瀏覽器實例，嘗試關閉它
                try:
                    await executor.automation.close_browser()
                except Exception:
                    pass
            
            # 創建新的自動化實例
            executor.automation = BrowserAutomation(
                log_callback=app.log_message,
                on_script_generated=app.on_script_generated,
                on_recording_stopped=app.on_recording_stopped
            )
            
            # 處理URL
            if url:
                # 確保URL是有效的
                if url.startswith("file://"):
                    # 本地文件URL，保持原樣
                    pass
                elif "://" not in url:
                    # 添加協議前綴
                    url = "https://" + url
            
            # 啟動瀏覽器
            await executor.automation.start_browser(headless=False)
            
            # 啟動錄製
            await executor.automation.start_recording(initial_url=url)
        except Exception as e:
            app.log_message(f"錄製啟動失敗: {e}")
            app.root.after(0, lambda: app.on_recording_stopped(False))
    
    def start_recording(url=None):
        """啟動錄製"""
        app.log_message("正在啟動錄製...")
        executor.run_task(start_recording_async(url))
    
    async def pause_recording_async():
        """暫停錄製的異步方法"""
        if executor.automation:
            executor.automation.pause_recording()
    
    def pause_recording():
        """暫停錄製"""
        executor.run_task(pause_recording_async())
    
    async def resume_recording_async():
        """繼續錄製的異步方法"""
        if executor.automation:
            executor.automation.resume_recording()
    
    def resume_recording():
        """繼續錄製"""
        executor.run_task(resume_recording_async())
    
    async def stop_recording_async():
        """停止錄製的異步方法"""
        if not executor.automation:
            app.log_message("沒有正在進行的錄製")
            app.root.after(0, lambda: app.on_recording_stopped(False))
            return
        
        try:
            # 停止錄製
            print("嘗試停止錄製...")
            result = await executor.automation.stop_recording()
            validation_success = False
            
            if result is not None:
                # 確保result是一個元組，包含script_content和script_filename
                if isinstance(result, tuple) and len(result) == 2:
                    script_content, script_filename = result
                    print(f"成功獲取錄製結果，腳本文件名: {script_filename}")
                    app.script_content = script_content  # 確保更新app的script_content
                    
                    try:
                        # 驗證腳本
                        print("開始驗證腳本...")
                        validation_success = await executor.automation.verify_script(script_filename)
                        print(f"腳本驗證結果: {validation_success}")
                    except Exception as e:
                        app.log_message(f"驗證腳本時出錯: {str(e)}")
                        print(f"驗證腳本時出錯: {e}")
                else:
                    app.log_message("錄製結果格式不正確")
                    print(f"錄製結果格式不正確: {result}")
            else:
                app.log_message("錄製未生成有效腳本")
                print("錄製未生成有效腳本")
            
            # 嘗試關閉瀏覽器
            try:
                await executor.automation.close_browser()
                print("瀏覽器已關閉")
            except Exception as e:
                print(f"關閉瀏覽器時出錯 (忽略): {e}")
            
            # 清除自動化實例
            executor.automation = None
            
            # 在UI線程更新結果
            app.root.after(0, lambda: app.on_recording_stopped(validation_success))
        except Exception as e:
            print(f"停止錄製時出錯: {e}")
            app.log_message(f"停止錄製時出錯: {str(e)}")
            app.root.after(0, lambda: app.on_recording_stopped(False))
    
    def stop_recording():
        """停止錄製"""
        app.log_message("正在停止錄製...")
        executor.run_task(stop_recording_async())
    
    # 替換執行腳本的方法
    async def execute_script_async(script_file):
        """異步執行腳本"""
        print("===execute_script_async被調用===")
        if not script_file:
            app.log_message("腳本檔案為空，無法執行")
            print("腳本檔案為空，無法執行")
            return
        
        try:
            # 關閉可能存在的瀏覽器實例
            if executor.automation:
                try:
                    print("關閉現有的瀏覽器實例")
                    await executor.automation.close_browser()
                except Exception as e:
                    print(f"關閉瀏覽器時出錯: {e}")
                    pass
            
            # 創建新的自動化實例
            executor.automation = BrowserAutomation(
                log_callback=app.log_message,
                on_script_end=app.on_script_execution_end
            )
            print("創建了新的BrowserAutomation實例")
            
            # 啟動瀏覽器
            print("正在啟動瀏覽器...")
            await executor.automation.start_browser(headless=False)
            print("瀏覽器已啟動")
            
            # 執行腳本
            print(f"開始執行腳本: {script_file}")
            success = await executor.automation.execute_script(script_file)
            print(f"腳本執行結果: {'成功' if success else '失敗'}")
            return success
        except Exception as e:
            print(f"執行腳本時出錯: {e}")
            app.log_message(f"執行腳本時出錯: {str(e)}")
            app.root.after(0, app.on_script_execution_end)
            return False
    
    def execute_script(script_file=None):
        """執行腳本"""
        print("===main.py中的execute_script被調用===")
        
        if not script_file:
            # 如果沒有指定腳本文件，使用界面中的腳本內容
            script_content = app.script_text.get(1.0, tk.END).strip()
            print(f"從app.script_text獲取的內容長度: {len(script_content)}")
            
            if not script_content:
                script_content = app.script_content.strip()
                print(f"從app.script_content獲取的內容長度: {len(script_content)}")
                
            if not script_content:
                app.log_message("腳本內容為空，無法執行")
                print("腳本內容為空，無法執行")
                return
                
            # 保存臨時腳本文件
            script_file = "temp_script.txt"
            try:
                with open(script_file, "w", encoding="utf-8") as f:
                    f.write(script_content)
                    print(f"main.py成功寫入臨時腳本: {script_file}")
            except Exception as e:
                app.log_message(f"保存臨時腳本失敗: {str(e)}")
                print(f"保存臨時腳本失敗: {e}")
                return
        
        # 更新按鈕狀態
        app.executing = True
        app.執行_btn.configure(state=tk.DISABLED)
        app.載入_btn.configure(state=tk.DISABLED)
        app.record_btn.configure(state=tk.DISABLED)
        app.record_local_btn.configure(state=tk.DISABLED)
        app.record_test_btn.configure(state=tk.DISABLED)
        
        app.log_message(f"開始執行腳本: {script_file}")
        print(f"main.py開始執行腳本: {script_file}")
        executor.run_task(execute_script_async(script_file))
    
    # 設置關閉窗口的處理函數
    def on_closing():
        """關閉窗口時的處理"""
        async def close_browser():
            if executor.automation:
                await executor.automation.close_browser()
        
        # 優雅關閉瀏覽器
        if executor.automation:
            executor.run_task(close_browser())
        
        # 停止執行器
        executor.stop()
        
        # 關閉窗口
        root.destroy()
        
        # 確保退出程序
        os._exit(0)

    # 將app的各個函數連接到真實實現
    app.start_recording = start_recording
    app.pause_recording = pause_recording
    app.resume_recording = resume_recording
    app.stop_recording = stop_recording
    
    # 替換執行腳本方法並設置標記
    app._execute_script_orig = app.execute_script  # 保存原始方法
    app.execute_script = execute_script
    app._execute_script_replaced = True
    
    # 設置窗口關閉處理函數
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # 啟動主循環
    try:
        root.mainloop()
    finally:
        # 確保優雅關閉
        executor.stop()
        os._exit(0)

if __name__ == "__main__":
    main()
