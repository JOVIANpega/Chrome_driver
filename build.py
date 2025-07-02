import os
import sys
import subprocess
import shutil
from datetime import datetime

# 獲取當前版本
def get_version():
    version = "2.0.0"  # 更新預設版本為2.0.0
    try:
        with open("app.py", "r", encoding="utf-8") as f:
            for line in f:
                if "APP_VERSION" in line:
                    version = line.split("=")[1].strip().strip('"\'')
                    break
    except:
        pass
    return version

# 獲取版本的主要部分（移除小版本號）
def get_major_version(version):
    parts = version.split(".")
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    return version

def main():
    # 獲取版本
    version = get_version()
    major_version = get_major_version(version)
    
    # 獲取當前日期
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # 創建構建目錄
    build_dir = "build"
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)
    
    # 創建dist目錄
    dist_dir = "dist"
    if not os.path.exists(dist_dir):
        os.makedirs(dist_dir)
    
    # 確保assets目錄存在
    assets_dir = "assets"
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
    
    # 確保圖標存在
    icon_path = os.path.join(assets_dir, "icon.ico")
    if not os.path.exists(icon_path):
        print(f"警告: 圖標文件 {icon_path} 不存在，將使用默認圖標")
        icon_path = ""
    
    # 設置版本文件
    version_info = f"""
# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    # Set not needed items to zero 0.
    filevers=({version.replace(".", ", ")}, 0),
    prodvers=({version.replace(".", ", ")}, 0),
    # Contains a bitmask that specifies the valid bits 'flags'r
    mask=0x3f,
    # Contains a bitmask that specifies the Boolean attributes of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x4 - NT and there is no need to change it.
    OS=0x40004,
    # The general type of file.
    # 0x1 - the file is an application.
    fileType=0x1,
    # The function of the file.
    # 0x0 - the function is not defined for this fileType
    subtype=0x0,
    # Creation date and time stamp.
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Chrome E2E助手開發團隊'),
        StringStruct(u'FileDescription', u'Chrome E2E助手 V{major_version} - 瀏覽器自動化測試工具'),
        StringStruct(u'FileVersion', u'{version}'),
        StringStruct(u'InternalName', u'Chrome_E2E_Assistant'),
        StringStruct(u'LegalCopyright', u'Copyright (c) 2025'),
        StringStruct(u'OriginalFilename', u'Chrome_E2E_Assistant.exe'),
        StringStruct(u'ProductName', u'Chrome E2E助手 V{major_version}'),
        StringStruct(u'ProductVersion', u'{version}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
    """
    
    version_file = "file_version_info.txt"
    with open(version_file, "w", encoding="utf-8") as f:
        f.write(version_info)
    
    # 輸出文件名
    output_name = f"Chrome_E2E_Assistant_V{major_version}"
    
    # 打包命令
    cmd = [
        "pyinstaller",
        "--onefile",
        "--noconsole",
        f"--version-file={version_file}",
        f"--name={output_name}",
        "--clean",
        "--log-level=INFO",
    ]
    
    if icon_path:
        cmd.append(f"--icon={icon_path}")
    
    # 添加資源文件
    cmd.extend([
        "--add-data", f"{assets_dir};{assets_dir}",
        "--add-data", f"web;web",
        "--add-data", f"version_info.txt;."
    ])
    
    cmd.append("main.py")
    
    # 執行打包
    print(f"正在打包 Chrome E2E助手 V{major_version} ({version})...")
    print(f"打包日期: {current_date}")
    subprocess.call(cmd)
    
    # 清理臨時文件
    if os.path.exists(version_file):
        os.remove(version_file)
    
    # 完成
    output_path = os.path.join(dist_dir, f"{output_name}.exe")
    
    if os.path.exists(output_path):
        print(f"打包成功! 檔案位於 {output_path}")
        print(f"檔案大小: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB")
    else:
        print("打包似乎失敗，請檢查錯誤訊息")

if __name__ == "__main__":
    main() 