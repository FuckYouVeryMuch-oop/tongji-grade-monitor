# Schedule Setup Guide

## Windows Task Scheduler

Create a daily task to run the monitor automatically:

1. Open **Task Scheduler**
2. Click **Create Task**
3. **General** tab: Name = "TongjiGradeMonitor", check "Run whether user is logged on or not"
4. **Triggers** tab: New → Daily, start at desired time, repeat every 5 hours
5. **Actions** tab: New → Start a program
   - Program: `path\to\python.exe`
   - Arguments: `path\to\main.py`
6. Click OK and enter your Windows password if prompted

## Linux / macOS (cron)

```bash
crontab -e
# Run every 5 hours
0 */5 * * * cd /path/to/project && python main.py
```
