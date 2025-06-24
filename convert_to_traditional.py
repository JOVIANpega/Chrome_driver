#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import opencc
import sys

def convert_file(file_path):
    """將檔案中的簡體中文轉換為繁體中文"""
    print(f"處理檔案: {file_path}")
    
    # 檢查檔案是否存在
    if not os.path.exists(file_path):
        print(f"錯誤: 檔案不存在 {file_path}")
        return False
    
    # 讀取檔案內容
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"讀取檔案時出錯 {file_path}: {str(e)}")
        return False
    
    # 初始化簡體到繁體轉換器
    converter = opencc.OpenCC('s2t')
    
    # 轉換內容
    converted_content = converter.convert(content)
    
    # 如果內容沒有變化，可能沒有簡體中文
    if content == converted_content:
        print(f"檔案 {file_path} 沒有需要轉換的簡體中文")
        return False
    
    # 寫入轉換後的內容
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(converted_content)
        print(f"成功轉換檔案 {file_path}")
        return True
    except Exception as e:
        print(f"寫入檔案時出錯 {file_path}: {str(e)}")
        return False

def process_python_files(directory='.'):
    """處理指定目錄下所有的 Python 檔案"""
    converted_files = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if convert_file(file_path):
                    converted_files.append(file_path)
    
    return converted_files

if __name__ == "__main__":
    directory = '.'
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    
    print(f"開始處理目錄: {directory}")
    converted_files = process_python_files(directory)
    
    print("\n轉換完成!")
    print(f"共轉換了 {len(converted_files)} 個檔案")
    if converted_files:
        print("已轉換的檔案:")
        for file in converted_files:
            print(f"- {file}") 