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
        """驗證頁面包含特定文字"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        try:
            page_source = self.driver.page_source
            if text in page_source:
                logging.info(f"驗證成功: 找到文字 '{text}'")
                return True
            else:
                logging.warning(f"驗證失敗: 未找到文字 '{text}'")
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
        if cmd == "CLICK_BY_TEXT":
            return self.click_by_text(params[0]) if params else False
        elif cmd == "CLICK_BY_ID":
            return self.click_by_id(params[0]) if params else False
        elif cmd == "WAIT":
            return self.wait(int(params[0])) if params else False
        elif cmd == "TYPE":
            return self.type_text(params[0]) if params else False
        elif cmd == "VERIFY_TEXT_CONTAINS":
            return self.verify_text_contains(params[0]) if params else False
        elif cmd == "VERIFY_TEXT_PATTERN":
            return self.verify_text_pattern(params[0]) if params else False
        elif cmd == "VERIFY_TEXT_SIMILAR":
            if len(params) > 1:
                return self.verify_text_similar(params[0], params[1])
            else:
                return self.verify_text_similar(params[0]) if params else False
        elif cmd == "VERIFY_ANY_TEXT":
            return self.verify_any_text(params) if params else False
        elif cmd == "VERIFY_ALL_TEXT":
            return self.verify_all_text(params) if params else False
        # 可以根據需要添加更多命令
        else:
            logging.warning(f"未知命令: {cmd}")
            return False
    
    def click_by_text(self, text: str) -> bool:
        """點擊包含指定文字的元素"""
        if not self.driver:
            logging.error("WebDriver 未初始化")
            return False
        
        try:
            # 嘗試使用不同的方法找到包含文字的元素
            methods = [
                # 精確匹配
                f"//button[text()='{text}']",
                f"//a[text()='{text}']",
                f"//input[@value='{text}']",
                f"//label[text()='{text}']",
                f"//*[text()='{text}']",
                
                # 包含文字
                f"//button[contains(text(),'{text}')]",
                f"//a[contains(text(),'{text}')]",
                f"//input[contains(@value,'{text}')]",
                f"//label[contains(text(),'{text}')]",
                f"//*[contains(text(),'{text}')]",
                
                # 包含文字的子元素
                f"//*[.//*[contains(text(),'{text}')]]"
            ]
            
            for xpath in methods:
                elements = self.driver.find_elements(By.XPATH, xpath)
                if elements:
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            element.click()
                            logging.info(f"已點擊包含文字 '{text}' 的元素")
                            return True
            
            logging.warning(f"找不到包含文字 '{text}' 的可點擊元素")
            return False
        except Exception as e:
            logging.error(f"點擊包含文字 '{text}' 的元素時發生錯誤: {str(e)}")
            return False
    
    def wait(self, seconds: int) -> bool:
        """等待指定秒數"""
        try:
            time.sleep(seconds)
            logging.info(f"已等待 {seconds} 秒")
            return True
        except Exception as e:
            logging.error(f"等待時發生錯誤: {str(e)}")
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