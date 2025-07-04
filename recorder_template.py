"""
此模組包含用於生成錄製腳本的模板。
"""
import os

def get_recorder_script_template(url):
    """
    返回錄製腳本的模板，替換其中的URL佔位符。
    
    Args:
        url: 要在錄製中打開的URL
        
    Returns:
        str: 完整的錄製腳本代碼
    """
    # 讀取JS錄製文件
    current_dir = os.path.dirname(os.path.abspath(__file__))
    js_path = os.path.join(current_dir, "recorder_script.js")
    
    with open(js_path, "r", encoding="utf-8") as f:
        recorder_js = f.read()
    
    return f'''
from playwright.sync_api import sync_playwright
import json
import os
import sys
import time
import re
import datetime

# 記錄的操作將保存到這個列表
recorded_actions = []

def generate_best_selector(page, element):
    """生成最佳選擇器，嘗試多種選擇器策略"""
    # 嘗試使用ID選擇器（最優先）
    try:
        id_val = page.evaluate("el => el.id", element)
        if id_val:
            return f"#{id_val}"
    except:
        pass
    
    # 嘗試使用name選擇器（針對表單元素）
    try:
        name_val = page.evaluate("el => el.getAttribute('name')", element)
        if name_val:
            return f"[name='{name_val}']"
    except:
        pass
    
    # 嘗試文本選擇器（對於按鈕等）
    try:
        text_val = page.evaluate("el => el.textContent?.trim()", element)
        if text_val and len(text_val) < 80:
            return f"text={text_val}"
    except:
        pass
    
    # 嘗試CSS類選擇器
    try:
        class_val = page.evaluate("el => el.className", element)
        if class_val and isinstance(class_val, str) and class_val.strip():
            return f".{class_val.strip().replace(' ', '.')}"
    except:
        pass
    
    # 最後使用標籤名稱
    try:
        tag_name = page.evaluate("el => el.tagName.toLowerCase()", element)
        return tag_name
    except:
        return "body"

def record():
    with sync_playwright() as playwright:
        # 啟動瀏覽器
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context(viewport={{"width": 1280, "height": 720}})
        
        # 設置頁面事件監聽
        page = context.new_page()
        
        # 打印提示信息
        print("========================================")
        print("錄製已開始，請在瀏覽器中操作...")
        print("當您完成操作，請手動關閉瀏覽器窗口")
        print("或按Ctrl+C來停止錄製")
        print("========================================")
        
        # 導航到URL
        page.goto("{url}")
        print(f"已打開頁面: {page.url}")
        
        # 注入錄製腳本
        page.evaluate(f"""() => {{
{recorder_js}
}}""")
        
        # 拦截console消息以捕获自定义事件
        page.on("console", lambda msg: handle_console_message(page, msg.text))
            
        # 记录导航事件
        page.on("framenavigated", lambda frame: 
            recorded_actions.append({{"type": "goto", "url": frame.url, "timestamp": time.time()}})
            if frame.is_main else None)
        
        print("正在錄製操作...")
        
        # 保存录制开始时间
        start_time = datetime.datetime.now()
        
        # 设置一个全局标志，表示我们是否要结束录制
        finished = False
        
        # 等待用户关闭浏览器
        try:
            # 使用一个更可靠的循环来检查浏览器是否仍然打开
            while not finished:
                try:
                    # 使用 page.title() 作为简单的"窗口存活检查"
                    # 如果页面已关闭，这将抛出异常
                    title = page.title()
                    
                    # 如果能获取标题，页面仍然存在，等待一会儿
                    time.sleep(0.5)
                except Exception as e:
                    # 如果访问页面属性抛出异常，说明页面可能已关闭
                    print("頁面已關閉，結束錄製...")
                    finished = True
                    break
                
        except KeyboardInterrupt:
            print("收到鍵盤中斷，停止錄製...")
            finished = True
        except Exception as e:
            print(f"錄製過程中發生錯誤: {{e}}")
        finally:
            # 计算录制时长
            duration = datetime.datetime.now() - start_time
            print(f"錄製時長: {{duration.total_seconds():.1f}} 秒")
            
            # 保存记录的操作
            try:
                if recorded_actions:
                    # 生成带时间戳的文件名
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    json_filename = f"recorded_actions_{timestamp}.json"
                    script_filename = f"recorded_script_{timestamp}.txt"
                    
                    # 保存JSON操作记录
                    scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Scripts")
                    os.makedirs(scripts_dir, exist_ok=True)
                    
                    json_path = os.path.join(scripts_dir, json_filename)
                    with open(json_path, "w", encoding="utf-8") as f:
                        json.dump(recorded_actions, f, indent=2, ensure_ascii=False)
                    print(f"已保存錄製操作到 {{json_path}}")
                    
                    # 生成Python代码
                    code = generate_code(recorded_actions)
                    
                    # 保存生成的代码到Scripts目录
                    script_path = os.path.join(scripts_dir, script_filename)
                    with open(script_path, "w", encoding="utf-8") as f:
                        f.write(code)
                    print(f"已保存生成的腳本到 {{script_path}}")
                    
                    # 同时保存到当前目录的generated_script.py用于GUI读取
                    with open("generated_script.py", "w", encoding="utf-8") as f:
                        f.write("""# Generated Playwright script
# 由錄製功能自動生成的腳本
# 可以直接在Playwright E2E助手中運行

# 啟動瀏覽器
browser = playwright.chromium.launch(headless=False)
page = browser.new_page()

# 錄製的操作:
""")
                        for line in code.split("\\n"):
                            if line.strip():
                                f.write(f"{line}\\n")
                        f.write("""
# 關閉瀏覽器
browser.close()
""")
                else:
                    print("沒有錄製到任何操作")
            except Exception as e:
                print(f"保存錄製操作時出錯: {{e}}")
            
            # 确保浏览器关闭
            try:
                browser.close()
                print("瀏覽器已關閉")
            except:
                pass

def handle_console_message(page, text):
    """处理从页面发送的控制台消息"""
    if text.startswith("RECORDER_CLICK:"):
        try:
            data = json.loads(text[len("RECORDER_CLICK:"):])
            
            # 獲取點擊的元素
            element = page.evaluate(f"() => document.elementsFromPoint({data['x']}, {data['y']})[0]")
            
            # 生成穩定的選擇器
            selector = generate_best_selector(page, element)
            
            recorded_actions.append({{
                "type": "click",
                "selector": selector,
                "raw_data": data,
                "timestamp": time.time()
            }})
            print(f"錄製: 點擊 {{selector}}")
        except Exception as e:
            print(f"處理點擊事件時出錯: {{e}}")
    
    elif text.startswith("RECORDER_FILL:"):
        try:
            data = json.loads(text[len("RECORDER_FILL:"):])
            
            # 建立選擇器
            selector = None
            if data.get('id'):
                selector = f"#{data['id']}"
            elif data.get('name'):
                selector = f"[name='{data['name']}']"
            else:
                selector = data['tagName'].lower()
                if data.get('type'):
                    selector += f"[type='{data['type']}']"
            
            recorded_actions.append({{
                "type": "fill",
                "selector": selector,
                "value": data.get('value', ''),
                "raw_data": data,
                "timestamp": time.time()
            }})
            print(f"錄製: 填寫 {{selector}} 為 {{data.get('value', '')}}")
        except Exception as e:
            print(f"處理填寫事件時出錯: {{e}}")
    
    elif text.startswith("RECORDER_SELECT:"):
        try:
            data = json.loads(text[len("RECORDER_SELECT:"):])
            
            # 建立選擇器
            selector = None
            if data.get('id'):
                selector = f"#{data['id']}"
            elif data.get('name'):
                selector = f"[name='{data['name']}']"
            else:
                selector = "select"
            
            recorded_actions.append({{
                "type": "select",
                "selector": selector,
                "value": data.get('value', ''),
                "text": data.get('selectedText', ''),
                "raw_data": data,
                "timestamp": time.time()
            }})
            print(f"錄製: 選擇 {{selector}} 為 {{data.get('selectedText', '')}}")
        except Exception as e:
            print(f"處理選擇事件時出錯: {{e}}")

def generate_code(actions):
    """从记录的操作生成Playwright Python代码"""
    if not actions:
        return ""
        
    # 基本代码结构
    code = []
    
    # 过滤和整理操作
    filtered_actions = []
    last_goto = None
    
    for action in actions:
        action_type = action.get("type")
        
        # 处理导航操作
        if action_type == "goto":
            # 只保留最后一次导航到同一URL
            url = action.get("url")
            if url and not url.startswith("about:blank"):
                last_goto = action
        else:
            filtered_actions.append(action)
    
    # 添加最后一次导航操作
    if last_goto:
        filtered_actions.insert(0, last_goto)
    
    # 生成代码
    for action in filtered_actions:
        action_type = action.get("type")
        
        if action_type == "goto":
            url = action.get("url")
            if url and not url.startswith("about:blank"):
                code.append(f'page.goto("{url}")')
                
        elif action_type == "click":
            selector = action.get("selector")
            if selector:
                code.append(f'page.click("{selector}")')
                
        elif action_type == "fill":
            selector = action.get("selector")
            value = action.get("value")
            if selector and value is not None:
                # 转义引号
                value = value.replace('"', '\\"')
                code.append(f'page.fill("{selector}", "{value}")')
                
        elif action_type == "select":
            selector = action.get("selector")
            value = action.get("value")
            if selector and value is not None:
                code.append(f'page.select_option("{selector}", "{value}")')
    
    return "\\n".join(code)

# 启动录制
record()
''' 