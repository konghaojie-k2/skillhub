<h1 align="center">🌅 daily-reflection</h1>

<p align="center">
  <strong>代码日志与项目规划助手 —— 让每一次会话都有迹可循</strong>
</p>

<p align="center">
  <a href="#-快速开始"><img src="https://img.shields.io/badge/快速开始-3_分钟-blue?style=for-the-badge" alt="Quick Start"></a>
  <a href="#-核心功能"><img src="https://img.shields.io/badge/功能-7+-purple?style=for-the-badge" alt="Features"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/开源协议-MIT-yellow?style=for-the-badge" alt="License"></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Claude_Code-skill?logo=claude&logoColor=white&color=cc785c" alt="Claude Code">
  <img src="https://img.shields.io/badge/Git_联动-daily--git--check-green?logo=git" alt="Git">
  <img src="https://img.shields.io/badge/跨会话同步-json-blue?logo=json" alt="JSON">
</p>

**daily-reflection** 是一个 Claude Code Skill，借鉴"吾日三省吾身"的理念，帮助你把每天的代码活动和项目状态关联起来。通过 `.daily_reflection/context-sync.json` 实现跨会话状态同步，让计划、执行与复盘形成闭环。

---

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| 🌅 **早省** | 会话开始时读取状态、生成今日计划、处理 inbox |
| 📝 **中省** | 实时记录关键文件变更，更新 `recent_changes` |
| 🌙 **晚省** | 会话结束时同步状态、归档发现、检查待办 |
| 🔄 **状态同步** | 通过 `context-sync.json` 持久化进度、待办、活跃陷阱 |
| 📋 **决策记录** | 自动/手动记录技术决策，区分活跃区与归档区 |
| 📥 **Inbox 处理** | 临时输入池，提取关键信息后自动清理 |
| 🐛 **错误捕捉** | 记录反复出现的陷阱，避免在同一个坑里绊倒两次 |

---

## 🤔 为什么需要这个项目？

在使用 Claude Code 进行多轮、跨会话开发时，常常会遇到这些问题：

- 🌀 **上下文丢失**：新会话不知道昨天做到哪里、接下来该做什么
- 📝 **计划与执行脱节**：有计划没记录，有执行没复盘
- 🐛 **重复踩坑**：同一个错误在不同会话中反复出现
- 📦 **决策遗忘**：重要的技术决策散落在聊天记录里，难以追溯

daily-reflection 通过结构化的本地文件（`context-sync.json`、`decisions.md`、`daily-status.md`）把项目状态沉淀下来，让 Claude 每次进入项目都能"接上上次的话"。

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────┐
│   早省      │ ──▶ │   执行 / 中省   │ ──▶ │   晚省      │
│ 读取计划    │     │ 记录关键变更    │     │ 同步 + 归档 │
└─────────────┘     └─────────────────┘     └─────────────┘
         ▲                                          │
         └──────────── context-sync.json ◀──────────┘
```

---

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/konghaojie-k2/daily-reflection-skill.git
cd daily-reflection-skill

# 将 skill 放到 Claude Code skills 目录
# Windows
Copy-Item -Recurse . "$env:USERPROFILE\.claude\skills\daily-reflection"

# macOS / Linux
cp -r . ~/.claude/skills/daily-reflection
```

### 项目初始化（可选）

首次触发"早省"或"状态同步"时，Agent 会自动检查并创建 `.daily_reflection/` 目录结构，无需手动操作。

如果你希望提前创建，可在目标项目根目录执行：

```powershell
New-Item -ItemType Directory -Force -Path .daily_reflection
New-Item -ItemType Directory -Force -Path .daily_reflection/inbox
New-Item -ItemType Directory -Force -Path .daily_reflection/archive
New-Item -ItemType File -Force -Path .daily_reflection/daily-status.md
New-Item -ItemType File -Force -Path .daily_reflection/context-sync.json
New-Item -ItemType File -Force -Path .daily_reflection/decisions.md
New-Item -ItemType File -Force -Path .daily_reflection/archive/findings-history.md
New-Item -ItemType File -Force -Path .daily_reflection/archive/tasks-history.md
```

### 基础用法

1. 早上打开项目，说：**"早省"** 或 **"做计划"**
2. 开发过程中，说：**"记录一下"** 或 **"中省"**
3. 结束工作时，说：**"晚省"** 或 **"今日结束"**

---

## 🎯 功能特性

### 与 daily-git-check 联动

早省时会自动检查：

```bash
git status
git fetch --all
git log HEAD..origin/<branch> --oneline
```

让你在进入开发前清楚本地与远程的差异。

### 结构化状态文件

**context-sync.json** —— 项目状态快照：

```json
{
  "last_session": "2026-05-11T13:05",
  "phase": "Phase 3/4",
  "progress": "95%",
  "pending_tasks": [
    {"id": "T-032", "title": "任务描述", "priority": "medium"}
  ],
  "active_findings": ["最多8条活跃陷阱"],
  "recent_changes": ["最近修改的关键文件，最多5个"],
  "next_focus": "下次建议的一句话"
}
```

### 决策知识库

`decisions.md` 区分活跃区与归档区：

- **活跃**：仍影响当前代码行为的决策
- **已执行完毕**：决策已落地，后续代码不再受约束
- **已推翻**：之前采纳，后发现不合适而撤销

### 智能归档

| 内容 | 上限 | 处理方式 |
|------|------|----------|
| `active_findings` | 8 条 | 超出后归档最老的 3 条 |
| decisions 活跃区 | 8 条 | 超出后归档最老的 3 条 |
| inbox 文件 | 7 天 | 超过 7 天未处理视为 stale |

---

## 🗺️ 开发路线

| 阶段 | 内容 | 状态 |
|------|------|------|
| **Phase 1** | 核心三省流程（早省/中省/晚省） | ✅ 已完成 |
| **Phase 2** | 与 daily-git-check 深度联动 | ✅ 已完成 |
| **Phase 3** | 重大变更自动触发决策记录 | ✅ 已完成 |
| **Phase 4** | 多项目状态聚合视图 | 📋 计划中 |

---

## 📦 技术栈

- **Skill 平台**: Claude Code
- **状态存储**: JSON + Markdown
- **脚本语言**: PowerShell（初始化脚本）
- **版本控制**: Git（联动 daily-git-check）
- **时间获取**: `get-current-time` skill 或 PowerShell 降级

---

## 📄 开源协议

MIT License

---

<div align="center">

**daily-reflection** — *吾日三省吾身，代码亦有痕*

</div>
