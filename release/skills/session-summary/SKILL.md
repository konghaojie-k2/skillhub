---
name: session-summary
description: Project Harness 的会话总结工具。生成当前对话的摘要，保存到 .project/memory/session-summaries/，并同步更新 project-state.json 和 user-contexts。当用户说"总结一下"、"记录会话"、"session summary"时触发。
---

# session-summary - Project Harness 会话总结

## 核心理念

把一次对话的产出快速沉淀到 Harness 中，不丢失上下文，不重复沟通。

## 触发条件

用户说以下任意触发词：
- "总结一下"
- "记录会话"
- "session summary"
- "生成 summary"

此外，当 agent-checklist.md Step 6B（上下文压缩时自动触发）激活时，也执行本流程。

## 执行流程

### 步骤 1：读取 Harness 状态

- [ ] 读取 `.project/project-state.json`
- [ ] 读取 `.project/user-contexts/index.json` 识别当前用户
- [ ] 读取对应的 `.project/user-contexts/{username}.json`

### 步骤 2：回顾对话内容

提取本次会话的关键信息：
- 创建/更新了哪些线程（T-XXX）
- 做出了什么技术决策
- 用户有什么待确认事项
- 完成了什么代码修改/文件变更

### 步骤 3：生成 Summary 文件

创建 `.project/memory/session-summaries/YYYY-MM-DD_HH-MM.md`：

```markdown
# Session Summary: YYYY-MM-DD HH:MM

## Metadata
- user: {username}
- threads_touched: [T-XXX, T-YYY]

## What Happened
- 要点 1
- 要点 2

## Outcomes
- [x] 已完成项
- [ ] 待办项（状态）

## Next Session Hints
- 给未来 Agent 的上下文提示
```

**约束**：
- 不超过 30 行
- 文件名格式：`YYYY-MM-DD_HH-MM.md`，冲突时加 `-2`、`-3`
- 无需用户确认，直接生成

### 步骤 4：同步更新 Harness 状态

1. **更新 `project-state.json`**：
   - 更新 `last_update` 为当前日期

2. **更新 `user-contexts/{username}.json` 的 `recent_sessions`**：
   - 追加新条目：
     ```json
     {
       "date": "YYYY-MM-DD",
       "summary_file": "memory/session-summaries/YYYY-MM-DD_HH-MM.md",
       "threads_touched": ["T-XXX"],
       "key_decisions": [],
       "pending_for_user": []
     }
     ```
   - 保留最近 10 条，超出时移除最旧的

### 步骤 5：向用户汇报

```text
✅ 会话总结已保存到 .project/memory/session-summaries/YYYY-MM-DD_HH-MM.md

本次会话涉及线程：[T-XXX, T-YYY]
已同步更新到 harness 状态。
```

## 与 daily-reflection 的区别

| | session-summary | daily-reflection |
|---|---|---|
| 数据位置 | `.project/memory/session-summaries/`（与 harness 统一） | `.daily_reflection/`（独立目录） |
| 触发方式 | 用户主动说"总结一下" 或 上下文压缩时自动 | 早省/中省/晚省时间驱动 |
| 输出内容 | 对话摘要 + harness 状态同步 | 代码日志 + 计划追踪 |
| 依赖 | project-state.json、user-contexts | task_plan.md、progress.md |

## 注意事项

- 本 skill **不生成 task_plan.md、progress.md**，那是 planning-with-files 的职责
- 本 skill **不做 git 检查、stash 提醒**，那是 daily-git-check 的职责
- 本 skill 只做一件事：把当前对话的产出快速写入 harness
