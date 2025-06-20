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
- 失敗步驟以紅色顯示
- 可調整字體大小

## 版本

目前版本: V0.3

### 更新日誌

**V0.3 (現行版本)**
- 模組化重構：將程式碼拆分為多個模組，提高可維護性
- 實際測試功能：實現了真實的測試功能，不再只是模擬
- 失敗步驟顯示：失敗的步驟會以紅色文字顯示
- 字體大小控制：可調整步驟視窗的字體大小
- 改進的錯誤處理：更詳細的錯誤日誌和異常處理
- 類型提示：添加了 Python 類型提示，提高代碼可讀性
- 常量定義：使用常量替代魔術數字

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
pyinstaller "Chrome自動化工具.spec"
```

## 目錄結構

- `chrome_automation_tool.py`: 主程式
- `selenium_handler.py`: Selenium 操作相關功能
- `step_window.py`: 步驟視窗相關功能
- `utils.py`: 工具函數和常量
- `command.txt`: 命令和關鍵字文件
- `web/`: 測試用 HTML 頁面
- `assets/`: 圖標等資源文件
- `dist/`: 打包後的可執行文件

## 作者

台灣的戰貓 