# Tongji Grade Monitor

>同济大学成绩监控脚本，登录教务系统自动查询成绩更新并弹窗通知。

## 本项目不会上传任何的个人信息，只会在本地处理

## 功能

- 自动登录同济统一身份认证
- 定时查询成绩 API
- 发现新成绩时弹窗 + 声音提醒
- 成绩历史记录保存

## 使用方式

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置账号

复制 `config.json.example` 修改文件名为 `config.json`，填入你的学号和密码：

```json
{
  "username": "YOUR_STUDENT_ID",
  "password": "YOUR_PASSWORD"
}
```

### 3. 运行

```bash
python main.py
```

### 定时任务（Windows）

用任务计划程序（Task Scheduler）每日定时运行 `python main.py`，详情见 `docs/schedule-setup.md`。

## 日志

程序运行时会自动生成 monitor.log 日志文件，记录每次检查的详细信息。
遇到问题时可以先查看日志排查。
