# Chrome 自動化工具 (Chrome Automation Tool)

![版本](https://img.shields.io/badge/版本-v0.7-blue)
![語言](https://img.shields.io/badge/語言-Python-green)
![框架](https://img.shields.io/badge/框架-Selenium-orange)

一個強大的Chrome瀏覽器自動化工具，使用Python和Selenium開發，提供圖形化界面進行網頁自動化測試。

## 主要功能

- 圖形化命令編輯器，直觀易用
- 支持多種自動化測試操作
- 模糊匹配與容錯功能
- 詳細的執行日誌與測試報告
- 步驟窗口實時顯示測試進度
- 支持多種自動化命令模板
- 命令參數智能提示與説明

## 截圖

![主界面](https://via.placeholder.com/800x500?text=主界面截圖)
![命令編輯器](https://via.placeholder.com/800x500?text=命令編輯器截圖)

## 功能列表

- 自動操作本地 HTML 頁面
- 登入表單填寫和測試
- 資料管理（項目新增和刪除）
- 搜尋功能測試
- 互動按鈕測試
- HTML 關鍵字搜尋功能
- 動態步驟顯示
- 詳細的執行日誌
- 多層次導航測試
- 產品詳細資訊頁面測試
- 訂單處理流程測試
- 無限滾動測試
- 可展開區域測試
- 模糊匹配與容錯功能
- 命令參數智能提示

## 安裝說明

1. 克隆此儲存庫:
```
git clone https://github.com/your-username/chrome-automation-tool.git
cd chrome-automation-tool
```

2. 安裝所需依賴:
```
pip install -r requirements.txt
```

3. 確保與Chrome版本相匹配的chromedriver.exe放置在項目根目錄下

## 使用方法

1. 運行主程序:
```
python chrome_automation_tool.py
```

2. 使用圖形化命令編輯器創建測試命令:
   - 點擊"命令編輯器"按鈕
   - 選擇命令類型和具體命令
   - 查看命令説明和參數示例
   - 輸入參數後添加命令
   - 保存命令序列

3. 點擊"開始自動化測試"執行測試

## 支持的命令類型

### 基礎操作指令
- `OPEN_URL = [URL]` - 開啟指定網頁
- `CLICK_BY_TEXT = [文字]` - 點擊包含指定文字的元素
- `CLICK_BY_ID = [ID]` - 點擊指定ID的元素
- `TYPE = [文字]` - 在當前焦點元素中輸入文字

### 驗證指令
- `VERIFY_TEXT_EXISTS = [文字]` - 驗證頁面包含特定文字
- `VERIFY_ELEMENT_EXISTS = [選擇器]` - 驗證元素存在
- `VERIFY_ELEMENT_VALUE = [選擇器]||[預期值]` - 驗證元素值符合預期

### 模糊匹配指令
- `VERIFY_TEXT_CONTAINS = [文字]` - 驗證頁面包含部分指定文字
- `VERIFY_TEXT_PATTERN = [正則表達式]` - 使用正則表達式驗證文字
- `VERIFY_TEXT_SIMILAR = [文字]||[相似度閾值]` - 驗證文字相似度超過閾值

## 版本歷史

**v0.7 (當前版本)**
- 簡化命令編輯器左區塊界面，提升易用性
- 添加命令參數智能提示功能
- 加入命令説明和參數示例
- 優化命令類型選擇界面，增加中文描述
- 改進視覺設計和間距
- 修復已知問題

**v0.6**
- 添加圖形化命令編輯器
- 支持命令模板功能
- 新增模式匹配與容錯功能
- 支持多條件邏輯
- 優化界面與使用體驗

**v0.5**
- 擴充指令集
- 支持多層次導航測試
- 新增多種驗證指令
- 添加字體大小調整功能

## 系統需求

- Python 3.6+
- Selenium 4.0+
- Chrome 瀏覽器
- 作業系統: Windows, macOS, Linux

## 授權

MIT

## 作者

台灣的戰貓 