from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import time
import os

# 設定 Chrome Driver 路徑
chromedriver_path = os.path.join(os.getcwd(), "chromedriver.exe")
service = Service(chromedriver_path)

# 啟動 Chrome
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=options)

# 開啟本機 HTML 測試頁
html_path = os.path.abspath("web/index.html")
driver.get("file:///" + html_path)

# 輸入帳號密碼
driver.find_element(By.NAME, "username").send_keys("admin")
driver.find_element(By.NAME, "password").send_keys("123456")

# 點擊登入
driver.find_element(By.XPATH, "//button[contains(text(), '登入')]").click()
time.sleep(1)

# 點擊「新增項目」
driver.find_element(By.XPATH, "//button[contains(text(), '新增項目')]").click()
time.sleep(1)

# 找到名稱為「測試1」的那一列，並刪除
row = driver.find_element(By.XPATH, "//tr[td[contains(text(), '測試1')]]")
delete_button = row.find_element(By.XPATH, ".//button[contains(text(), '刪除')]")
delete_button.click()

time.sleep(2)
input("✅ 自動化完成，請按 Enter 關閉...")
driver.quit()
