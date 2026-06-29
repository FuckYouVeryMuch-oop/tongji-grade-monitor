import tkinter as tk
from tkinter import messagebox
import threading
import time
import winsound
import pyautogui

class Notifier:
    def __init__(self):
        self.notification_queue = []
        self.notification_thread = None
        self.running = False
    
    def show_notification(self, title, message, sound=True, flash=True):
        """显示通知"""
        # 添加到队列
        self.notification_queue.append({
            'title': title,
            'message': message,
            'sound': sound,
            'flash': flash
        })
        
        # 启动通知线程（如果未启动）
        if not self.running:
            self.start_notification_thread()
    
    def start_notification_thread(self):
        """启动通知线程"""
        self.running = True
        self.notification_thread = threading.Thread(target=self._notification_worker)
        self.notification_thread.daemon = True
        self.notification_thread.start()
    
    def _notification_worker(self):
        """通知工作线程"""
        while self.running:
            if self.notification_queue:
                notification = self.notification_queue.pop(0)
                self._show_single_notification(notification)
            
            time.sleep(0.5)
        
        # 关闭所有Tkinter窗口
        try:
            tk.Tk().quit()
        except:
            pass
    
    def _show_single_notification(self, notification):
        """显示单个通知"""
        try:
            # 播放声音
            if notification['sound']:
                self._play_notification_sound()
            
            # 窗口闪烁效果
            if notification['flash']:
                self._flash_window()
            
            # 创建Tkinter窗口
            root = tk.Tk()
            root.withdraw()  # 隐藏主窗口
            
            # 设置窗口置顶
            root.attributes('-topmost', True)
            
            # 显示消息框
            messagebox.showinfo(
                notification['title'],
                notification['message']
            )
            
            # 销毁窗口
            root.destroy()
            
        except Exception as e:
            print(f"显示通知失败: {e}")
    
    def _play_notification_sound(self):
        """播放通知声音"""
        try:
            # Windows系统声音
            for i in range(3):
                winsound.Beep(1000 + i * 200, 300)
        except:
            try:
                # 备用方案
                import os
                os.system('powershell (New-Object Media.SoundPlayer "C:\Windows\Media\notify.wav").PlaySync();')
            except:
                pass
    
    def _flash_window(self):
        """窗口闪烁效果"""
        try:
            # 获取当前活动窗口并闪烁
            for _ in range(3):
                pyautogui.getActiveWindow().flash()
                time.sleep(0.3)
        except:
            pass
    
    def show_grade_update(self, update_info):
        """显示成绩更新通知"""
        title = "🎉 发现新成绩!"
        
        # 构建消息内容
        message = f"发现 {len(update_info['new_courses'])} 门课程的新成绩!\n\n"
        message += f"更新时间: {update_info['new_update_time']}\n"
        message += f"上次更新: {update_info['old_update_time']}\n\n"
        
        message += "新成绩详情:\n"
        for i, course in enumerate(update_info['new_courses'], 1):
            message += f"{i}. {course['course_name']}: {course['score']} ({course['term']})\n"
        
        message += "\n点击确定查看详细信息..."
        
        self.show_notification(title, message)
    
    def stop(self):
        """停止通知器"""
        self.running = False
        if self.notification_thread:
            self.notification_thread.join(timeout=1)