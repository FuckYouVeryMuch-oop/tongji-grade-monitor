import json
import time
from datetime import datetime

def load_config(config_file='config.json'):
    """加载配置文件"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"配置文件 {config_file} 不存在")
        print("请复制 config.json.example 为 config.json，然后填入你的学号和密码")
        print("  命令: cp config.json.example config.json\n")
        return get_default_config()
    except json.JSONDecodeError as e:
        print(f"配置文件格式错误: {e}")
        return get_default_config()

def get_default_config():
    """获取默认配置"""
    return {
        "username": "",
        "password": "",
        "check_interval": 300,
        "re_login_interval": 1800,
        "max_retries": 3,
        "save_to_file": True,
        "data_file": "grades_data.json",
        "log_level": "INFO",
        "headless_mode": False
    }

def save_config(config, config_file='config.json'):
    """保存配置文件"""
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"配置已保存到 {config_file}")
    except Exception as e:
        print(f"保存配置失败: {e}")

def print_banner():
    """打印程序横幅"""
    banner = """
=====================================
    同济大学成绩监控系统 v1.0
    Tongji Grade Monitor
=====================================
"""
    print(banner)

def format_time_delta(seconds):
    """格式化时间差"""
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if hours > 0:
        parts.append(f"{int(hours)}小时")
    if minutes > 0:
        parts.append(f"{int(minutes)}分钟")
    if seconds > 0 or not parts:
        parts.append(f"{int(seconds)}秒")

    return "".join(parts)
