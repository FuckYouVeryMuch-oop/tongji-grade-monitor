@echo off
cd /d "%~dp0"

tasklist /fi "imagename eq pythonw.exe" 2>nul | find /i "pythonw.exe" >nul
if %errorlevel%==0 (
    echo =====================================
    echo   Tongji Grade Monitor
    echo =====================================
    echo.
    echo Already running! Check task manager.
    echo See monitor.log for details.
    echo.
    echo This window will close in 10 seconds...
    ping -n 11 127.0.0.1 >nul
    exit
)

echo =====================================
echo   Tongji Grade Monitor
echo =====================================
echo.
echo Starting background monitor...
start /min "" pythonw main.py
echo.
echo Started! Check task manager for pythonw.exe
echo See monitor.log for details.
echo.
echo This window will close in 10 seconds...
ping -n 11 127.0.0.1 >nul
exit