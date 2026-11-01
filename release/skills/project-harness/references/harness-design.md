# Harness 设计原理

## 核心理念

Project Harness 是"文件系统即共享记忆"的实现，让 AI Agent 和人类协作者通过读写结构化文档来对齐上下文，而非依赖对话记忆。

## 为什么需要 Harness？

### 问题：对话记忆不可靠

- 每次新对话，Agent 从零开始，丢失之前的工作上下文
- 人类需要反复解释项目背景、技术决策、约束条件
- 多人协作时，信息在不同对话间割裂

### 解决方案：Harness 作为共享记忆

- **文件系统持久化**：关键信息写入文件，下次对话仍可读取
- **结构化组织**：按目录分类（状态、决策、用户、素材），Agent 知道去哪找信息
- **自检机制**：Agent 进入时主动检查状态，无需人类重复介绍

## Harness 目录结构

```
.project/                # AI 运行时与共享状态
├── project-state.json   # 全局项目状态（快速加载器）
├── bootstrap.md         # 初始化开关（一次性）
├── agent-checklist.md   # Agent 自检清单
├── user-contexts/       # 个人上下文
│   ├── index.json       # 用户注册表
│   ├── _template.json   # 模板
│   └── {username}.json  # 个人上下文文件
└── memory/              # 增量知识
    ├── decision-log.md  # 决策日志
    ├── feedback-log.md  # 反馈日志
    └── session-summaries/

00-meta/                 # 跨阶段知识
├── glossary.md          # 术语表
├── stakeholders.md      # 关键人员
└── decisions/           # ADR（架构决策记录）

90-inbox/                # 待处理输入
99-archive/              # 归档文档
```

## 关键文件说明

### project-state.json

**作用**：全局状态的"快速加载器"，Agent 每次进入先读取此文件。

**包含内容**：
- 项目名称、当前阶段
- 活跃线程列表（正在进行的工作）
- 待决策事项
- inbox 状态

### user-contexts/{username}.json

**作用**：个人偏好与关注点，让 Agent 为不同用户提供个性化服务。

**包含内容**：
- 用户身份信息
- 沟通风格偏好
- 关注的线程列表
- 最近会话摘要

### memory/

**作用**：增量知识积累，记录"为什么"而非"是什么"。

**内容类型**：
- `decision-log.md`：为什么选择 X 而非 Y
- `feedback-log.md`：用户对 Agent 行为的反馈
- `session-summaries/`：每次会话的简要总结

## Agent 行为模式

### 模式 A：提议后确认

对于写入操作（更新状态、创建 ADR），Agent **必须先提议，经人类确认后再执行**。

**原因**：
- 防止 Agent 误写重要状态
- 让人类保持对项目的控制权
- 建立信任，而非盲信

### 模式 B：自动执行

对于读取操作、个人上下文更新，Agent 可直接执行。

**原因**：
- 读取不影响项目状态
- 个人上下文属于用户自己，可自主管理

## 与 AutoResearch 的整合

AutoResearch 提供量化评估迭代机制，与 Harness 整合形成完整的项目运营框架：

1. **Harness**：管理项目上下文、决策记录、用户管理
2. **AutoResearch**：管理量化评估、迭代优化、实验记录

整合方式：
- AutoResearch 的实验结果可写入 `memory/session-summaries/`
- 量化评估指标可记录在 `project-state.json` 的 `metrics` 字段
- 优化决策可通过 ADR 记录

## 项目扩展

Harness 框架提供通用骨架，项目可根据自身生命周期添加业务目录。

### 框架层 vs 项目层

| 层级 | 内容 | 定义位置 |
|------|------|----------|
| 框架层 | `.project/`, `00-meta/`, `90-inbox/`, `99-archive/` | skill 定义（通用） |
| 项目层 | 阶段目录、研究目录、附件库等 | `CLAUDE.md` 定义（项目特定） |

### 常见项目扩展

```
10-presales/        # 售前阶段
20-implementation/  # 实施阶段
30-operations/      # 运维阶段
40-studies/         # 研究与学习笔记
50-attachments/     # 附件与素材库
```

### Agent 如何获取项目扩展

Agent 进入项目时，按以下顺序加载上下文：

1. 读取 `CLAUDE.md`（项目宪法）→ 获取项目特定目录结构
2. 读取 `.project/project-state.json` → 获取全局状态
3. 读取 `.project/user-contexts/{username}.json` → 获取个人上下文

这样 Agent 既了解框架的通用规则，又了解项目的特定扩展。

## 最佳实践

1. **每次对话开始**：Agent 执行自检清单，主动汇报状态
2. **每次对话结束**：Agent 提议更新状态，人类确认后写入
3. **决策时**：创建 ADR，记录背景、选项、结果、后果
4. **新用户时**：创建个人上下文文件，让 Agent 了解偏好
5. **资料入 Inbox**：Agent 发现后提议归档位置，人类确认后移动