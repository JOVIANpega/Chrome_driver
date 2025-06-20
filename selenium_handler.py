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
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

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