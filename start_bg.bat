@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo =====================================
echo   Tongji Grade Monitor
echo   成绩监控 - 后台运行
echo =====================================
echo.
echo 正在启动，请稍候...
start /min "" "D:\_DevTools\Annaconda\pythonw.exe" main.py
echo.
echo ✅ 已启动！可通过以下方式确认运行状态：
echo    - 任务管理器查看 pythonw.exe 进程
echo    - 查看 monitor.log 日志文件
echo.
echo 窗口将在 3 秒后自动关闭...
ping -n 4 127.0.0.1 >nul
exit
