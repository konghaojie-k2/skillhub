---
name: get-current-time
description: 获取当前时间。用于回答关于当前时间、日期的问题。
---

# Get Current Time

使用系统命令获取当前时间：

**Windows:**
```bash
powershell -Command "Get-Date -Format 'yyyy-MM-dd HH:mm:ss'"
```

**Unix/Linux/Mac:**
```bash
date '+%Y-%m-%d %H:%M:%S'
```

返回格式：`YYYY-MM-DD HH:MM:SS`
