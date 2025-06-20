# -*- coding: utf-8 -*-
import os
import time
import logging
from typing import Optional, List, Tuple, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, ElementNotInteractableException

import utils

class SeleniumHandler:
    def __init__(self) -> None:
        self.driver: Optional[webdriver.Chrome] = None
        self.chromedriver_path: Optional[str] = None
    
    def find_chromedriver(self) -> bool:
        """尋找 chromedriver.exe"""
        # 檢查當前目錄
        chromedriver_path = os.path.join(os.getcwd(), "chromedriver.exe")
        if os.path.exists(chromedriver_path):
            self.chromedriver_path = chromedriver_path
            logging.info(f"已找到 ChromeDriver: {chromedriver_path}")
            return True
        
        # 如果找不到，記錄錯誤
        logging.error("錯誤: 未找到 chromedriver.exe，請確保它與程式在同一目錄")
        return False
    
    def initialize_driver(self) -> bool:
        """初始化 WebDriver"""
        if not self.chromedriver_path or not os.path.exists(self.chromedriver_path):
            logging.error("錯誤: 未找到 chromedriver.exe")
            return False
        
        try:
            # 初始化 WebDriver
            options = webdriver.ChromeOptions()
            options.add_argument("--start-maximized")
            options.add_argument("--disable-notifications")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            
            service = Service(executable_path=self.chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
            logging.info("Chrome WebDriver 初始化成功")
            return True
        except WebDriverException as e:
            logging.error(f"初始化 Chrome WebDriver 失敗: {str(e)}")
            return False
    
    def open_html_page(self, url_path: str) -> bool:
        """打開本地 HTML 頁面"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        try:
            # 確保 URL 路徑存在
            html_path = os.path.abspath(url_path)
            if not os.path.exists(html_path):
                logging.error(f"錯誤: 找不到 HTML 檔案: {html_path}")
                return False
            
            # 打開 HTML 頁面
            file_url = f"file:///{html_path.replace(os.sep, '/')}"
            self.driver.get(file_url)
            logging.info(f"已打開頁面: {file_url}")
            
            # 等待頁面載入
            try:
                wait = WebDriverWait(self.driver, utils.DEFAULT_WAIT_TIME)
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                time.sleep(1)  # 額外等待確保頁面完全載入
                return True
            except TimeoutException:
                logging.warning("警告: 頁面載入超時")
                return False
        except Exception as e:
            logging.error(f"打開頁面時發生錯誤: {str(e)}")
            return False
    
    def test_login_form(self) -> bool:
        """測試登入表單"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        try:
            wait = WebDriverWait(self.driver, utils.DEFAULT_WAIT_TIME)
            
            # 尋找使用者名稱輸入框
            username_input = wait.until(EC.element_to_be_clickable((By.ID, "username")))
            username_input.click()
            username_input.clear()
            username_input.send_keys("測試使用者")
            logging.info("輸入使用者名稱: 測試使用者")
            time.sleep(0.5)
            
            # 尋找密碼輸入框
            password_input = wait.until(EC.element_to_be_clickable((By.ID, "password")))
            password_input.click()
            password_input.clear()
            password_input.send_keys("密碼123")
            logging.info("輸入密碼: 密碼123")
            time.sleep(0.5)
            
            # 點擊登入按鈕
            login_button = wait.until(EC.element_to_be_clickable((By.ID, "login-button")))
            login_button.click()
            logging.info("點擊登入按鈕")
            time.sleep(1)
            
            # 檢查登入結果
            login_result = wait.until(EC.presence_of_element_located((By.ID, "login-result")))
            if "成功" in login_result.text:
                logging.info("登入成功")
                return True
            else:
                logging.warning(f"登入失敗: {login_result.text}")
                return False
        except (NoSuchElementException, TimeoutException) as e:
            logging.error(f"登入表單測試失敗: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"登入表單測試時發生未知錯誤: {str(e)}")
            return False
    
    def test_data_management(self) -> bool:
        """測試資料管理功能"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        try:
            wait = WebDriverWait(self.driver, utils.DEFAULT_WAIT_TIME)
            
            # 輸入項目名稱
            item_name_input = wait.until(EC.element_to_be_clickable((By.ID, "item-name")))
            item_name_input.click()
            item_name_input.clear()
            item_name_input.send_keys("筆記型電腦")
            logging.info("輸入項目名稱: 筆記型電腦")
            time.sleep(0.5)
            
            # 選擇類別
            item_category = wait.until(EC.element_to_be_clickable((By.ID, "item-category")))
            item_category.click()
            time.sleep(0.5)
            
            # 輸入價格
            price_input = wait.until(EC.element_to_be_clickable((By.ID, "item-price")))
            price_input.click()
            price_input.clear()
            price_input.send_keys("25000")
            logging.info("輸入價格: 25000")
            time.sleep(0.5)
            
            # 點擊新增項目按鈕
            add_button = wait.until(EC.element_to_be_clickable((By.ID, "add-item")))
            add_button.click()
            logging.info("點擊新增項目按鈕")
            time.sleep(1)
            
            # 檢查項目是否已新增
            try:
                table = wait.until(EC.presence_of_element_located((By.ID, "items-table")))
                rows = table.find_elements(By.TAG_NAME, "tr")
                for row in rows:
                    if "筆記型電腦" in row.text and "25000" in row.text:
                        logging.info("成功新增項目")
                        return True
                
                logging.warning("未找到新增的項目")
                return False
            except (NoSuchElementException, TimeoutException):
                logging.warning("未找到項目表格或新增的項目")
                return False
        except (NoSuchElementException, TimeoutException) as e:
            logging.error(f"資料管理測試失敗: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"資料管理測試時發生未知錯誤: {str(e)}")
            return False
    
    def test_search_function(self) -> bool:
        """測試搜尋功能"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        try:
            wait = WebDriverWait(self.driver, utils.DEFAULT_WAIT_TIME)
            
            # 輸入搜尋關鍵字
            search_input = wait.until(EC.element_to_be_clickable((By.ID, "search-text")))
            search_input.click()
            search_input.clear()
            search_input.send_keys("筆記型電腦")
            logging.info("輸入搜尋關鍵字: 筆記型電腦")
            time.sleep(0.5)
            
            # 點擊搜尋按鈕
            search_button = wait.until(EC.element_to_be_clickable((By.ID, "search-button")))
            search_button.click()
            logging.info("點擊搜尋按鈕")
            time.sleep(1)
            
            # 檢查搜尋結果
            search_result = wait.until(EC.presence_of_element_located((By.ID, "search-result")))
            if search_result.text and "找到" in search_result.text:
                logging.info(f"搜尋成功: {search_result.text}")
                return True
            else:
                logging.warning(f"搜尋結果不符預期: {search_result.text}")
                return False
        except (NoSuchElementException, TimeoutException) as e:
            logging.error(f"搜尋功能測試失敗: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"搜尋功能測試時發生未知錯誤: {str(e)}")
            return False
    
    def test_interactive_buttons(self) -> bool:
        """測試互動按鈕"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        try:
            wait = WebDriverWait(self.driver, utils.DEFAULT_WAIT_TIME)
            success_count = 0
            
            # 測試顯示訊息按鈕
            try:
                show_message_button = wait.until(EC.element_to_be_clickable((By.ID, "show-message")))
                show_message_button.click()
                logging.info("點擊顯示訊息按鈕")
                time.sleep(1)
                
                message_area = wait.until(EC.presence_of_element_located((By.ID, "message-area")))
                if message_area.text:
                    logging.info(f"顯示訊息成功: {message_area.text}")
                    success_count += 1
            except (NoSuchElementException, TimeoutException, ElementNotInteractableException) as e:
                logging.warning(f"顯示訊息按鈕測試失敗: {str(e)}")
            
            # 測試改變顏色按鈕
            try:
                change_color_button = wait.until(EC.element_to_be_clickable((By.ID, "change-color")))
                change_color_button.click()
                logging.info("點擊改變顏色按鈕")
                time.sleep(1)
                success_count += 1
            except (NoSuchElementException, TimeoutException, ElementNotInteractableException) as e:
                logging.warning(f"改變顏色按鈕測試失敗: {str(e)}")
            
            # 測試計數按鈕
            try:
                count_button = wait.until(EC.element_to_be_clickable((By.ID, "count-button")))
                original_text = count_button.text
                count_button.click()
                logging.info("點擊計數按鈕")
                time.sleep(1)
                
                count_button = wait.until(EC.presence_of_element_located((By.ID, "count-button")))
                if count_button.text != original_text:
                    logging.info(f"計數按鈕測試成功: {original_text} -> {count_button.text}")
                    success_count += 1
            except (NoSuchElementException, TimeoutException, ElementNotInteractableException) as e:
                logging.warning(f"計數按鈕測試失敗: {str(e)}")
            
            # 如果至少有兩個按鈕測試成功，則視為整體測試成功
            return success_count >= 2
        except Exception as e:
            logging.error(f"互動按鈕測試時發生未知錯誤: {str(e)}")
            return False
    
    def search_keyword(self, keyword: str) -> bool:
        """搜尋關鍵字"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        try:
            # 尋找自訂文字區域
            custom_text_element = self.driver.find_element(By.ID, "customText")
            
            # 獲取文字內容
            text_content = custom_text_element.text
            
            # 檢查關鍵字是否存在
            if keyword in text_content:
                # 使用 JavaScript 高亮顯示關鍵字
                script = """
                var element = arguments[0];
                var keyword = arguments[1];
                var text = element.innerHTML;
                
                // 移除之前的高亮
                text = text.replace(/<span class="highlight">(.*?)<\/span>/g, '$1');
                
                // 高亮新的關鍵字
                var regex = new RegExp(keyword, 'g');
                var newText = text.replace(regex, '<span class="highlight">$&</span>');
                
                element.innerHTML = newText;
                
                // 滾動到第一個高亮處
                var highlightElement = element.querySelector('.highlight');
                if (highlightElement) {
                    highlightElement.scrollIntoView({behavior: "smooth", block: "center"});
                    return true;
                }
                return false;
                """
                result = self.driver.execute_script(script, custom_text_element, keyword)
                
                if result:
                    logging.info(f"找到關鍵字: {keyword}")
                    return True
                else:
                    logging.info(f"找到關鍵字但無法高亮顯示: {keyword}")
                    return True
            else:
                logging.info(f"未找到關鍵字: {keyword}")
                return False
                
        except NoSuchElementException:
            logging.error(f"錯誤: 找不到自訂文字區域，無法搜尋關鍵字: {keyword}")
            return False
        except WebDriverException as e:
            logging.error(f"搜尋關鍵字時發生錯誤: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"搜尋關鍵字時發生未知錯誤: {str(e)}")
            return False
    
    def close_driver(self) -> None:
        """關閉 WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                logging.info("已關閉 Chrome WebDriver")
            except Exception as e:
                logging.error(f"關閉 WebDriver 時發生錯誤: {str(e)}")
            finally:
                self.driver = None 