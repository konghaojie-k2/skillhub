---
name: market-datasets
description: 管理本地数据集市场。用于列出、上传、分析、删除数据集。支持 CSV、JSON、Parquet 格式，包含质量分析和元数据提取。当用户需要查找、分析数据集时使用。
license: MIT
metadata:
  emoji: "📊"
  version: "1.0.0"
  author: "nanobot"
---

# Market Datasets

## Overview

本地数据集管理工具，支持结构化数据存储、质量分析和元数据管理。

## 快速开始

```bash
cd C:\CODE\agent_simple_creator\backend
uv run python cli/main.py datasets <command>
```

## 环境配置

确保环境变量已设置：

```bash
DATABASE_URL=sqlite+aiosqlite:///./agent_builder.db
ENCRYPTION_KEY=your-encryption-key
LLM_API_KEY=your-deepseek-api-key
```

## 命令列表

### list - 列出数据集

```bash
uv run python cli/main.py datasets list --user-id <user_id> --type <csv|json|parquet> --category <category> --limit <number>
```

选项：
- `--user-id`: 用户ID (default: "default")
- `--type`: 数据集类型过滤 (csv, json, parquet)
- `--category`: 分类过滤
- `--limit`: 返回数量限制 (default: 50)

### get - 获取数据集详情

```bash
uv run python cli/main.py datasets get <dataset_id> --user-id <user_id>
```

返回数据集详细信息，包括：
- 名称、描述、分类、标签
- 行数、数据类型
- Schema（列信息）
- 分析结果（quality_score, column_semantics 等）

### upload - 上传数据集

```bash
uv run python cli/main.py datasets upload <file_path> --name <name> --description <desc> --category <cat> --tags <tag1,tag2> --user-id <user_id>
```

自动识别文件类型（csv/json/parquet），提取 schema 和行数。

### analyze - 分析数据集

```bash
uv run python cli/main.py datasets analyze <dataset_id> --user-id <user_id> --sample-size <number>
```

返回数据集的详细分析：
- 基础统计（行数、列数、内存占用）
- 列语义（每列的含义和类型）
- 数据分布
- 质量分数
- 数据理解（LLM 生成）

### delete - 删除数据集

```bash
uv run python cli/main.py datasets delete <dataset_id> --user-id <user_id>
```

## 搜索策略（重要）

当需要搜索数据集时，Agent 应组合使用以下命令：

### 场景 1：按分类/标签筛选
```bash
# 列出特定分类的数据集
uv run python cli/main.py datasets list --category 销售

# 列出包含特定标签的数据集
uv run python cli/main.py datasets list --type csv
```

### 场景 2：查看分析结果（搜索元数据）
```bash
# 先列出数据集
uv run python cli/main.py datasets list

# 查看某个数据集的分析结果
uv run python cli/main.py datasets get <dataset_id>
# 返回的 extra_metadata 包含：
#   - quality_score.overall_score（质量分数）
#   - column_semantics（列语义，如"销售金额"、"客户名称"）
#   - data_understanding（数据理解）
#   - quick_summary（快速摘要）
```

### 场景 3：语义搜索意图转换
对于 "质量高的数据集"、"销售相关数据" 等意图：
1. 先 list 列出数据集
2. 对候选数据集执行 get 获取分析结果
3. 根据 extra_metadata 中的 quality_score、column_semantics 等判断是否匹配

## 数据存储位置

- 数据文件：`~/.nanobot/workspace/market/data/<year-month>/<dataset_id>/`
- 数据库：SQLite（agent_builder.db）

## 示例

```bash
# 列出所有数据集
uv run python cli/main.py datasets list

# 上传 CSV 数据集
uv run python cli/main.py datasets upload data.csv --name "销售数据" --category "财务"

# 分析数据集
uv run python cli/main.py datasets analyze dataset-123

# 查看质量分数
uv run python cli/main.py datasets get dataset-123
```