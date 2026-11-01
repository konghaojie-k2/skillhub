---
name: market-documents
description: 管理本地文档市场。用于列出、上传、预览、下载、删除文档。支持 PDF、Markdown、文本等多种格式。当用户需要查找、阅读文档时使用。
license: MIT
metadata:
  emoji: "📄"
  version: "1.0.0"
  author: "nanobot"
---

# Market Documents

## Overview

本地文档管理工具，支持文件存储、文本提取和全文搜索。

## 快速开始

```bash
cd C:\CODE\agent_simple_creator\backend
uv run python cli/main.py documents <command>
```

## 环境配置

确保环境变量已设置：

```bash
DATABASE_URL=sqlite+aiosqlite:///./agent_builder.db
ENCRYPTION_KEY=your-encryption-key
```

## 命令列表

### list - 列出文档

```bash
uv run python cli/main.py documents list --user-id <user_id> --project-id <project_id> --stage <stage> --category <category> --type <doc_type> --limit <number> --page <page>
```

选项：
- `--user-id`: 用户ID (default: "default")
- `--project-id`: 项目ID过滤
- `--stage`: 项目阶段 (planning/in_progress/completed)
- `--category`: 分类过滤
- `--type`: 文档类型
- `--limit`: 每页数量 (default: 50)
- `--page`: 页码 (default: 1)

### show - 查看文档详情

```bash
uv run python cli/main.py documents show <doc_id> --user-id <user_id>
```

返回文档详细信息，包括：
- 名称、描述、分类、标签
- 文件信息（大小、类型）
- 项目和阶段信息
- 内容预览（前1000字符）

### upload - 上传文档

```bash
uv run python cli/main.py documents upload <file_path> --name <name> --description <desc> --project-id <project_id> --stage <stage> --tags <tag1,tag2> --user-id <user_id>
```

自动：
- 提取 PDF 文本内容（用于搜索）
- 保存原始文件
- 存储提取的文本为 .txt 文件

### download - 下载文档

```bash
uv run python cli/main.py documents download <doc_id> --output <path> --user-id <user_id>
```

下载文档原始文件。

### preview - 预览文档内容

```bash
uv run python cli/main.py documents preview <doc_id> --max-size <number> --user-id <user_id>
```

预览文档内容（文本文件或提取的 PDF 文本）。

### delete - 删除文档

```bash
uv run python cli/main.py documents delete <doc_id> --user-id <user_id>
```

## 搜索策略（重要）

当需要搜索文档时，Agent 应使用以下方式：

### 场景 1：按条件筛选
```bash
# 按项目筛选
uv run python cli/main.py documents list --project-id <project_id>

# 按阶段筛选
uv run python cli/main.py documents list --stage in_progress

# 按分类/标签筛选
uv run python cli/main.py documents list --category 技术文档
```

### 场景 2：全文搜索（使用 grep）

文档上传时会自动提取文本并保存为 .txt 文件，可使用 grep 搜索：

```bash
# 在所有文档中搜索关键词
grep -ri "项目目标" ~/.nanobot/workspace/market/documents/

# 搜索多个关键词
grep -li "SOW\|工作说明书" ~/.nanobot/workspace/market/documents/
```

grep 选项：
- `-i`: 忽略大小写
- `-r`: 递归搜索
- `-l`: 只显示文件名
- `-n`: 显示行号

### 场景 3：获取详细内容
找到相关文档后，使用 show 查看详情：
```bash
uv run python cli/main.py documents show <doc_id>
```

## 数据存储位置

- 原始文件：`~/.nanobot/workspace/market/documents/<year-month>/<doc_id>/`
- 文本提取：`~/.nanobot/workspace/market/documents/<year-month>/<doc_id>/<doc_id>.txt`
- 数据库：SQLite（agent_builder.db）

## 示例

```bash
# 列出所有文档
uv run python cli/main.py documents list

# 上传 PDF 文档
uv run python cli/main.py documents upload合同.pdf --name "技术协议" --project-id "项目A"

# 搜索包含"验收标准"的文档
grep -ri "验收标准" ~/.nanobot/workspace/market/documents/

# 预览文档内容
uv run python cli/main.py documents preview doc-123
```