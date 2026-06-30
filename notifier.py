import tkinter as tk
from tkinter import messagebox
import threading
import time
import logging

log = logging.getLogger("GradeMonitor")

class Notifier:
    def __init__(self):
        self.notification_queue = []
        self.notification_thread = None
        self.running = False

    def show_notification(self, title, message, sound=True, flash=True):
        self.notification_queue.append({'title': title, 'message': message, 'sound': sound, 'flash': flash})
        if not self.running:
            self.start_notification_thread()

    def start_notification_thread(self):
        self.running = True
        self.notification_thread = threading.Thread(target=self._notification_worker)
        self.notification_thread.daemon = True
        self.notification_thread.start()

    def _notification_worker(self):
        while self.running:
            if self.notification_queue:
                notification = self.notification_queue.pop(0)
                self._show_single_notification(notification)
            time.sleep(0.5)
        try:
            tk.Tk().quit()
        except:
            pass

    def _show_single_notification(self, notification):
        try:
            if notification['sound']:
                self._play_notification_sound()
            if notification['flash']:
                self._flash_window()
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            messagebox.showinfo(notification['title'], notification['message'])
            root.destroy()
        except Exception as e:
            log.warning(f"显示通知时出错: {e}")

    def _play_notification_sound(self):
        try:
            import winsound
            for i in range(3):
                winsound.Beep(1000 + i * 200, 300)
        except:
            pass

    def _flash_window(self):
        try:
            import pyautogui
            for _ in range(3):
                pyautogui.getActiveWindow().flash()
                time.sleep(0.3)
        except:
            pass

    def show_grade_update(self, update_info):
        title = "发现新成绩!"
        message = f"发现 {len(update_info['new_courses'])} 门课程的新成绩\n\n"
        message += f"更新时间: {update_info['new_update_time']}\n"
        message += f"上次更新: {update_info['old_update_time']}\n\n"
        message += "新成绩详情:\n"
        for i, course in enumerate(update_info['new_courses'], 1):
            message += f"{i}. {course['course_name']}: {course['score']} ({course['term']})\n"
        message += "\n点击确定查看详细信息..."
        log.info(f"弹窗通知: {len(update_info['new_courses'])} 门新成绩")
        self.show_notification(title, message)

    def stop(self):
        self.running = False
        if self.notification_thread:
            self.notification_thread.join(timeout=1)
