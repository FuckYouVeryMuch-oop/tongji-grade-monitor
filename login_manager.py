import time
import os
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException

log = logging.getLogger("GradeMonitor")

class LoginManager:
    def __init__(self, config):
        self.config = config
        self.driver = None
        self.cookies = {}
        self.last_login_time = 0

    def _find_local_driver(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(script_dir, "driver", "chromedriver-win64", "chromedriver.exe"),
            os.path.join(script_dir, "driver", "chromedriver.exe"),
        ]
        for path in candidates:
            if os.path.exists(path):
                log.info(f"使用本地驱动: {path}")
                return path
        return None

    def setup_browser(self):
        chrome_options = Options()
        if self.config.get('headless_mode', True):
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')

        try:
            local_driver = self._find_local_driver()
            if local_driver:
                service = Service(executable_path=local_driver)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                log.info("未找到本地驱动，尝试自动下载 (webdriver-manager)...")
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception as e:
            log.error(f"启动浏览器失败: {e}")
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
            except Exception as e2:
                log.error(f"也失败了: {e2}")
                raise

    def login(self):
        try:
            log.info("开始登录...")
            self.driver.get("https://1.tongji.edu.cn/oldStysteMyGrades")
            wait = WebDriverWait(self.driver, 10)

            username_input = wait.until(EC.presence_of_element_located((By.ID, "j_username")))
            username_input.clear()
            username_input.send_keys(self.config['username'])
            time.sleep(0.5)

            password_input = self.driver.find_element(By.ID, "j_password")
            password_input.clear()
            password_input.send_keys(self.config['password'])
            time.sleep(0.5)

            login_button = self.driver.find_element(By.ID, "loginButton")
            login_button.click()
            time.sleep(3)

            for _ in range(10):
                if "authcenter" not in self.driver.current_url:
                    break
                time.sleep(2)

            if "workbench" in self.driver.current_url or "oldStysteMyGrades" in self.driver.current_url:
                self._save_cookies()
                self.last_login_time = time.time()
                log.info("登录成功!")
                return True
            else:
                log.warning(f"登录失败，当前页面: {self.driver.current_url}")
                self.driver.save_screenshot(f"login_error_{int(time.time())}.png")
                return False

        except Exception as e:
            log.error(f"登录过程中出错: {str(e)}")
            if self.driver:
                self.driver.save_screenshot(f"login_exception_{int(time.time())}.png")
            return False

    def _save_cookies(self):
        self.cookies = {}
        for cookie in self.driver.get_cookies():
            self.cookies[cookie['name']] = cookie['value']
        log.info(f"获取到 {len(self.cookies)} 个cookies")

    def get_cookies(self):
        return self.cookies.copy()

    def is_login_expired(self):
        if not self.cookies:
            return True
        if time.time() - self.last_login_time > self.config.get('re_login_interval', 1800):
            return True
        return False

    def refresh_login_if_needed(self):
        if self.is_login_expired():
            log.info("登录已过期，重新登录...")
            return self.login()
        return True

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
