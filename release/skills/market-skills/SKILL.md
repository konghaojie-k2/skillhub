---
name: market-skills
description: 管理本地技能市场。用于列出、查看、下载、删除技能。支持数据库技能和文件系统预置技能。当用户需要查找、使用技能时使用。
license: MIT
metadata:
  emoji: "🛠️"
  version: "1.0.0"
  author: "nanobot"
---

# Market Skills

## Overview

本地技能管理工具，支持自定义技能和预置技能。

## 快速开始

```bash
cd C:\CODE\agent_simple_creator\backend
uv run python cli/main.py skills <command>
```

## 环境配置

确保环境变量已设置：

```bash
DATABASE_URL=sqlite+aiosqlite:///./agent_builder.db
ENCRYPTION_KEY=your-encryption-key
```

## 命令列表

### list - 列出技能

```bash
uv run python cli/main.py skills list --user-id <user_id> --category <category> --status <status> --sort <newest|popular|rating> --limit <number>
```

选项：
- `--user-id`: 用户ID (default: "default")
- `--category`: 分类过滤
- `--status`: 状态过滤 (pending/approved/rejected)
- `--sort`: 排序方式 (newest/popular/rating)
- `--limit`: 返回数量限制 (default: 50)

### get - 获取技能详情

```bash
uv run python cli/main.py skills get <skill_id> --user-id <user_id>
```

返回技能详细信息，包括：
- 名称、描述、分类、标签
- 内容（prompt/template）
- 参数 schema
- 统计数据（评分、下载次数）

### filesystem - 列出文件系统预置技能

```bash
uv run python cli/main.py skills filesystem
```

列出 `~/.nanobot/workspace/market/skills/public/` 目录下的预置技能。

返回：
- 技能名称
- 描述
- 分类
- 文件夹路径

### download - 下载技能内容

```bash
uv run python cli/main.py skills download <skill_id> --output <path> --user-id <user_id>
```

下载技能内容到文件。

### delete - 删除技能

```bash
uv run python cli/main.py skills delete <skill_id> --user-id <user_id>
```

## 搜索策略（重要）

当需要搜索技能时，Agent 应使用以下方式：

### 场景 1：列出并筛选
```bash
# 列出所有技能
uv run python cli/main.py skills list

# 按分类筛选
uv run python cli/main.py skills list --category tool
```

### 场景 2：查看预置技能
```bash
# 列出文件系统中的预置技能
uv run python cli/main.py skills filesystem
```

返回预置技能的名称、描述、分类，可直接使用。

### 场景 3：获取技能详情
找到目标技能后，查看详细内容：
```bash
uv run python cli/main.py skills get <skill_id>
```

返回技能的内容（prompt）、参数 schema 等。

## 数据存储位置

- 数据库技能：`~/.nanobot/workspace/market/skills/database/`
- 预置技能：`~/.nanobot/workspace/market/skills/public/`
- 数据库：SQLite（agent_builder.db）

## 示例

```bash
# 列出所有技能
uv run python cli/main.py skills list

# 查看预置技能
uv run python cli/main.py skills filesystem

# 获取技能详情
uv run python cli/main.py skills get skill-123

# 下载技能内容
uv run python cli/main.py skills download skill-123 --output ./my-skill.md
```