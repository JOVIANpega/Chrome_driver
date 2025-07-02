# Chrome E2E助手 V2.0

一個簡單易用的瀏覽器自動化GUI工具，使用Python和Playwright開發。

## 版本資訊

**當前版本：V2.0 (2025-07-02)**

### 新增功能
- 改進的使用者介面，增加明顯的底部按鈕
- 新增字體大小調整功能，適應不同螢幕尺寸
- 優化腳本載入和執行流程，提高穩定性
- 改進錄製和執行過程中的錯誤處理
- 錄製完成後自動驗證腳本功能
- 新增詢問是否立即執行錄製腳本的選項

## 功能特點

- 基於Playwright的瀏覽器自動化
- 簡潔直觀的GUI界面
- 支援多種驗證點：文字、網址、截圖、OCR
- 支援條件判斷和分支執行
- 支援多分頁操作
- 可保存和載入自動化腳本

## 安裝指南

1. 確保已安裝Python 3.8+
2. 安裝依賴套件：
   ```
   pip install -r requirements.txt
   ```
3. 安裝Playwright瀏覽器：
   ```
   python -m playwright install
   ```
4. 運行應用：
   ```
   python main.py
   ```

## 腳本語法

腳本採用簡單的指令格式：`命令 = 參數`

### 基本操作
- `OPEN_URL = https://example.com` - 打開網址
- `FILL = input[name="username"] || myusername` - 填寫表單
- `CLICK_BY = button#submit` - 點擊元素

### 驗證點
- `ASSERT_TEXT = 歡迎登入` - 驗證頁面包含指定文字
- `ASSERT_URL = dashboard` - 驗證URL包含指定文字
- `SCREENSHOT_ASSERT = 100,100,300,300` - 截圖驗證
- `OCR_ASSERT = 100,100,300,300||會員中心` - OCR文字驗證

### 條件控制
- `IF_TEXT_EXISTS = 登入成功` - 如果文字存在
- `IF_URL_CONTAINS = dashboard` - 如果URL包含
- `IF_OCR_CONTAINS = 100,100,300,300||成功` - 如果OCR區域包含
- `ELSE` - 否則
- `ENDIF` - 結束條件塊

### 等待控制
- `WAIT = 5` - 等待秒數
- `WAIT_FOR_TEXT = 加載完成` - 等待文字出現
- `WAIT_FOR_URL = success` - 等待URL包含

### 分頁操作
- `SWITCH_TAB = 1` - 切換到指定分頁
- `CLOSE_TAB` - 關閉當前分頁

## 版本更新歷史

### V2.0 (2025-07-02)
- 修復腳本載入按鈕無法正常工作的問題
- 修復錄製和執行腳本時的錯誤處理
- 解決 `AttributeError: 'BrowserAutomation' object has no attribute 'is_paused'` 錯誤
- 增強錯誤處理，確保瀏覽器關閉時能優雅退出
- 新增字體大小調整功能，支援從8至24的字體範圍調整
- 優化UI佈局，增加底部功能按鈕，提升視覺效果
- 新增錄製完成後詢問是否立即執行腳本的功能

### V1.0 (2025-07-01)
- 初始版本發布
- 基本的瀏覽器自動化功能
- 腳本錄製與執行功能
- 基本的GUI界面

## 常見問題

### "ValueError: source code string cannot contain null bytes"

如果遇到此錯誤，可能是文件中包含無效字元。解決方法：

1. 使用純文本編輯器重新創建文件
2. 或者執行以下命令修復：
   ```
   copy app_clean.py app.py
   copy main_clean.py main.py
   ```

### 瀏覽器無法啟動

請確保已正確安裝Playwright瀏覽器：
```
python -m playwright install
```

### AttributeError: 'BrowserAutomation' object has no attribute 'is_paused'

如果遇到此錯誤，請確保使用最新版本的應用程式。在V2.0版本中，此問題已修復。

## 授權

本軟體採用MIT授權。 