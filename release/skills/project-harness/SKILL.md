---
name: project-harness
description: Project Harness - AI-Agent 协作项目管理框架。用于：(1) 初始化新项目的 harness 目录结构，建立 AI 与人类的共享记忆系统；(2) Agent 进入项目时执行自检，主动汇报项目状态；(3) 管理项目状态、用户上下文、决策记录、inbox 工作流；(4) 量化评估迭代优化。当用户需要初始化新项目、建立 AI 协作工作区、或希望 Agent 具备项目状态感知能力时使用此 skill。TRIGGER：用户说"初始化项目"、"创建 harness"、"新项目设置"、"建立 AI 协作框架"、"使用 harness 理念运营项目"。
---

# Project Harness

AI-Agent 协作项目管理框架。通过文件系统建立共享记忆，让 Agent 每次进入都能"理解"项目状态。

## 核心概念

- **Harness**：文件系统即共享记忆，关键信息持久化，跨对话保持上下文
- **自检机制**：Agent 进入时主动检查状态，无需人类重复介绍
- **提议后确认**：写入操作先提议，人类确认后执行
- **AutoResearch**：量化评估迭代，自动优化直至达到目标

## 快速开始

### 初始化新项目

```bash
cd {skill-path}
uv run scripts/init_project.py --name "项目名称" --path ./项目目录 --description "项目描述"
```

这会创建完整的 harness 目录结构：
- `.project/` - AI 运行时与共享状态
- `00-meta/` - 跨阶段知识（术语表、决策记录）
- `90-inbox/` - 待处理输入
- `99-archive/` - 归档文档

### Agent 自检流程

每次对话开始时，Agent 应执行自检：

1. 检查 `.project/bootstrap.md`（初始化开关）
2. 读取 `.project/project-state.json`（全局状态）
3. 识别用户，读取 `.project/user-contexts/{username}.json`
4. 扫描 `90-inbox/`（待处理文件）
5. 检查活跃线程状态
6. 主动汇报项目状态

详见 [workflow-guide.md](workflow-guide.md)。

## 目录结构

**框架层（通用）**：

```
.project/
├── project-state.json      # 全局项目状态（快速加载器）
├── bootstrap.md            # 初始化开关（一次性，完成后删除）
├── agent-checklist.md      # Agent 自检清单
├── user-contexts/
│   ├── index.json          # 用户注册表
│   ├── _template.json      # 模板
│   └── {username}.json     # 个人上下文文件
└── memory/
    ├── decision-log.md     # 决策日志
    ├── feedback-log.md     # 反馈日志
    └── session-summaries/  # 会话总结

00-meta/
├── glossary.md             # 术语表
├── stakeholders.md         # 关键人员
└── decisions/              # ADR（架构决策记录）

90-inbox/                   # 待处理输入
99-archive/                 # 归档文档
```

**项目层（可扩展）**：

项目可在框架基础上添加阶段目录、研究目录、附件库等。具体结构由项目 `CLAUDE.md` 定义。

常见扩展模式：
```
10-presales/                # 售前阶段（可选）
20-implementation/          # 实施阶段（可选）
30-operations/              # 运维阶段（可选）
40-studies/                 # 研究与学习笔记（可选）
50-attachments/             # 附件与素材库（可选）
```

**设计原则**：框架提供 `.project/` + `00-meta/` + `90-inbox/` + `99-archive/` 的通用骨架，项目根据自身生命周期添加业务目录。

## 核心能力

### 1. 项目初始化 Wizard

使用 `scripts/init_project.py` 创建 harness 结构，或手动从模板复制文件。

模板位于 `assets/templates/`：
- `project_state_template.json`
- `user_context_template.json`
- `agent_checklist_template.md`
- `bootstrap_template.md`

### 2. Agent 自检清单

`.project/agent-checklist.md` 定义 Agent 进入项目时的行为：
- 加载上下文
- 扫描 inbox
- 检查变更
- 检查线程
- 主动汇报

### 3. 项目状态管理

`.project/project-state.json` 包含：
- 项目名称、当前阶段
- 活跃线程（正在进行的工作）
- 待决策事项
- inbox 状态

### 4. 用户上下文管理

`.project/user-contexts/{username}.json` 记录：
- 用户身份信息
- 沟通风格偏好
- 关注的线程列表
- 最近会话摘要

### 5. 决策记录

ADR (Architecture Decision Record) 存放在 `00-meta/decisions/`：
- 背景
- 考虑的选项
- 决策结果
- 理由
- 后果

### 6. Inbox 工作流

人类将原始材料放入 `90-inbox/`，Agent 发现后：
- 分析内容
- 提议归档位置
- 人类确认后移动

### 7. 量化评估迭代

`scripts/autoresearch.py` 提供：
- 评估函数定义
- 目标分数设置
- 自动迭代优化
- 回滚机制

```python
from autoresearch import AutoResearch

ar = AutoResearch(
    evaluate_func=evaluate,
    target_score=100,
    max_iterations=50,
    backup_files=['target.md'],
    experiment_func=experiment
)

results = ar.run()
```

## 行为模式

### 模式 A：提议后确认（写入操作）

对于更新状态、创建 ADR 等写入操作，**必须先提议，经人类确认后再执行**。

### 模式 B：自动执行（读取操作）

对于读取操作、个人上下文更新，可直接执行。

## 详细参考

- [harness-design.md](harness-design.md) - Harness 设计原理
- [workflow-guide.md](workflow-guide.md) - 工作流指南

## Scripts

| 脚本 | 功能 |
|------|------|
| `init_project.py` | 初始化项目 harness 结构 |
| `autoresearch.py` | 量化评估迭代框架 |

## Assets

| 模板 | 用途 |
|------|------|
| `project_state_template.json` | 项目状态文件模板 |
| `user_context_template.json` | 用户上下文模板 |
| `user_context_index.json` | 用户注册表模板 |
| `agent_checklist_template.md` | Agent 自检清单模板 |
| `bootstrap_template.md` | 初始化向导模板 |
| `glossary_template.md` | 术语表模板 |
| `stakeholders_template.md` | 关键人员模板 |