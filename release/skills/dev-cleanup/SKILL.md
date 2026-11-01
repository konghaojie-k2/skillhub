---
name: dev-cleanup
description: 清理 Windows 开发环境中被占用的后台进程与端口，并处理 Next.js dev lock 文件残留。当用户遇到"端口被占用"、"启动失败"、"需要杀掉前后端进程"或"清理开发环境"时使用。
---

# Dev Cleanup

## Overview

提供一键清理开发环境后台进程的能力。主要解决 Windows 下 Git Bash / CMD 中杀进程繁琐、Next.js lock 文件残留导致无法重启等问题。

## Quick Start

运行 bundled 脚本清理默认端口（3000、8000）及 Next.js lock：

```bash
# 在项目根目录执行
python C:/Users/17625/.claude/skills/dev-cleanup/scripts/cleanup_ports.py
```

## Usage

### 清理默认端口
脚本默认会检查并强制终止占用 **3000**（前端）和 **8000**（后端）端口的进程：

```bash
python scripts/cleanup_ports.py
```

### 清理指定端口
传入自定义端口列表：

```bash
python scripts/cleanup_ports.py --ports 3001 8080 5000
```

### 指定项目根目录清理 lock
如果 `frontend/.next/dev/lock` 不在当前目录，可指定项目根目录：

```bash
python scripts/cleanup_ports.py --project-root C:/path/to/project
```

## How It Works

1. 对每个目标端口调用 `netstat -ano` 查找监听状态的 PID。
2. 使用 `taskkill /F /PID <pid>` 强制终止进程。
3. 删除 `frontend/.next/dev/lock`（如果存在），避免 Next.js 提示 `Unable to acquire lock`。

## Notes

- 该脚本仅在 **Windows** 环境下有效（依赖 `netstat` + `taskkill`）。
- 如果 `npx kill-port` 可用，也可作为更快捷的替代方案：`npx kill-port 3000 8000`。
- 清理后建议重新启动前后端服务。
