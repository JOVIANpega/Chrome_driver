import os
import sys
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    try:
        # 初始化 WebDriver
        chromedriver_path = os.path.join(os.getcwd(), "chromedriver.exe")
        if not os.path.exists(chromedriver_path):
            logging.error("找不到 chromedriver.exe")
            return False
        
        # 初始化 WebDriver
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(executable_path=chromedriver_path)
        driver = webdriver.Chrome(service=service, options=options)
        
        logging.info("Chrome WebDriver 初始化成功")
        
        # 打開測試頁面
        html_path = os.path.join(os.getcwd(), "web", "360_TEST_WEBFILE.html")
        if not os.path.exists(html_path):
            logging.error(f"找不到 HTML 檔案: {html_path}")
            return False
        
        file_url = f"file:///{html_path.replace(os.sep, '/').lstrip('/')}"
        logging.info(f"嘗試打開頁面: {file_url}")
        driver.get(file_url)
        
        # 等待頁面載入
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)  # 確保頁面完全載入
        logging.info("頁面已成功載入")
        
        # 測試登入功能
        try:
            # 等待登入表單載入
            wait.until(EC.presence_of_element_located((By.ID, "loginForm")))
            logging.info("登入表單已載入")
            
            # 點擊使用者名稱輸入框
            username = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#loginForm #username")))
            username.click()
            username.clear()
            username.send_keys("admin")
            logging.info("已輸入使用者名稱: admin")
            
            # 點擊密碼輸入框
            password = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#loginForm #password")))
            password.click()
            password.clear()
            password.send_keys("Pega#1234")
            logging.info("已輸入密碼: Pega#1234")
            
            # 點擊登入按鈕
            login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#loginForm .login-button")))
            login_button.click()
            logging.info("已點擊登入按鈕")
            
            # 等待登入結果
            time.sleep(2)
            
            # 檢查登入成功訊息
            try:
                login_success = wait.until(EC.visibility_of_element_located((By.ID, "loginSuccess")))
                if login_success.is_displayed():
                    logging.info("登入成功訊息已顯示")
                    
                    # 等待登入遮罩消失
                    time.sleep(1)
                    try:
                        wait.until(EC.invisibility_of_element_located((By.ID, "login-overlay")))
                        logging.info("登入遮罩已消失，登入完成")
                    except:
                        logging.warning("登入遮罩未消失")
                else:
                    logging.warning("登入成功訊息未顯示")
            except:
                logging.error("找不到登入成功訊息")
                
                # 檢查是否有錯誤訊息
                try:
                    login_error = driver.find_element(By.ID, "loginError")
                    if login_error.is_displayed():
                        logging.error(f"登入失敗: {login_error.text}")
                except:
                    logging.error("找不到登入錯誤訊息")
            
        except Exception as e:
            logging.error(f"登入測試時發生錯誤: {str(e)}")
        
        # 關閉瀏覽器
        time.sleep(3)  # 等待一段時間以便觀察結果
        driver.quit()
        logging.info("測試完成")
        
    except Exception as e:
        logging.error(f"測試過程中發生錯誤: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    main() 