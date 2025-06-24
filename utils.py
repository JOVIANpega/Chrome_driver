# -*- coding: utf-8 -*-
import os
import sys
import logging
import json
import re
import difflib
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime
import time

# 版本信息
VERSION = "0.9.1"
VERSION_DATE = "2023-09-26"

# 常量定義
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
STEP_WINDOW_WIDTH = 250
STEP_WINDOW_HEIGHT = 500
DEFAULT_WAIT_TIME = 5
LOG_FILE = "log.txt"
COMMAND_FILE = "command.txt"
DEFAULT_FONT_SIZE = 12
MIN_FONT_SIZE = 8
MAX_FONT_SIZE = 18

# 指令類型常量
CMD_BASIC = "basic"           # 基本操作指令
CMD_VERIFY = "verify"         # 驗證指令
CMD_WAIT = "wait"             # 等待指令
CMD_NAV = "navigation"        # 導航指令
CMD_TEST = "test"             # 測試案例相關指令
CMD_FUZZY = "fuzzy"           # 模糊匹配指令

# 相似度閾值常量
DEFAULT_SIMILARITY_THRESHOLD = 0.8  # 80% 相似度

# 指令定義
COMMANDS = {
    # 基本操作指令
    "OPEN_URL": CMD_BASIC,
    "WAIT": CMD_BASIC,
    "REFRESH": CMD_BASIC,
    "BACK": CMD_BASIC,
    "CLICK_BY_TEXT": CMD_BASIC,
    "CLICK_BY_ID": CMD_BASIC,
    "TYPE": CMD_BASIC,
    "LOGIN": CMD_BASIC,
    
    # 驗證指令
    "VERIFY_TEXT_EXISTS": CMD_VERIFY,
    "VERIFY_TEXT_NOT_EXISTS": CMD_VERIFY,
    "VERIFY_ELEMENT_EXISTS": CMD_VERIFY,
    "VERIFY_ELEMENT_VALUE": CMD_VERIFY,
    "VERIFY_COUNT": CMD_VERIFY,
    
    # 等待指令
    "WAIT_FOR_TEXT": CMD_WAIT,
    "WAIT_FOR_ELEMENT": CMD_WAIT,
    "WAIT_FOR_PAGE_LOAD": CMD_WAIT,
    "WAIT_UNTIL_CHANGES": CMD_WAIT,
    "POLL_UNTIL": CMD_WAIT,
    
    # 導航與互動指令
    "NAV_SEQUENCE_START": CMD_NAV,
    "NAV_SEQUENCE_END": CMD_NAV,
    "SCROLL_TO_ELEMENT": CMD_NAV,
    "SCROLL_TO_BOTTOM": CMD_NAV,
    "EXPAND": CMD_NAV,
    
    # 測試案例相關
    "TEST_CASE": CMD_TEST,
    "DESCRIPTION": CMD_TEST,
    "SEVERITY": CMD_TEST,
    
    # 模糊匹配指令 (新增)
    "VERIFY_TEXT_CONTAINS": CMD_FUZZY,      # 文本包含部分匹配
    "VERIFY_TEXT_PATTERN": CMD_FUZZY,       # 文本模式匹配 (支持正則表達式)
    "VERIFY_TEXT_SIMILAR": CMD_FUZZY,       # 文本相似度匹配 (支持模糊匹配)
    "VERIFY_ANY_TEXT": CMD_FUZZY,           # 多條件 OR 關係匹配 (任一條件符合即通過)
    "VERIFY_ALL_TEXT": CMD_FUZZY,           # 多條件 AND 關係匹配 (所有條件都符合才通過)
}

# 設置文件路徑
SETTINGS_FILE = "settings.json"

def setup_logging() -> None:
    """設置日誌系統"""
    # 確保日誌目錄存在
    log_dir = "automation_logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 設置日誌檔案名稱，使用當前日期時間
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"automation_{current_time}.log")
    
    # 配置日誌
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 同時輸出到控制檯
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    
    # 將 log.txt 設置為默認日誌
    handler = logging.FileHandler('log.txt', mode='a')
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)
    logging.getLogger('').addHandler(handler)

