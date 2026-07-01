import time
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

log = logging.getLogger("GradeMonitor")


class GradeFetcher:
    def __init__(self, login_manager, config):
        self.login_manager = login_manager
        self.config = config
        self.last_update_time = ""
        self.grade_history = []
        self.session = self._create_session()
        self.load_history()

    def _create_session(self):
        session = requests.Session()
        retry_strategy = Retry(
            total=5,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def load_history(self):
        try:
            if self.config.get("save_to_file", True):
                file_path = self.config.get("data_file", "grades_data.json")
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.grade_history = data.get("history", [])
                    self.last_update_time = data.get("last_update", "")
        except (FileNotFoundError, json.JSONDecodeError):
            self.grade_history = []
            self.last_update_time = ""

    def save_history(self, grades_data):
        if not self.config.get("save_to_file", True):
            return
        data = {
            "last_update": self.last_update_time,
            "history": self.grade_history[-50:],
            "last_check": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        try:
            file_path = self.config.get("data_file", "grades_data.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log.error(f"保存历史数据失败: {e}")

    def _fetch_via_browser(self):
        try:
            driver = self.login_manager.driver
            if not driver:
                return None
            timestamp = int(time.time() * 1000)
            student_id = self.config.get("student_id", self.config["username"])
            url = f"https://1.tongji.edu.cn/api/scoremanagementservice/scoreGrades/getMyGrades?studentId={student_id}&_t={timestamp}"
            driver.get(url)
            time.sleep(2)
            from selenium.webdriver.common.by import By

            # 优先获取纯文本内容，避免 HTML 标签干扰
            raw = None
            try:
                body = driver.find_element(By.TAG_NAME, "body")
                raw = body.text
            except Exception:
                try:
                    pre = driver.find_element(By.TAG_NAME, "pre")
                    raw = pre.text
                except Exception:
                    raw = driver.page_source

            if not raw or not raw.strip():
                return None

            # Try direct JSON parse first
            try:
                data = json.loads(raw)
                if isinstance(data, dict) and data.get("code") == 200:
                    log.info("成功获取成绩数据 (via browser)")
                    return data
            except Exception:
                pass

            # Fallback: brace-matching extraction (more accurate than regex)
            try:
                start = raw.find("{")
                if start >= 0:
                    depth = 0
                    for i in range(start, len(raw)):
                        ch = raw[i]
                        if ch == "{":
                            depth += 1
                        elif ch == "}":
                            depth -= 1
                            if depth == 0:
                                json_str = raw[start:i + 1]
                                data = json.loads(json_str)
                                if isinstance(data, dict) and data.get("code") == 200:
                                    log.info("成功获取成绩数据 (via browser - extracted)")
                                    return data
                                break
            except Exception:
                pass

            return None
        except Exception as e:
            log.error(f"浏览器兜底也失败了: {e}")
            return None

    def fetch_grades(self):
        cookies = self.login_manager.get_cookies()
        if not cookies:
            log.warning("没有有效的cookies，请先登录")
            return None

        timestamp = int(time.time() * 1000)
        url = "https://1.tongji.edu.cn/api/scoremanagementservice/scoreGrades/getMyGrades"
        params = {
            "studentId": self.config.get("student_id", self.config["username"]),
            "_t": timestamp,
        }
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://1.tongji.edu.cn/oldStysteMyGrades",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Connection": "keep-alive",
        }

        for attempt in range(1, 4):
            log.info(f"正在获取成绩... (第{attempt}次)")
            try:
                resp = self.session.get(
                    url, params=params, headers=headers, cookies=cookies, timeout=15
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("code") == 200:
                        log.info("成功获取成绩数据")
                        return data
                    log.warning(f"API返回错误: {data.get('msg')}")
                    return None
            except requests.exceptions.SSLError:
                log.warning("SSL 错误，尝试跳过证书验证...")
                try:
                    resp = self.session.get(
                        url,
                        params=params,
                        headers=headers,
                        cookies=cookies,
                        timeout=15,
                        verify=False,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("code") == 200:
                            log.info("成功获取成绩数据 (verify=False)")
                            return data
                except Exception as e2:
                    log.warning(f"验证失败: {e2}")
            except Exception as e:
                log.warning(f"请求异常: {e}")
            time.sleep(2 * attempt)

        log.warning("requests 全部失败，改用浏览器获取...")
        return self._fetch_via_browser()

    def check_for_updates(self, grades_data):
        if not grades_data or "data" not in grades_data:
            return False, None
        latest_time = self._extract_latest_update_time(grades_data)
        if not latest_time:
            return False, None
        check_time = time.strftime("%Y-%m-%d %H:%M:%S")
        self.grade_history.append(
            {
                "check_time": check_time,
                "latest_update": latest_time,
                "has_new": latest_time != self.last_update_time
                and self.last_update_time != "",
            }
        )
        if self.last_update_time and latest_time > self.last_update_time:
            new_courses = self._find_new_courses(grades_data)
            old_time = self.last_update_time
            self.last_update_time = latest_time
            self.save_history(grades_data)
            return True, {
                "new_update_time": latest_time,
                "old_update_time": old_time,
                "new_courses": new_courses,
                "total_data": grades_data,
            }
        if not self.last_update_time:
            self.last_update_time = latest_time
            self.save_history(grades_data)
        return False, None

    def _extract_latest_update_time(self, grades_data):
        latest_time = ""
        try:
            for term in grades_data["data"].get("term", []):
                for course in term.get("creditInfo", []):
                    update_time = course.get("updateTime", "")
                    if update_time and update_time > latest_time:
                        latest_time = update_time
        except Exception:
            pass
        return latest_time

    def _find_new_courses(self, grades_data):
        new_courses = []
        try:
            for term in grades_data["data"].get("term", []):
                for course in term.get("creditInfo", []):
                    update_time = course.get("updateTime", "")
                    if update_time and update_time > self.last_update_time:
                        new_courses.append(
                            {
                                "course_name": course.get("courseName", ""),
                                "score": course.get("score", ""),
                                "update_time": update_time,
                                "term": term.get("termName", ""),
                            }
                        )
        except Exception:
            pass
        return new_courses

    def get_summary(self, grades_data):
        if not grades_data or "data" not in grades_data:
            return "无数据"
        data = grades_data["data"]
        return f"平均绩点: {data.get('totalGradePoint', 'N/A')}, 实际学分: {data.get('actualCredit', 'N/A')}"
