---
name: market-experiments
description: 管理本地实验。用于创建实验、记录结果、沉淀经验教训。当用户需要记录实验过程、分析结果、总结经验时使用。
license: MIT
metadata:
  emoji: "🧪"
  version: "1.0.0"
  author: "nanobot"
---

# Market Experiments

## Overview

本地实验管理工具，支持实验记录、结果存储和经验沉淀。

## 快速开始

```bash
cd C:\CODE\agent_simple_creator\backend
uv run python cli/main.py experiments <command>
```

## 环境配置

确保环境变量已设置：

```bash
DATABASE_URL=sqlite+aiosqlite:///./agent_builder.db
ENCRYPTION_KEY=your-encryption-key
```

## 命令列表

### list - 列出实验

```bash
uv run python cli/main.py experiments list --limit <number>
```

选项：
- `--limit`: 返回数量限制 (default: 50)

返回实验列表，包含：
- 实验ID
- 实验名称
- 目标
- 状态（pending/running/success/failed）
- 创建时间

### create - 创建实验

```bash
uv run python cli/main.py experiments create --name <name> --goal <goal>
```

选项：
- `--name` (required): 实验名称
- `--goal`: 实验目标/目的

创建实验后会生成实验目录用于存储结果。

### get - 获取实验详情

```bash
uv run python cli/main.py experiments get <exp_id>
```

返回实验详细信息，包括：
- 实验名称和目标
- 当前状态
- 创建时间
- 引用的数据集、文档、技能
- 结果文件列表

### lessons - 经验教训

```bash
uv run python cli/main.py experiments lessons <exp_id>
```

编辑实验的经验教训记录（使用默认编辑器打开 markdown 文件）。

记录内容包括：
- 成功经验
- 失败教训
- 改进建议

### result - 添加结果

```bash
uv run python cli/main.py experiments result <exp_id> <filename> --content "<content>"
```

选项：
- `--content`: 结果内容（文本）
- 不带 --content 时打开默认编辑器

结果文件保存在实验目录的 results/ 子目录。

### delete - 删除实验

```bash
uv run python cli/main.py experiments delete <exp_id>
```

删除实验及其所有结果文件。

## 数据存储位置

- 实验目录：`~/.nanobot/workspace/market/experiments/<year-month>/<exp_id>/`
- 目录结构：
  ```
  <exp_id>/
  ├── metadata.json      # 实验元数据
  ├── results/            # 结果文件
  │   └── *.json
  └── lessons.md         # 经验教训
  ```

## 实验流程

### 1. 创建实验
```bash
uv run python cli/main.py experiments create --name "测试新算法" --goal "验证准确率"
```

### 2. 执行实验并记录结果
```bash
# 添加结果文件
uv run python cli/main.py experiments result <exp_id> accuracy.json --content '{"accuracy": 0.95}'

# 或使用默认编辑器
uv run python cli/main.py experiments result <exp_id> summary.md
```

### 3. 总结经验教训
```bash
uv run python cli/main.py experiments lessons <exp_id>
```

记录：
- 成功点
- 问题
- 改进方向

### 4. 查看历史
```bash
uv run python cli/main.py experiments list
uv run python cli/main.py experiments get <exp_id>
```

## 示例

```bash
# 列出所有实验
uv run python cli/main.py experiments list

# 创建新实验
uv run python cli/main.py experiments create --name "LangChain测试" --goal "测试RAG效果"

# 添加结果
uv run python cli/main.py experiments result exp-xxx evaluation.json --content '{"precision": 0.9}'

# 记录经验
uv run python cli/main.py experiments lessons exp-xxx

# 查看实验
uv run python cli/main.py experiments get exp-xxx
```