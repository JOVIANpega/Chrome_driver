# Chrome 自動化工具

一個強大的 Chrome 自動化工具，使用 Python 和 Selenium 來自動化瀏覽器操作和測試。

## 功能特點

- 自動操作本地 HTML 頁面
- 登入表單填寫和測試
- 資料管理（項目新增和刪除）
- 搜尋功能測試
- 互動按鈕測試
- HTML 關鍵字搜尋功能
- 動態步驟顯示
- 詳細的執行日誌

## 版本

目前版本: V0.3

### 更新日誌

**V0.3 (現行版本)**
- 添加類型提示，提高代碼可讀性和可維護性
- 改進異常處理，更穩定的執行
- 定義常量，避免魔術數字
- 優化代碼結構
- 修復關鍵字搜尋功能

**V0.2**
- 動態步驟清單：步驟列表在執行時動態生成
- 自動從 command.txt 讀取關鍵字
- 靈活的步驟管理
- 改進的關鍵字搜尋
- 修復滾動條問題

**V0.1**
- 基本的 Chrome 自動化功能
- 支持登入、新增項目、搜尋、互動按鈕測試等功能
- 步驟視窗顯示當前執行步驟
- 日誌記錄功能

## 使用方法

1. 確保 chromedriver.exe 與程式在同一目錄
2. 執行 `python chrome_automation_tool.py` 或直接運行打包好的 `Chrome自動化工具.exe`
3. 在 command.txt 中可以添加關鍵字（每行一個，不含 # 和 = 符號的行）

## 系統需求

- Python 3.6+
- Selenium
- Chrome 瀏覽器
- chromedriver.exe (與您的 Chrome 版本相符)

## 打包說明

使用 PyInstaller 打包：
```
pyinstaller --onefile --noconsole --icon=icon.ico --add-data "web;web" --name "Chrome自動化工具" chrome_automation_tool.py
```

## 目錄結構

- `chrome_automation_tool.py`: 主程式
- `command.txt`: 命令和關鍵字文件
- `web/`: 測試用 HTML 頁面
- `assets/`: 圖標等資源文件
- `dist/`: 打包後的可執行文件

## 作者

台灣的戰貓 