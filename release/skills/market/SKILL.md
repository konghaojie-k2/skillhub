---
name: market
description: 本地市场服务 CLI，用于管理数据集、文档、技能和实验。当用户需要查找、分析、管理任何市场资源时使用。支持无服务器的本地 CLI 管理。
license: MIT
metadata:
  emoji: "🏪"
  version: "1.0.0"
  author: "nanobot"
---

# Market Service CLI

## Overview

统一的市场服务 CLI，管理四类资源：
- **Datasets**: CSV、JSON、Parquet 数据，包含质量分析
- **Documents**: 文档管理，支持 PDF、Markdown、文本
- **Skills**: Agent 技能，支持数据库和文件系统预置技能
- **Experiments**: 实验记录，包含目标、结果和经验教训

## 存储位置

所有资源存储在：`~/.nanobot/workspace/market/`

```
market/
├── documents/          # 文档文件（含提取的 .txt 文本）
│   └── 2026-03/
└── experiments/        # 实验记录
    └── 2026-03/
```

数据库位置：`~/.nanobot/agent_builder.db`

## 快速开始

```bash
cd C:\CODE\agent_simple_creator\backend
uv run python cli/main.py <command-group> <command>
```

或全局安装：

```bash
cd C:\CODE\agent_simple_creator\backend
uv tool install -e .

# 直接使用：
market datasets list
market documents list
market skills list
```

## 命令组

### 1. Datasets（数据集）

```bash
# 列出数据集
uv run python cli/main.py datasets list --user-id <id> --type <csv|json|parquet> --category <cat> --limit <n>

# 获取数据集详情
uv run python cli/main.py datasets get <dataset_id> --user-id <id>

# 上传数据集
uv run python cli/main.py datasets upload <file_path> --name <name> --description <desc> --category <cat> --tags <tags>

# 分析数据集
uv run python cli/main.py datasets analyze <dataset_id> --user-id <id> --sample-size <n>

# 删除数据集
uv run python cli/main.py datasets delete <dataset_id> --user-id <id>
```

### 2. Documents（文档）

```bash
# 列出文档
uv run python cli/main.py documents list --user-id <id> --project-id <project_id> --stage <stage> --category <cat> --limit <n> --page <p>

# 查看文档详情
uv run python cli/main.py documents show <doc_id> --user-id <id>

# 上传文档
uv run python cli/main.py documents upload <file_path> --name <name> --description <desc> --project-id <project_id> --stage <stage>

# 下载文档
uv run python cli/main.py documents download <doc_id> --output <path> --user-id <id>

# 预览文档
uv run python cli/main.py documents preview <doc_id> --user-id <id>

# 删除文档
uv run python cli/main.py documents delete <doc_id> --user-id <id>
```

### 3. Skills（技能）

```bash
# 列出技能
uv run python cli/main.py skills list --user-id <id> --category <cat> --limit <n>

# 获取技能详情
uv run python cli/main.py skills get <skill_id> --user-id <id>

# 列出文件系统预置技能
uv run python cli/main.py skills filesystem

# 下载技能
uv run python cli/main.py skills download <skill_id> --output <path> --user-id <id>

# 删除技能
uv run python cli/main.py skills delete <skill_id> --user-id <id>
```

### 4. Experiments（实验）

```bash
# 列出实验
uv run python cli/main.py experiments list --limit <n>

# 创建实验
uv run python cli/main.py experiments create --name <name> --goal <goal>

# 获取实验详情
uv run python cli/main.py experiments get <exp_id>

# 添加结果
uv run python cli/main.py experiments result <exp_id> --content "<content>"

# 删除实验
uv run python cli/main.py experiments delete <exp_id>
```

## 搜索策略（重要）

当需要搜索资源时，请参考各子技能的 SKILL.md：

- **market-datasets**: 搜索数据集元数据和分析结果
- **market-documents**: 使用 grep 全文搜索
- **market-skills**: 列出并筛选预置技能

### 搜索文档示例

```bash
# 方法 1：按条件筛选
uv run python cli/main.py documents list --project-id <project_id> --stage in_progress

# 方法 2：使用 grep 全文搜索（推荐）
grep -ri "关键词" ~/.nanobot/workspace/market/documents/
grep -li "SOW\|工作说明书" ~/.nanobot/workspace/market/documents/
```

### 搜索数据集示例

```bash
# 列出所有数据集
uv run python cli/main.py datasets list

# 获取分析结果（含 quality_score, column_semantics）
uv run python cli/main.py datasets get <dataset_id>
# extra_metadata 字段包含：
#   - quality_score.overall_score
#   - column_semantics
#   - data_understanding
```

## 子技能

详细命令和搜索策略请参考：
- `~/.nanobot/workspace/skills/market-datasets/SKILL.md`
- `~/.nanobot/workspace/skills/market-documents/SKILL.md`
- `~/.nanobot/workspace/skills/market-skills/SKILL.md`
- `~/.nanobot/workspace/skills/market-experiments/SKILL.md`

## 示例

```bash
# 列出所有资源
uv run python cli/main.py datasets list
uv run python cli/main.py documents list
uv run python cli/main.py skills list

# 上传并分析数据集
uv run python cli/main.py datasets upload sales.csv --name "销售数据"
uv run python cli/main.py datasets analyze <dataset_id>

# 搜索文档
grep -ri "验收标准" ~/.nanobot/workspace/market/documents/

# 查看预置技能
uv run python cli/main.py skills filesystem
```