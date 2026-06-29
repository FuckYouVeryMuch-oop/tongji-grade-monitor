import time
import json
import requests
from datetime import datetime

class GradeFetcher:
    def __init__(self, login_manager, config):
        self.login_manager = login_manager
        self.config = config
        self.last_update_time = ""
        self.grade_history = []
        self.load_history()
    
    def load_history(self):
        """加载历史成绩数据"""
        try:
            if self.config.get('save_to_file', True):
                with open(self.config.get('data_file', 'grades_data.json'), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.grade_history = data.get('history', [])
                    self.last_update_time = data.get('last_update', "")
        except (FileNotFoundError, json.JSONDecodeError):
            self.grade_history = []
            self.last_update_time = ""
    
    def save_history(self, grades_data):
        """保存历史成绩数据"""
        if not self.config.get('save_to_file', True):
            return
        
        data = {
            'last_update': self.last_update_time,
            'history': self.grade_history[-50:],  # 只保留最近50次
            'last_check': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            with open(self.config.get('data_file', 'grades_data.json'), 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史数据失败: {e}")
    
    def fetch_grades(self):
        """获取成绩数据"""
        try:
            # 获取当前cookies
            cookies = self.login_manager.get_cookies()
            if not cookies:
                print("没有有效的cookies，请先登录")
                return None
            
            # 构造请求
            timestamp = int(time.time() * 1000)
            url = f"https://1.tongji.edu.cn/api/scoremanagementservice/scoreGrades/getMyGrades"
            
            params = {
                'studentId': self.config.get('student_id', self.config['username']),
                '_t': timestamp
            }
            
            headers = {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Referer': 'https://1.tongji.edu.cn/oldStysteMyGrades',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            print(f"[{time.strftime('%H:%M:%S')}] 正在获取成绩...")
            response = requests.get(url, params=params, headers=headers, cookies=cookies, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 200:
                    print(f"[{time.strftime('%H:%M:%S')}] 成功获取成绩数据")
                    return data
                else:
                    print(f"API返回错误: {data.get('msg')}")
            else:
                print(f"请求失败，状态码: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"网络请求失败: {e}")
        except Exception as e:
            print(f"获取成绩时出错: {e}")
        
        return None
    
    def check_for_updates(self, grades_data):
        """检查是否有新成绩"""
        if not grades_data or 'data' not in grades_data:
            return False, None
        
        # 获取最新的更新时间
        latest_time = self._extract_latest_update_time(grades_data)
        
        if not latest_time:
            return False, None
        
        # 记录本次查询
        check_time = time.strftime('%Y-%m-%d %H:%M:%S')
        self.grade_history.append({
            'check_time': check_time,
            'latest_update': latest_time,
            'has_new': latest_time != self.last_update_time and self.last_update_time != ""
        })
        
        # 检查是否有更新
        if self.last_update_time and latest_time > self.last_update_time:
            # 找到具体的新成绩
            new_courses = self._find_new_courses(grades_data)
            
            # 更新最后更新时间
            old_time = self.last_update_time
            self.last_update_time = latest_time
            
            # 保存历史
            self.save_history(grades_data)
            
            return True, {
                'new_update_time': latest_time,
                'old_update_time': old_time,
                'new_courses': new_courses,
                'total_data': grades_data
            }
        
        # 首次运行或没有新成绩
        if not self.last_update_time:
            self.last_update_time = latest_time
            self.save_history(grades_data)
        
        return False, None
    
    def _extract_latest_update_time(self, grades_data):
        """提取最新的更新时间"""
        latest_time = ""
        
        try:
            for term in grades_data['data'].get('term', []):
                for course in term.get('creditInfo', []):
                    update_time = course.get('updateTime', '')
                    if update_time and update_time > latest_time:
                        latest_time = update_time
        except Exception as e:
            print(f"提取更新时间失败: {e}")
        
        return latest_time
    
    def _find_new_courses(self, grades_data):
        """找到具体的新成绩课程"""
        new_courses = []
        
        try:
            for term in grades_data['data'].get('term', []):
                for course in term.get('creditInfo', []):
                    update_time = course.get('updateTime', '')
                    if update_time and update_time > self.last_update_time:
                        new_courses.append({
                            'course_name': course.get('courseName', ''),
                            'score': course.get('score', ''),
                            'update_time': update_time,
                            'term': term.get('termName', '')
                        })
        except Exception as e:
            print(f"查找新课程失败: {e}")
        
        return new_courses
    
    def get_summary(self, grades_data):
        """获取成绩摘要"""
        if not grades_data or 'data' not in grades_data:
            return "无数据"
        
        data = grades_data['data']
        return f"平均绩点: {data.get('totalGradePoint', 'N/A')}, 实际学分: {data.get('actualCredit', 'N/A')}"