def read_commands() -> List[Tuple[str, List[str]]]:
    """讀取命令檔案"""
    commands = []
    try:
        if os.path.exists(COMMAND_FILE):
            with open(COMMAND_FILE, "r", encoding="utf-8") as f:
                in_nav_sequence = False
                nav_sequence_commands = []
                nav_sequence_name = ""
                
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    
                    # 處理導航序列
                    if line.startswith("NAV_SEQUENCE_START"):
                        in_nav_sequence = True
                        if "=" in line:
                            _, nav_sequence_name = line.split("=", 1)
                            nav_sequence_name = nav_sequence_name.strip()
                        else:
                            nav_sequence_name = "Navigation Sequence"
                        continue
                    
                    if line.startswith("NAV_SEQUENCE_END"):
                        in_nav_sequence = False
                        commands.append(("NAV_SEQUENCE", [nav_sequence_name] + nav_sequence_commands))
                        nav_sequence_commands = []
                        continue
                    
                    if in_nav_sequence:
                        if "=" in line:
                            cmd, params_str = line.split("=", 1)
                            cmd = cmd.strip()
                            params = [p.strip() for p in params_str.split("||")]
                            nav_sequence_commands.append(f"{cmd}:{','.join(params)}")
                        continue
                    
                    # 處理一般指令
                    if "=" in line:
                        cmd, params_str = line.split("=", 1)
                        cmd = cmd.strip()
                        params = [p.strip() for p in params_str.split("||")]
                        commands.append((cmd, params))
            
            logging.info(f"已載入 {len(commands)} 個命令")
        else:
            logging.info(f"找不到 {COMMAND_FILE} 檔案")
    except Exception as e:
        logging.error(f"讀取命令檔案時發生錯誤: {str(e)}")
    
    return commands

