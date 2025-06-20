# -*- coding: utf-8 -*-
import os
import logging
from typing import List, Tuple

# 常量定義
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
STEP_WINDOW_WIDTH = 250
STEP_WINDOW_HEIGHT = 500
DEFAULT_WAIT_TIME = 5
LOG_FILE = "log.txt"
COMMAND_FILE = "command.txt"
DEFAULT_FONT_SIZE = 10

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
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    
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
                        "=" in line or "||" in line):
                        continue
                    keywords.append(line)
            
            logging.info(f"已載入 {len(keywords)} 個關鍵字")
        else:
            logging.info(f"找不到 {COMMAND_FILE} 檔案")
    except Exception as e:
        logging.error(f"讀取關鍵字時發生錯誤: {str(e)}")
    
    return keywords 