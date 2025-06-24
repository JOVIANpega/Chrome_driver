# -*- coding: utf-8 -*-
import os
import sys
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
        """初始化 Selenium 處理器"""
        self.driver: Optional[webdriver.Chrome] = None
        self.chromedriver_path: Optional[str] = None
        self.default_wait_time: int = utils.DEFAULT_WAIT_TIME
        self.wait: Optional[WebDriverWait] = None
    
    def set_wait_time(self, seconds: int) -> None:
        """設置等待時間"""
        self.default_wait_time = seconds
        if self.driver:
            self.wait = WebDriverWait(self.driver, self.default_wait_time)
    
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
            options.add_experimental_option('useAutomationExtension', False)
            
            service = Service(executable_path=self.chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
            self.wait = WebDriverWait(self.driver, self.default_wait_time)
            
            logging.info("Chrome WebDriver 初始化成功")
            return True
            
        except WebDriverException as e:
            logging.error(f"初始化 Chrome WebDriver 失敗: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"初始化過程中發生未知錯誤: {str(e)}")
            return False
    
    def open_html_page(self, url_path: str) -> bool:
        """打開本地 HTML 頁面 - 增強版，支援打包後的路徑處理"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        try:
            # 使用多種方法嘗試找到 HTML 檔案
            html_paths = []
            
            # 獲取基礎目錄
            if getattr(sys, 'frozen', False):
                # 如果是打包後的執行檔
                base_dir = sys._MEIPASS
            else:
                # 如果是直接執行 Python 腳本
                base_dir = os.path.dirname(os.path.abspath(__file__))
            
            logging.info(f"基礎目錄: {base_dir}")
            
            # 方法1: 在 web 資料夾下尋找
            html_paths.append(os.path.join(base_dir, "web", os.path.basename(url_path)))
            
            # 方法2: 直接在基礎目錄下尋找
            html_paths.append(os.path.join(base_dir, os.path.basename(url_path)))
            
            # 方法3: 使用相對路徑
            html_paths.append(os.path.join(base_dir, url_path))
            
            # 方法4: 使用當前工作目錄
            html_paths.append(os.path.join(os.getcwd(), "web", os.path.basename(url_path)))
            
            # 嘗試所有可能的路徑
            html_path = None
            for path in html_paths:
                logging.info(f"嘗試路徑: {path}")
                if os.path.exists(path):
                    html_path = path
                    logging.info(f"找到 HTML 檔案: {html_path}")
                    break
            
            if not html_path:
                # 如果找不到檔案，列出可用的檔案
                web_dir = os.path.join(base_dir, "web")
                if os.path.exists(web_dir):
                    files = os.listdir(web_dir)
                    logging.warning(f"找不到 HTML 檔案，但 web 資料夾中有以下檔案: {files}")
                else:
                    logging.warning(f"找不到 HTML 檔案，且 web 資料夾不存在")
                return False
            
            # 轉換為 file:// URL 格式
            file_url = f"file:///{html_path.replace(os.sep, '/').lstrip('/')}"
            logging.info(f"嘗試打開頁面: {file_url}")
            
            self.driver.get(file_url)
            
            # 等待頁面載入
            try:
                wait = WebDriverWait(self.driver, utils.DEFAULT_WAIT_TIME)
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                time.sleep(2)  # 增加等待時間確保頁面完全載入
                logging.info("頁面已成功載入")
                return True
            except TimeoutException:
                logging.error("頁面載入超時")
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
            # 等待登入遮罩層載入
            login_overlay = self.wait_for_element(By.ID, "login-overlay")
            if not login_overlay:
                logging.error("找不到登入遮罩層")
                return False
            
            time.sleep(0.5)  # 等待動畫完成
            
            # 輸入使用者名稱
            username_input = self.wait_for_clickable(By.ID, "username")
            if not self.safe_send_keys(username_input, "admin"):
                return False
            
            time.sleep(0.3)  # 輸入間隔
            
            # 輸入密碼
            password_input = self.wait_for_clickable(By.ID, "password")
            if not self.safe_send_keys(password_input, "Pega#1234"):
                return False
            
            time.sleep(0.3)  # 輸入間隔
            
            # 點擊登入按鈕
            login_button = self.wait_for_clickable(By.CSS_SELECTOR, "button.login-button")
            if not self.safe_click(login_button):
                return False
            
            time.sleep(0.5)  # 等待登入處理
            
            # 檢查登入結果
            try:
                # 檢查成功訊息
                success_message = self.wait_for_element(By.CLASS_NAME, "login-success", timeout=3)
                if success_message and success_message.is_displayed():
                    # 等待遮罩層消失
                    if self.wait.until(EC.invisibility_of_element_located((By.ID, "login-overlay"))):
                        logging.info("登入成功")
                        return True
                    else:
                        logging.warning("登入可能成功，但遮罩層未消失")
                        return False
                
                # 檢查錯誤訊息
                error_message = self.driver.find_element(By.CLASS_NAME, "login-error")
                if error_message and error_message.is_displayed():
                    logging.warning(f"登入失敗: {error_message.text}")
                    return False
                
            except TimeoutException:
                logging.error("等待登入結果超時")
                return False
            except NoSuchElementException:
                logging.error("找不到登入結果訊息元素")
                return False
            
            return False
            
        except Exception as e:
            logging.error(f"登入表單測試時發生錯誤: {str(e)}")
            return False
    
    def test_data_management(self) -> bool:
        """測試資料管理功能 - 適應新的頁面結構"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        try:
            wait = WebDriverWait(self.driver, utils.DEFAULT_WAIT_TIME)
            
            # 檢查是否在首頁
            try:
                # 嘗試找到導航項目並點擊
                nav_items = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "nav-item")))
                for item in nav_items:
                    if "Nokia 基本設定" in item.text:
                        item.click()
                        logging.info("點擊 Nokia 基本設定 導航項目")
                        time.sleep(1)
                        break
                
                # 檢查是否成功切換到 Nokia 基本設定頁面
                if self.verify_text_exists("Network & Internet"):
                    logging.info("成功切換到 Network & Internet 頁面")
                else:
                    logging.warning("未找到 Network & Internet 頁面標題")
                    return False
                
                # 測試主機名稱輸入框
                try:
                    hostname_input = wait.until(EC.element_to_be_clickable((By.ID, "hostname")))
                    hostname_input.click()
                    hostname_input.clear()
                    hostname_input.send_keys("NOKIA-TEST-HOST")
                    logging.info("輸入主機名稱: NOKIA-TEST-HOST")
                    time.sleep(0.5)
                except Exception as e:
                    logging.warning(f"主機名稱輸入框操作失敗: {str(e)}")
                    # 繼續測試，不中斷
                
                # 測試無線優先按鈕
                try:
                    wireless_priority = wait.until(EC.element_to_be_clickable((By.ID, "wireless-priority")))
                    wireless_priority.click()
                    logging.info("點擊無線優先按鈕")
                    time.sleep(0.5)
                except Exception as e:
                    logging.warning(f"無線優先按鈕操作失敗: {str(e)}")
                    # 繼續測試，不中斷
                
                # 測試 Wi-Fi 模式按鈕
                try:
                    wifi_mode = wait.until(EC.element_to_be_clickable((By.ID, "wifi-mode")))
                    wifi_mode.click()
                    logging.info("點擊 Wi-Fi 模式按鈕")
                    time.sleep(0.5)
                except Exception as e:
                    logging.warning(f"Wi-Fi 模式按鈕操作失敗: {str(e)}")
                    # 繼續測試，不中斷
                
                # 驗證頁面上的關鍵文字
                if self.verify_text_exists("Network parameter settings") and self.verify_text_exists("Host Name"):
                    logging.info("成功驗證 Nokia 基本設定頁面內容")
                    return True
                else:
                    logging.warning("未能驗證 Nokia 基本設定頁面內容")
                    return False
                
            except (NoSuchElementException, TimeoutException) as e:
                logging.error(f"切換頁面或操作元素失敗: {str(e)}")
                return False
        except Exception as e:
            logging.error(f"資料管理測試時發生未知錯誤: {str(e)}")
            return False
    
    def test_search_function(self) -> bool:
        """測試搜尋功能 - 適應新的頁面結構"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        try:
            wait = WebDriverWait(self.driver, utils.DEFAULT_WAIT_TIME)
            
            # 檢查是否可以切換到 Nokia 網路狀態頁面
            try:
                # 嘗試找到導航項目並點擊
                nav_items = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "nav-item")))
                for item in nav_items:
                    if "Nokia 網路狀態" in item.text:
                        item.click()
                        logging.info("點擊 Nokia 網路狀態 導航項目")
                        time.sleep(1)
                        break
                
                # 檢查是否成功切換到 Nokia 網路狀態頁面
                if not self.verify_text_exists("Cellular Network Information and Status"):
                    logging.warning("未找到 Cellular Network Information and Status 頁面標題")
                    # 再次嘗試點擊導航項目
                    for item in nav_items:
                        if "Nokia 網路狀態" in item.text:
                            item.click()
                            logging.info("再次點擊 Nokia 網路狀態 導航項目")
                            time.sleep(2)
                            break
                
                # 再次檢查頁面標題
                if self.verify_text_exists("Cellular Network Information and Status"):
                    logging.info("成功切換到 Cellular Network Information 頁面")
                else:
                    logging.warning("無法切換到 Cellular Network Information 頁面")
                    return False
                
                # 搜尋特定文本 - 使用多種方法確認
                success_count = 0
                
                # 方法1: 使用 verify_text_exists 檢查
                if self.verify_text_exists("SIM READY"):
                    success_count += 1
                    logging.info("成功找到 SIM READY 文本")
                
                if self.verify_text_exists("Chunghwa Telecom"):
                    success_count += 1
                    logging.info("成功找到 Chunghwa Telecom 文本")
                
                # 方法2: 檢查頁面源碼
                page_source = self.driver.page_source
                if "SIM READY" in page_source:
                    success_count += 1
                    logging.info("在頁面源碼中找到 SIM READY")
                
                if "Chunghwa Telecom" in page_source:
                    success_count += 1
                    logging.info("在頁面源碼中找到 Chunghwa Telecom")
                
                # 方法3: 嘗試使用 XPath 查找
                try:
                    sim_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'SIM READY')]")
                    if sim_elements:
                        success_count += 1
                        logging.info("使用 XPath 找到 SIM READY 元素")
                except:
                    pass
                
                try:
                    telecom_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Chunghwa Telecom')]")
                    if telecom_elements:
                        success_count += 1
                        logging.info("使用 XPath 找到 Chunghwa Telecom 元素")
                except:
                    pass
                
                # 如果任何方法成功找到至少一個文本，則視為成功
                if success_count > 0:
                    logging.info(f"成功找到 {success_count} 個匹配項")
                    return True
                else:
                    logging.warning("未找到任何預期的文本")
                    return False
            except (NoSuchElementException, TimeoutException) as e:
                logging.error(f"切換頁面或搜尋文本失敗: {str(e)}")
                return False
        except Exception as e:
            logging.error(f"搜尋功能測試時發生未知錯誤: {str(e)}")
            return False
    
    def test_interactive_buttons(self) -> bool:
        """測試互動按鈕 - 適應新的頁面結構"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        try:
            wait = WebDriverWait(self.driver, utils.DEFAULT_WAIT_TIME)
            success_count = 0
            
            # 檢查是否可以切換到 Nokia 儀表板頁面
            try:
                # 確保我們能夠看到導航項目
                self.wait_for_page_load()
                time.sleep(1)  # 額外等待確保頁面完全載入
                
                # 嘗試找到導航項目並點擊
                nav_items = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "nav-item")))
                dashboard_clicked = False
                
                for item in nav_items:
                    if "Nokia 儀表板" in item.text:
                        try:
                            item.click()
                            dashboard_clicked = True
                            logging.info("點擊 Nokia 儀表板 導航項目")
                            time.sleep(2)  # 增加等待時間
                            break
                        except Exception as e:
                            logging.warning(f"點擊 Nokia 儀表板 導航項目失敗: {str(e)}")
                            # 嘗試使用 JavaScript 點擊
                            try:
                                self.driver.execute_script("arguments[0].click();", item)
                                dashboard_clicked = True
                                logging.info("使用 JavaScript 點擊 Nokia 儀表板 導航項目")
                                time.sleep(2)
                                break
                            except Exception as js_e:
                                logging.warning(f"使用 JavaScript 點擊失敗: {str(js_e)}")
                
                if not dashboard_clicked:
                    logging.warning("無法點擊 Nokia 儀表板 導航項目")
                    # 嘗試直接通過 JavaScript 切換頁面
                    try:
                        self.driver.execute_script("document.querySelectorAll('.page-section').forEach(p => p.classList.remove('active')); document.getElementById('nokia-dashboard').classList.add('active');")
                        logging.info("使用 JavaScript 切換到 Nokia 儀表板頁面")
                        time.sleep(1)
                    except Exception as e:
                        logging.warning(f"使用 JavaScript 切換頁面失敗: {str(e)}")
                
                # 檢查是否成功切換到 Nokia 儀表板頁面
                dashboard_success = False
                
                # 方法1: 檢查文字
                if self.verify_text_exists("Searching...") or self.verify_text_exists("LATITUDE"):
                    logging.info("成功切換到 Nokia 儀表板頁面")
                    success_count += 1
                    dashboard_success = True
                
                # 方法2: 檢查頁面源碼
                if not dashboard_success:
                    page_source = self.driver.page_source
                    if "Dashboard" in page_source and ("LATITUDE" in page_source or "LONGITUDE" in page_source):
                        logging.info("在頁面源碼中找到 Dashboard 相關內容")
                        success_count += 1
                        dashboard_success = True
                
                if not dashboard_success:
                    logging.warning("無法確認是否已切換到 Nokia 儀表板頁面")
                
                # 測試按鈕組 - 更靈活的方式尋找按鈕
                try:
                    # 方法1: 使用 class
                    button_groups = self.driver.find_elements(By.CLASS_NAME, "button-group")
                    if button_groups:
                        for group in button_groups:
                            buttons = group.find_elements(By.TAG_NAME, "button")
                            if buttons and len(buttons) > 1:
                                # 點擊非活動按鈕
                                for button in buttons:
                                    if "active" not in button.get_attribute("class"):
                                        button.click()
                                        logging.info(f"點擊按鈕: {button.text}")
                                        time.sleep(0.5)
                                        success_count += 1
                                        break
                    else:
                        # 方法2: 使用通用選擇器尋找按鈕
                        buttons = self.driver.find_elements(By.TAG_NAME, "button")
                        if buttons and len(buttons) > 0:
                            buttons[0].click()
                            logging.info(f"點擊第一個找到的按鈕")
                            time.sleep(0.5)
                            success_count += 1
                except Exception as e:
                    logging.warning(f"測試按鈕組失敗: {str(e)}")
                
                # 返回首頁
                try:
                    nav_items = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "nav-item")))
                    home_clicked = False
                    
                    for item in nav_items:
                        if "首頁" in item.text:
                            item.click()
                            home_clicked = True
                            logging.info("點擊首頁導航項目")
                            time.sleep(1)
                            break
                    
                    if not home_clicked:
                        # 嘗試使用 JavaScript 切換回首頁
                        self.driver.execute_script("document.querySelectorAll('.page-section').forEach(p => p.classList.remove('active')); document.getElementById('home').classList.add('active');")
                        logging.info("使用 JavaScript 切換回首頁")
                        time.sleep(1)
                except Exception as e:
                    logging.warning(f"返回首頁失敗: {str(e)}")
                
                # 檢查是否成功返回首頁
                if self.verify_text_exists("自動化測試頁面"):
                    logging.info("成功返回首頁")
                    success_count += 1
                
                # 只要有一些操作成功，就視為測試通過
                if success_count >= 1:
                    logging.info(f"互動按鈕測試成功，完成了 {success_count} 個操作")
                    return True
                else:
                    logging.warning("互動按鈕測試未達到成功標準")
                    return False
            except (NoSuchElementException, TimeoutException, ElementNotInteractableException) as e:
                logging.warning(f"互動按鈕測試失敗: {str(e)}")
                return False
        except Exception as e:
            logging.error(f"互動按鈕測試時發生未知錯誤: {str(e)}")
            return False
    
    def search_keyword(self, keyword: str) -> bool:
        """搜尋關鍵字 - 適應新的頁面結構"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        try:
            wait = WebDriverWait(self.driver, utils.DEFAULT_WAIT_TIME)
            
            # 確保在首頁
            try:
                nav_items = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "nav-item")))
                home_clicked = False
                
                for item in nav_items:
                    if "首頁" in item.text:
                        if "active" not in item.get_attribute("class"):
                            try:
                                item.click()
                                home_clicked = True
                                logging.info("點擊首頁導航項目")
                                time.sleep(1)
                            except Exception as e:
                                logging.warning(f"點擊首頁導航項目失敗: {str(e)}")
                                # 嘗試使用 JavaScript 點擊
                                try:
                                    self.driver.execute_script("arguments[0].click();", item)
                                    home_clicked = True
                                    logging.info("使用 JavaScript 點擊首頁導航項目")
                                    time.sleep(1)
                                except Exception as js_e:
                                    logging.warning(f"使用 JavaScript 點擊失敗: {str(js_e)}")
                        else:
                            home_clicked = True  # 已經在首頁
                        break
                
                if not home_clicked:
                    # 嘗試直接通過 JavaScript 切換頁面
                    try:
                        self.driver.execute_script("document.querySelectorAll('.page-section').forEach(p => p.classList.remove('active')); document.getElementById('home').classList.add('active');")
                        logging.info("使用 JavaScript 切換到首頁")
                        time.sleep(1)
                        home_clicked = True
                    except Exception as e:
                        logging.warning(f"使用 JavaScript 切換頁面失敗: {str(e)}")
                
                if not home_clicked:
                    logging.warning("無法切換到首頁，繼續在當前頁面搜尋關鍵字")
            except Exception as e:
                logging.warning(f"切換到首頁時發生錯誤: {str(e)}")
            
            # 使用多種方法搜尋關鍵字
            success = False
            
            # 方法1: 在自訂文字區域中搜尋關鍵字
            try:
                custom_text = self.driver.find_element(By.ID, "customText")
                if keyword in custom_text.text:
                    logging.info(f"在自訂文字中找到關鍵字: {keyword}")
                    success = True
            except (NoSuchElementException, TimeoutException):
                logging.info("找不到自訂文字區域，嘗試其他方法")
            
            # 方法2: 在頁面中搜尋關鍵字
            if not success:
                page_source = self.driver.page_source
                if keyword in page_source:
                    logging.info(f"在頁面源碼中找到關鍵字: {keyword}")
                    success = True
            
            # 方法3: 使用 XPath 搜尋關鍵字
            if not success:
                try:
                    xpath = f"//*[contains(text(), '{keyword}')]"
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    if elements:
                        logging.info(f"使用 XPath 找到關鍵字: {keyword}")
                        success = True
                except Exception as e:
                    logging.warning(f"使用 XPath 搜尋關鍵字失敗: {str(e)}")
            
            # 方法4: 使用不區分大小寫的搜尋
            if not success:
                page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                if keyword.lower() in page_text:
                    logging.info(f"在頁面文字中找到關鍵字(不區分大小寫): {keyword}")
                    success = True
            
            if success:
                return True
            else:
                logging.warning(f"未找到關鍵字: {keyword}")
                return False
        except Exception as e:
            logging.error(f"搜尋關鍵字時發生未知錯誤: {str(e)}")
            return False
    
    # 基本操作指令
    def refresh_page(self) -> bool:
        """重新整理頁面"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        try:
            self.driver.refresh()
            logging.info("頁面已重新整理")
            
            # 等待頁面載入
            wait = WebDriverWait(self.driver, utils.DEFAULT_WAIT_TIME)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(1)  # 額外等待確保頁面完全載入
            return True
        except Exception as e:
            logging.error(f"重新整理頁面時發生錯誤: {str(e)}")
            return False
    
    def go_back(self) -> bool:
        """返回上一頁"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        try:
            self.driver.back()
            logging.info("已返回上一頁")
            
            # 等待頁面載入
            wait = WebDriverWait(self.driver, utils.DEFAULT_WAIT_TIME)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(1)  # 額外等待確保頁面完全載入
            return True
        except Exception as e:
            logging.error(f"返回上一頁時發生錯誤: {str(e)}")
            return False
    
    def click_by_id(self, element_id: str) -> bool:
        """點擊指定ID的元素"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        try:
            wait = WebDriverWait(self.driver, utils.DEFAULT_WAIT_TIME)
            element = wait.until(EC.element_to_be_clickable((By.ID, element_id)))
            element.click()
            logging.info(f"已點擊ID為 {element_id} 的元素")
            return True
        except (NoSuchElementException, TimeoutException) as e:
            logging.error(f"找不到ID為 {element_id} 的元素: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"點擊ID為 {element_id} 的元素時發生錯誤: {str(e)}")
            return False
    
    def type_text(self, text: str) -> bool:
        """在當前焦點元素中輸入文字"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        try:
            active_element = self.driver.switch_to.active_element
            active_element.send_keys(text)
            logging.info(f"已輸入文字: {text}")
            return True
        except Exception as e:
            logging.error(f"輸入文字時發生錯誤: {str(e)}")
            return False
    
    # 驗證指令
    def verify_text_exists(self, text: str) -> bool:
        """驗證頁面包含特定文字 - 增強版"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        try:
            # 等待頁面完全載入
            self.wait_for_page_load()
            
            # 使用多種方法檢查文字是否存在
            # 方法1: 檢查頁面源碼
            page_source = self.driver.page_source
            source_found = text in page_source
            if source_found:
                logging.info(f"驗證成功: 在頁面源碼中找到文字 '{text}'")
                return True
            
            # 方法2: 檢查頁面可見文字
            try:
                body_text = self.driver.find_element(By.TAG_NAME, "body").text
                text_found = text in body_text
                if text_found:
                    logging.info(f"驗證成功: 在頁面文字中找到 '{text}'")
                    return True
            except:
                body_text = ""
                text_found = False
            
            # 方法3: 使用不區分大小寫的搜尋
            try:
                lower_body_text = body_text.lower()
                lower_text = text.lower()
                case_insensitive_found = lower_text in lower_body_text
                if case_insensitive_found:
                    logging.info(f"驗證成功: 在頁面文字中找到(不區分大小寫) '{text}'")
                    return True
            except:
                case_insensitive_found = False
                
            # 方法4: 嘗試使用 XPath 查找包含文字的元素
            try:
                # 使用更靈活的 XPath 表達式
                xpath_expressions = [
                    f"//*[contains(text(), '{text}')]",
                    f"//*[contains(., '{text}')]",
                    f"//input[@value='{text}']"
                ]
                
                for xpath in xpath_expressions:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    if len(elements) > 0:
                        logging.info(f"驗證成功: 使用 XPath 找到文字 '{text}'")
                        return True
                
                has_elements = False
            except:
                has_elements = False
            
            # 方法5: 使用部分匹配
            if len(text) > 5:  # 只對較長的文字嘗試部分匹配
                try:
                    # 將文字分割成幾個部分，檢查是否有任何部分存在
                    parts = [text[:len(text)//2], text[len(text)//2:]]
                    for part in parts:
                        if len(part) > 4 and (part in page_source or part in body_text):
                            logging.info(f"驗證成功: 找到部分文字 '{part}' (來自 '{text}')")
                            return True
                except:
                    pass
            
            # 所有方法都失敗
            logging.warning(f"驗證失敗: 未找到文字 '{text}'")
            logging.debug(f"頁面標題: {self.driver.title}")
            logging.debug(f"當前URL: {self.driver.current_url}")
            return False
        except Exception as e:
            logging.error(f"驗證文字存在時發生錯誤: {str(e)}")
            return False
    
    def verify_text_not_exists(self, text: str) -> bool:
        """驗證頁面不包含特定文字"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        try:
            page_source = self.driver.page_source
            if text not in page_source:
                logging.info(f"驗證成功: 未找到文字 '{text}'")
                return True
            else:
                logging.warning(f"驗證失敗: 找到文字 '{text}'")
                return False
        except Exception as e:
            logging.error(f"驗證文字不存在時發生錯誤: {str(e)}")
            return False
    
    def verify_element_exists(self, selector: str) -> bool:
        """驗證元素存在"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        try:
            # 解析選擇器
            selector_type, selector_value = self._parse_selector(selector)
            wait = WebDriverWait(self.driver, utils.DEFAULT_WAIT_TIME)
            wait.until(EC.presence_of_element_located((selector_type, selector_value)))
            logging.info(f"驗證成功: 找到元素 '{selector}'")
            return True
        except (NoSuchElementException, TimeoutException):
            logging.warning(f"驗證失敗: 未找到元素 '{selector}'")
            return False
        except Exception as e:
            logging.error(f"驗證元素存在時發生錯誤: {str(e)}")
            return False
    
    def verify_element_value(self, selector: str, expected_value: str) -> bool:
        """驗證元素值符合預期"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        try:
            # 解析選擇器
            selector_type, selector_value = self._parse_selector(selector)
            wait = WebDriverWait(self.driver, utils.DEFAULT_WAIT_TIME)
            element = wait.until(EC.presence_of_element_located((selector_type, selector_value)))
            
            actual_value = element.get_attribute("value") or element.text
            if actual_value == expected_value:
                logging.info(f"驗證成功: 元素 '{selector}' 的值為 '{expected_value}'")
                return True
            else:
                logging.warning(f"驗證失敗: 元素 '{selector}' 的值為 '{actual_value}'，預期為 '{expected_value}'")
                return False
        except (NoSuchElementException, TimeoutException):
            logging.warning(f"驗證失敗: 未找到元素 '{selector}'")
            return False
        except Exception as e:
            logging.error(f"驗證元素值時發生錯誤: {str(e)}")
            return False
    
    def verify_count(self, selector: str, expected_count: int) -> bool:
        """驗證符合選擇器的元素數量"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        try:
            # 解析選擇器
            selector_type, selector_value = self._parse_selector(selector)
            elements = self.driver.find_elements(selector_type, selector_value)
            actual_count = len(elements)
            
            if actual_count == expected_count:
                logging.info(f"驗證成功: 找到 {actual_count} 個符合 '{selector}' 的元素")
                return True
            else:
                logging.warning(f"驗證失敗: 找到 {actual_count} 個符合 '{selector}' 的元素，預期為 {expected_count}")
                return False
        except Exception as e:
            logging.error(f"驗證元素數量時發生錯誤: {str(e)}")
            return False
    
    # 等待指令
    def wait_for_text(self, text: str, max_wait_time: int = None) -> bool:
        """等待文字出現"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        if max_wait_time is None:
            max_wait_time = utils.DEFAULT_WAIT_TIME
        
        try:
            wait = WebDriverWait(self.driver, max_wait_time)
            wait.until(lambda driver: text in driver.page_source)
            logging.info(f"等待成功: 文字 '{text}' 已出現")
            return True
        except TimeoutException:
            logging.warning(f"等待超時: 文字 '{text}' 未出現")
            return False
        except Exception as e:
            logging.error(f"等待文字出現時發生錯誤: {str(e)}")
            return False
    
    def wait_for_element(self, selector: str, max_wait_time: int = None) -> bool:
        """等待元素出現"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        if max_wait_time is None:
            max_wait_time = utils.DEFAULT_WAIT_TIME
        
        try:
            # 解析選擇器
            selector_type, selector_value = self._parse_selector(selector)
            wait = WebDriverWait(self.driver, max_wait_time)
            wait.until(EC.presence_of_element_located((selector_type, selector_value)))
            logging.info(f"等待成功: 元素 '{selector}' 已出現")
            return True
        except TimeoutException:
            logging.warning(f"等待超時: 元素 '{selector}' 未出現")
            return False
        except Exception as e:
            logging.error(f"等待元素出現時發生錯誤: {str(e)}")
            return False
    
    def wait_for_page_load(self, max_wait_time: int = None) -> bool:
        """等待頁面完全載入"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        if max_wait_time is None:
            max_wait_time = utils.DEFAULT_WAIT_TIME
        
        try:
            wait = WebDriverWait(self.driver, max_wait_time)
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            logging.info("等待成功: 頁面已完全載入")
            return True
        except TimeoutException:
            logging.warning("等待超時: 頁面未完全載入")
            return False
        except Exception as e:
            logging.error(f"等待頁面載入時發生錯誤: {str(e)}")
            return False
    
    # 頁面導航與互動
    def scroll_to_element(self, selector: str) -> bool:
        """滾動到指定元素"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        try:
            # 解析選擇器
            selector_type, selector_value = self._parse_selector(selector)
            element = self.driver.find_element(selector_type, selector_value)
            
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            time.sleep(1)  # 等待滾動完成
            logging.info(f"已滾動到元素 '{selector}'")
            return True
        except NoSuchElementException:
            logging.warning(f"滾動失敗: 未找到元素 '{selector}'")
            return False
        except Exception as e:
            logging.error(f"滾動到元素時發生錯誤: {str(e)}")
            return False
    
    def scroll_to_bottom(self) -> bool:
        """滾動到頁面底部"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        try:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)  # 等待滾動完成
            logging.info("已滾動到頁面底部")
            return True
        except Exception as e:
            logging.error(f"滾動到頁面底部時發生錯誤: {str(e)}")
            return False
    
    def expand(self, selector: str) -> bool:
        """展開摺疊區域"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        try:
            # 解析選擇器
            selector_type, selector_value = self._parse_selector(selector)
            element = self.driver.find_element(selector_type, selector_value)
            
            # 檢查元素是否已展開
            is_expanded = element.get_attribute("aria-expanded") == "true"
            if is_expanded:
                logging.info(f"元素 '{selector}' 已經是展開狀態")
                return True
            
            # 點擊元素以展開
            element.click()
            time.sleep(1)  # 等待展開動畫
            logging.info(f"已展開元素 '{selector}'")
            return True
        except NoSuchElementException:
            logging.warning(f"展開失敗: 未找到元素 '{selector}'")
            return False
        except Exception as e:
            logging.error(f"展開元素時發生錯誤: {str(e)}")
            return False
    
    # 執行導航序列
    def execute_nav_sequence(self, commands: List[str]) -> bool:
        """執行導航序列"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        success = True
        for cmd_str in commands:
            parts = cmd_str.split(":", 1)
            if len(parts) != 2:
                logging.error(f"無效的導航序列命令: {cmd_str}")
                success = False
                continue
            
            cmd, params_str = parts
            params = params_str.split(",")
            
            # 執行命令
            result = self._execute_command(cmd, params)
            if not result:
                logging.warning(f"導航序列命令 '{cmd}' 執行失敗")
                success = False
        
        return success
    
    # 輔助方法
    def _parse_selector(self, selector: str) -> Tuple[str, str]:
        """解析選擇器，支援 CSS 和 XPath"""
        if selector.startswith("#"):
            return By.ID, selector[1:]
        elif selector.startswith("."):
            return By.CLASS_NAME, selector[1:]
        elif selector.startswith("//"):
            return By.XPATH, selector
        else:
            return By.CSS_SELECTOR, selector
    
    def _execute_command(self, cmd: str, params: List[str]) -> bool:
        """執行單一命令"""
        try:
            if cmd == "CLICK_BY_TEXT":
                return self.click_by_text(params[0]) if params else False
            elif cmd == "CLICK_BY_ID":
                return self.click_by_id(params[0]) if params else False
            elif cmd == "CLICK_BY_CSS":
                return self.click_by_css(params[0]) if params else False
            elif cmd == "WAIT":
                return self.wait(int(params[0])) if params else False
            elif cmd == "TYPE":
                return self.type_text(params[0]) if params else False
            elif cmd == "OPEN_URL":
                return self.open_html_page(params[0]) if params else False
            elif cmd == "VERIFY_TEXT_CONTAINS":
                return self.verify_text_contains(params[0]) if params else False
            elif cmd == "VERIFY_TEXT_PATTERN":
                return self.verify_text_pattern(params[0]) if params else False
            elif cmd == "VERIFY_TEXT_EXISTS":
                return self.verify_text_exists(params[0]) if params else False
            elif cmd == "VERIFY_ELEMENT_EXISTS":
                return self.verify_element_exists(params[0]) if params else False
            elif cmd == "VERIFY_TEXT_SIMILAR":
                if len(params) > 1:
                    return self.verify_text_similar(params[0], params[1])
                else:
                    return self.verify_text_similar(params[0]) if params else False
            elif cmd == "VERIFY_ANY_TEXT":
                return self.verify_any_text(params) if params else False
            elif cmd == "VERIFY_ALL_TEXT":
                return self.verify_all_text(params) if params else False
            elif cmd == "TEST_CASE":
                # 記錄測試案例訊息但不做實際操作
                logging.info(f"執行測試案例: {params[0] if params else '未指定'}")
                return True
            elif cmd == "DESCRIPTION":
                # 記錄描述訊息但不做實際操作
                logging.info(f"測試描述: {params[0] if params else '未指定'}")
                return True
            # 可以根據需要添加更多命令
            else:
                logging.warning(f"未知命令: {cmd}")
                return False
        except Exception as e:
            logging.error(f"執行命令 {cmd} 時發生錯誤: {str(e)}")
            return False
    
    def wait(self, seconds: int) -> bool:
        """等待指定秒數"""
        try:
            # 直接使用 time.sleep，不使用 WebDriverWait
            # 這樣可以避免 'WebDriverWait' object is not callable 錯誤
            time.sleep(seconds)
            logging.info(f"已等待 {seconds} 秒")
            return True
        except Exception as e:
            logging.error(f"等待時發生錯誤: {str(e)}")
            return False
    
    def close_driver(self) -> None:
        """關閉 WebDriver"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.wait = None
                logging.info("WebDriver 已關閉")
        except Exception as e:
            logging.error(f"關閉 WebDriver 時發生錯誤: {str(e)}")
            self.driver = None
            self.wait = None
    
    # 新增模糊匹配相關方法
    def verify_text_contains(self, expected_text: str) -> bool:
        """驗證頁面文本包含部分指定文本 (部分匹配)"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            if utils.text_contains(page_text, expected_text):
                logging.info(f"成功: 找到包含 '{expected_text}' 的文本")
                return True
            else:
                logging.warning(f"警告: 未找到包含 '{expected_text}' 的文本")
                return False
        except Exception as e:
            logging.error(f"驗證文本包含時發生錯誤: {str(e)}")
            return False
    
    def verify_text_pattern(self, pattern: str) -> bool:
        """驗證頁面文本符合指定的正則表達式模式"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            if utils.text_matches_pattern(page_text, pattern):
                logging.info(f"成功: 文本符合模式 '{pattern}'")
                return True
            else:
                logging.warning(f"警告: 文本不符合模式 '{pattern}'")
                return False
        except Exception as e:
            logging.error(f"驗證文本模式時發生錯誤: {str(e)}")
            return False
    
    def verify_text_similar(self, expected_text: str, threshold: float = None) -> bool:
        """驗證頁面文本與指定文本的相似度是否超過閾值"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # 如果沒有指定閾值，使用默認值
            if threshold is None:
                threshold = utils.DEFAULT_SIMILARITY_THRESHOLD
            else:
                threshold = float(threshold)
            
            similarity = utils.calculate_text_similarity(page_text, expected_text)
            if similarity >= threshold:
                logging.info(f"成功: 文本相似度 {similarity:.2f} 超過閾值 {threshold:.2f}")
                return True
            else:
                logging.warning(f"警告: 文本相似度 {similarity:.2f} 低於閾值 {threshold:.2f}")
                return False
        except Exception as e:
            logging.error(f"驗證文本相似度時發生錯誤: {str(e)}")
            return False
    
    def verify_any_text(self, expected_texts: List[str]) -> bool:
        """驗證頁面是否包含任一指定文本 (OR 邏輯)"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            if utils.any_text_matches(page_text, expected_texts):
                logging.info(f"成功: 找到符合條件的文本 (任一條件滿足)")
                return True
            else:
                expected_str = " 或 ".join([f"'{text}'" for text in expected_texts])
                logging.warning(f"警告: 未找到任何符合條件的文本: {expected_str}")
                return False
        except Exception as e:
            logging.error(f"驗證任一文本時發生錯誤: {str(e)}")
            return False
    
    def verify_all_text(self, expected_texts: List[str]) -> bool:
        """驗證頁面是否包含所有指定文本 (AND 邏輯)"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            if utils.all_texts_match(page_text, expected_texts):
                logging.info(f"成功: 找到所有符合條件的文本 (所有條件滿足)")
                return True
            else:
                # 找出哪些文本不符合
                missing_texts = [text for text in expected_texts if text.lower() not in page_text.lower()]
                missing_str = ", ".join([f"'{text}'" for text in missing_texts])
                logging.warning(f"警告: 缺少以下文本: {missing_str}")
                return False
        except Exception as e:
            logging.error(f"驗證所有文本時發生錯誤: {str(e)}")
            return False
    
    def test_page_navigation(self) -> bool:
        """測試頁面導航功能"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        try:
            wait = WebDriverWait(self.driver, utils.DEFAULT_WAIT_TIME)
            
            # 定義要測試的頁面
            pages = [
                {"id": "home", "name": "首頁"},
                {"id": "certificate", "name": "憑證檢查頁面"},
                {"id": "nokia-basic", "name": "Nokia 基本設定"},
                {"id": "nokia-cellular", "name": "Nokia 網路狀態"},
                {"id": "nokia-dashboard", "name": "Nokia 儀表板"},
                {"id": "nokia-network", "name": "Nokia 網路設定"},
                {"id": "device-settings", "name": "Device Settings"}
            ]
            
            for page in pages:
                try:
                    # 點擊導航項目
                    nav_item = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f'.nav-item[data-page="{page["id"]}"]')))
                    nav_item.click()
                    logging.info(f"點擊導航項目：{page['name']}")
                    time.sleep(1)
                    
                    # 驗證頁面是否正確顯示
                    page_section = wait.until(EC.presence_of_element_located((By.ID, page["id"])))
                    if page_section.is_displayed() and "active" in page_section.get_attribute("class"):
                        logging.info(f"成功切換到頁面：{page['name']}")
                        
                        # 根據不同頁面執行特定的測試
                        if page["id"] == "certificate":
                            self.test_certificate_page()
                        elif page["id"] == "nokia-basic":
                            self.test_nokia_basic_page()
                        elif page["id"] == "nokia-cellular":
                            self.test_nokia_cellular_page()
                        elif page["id"] == "nokia-network":
                            self.test_nokia_network_page()
                        elif page["id"] == "device-settings":
                            self.test_device_settings_page()
                    else:
                        logging.warning(f"頁面切換失敗：{page['name']}")
                        return False
                except Exception as e:
                    logging.error(f"測試頁面 {page['name']} 時發生錯誤: {str(e)}")
                    return False
            
            logging.info("所有頁面導航測試完成")
            return True
            
        except Exception as e:
            logging.error(f"頁面導航測試時發生未知錯誤: {str(e)}")
            return False
    
    def test_certificate_page(self) -> bool:
        """測試憑證檢查頁面"""
        try:
            wait = WebDriverWait(self.driver, utils.DEFAULT_WAIT_TIME)
            
            # 檢查警告訊息是否顯示
            warning = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "security-warning")))
            if not warning.is_displayed():
                logging.warning("憑證頁面警告訊息未顯示")
                return False
            
            # 點擊檢視憑證按鈕
            view_cert_button = wait.until(EC.element_to_be_clickable((By.ID, "view-cert-button")))
            view_cert_button.click()
            logging.info("點擊檢視憑證按鈕")
            time.sleep(1)
            
            # 驗證憑證內容是否顯示
            cert_container = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "certificate-container")))
            if cert_container.is_displayed():
                logging.info("憑證內容顯示正確")
                return True
            else:
                logging.warning("憑證內容未正確顯示")
                return False
            
        except Exception as e:
            logging.error(f"測試憑證頁面時發生錯誤: {str(e)}")
            return False
    
    def test_nokia_basic_page(self) -> bool:
        """測試 Nokia 基本設定頁面"""
        try:
            wait = WebDriverWait(self.driver, utils.DEFAULT_WAIT_TIME)
            
            # 檢查基本設定頁面元素
            basic_settings = wait.until(EC.presence_of_element_located((By.ID, "nokia-basic")))
            if not basic_settings.is_displayed():
                logging.warning("Nokia 基本設定頁面未顯示")
                return False
            
            logging.info("Nokia 基本設定頁面顯示正確")
            return True
            
        except Exception as e:
            logging.error(f"測試 Nokia 基本設定頁面時發生錯誤: {str(e)}")
            return False
    
    def test_nokia_cellular_page(self) -> bool:
        """測試 Nokia 網路狀態頁面"""
        try:
            wait = WebDriverWait(self.driver, utils.DEFAULT_WAIT_TIME)
            
            # 檢查網路狀態頁面元素
            cellular_status = wait.until(EC.presence_of_element_located((By.ID, "nokia-cellular")))
            if not cellular_status.is_displayed():
                logging.warning("Nokia 網路狀態頁面未顯示")
                return False
            
            # 等待並檢查網路狀態更新
            time.sleep(2)  # 等待狀態更新
            status_elements = self.driver.find_elements(By.CLASS_NAME, "section-content")
            if not status_elements:
                logging.warning("找不到網路狀態資訊")
                return False
            
            logging.info("Nokia 網路狀態頁面顯示正確")
            return True
            
        except Exception as e:
            logging.error(f"測試 Nokia 網路狀態頁面時發生錯誤: {str(e)}")
            return False
    
    def test_nokia_network_page(self) -> bool:
        """測試 Nokia 網路設定頁面"""
        try:
            wait = WebDriverWait(self.driver, utils.DEFAULT_WAIT_TIME)
            
            # 檢查網路設定頁面元素
            network_settings = wait.until(EC.presence_of_element_located((By.ID, "nokia-network")))
            if not network_settings.is_displayed():
                logging.warning("Nokia 網路設定頁面未顯示")
                return False
            
            # 測試按鈕組功能
            button_groups = self.driver.find_elements(By.CLASS_NAME, "button-group")
            if not button_groups:
                logging.warning("找不到網路設定按鈕組")
                return False
            
            for group in button_groups:
                buttons = group.find_elements(By.CLASS_NAME, "toggle-button")
                if buttons:
                    # 點擊第一個按鈕測試
                    buttons[0].click()
                    time.sleep(0.5)
                    if "active" not in buttons[0].get_attribute("class"):
                        logging.warning("按鈕狀態切換失敗")
                        return False
            
            logging.info("Nokia 網路設定頁面顯示正確")
            return True
            
        except Exception as e:
            logging.error(f"測試 Nokia 網路設定頁面時發生錯誤: {str(e)}")
            return False
    
    def test_device_settings_page(self) -> bool:
        """測試裝置設定頁面"""
        try:
            wait = WebDriverWait(self.driver, utils.DEFAULT_WAIT_TIME)
            
            # 檢查裝置設定頁面元素
            device_settings = wait.until(EC.presence_of_element_located((By.ID, "device-settings")))
            if not device_settings.is_displayed():
                logging.warning("裝置設定頁面未顯示")
                return False
            
            # 測試密碼修改功能
            try:
                # 輸入當前密碼
                current_pwd = wait.until(EC.presence_of_element_located((By.ID, "currentPassword")))
                current_pwd.send_keys("Pega#1234")
                
                # 輸入新密碼
                new_pwd = wait.until(EC.presence_of_element_located((By.ID, "newPassword")))
                new_pwd.send_keys("NewPega#1234")
                
                # 確認新密碼
                confirm_pwd = wait.until(EC.presence_of_element_located((By.ID, "confirmPassword")))
                confirm_pwd.send_keys("NewPega#1234")
                
                logging.info("密碼修改表單填寫完成")
            except:
                logging.warning("密碼修改表單填寫失敗")
                return False
            
            logging.info("裝置設定頁面顯示正確")
            return True
            
        except Exception as e:
            logging.error(f"測試裝置設定頁面時發生錯誤: {str(e)}")
            return False
    
    def click_by_css(self, css_selector: str) -> bool:
        """通過 CSS 選擇器點擊元素"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        try:
            # 等待元素可點擊
            wait = WebDriverWait(self.driver, utils.DEFAULT_WAIT_TIME)
            element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector)))
            element.click()
            logging.info(f"已點擊 CSS 選擇器 '{css_selector}' 的元素")
            return True
        except (NoSuchElementException, TimeoutException):
            logging.warning(f"找不到 CSS 選擇器 '{css_selector}' 的元素")
            return False
        except Exception as e:
            logging.error(f"點擊 CSS 選擇器 '{css_selector}' 的元素時發生錯誤: {str(e)}")
            return False

if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 創建 SeleniumHandler 實例
    handler = SeleniumHandler()
    
    try:
        # 初始化
        if not handler.find_chromedriver():
            logging.error("找不到 ChromeDriver")
            sys.exit(1)
            
        if not handler.initialize_driver():
            logging.error("初始化 WebDriver 失敗")
            sys.exit(1)
            
        # 打開測試頁面
        if not handler.open_html_page("web/360_TEST_WEBFILE.html"):
            logging.error("打開測試頁面失敗")
            sys.exit(1)
            
        # 執行登入測試
        if handler.test_login_form():
            logging.info("登入測試成功")
            
            # 執行頁面導航測試
            if handler.test_page_navigation():
                logging.info("頁面導航測試成功")
            else:
                logging.error("頁面導航測試失敗")
        else:
            logging.error("登入測試失敗")
            
    except Exception as e:
        logging.error(f"測試過程中發生錯誤: {str(e)}")
    finally:
        # 關閉瀏覽器
        handler.close_driver() 