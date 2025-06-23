# -*- coding: utf-8 -*-
import os
import logging
from typing import List, Tuple, Dict, Any, Optional

# 常量定義
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
STEP_WINDOW_WIDTH = 250
STEP_WINDOW_HEIGHT = 500
DEFAULT_WAIT_TIME = 5
LOG_FILE = "log.txt"
COMMAND_FILE = "command.txt"
DEFAULT_FONT_SIZE = 10

# 指令類型常量
CMD_BASIC = "basic"           # 基本操作指令
CMD_VERIFY = "verify"         # 驗證指令
CMD_WAIT = "wait"             # 等待指令
CMD_NAV = "navigation"        # 導航指令
CMD_TEST = "test"             # 測試案例相關指令

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
    "SEVERITY": CMD_TEST
}

# 設定日誌
def setup_logging():
    """設定日誌系統"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )

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
    """從 command.txt 讀取關鍵字"""
    keywords = []
    try:
        if os.path.exists(COMMAND_FILE):
            with open(COMMAND_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # 跳過空行、註解行和指令行
                    if (not line or line.startswith("#") or 
                        "=" in line or "||" in line or
                        line in ["NAV_SEQUENCE_START", "NAV_SEQUENCE_END"]):
                        continue
                    keywords.append(line)
            
            logging.info(f"已載入 {len(keywords)} 個關鍵字")
        else:
            logging.info(f"找不到 {COMMAND_FILE} 檔案")
    except Exception as e:
        logging.error(f"讀取關鍵字時發生錯誤: {str(e)}")
    
    return keywords

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