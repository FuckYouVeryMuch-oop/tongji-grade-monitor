@echo off
cd /d "%~dp0"
echo =====================================
echo   Tongji Grade Monitor
echo =====================================
echo.
echo Running in foreground...
echo Close the window or press Ctrl+C to stop.
echo.
python main.py
echo.
pause
