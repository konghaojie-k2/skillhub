# 文件格式与归档规则

写入 `.daily_reflection/` 下任何文件前，先按本文格式执行。

## 目录

- [context-sync.json](#context-syncjson)
- [decisions.md](#decisionsmd)
- [daily-status.md](#daily-statusmd)
- [归档规则](#归档规则)
- [CLAUDE.md 注入模板](#claudemd-注入模板)

## context-sync.json

```json
{
  "last_session": "2026-05-11T13:05",
  "phase": "Phase 3/4",
  "progress": "95%",
  "pending_tasks": [
    {"id": "T-032", "title": "任务描述", "priority": "medium"}
  ],
  "active_findings": ["最多 8 条活跃陷阱"],
  "recent_changes": ["最近修改的关键文件，最多 5 个"],
  "next_focus": "下次建议的一句话"
}
```

## decisions.md

```markdown
# 决策记录

> 活跃决策（仍影响当前行为）在前，归档（已完结）在后，以 `---` 分隔。

---

## [活跃] 决策标题
- **日期**: 2026-05-11
- **约束**: 对代码的约束/规则（必须仍生效）
- **原因**: 选择原因
- **状态**: 已采纳 / 待实现 / 稳定
```

### 状态与归位

| 状态 | 定义 | 位置 |
|------|------|------|
| 活跃 | 仍影响当前代码行为 | decisions.md 活跃区 |
| 已执行完毕 | 决策已落地，后续代码不再受约束 | `archive/decisions-history.md` |
| 已推翻 | 采纳后撤销 | `archive/decisions-history.md`（写明推翻原因） |

- 同一件事只在一处出现，禁止活跃/归档重复。
- 归档时机：重构完成、功能取消/推翻 → 立即归档；规则稳定运行超 30 天 → 归档。

## daily-status.md

```markdown
# 每日流程

> 强制每日检查清单，不存具体业务数据。

## 早省
- [ ] 读取 context-sync.json，确认阶段、进度、待办
- [ ] `gh issue list`，新 issue 是否纳入今日任务
- [ ] 检查 inbox/ 是否有新文件
- [ ] 确认今日主攻方向（参考 next_focus）

## 晚省
- [ ] 更新 context-sync.json
- [ ] active_findings > 8 条则归档 3 条
- [ ] 新决策追加到 decisions.md（按状态归位）
- [ ] 完成任务从 pending_tasks 移除
```

## 归档规则

| 内容 | 保留上限 | 归档位置 |
|------|---------|---------|
| `active_findings` | 8 条 | `archive/findings-history.md` |
| decisions 活跃区 | 8 条 | `archive/decisions-history.md` |
| 已完成任务 | 完成后即移 | `archive/tasks-history.md` |
| inbox 文件 | 7 天 | 超期视为 stale，提醒清理 |

超量时归档最老的 3 条。

## CLAUDE.md 注入模板

项目根目录有 `CLAUDE.md`/`AGENT.md` 且未提及 `.daily_reflection` 时，在文件末尾追加：

```markdown
## 上下文管理

本项目使用 **daily-reflection** skill 进行跨会话状态同步，数据存放在 `.daily_reflection/`：

- `context-sync.json` — 核心状态（进度、待办、活跃陷阱、最近文件）
- `decisions.md` — 决策记录（活跃区 + 归档区）
- `daily-status.md` — 每日流程打卡（早省/晚省 checklist）
- `archive/` — 归档历史
- `inbox/` — 临时输入池

触发词："早省"、"中省"、"晚省"、"状态同步"、"决策记录"。
```
