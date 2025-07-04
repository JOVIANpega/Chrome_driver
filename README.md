# Playwright E2E助手 V2.0

一個簡單易用的瀏覽器自動化GUI工具，使用Python和Playwright開發，支持原生Playwright Python語法。

## 專案說明

此專案是一個重構版本，從原本的自創腳本語法改為支援Playwright的原生Python語法，讓使用者可以直接編寫標準Playwright代碼並執行。

## 主要功能

- **原生Playwright語法支持**：直接編寫和執行標準Playwright Python代碼
- **腳本錄製功能**：透過瀏覽器操作自動生成Playwright代碼
- **雙面板界面**：左側編輯腳本，右側查看執行日誌
- **無頭模式選項**：可選擇是否在後台執行瀏覽器
- **字體大小調整**：支援從8至24的字體範圍調整
- **腳本管理**：可保存和載入自動化腳本
- **錯誤處理**：詳細的執行錯誤報告
- **打包部署**：可打包為單一EXE檔案，方便分享使用

## 安裝方式

### 方法一：使用EXE檔案（推薦）

1. 下載最新的發布版本EXE檔案
2. 直接運行EXE檔案即可使用

### 方法二：從源碼運行

1. 確保已安裝Python 3.8+
2. 克隆此儲存庫：
   ```
   git clone https://github.com/JOVIANpega/Playwright_E2E.git
   cd Playwright_E2E
   ```
3. 安裝依賴套件：
   ```
   pip install -r requirements.txt
   ```
4. 安裝Playwright瀏覽器：
   ```
   python -m playwright install
   ```
5. 運行程式：
   ```
   python main.py
   ```

## 使用方法

### 方法一：錄製腳本

1. 在「腳本錄製」區域填寫起始URL，或使用「錄製測試頁面」按鈕
2. 點擊「開始錄製」按鈕，將打開瀏覽器
3. 在瀏覽器中進行操作（點擊、輸入等），這些操作將被記錄
4. 操作完成後關閉瀏覽器或點擊「停止錄製」按鈕
5. 錄製的操作會以Playwright原生Python語法顯示在左側編輯區
6. 可以直接編輯腳本，然後點擊「執行腳本」按鈕運行

### 方法二：手動編寫腳本

1. 在左側面板中編寫Playwright腳本（使用原生語法）
2. 選擇是否啟用無頭模式
3. 點擊「執行腳本」按鈕運行自動化測試
4. 在右側面板查看執行日誌和錯誤信息
5. 使用「A+/A-」按鈕調整界面字體大小

## 腳本語法

此版本使用標準Playwright Python語法，不需要添加import語句或with sync_playwright()包裝。例如：

```python
browser = playwright.chromium.launch(headless=False)
page = browser.new_page()
page.goto("https://example.com")
page.fill("input[name='username']", "testuser")
page.click("text=Login")
assert "Welcome" in page.content()
browser.close()
```

## 錄製功能支持的操作

目前錄製功能支持以下操作：

1. 頁面導航 (`page.goto()`)
2. 點擊元素 (`page.click()`)
3. 填寫表單 (`page.fill()`)

錄製過程會使用元素的ID、類名、文本內容等生成選擇器，以便Playwright能準確定位元素。

## 常見問題解答

### 是否需要包含import語句？
不需要，程式會自動處理必要的導入。只需撰寫Playwright代碼本身。

### 如何調試腳本錯誤？
錯誤信息會顯示在右側日誌面板中，包含行號和詳細的異常信息。

### 腳本執行時瀏覽器沒有顯示？
請檢查"無頭模式"是否被勾選，將其取消勾選即可看到瀏覽器界面。

### 錄製功能沒有捕獲我的所有操作？
錄製功能目前主要支援點擊和輸入操作。對於更複雜的操作（如拖拽、懸停等），建議手動編輯腳本添加。

## 系統需求

- Windows 10 或以上版本
- Python 3.8+（從源碼運行時需要）
- 與系統相容的Chrome、Firefox或Edge瀏覽器

## 版本歷史

### V2.02 (2025-07-17)
- 修復錄製功能中瀏覽器快速關閉的問題
- 改進瀏覽器窗口存活檢測機制，使用 page.title() 方法
- 新增錄製時間戳記錄，更好地追蹤錄製過程
- 優化錄製腳本的保存方式，自動生成帶時間戳的文件名
- 改進錄製過程中的用戶提示訊息

### V2.0 (2025-07-15)
- 重構為使用原生Playwright Python語法
- 新增腳本錄製功能，自動生成Playwright代碼
- 雙面板界面設計
- 支持無頭模式選項
- 詳細的執行錯誤報告

### V1.0 (2024-12-01)
- 首次發布版本
- 使用自創腳本語法

## 開發說明

本工具使用以下技術:
- **Python**: 核心開發語言
- **Tkinter**: GUI框架
- **Playwright**: 瀏覽器自動化引擎
- **PyInstaller**: 打包成EXE

## 授權協議

本軟體為自由軟體，使用MIT授權協議。詳情請參閱LICENSE文件。 