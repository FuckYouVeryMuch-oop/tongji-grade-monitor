import time
import sys
from login_manager import LoginManager
from grade_fetcher import GradeFetcher
from notifier import Notifier
from utils import load_config, print_banner, format_time_delta

class GradeMonitor:
    def __init__(self, config):
        self.config = config
        self.login_manager = None
        self.grade_fetcher = None
        self.notifier = None
        self.running = False
        self.last_check_time = 0

    def initialize(self):
        """初始化组件"""
        print("初始化组件...")

        self.login_manager = LoginManager(self.config)
        self.login_manager.setup_browser()

        self.grade_fetcher = GradeFetcher(self.login_manager, self.config)

        self.notifier = Notifier()

        print("组件初始化完成")

    def run_once(self):
        """执行一次完整的检查"""
        try:
            print(f"\n[{time.strftime('%H:%M:%S')}] 开始检查...")

            if not self.login_manager.refresh_login_if_needed():
                print("登录失败，尝试重新初始化...")
                self.login_manager.close()
                self.login_manager.setup_browser()
                if not self.login_manager.login():
                    print("重新登录失败，等待下次尝试")
                    return False

            grades = self.grade_fetcher.fetch_grades()
            if not grades:
                print("获取成绩失败")
                return False

            summary = self.grade_fetcher.get_summary(grades)
            print(f"当前状态: {summary}")

            has_update, update_info = self.grade_fetcher.check_for_updates(grades)

            if has_update:
                print(f"🎉 发现新成绩更新 (共 {len(update_info['new_courses'])} 门)")

                self.notifier.show_grade_update(update_info)

                print("新成绩详情:")
                for course in update_info['new_courses']:
                    print(f"  - {course['course_name']}: {course['score']}")
            else:
                print("暂无新成绩")

            self.last_check_time = time.time()
            return True

        except Exception as e:
            print(f"检查过程中出错: {e}")
            import traceback
            traceback.print_exc()
            return False

    def run_continuous(self):
        """连续运行监控"""
        self.running = True

        self.run_once()

        check_interval = self.config.get('check_interval', 300)

        print(f"\n监控已启动，每 {format_time_delta(check_interval)} 检查一次")
        print("按 Ctrl+C 停止程序\n")

        try:
            while self.running:
                next_check = self.last_check_time + check_interval
                wait_time = max(0, next_check - time.time())

                if wait_time > 0:
                    for i in range(int(wait_time), 0, -1):
                        if not self.running:
                            break
                        sys.stdout.write(f"\r下次检查 {format_time_delta(i)}后")
                        sys.stdout.flush()
                        time.sleep(1)

                    if self.running:
                        sys.stdout.write("\r" + " " * 50 + "\r")
                        sys.stdout.flush()

                if self.running:
                    self.run_once()

        except KeyboardInterrupt:
            print("\n\n检测到用户中断，正在退出...")
        finally:
            self.stop()

    def stop(self):
        """停止监控"""
        print("正在停止监控...")
        self.running = False

        if self.notifier:
            self.notifier.stop()

        if self.login_manager:
            self.login_manager.close()

        print("监控已停止")

def main():
    """主函数"""
    print_banner()

    config = load_config()

    if not config.get('username') or not config.get('password'):
        print("错误: 请先在 config.json 中配置学号和密码（参考 config.json.example）")
        input("按回车键退出...")
        return

    monitor = GradeMonitor(config)

    try:
        monitor.initialize()

        print("正在尝试登录...")
        if not monitor.login_manager.login():
            print("首次登录失败，请检查学号和密码")
            input("按回车键退出...")
            return

        monitor.run_continuous()

    except Exception as e:
        print(f"程序运行出错: {e}")
        import traceback
        traceback.print_exc()
        input("按回车键退出...")
    finally:
        if monitor:
            monitor.stop()

if __name__ == "__main__":
    main()