def load_keywords_from_command() -> List[str]:
    """從命令檔案讀取關鍵字 - 增強版"""
    try:
        keywords = []
        
        # 檢查命令檔案是否存在
        if not os.path.exists("command.txt"):
            logging.error("找不到 command.txt 檔案")
            return []
        
        with open("command.txt", "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                # 忽略註釋行和空行
                if not line or line.startswith("#"):
                    continue
                
                # 尋找 VERIFY_TEXT_EXISTS 命令中的關鍵字
                if line.startswith("VERIFY_TEXT_EXISTS="):
                    keyword = line.split("=", 1)[1].strip()
                    # 如果關鍵字不是指令或設定，則加入列表
                    if keyword and not keyword.startswith("#") and len(keyword) > 3 and not any(x in keyword for x in ["=", "||", "<", ">"]):
                        keywords.append(keyword)
                        logging.debug(f"從 VERIFY_TEXT_EXISTS 找到關鍵字: {keyword}")
                        
                # 尋找 VERIFY_TEXT_CONTAINS 命令中的關鍵字
                elif line.startswith("VERIFY_TEXT_CONTAINS="):
                    parts = line.split("=", 1)[1].strip().split("||")
                    if len(parts) > 0 and parts[0].strip():
                        keyword = parts[0].strip()
                        if len(keyword) > 3:
                            keywords.append(keyword)
                            logging.debug(f"從 VERIFY_TEXT_CONTAINS 找到關鍵字: {keyword}")
                
                # 尋找特定的關鍵字，這些關鍵字可能在測試中特別重要
                elif any(important in line for important in ["挪威", "台灣", "蕭美琴", "Nokia", "Camera"]):
                    # 從行中提取可能的關鍵字
                    potential_keywords = [word for word in line.split() if len(word) > 3 and not any(x in word for x in ["=", "||", "<", ">", "#"])]
                    for keyword in potential_keywords:
                        if keyword not in keywords:
                            keywords.append(keyword)
                            logging.debug(f"從特定行中找到關鍵字: {keyword}")
        
        # 移除重複的關鍵字
        unique_keywords = list(set(keywords))
        
        # 確保重要的關鍵字被包含
        important_keywords = ["挪威國家廣播公司", "台灣的戰貓", "蕭美琴", "Nokia 360 Camera", "自動化測試頁面"]
        for keyword in important_keywords:
            if keyword not in unique_keywords:
                unique_keywords.append(keyword)
                logging.debug(f"添加重要關鍵字: {keyword}")
        
        # 只保留前10個關鍵字
        result_keywords = unique_keywords[:10] if len(unique_keywords) > 10 else unique_keywords
        
        logging.info(f"已載入 {len(result_keywords)} 個關鍵字")
        return result_keywords
    except Exception as e:
        logging.error(f"讀取關鍵字時發生錯誤: {str(e)}")
        logging.debug(f"錯誤詳情: {traceback.format_exc()}")
        
        # 返回一些默認關鍵字，確保測試可以繼續
        default_keywords = ["挪威國家廣播公司", "台灣的戰貓", "蕭美琴", "Nokia 360 Camera", "自動化測試頁面"]
        logging.info(f"使用 {len(default_keywords)} 個默認關鍵字")
        return default_keywords

def parse_command_param(param: str, default_value: Any = None) -> Any:
    """解析命令參數，處理特殊值和預設值"""
    if not param:
        return default_value
    
    # 處理數字
    if param.isdigit():
        return int(param)
    
    # 處理布林值
    if param.lower() == "true":
        return True
    if param.lower() == "false":
        return False
    
    # 返回字串
    return param

def get_command_type(cmd: str) -> str:
    """獲取命令類型"""
    return COMMANDS.get(cmd, "unknown")

def is_verification_command(cmd: str) -> bool:
    """檢查是否為驗證命令"""
    return get_command_type(cmd) == CMD_VERIFY

def is_wait_command(cmd: str) -> bool:
    """檢查是否為等待命令"""
    return get_command_type(cmd) == CMD_WAIT 

def is_fuzzy_command(cmd: str) -> bool:
    """檢查是否為模糊匹配命令"""
    return get_command_type(cmd) == CMD_FUZZY

def calculate_text_similarity(text1: str, text2: str) -> float:
    """計算兩個文本的相似度 (0.0 到 1.0)"""
    return difflib.SequenceMatcher(None, text1, text2).ratio()

def text_contains(page_text: str, expected_text: str) -> bool:
    """檢查頁面文本是否包含預期文本 (部分匹配)"""
    return expected_text.lower() in page_text.lower()

def text_matches_pattern(page_text: str, pattern: str) -> bool:
    """檢查頁面文本是否符合正則表達式模式"""
    try:
        regex = re.compile(pattern, re.IGNORECASE)
        return bool(regex.search(page_text))
    except re.error as e:
        logging.error(f"正則表達式錯誤: {str(e)}")
        return False

def text_is_similar(page_text: str, expected_text: str, threshold: float = DEFAULT_SIMILARITY_THRESHOLD) -> bool:
    """檢查頁面文本與預期文本的相似度是否超過閾值"""
    return calculate_text_similarity(page_text.lower(), expected_text.lower()) >= threshold

def any_text_matches(page_text: str, expected_texts: List[str]) -> bool:
    """檢查頁面文本是否匹配任一預期文本 (OR 邏輯)"""
    return any(expected_text.lower() in page_text.lower() for expected_text in expected_texts)

def all_texts_match(page_text: str, expected_texts: List[str]) -> bool:
    """檢查頁面文本是否匹配所有預期文本 (AND 邏輯)"""
    return all(expected_text.lower() in page_text.lower() for expected_text in expected_texts)

def get_resource_path(relative_path: str) -> str:
    """獲取資源文件的絕對路徑（打包後可用）"""
    try:
        # PyInstaller 創建臨時文件夾 _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def save_settings(settings: Dict[str, Any]) -> bool:
    """保存設置到JSON文件"""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as file:
            json.dump(settings, file, ensure_ascii=False, indent=4)
        logging.info("設置已保存")
        return True
    except Exception as e:
        logging.error(f"保存設置時發生錯誤: {str(e)}")
        return False

def load_settings() -> Dict[str, Any]:
    """從JSON文件加載設置"""
    default_settings = {
        "font_size": DEFAULT_FONT_SIZE,
        "test_results": {},
        "last_run_date": ""
    }
    
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as file:
                settings = json.load(file)
            logging.info("設置已載入")
            return settings
        else:
            logging.info("未找到設置文件，使用默認設置")
            return default_settings
    except Exception as e:
        logging.error(f"載入設置時發生錯誤: {str(e)}")
        return default_settings

def update_test_results(test_name: str, passed: bool) -> None:
    """更新測試結果"""
    settings = load_settings()
    
    if "test_results" not in settings:
        settings["test_results"] = {}
    
    # 更新測試結果
    settings["test_results"][test_name] = passed
    
    # 更新最後執行日期
    settings["last_run_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 保存設置
    save_settings(settings) 