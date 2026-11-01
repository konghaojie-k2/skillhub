---
name: daily-reflection
description: 代码日志与项目规划助手。记录每日代码活动，与 daily-git-check 联动追踪任务进度。当用户说"记录代码"、"写日志"、"今日代码"、"做计划"、"早省"、"中省"、"晚省"、"状态同步"、"继续上次"、"昨日遗留"、"决策记录"时触发。
---

# daily-reflection

借鉴"吾日三省吾身"，通过 `.daily_reflection/` 下的本地文件实现跨会话状态同步：
- **早省**：读状态 → 生成今日计划
- **中省**：记录关键文件变更
- **晚省**：同步状态 + 归档

## 数据存储

| 文件 | 说明 |
|------|------|
| `context-sync.json` | 核心状态快照（phase / progress / pending_tasks / active_findings / recent_changes / next_focus） |
| `decisions.md` | 决策记录（活跃区在前，归档区在后，`---` 分隔） |
| `daily-status.md` | 每日流程打卡 checklist（不存业务数据） |
| `archive/findings-history.md` | 已解决/过时陷阱的归档 |
| `archive/decisions-history.md` | 已完结决策的归档 |
| `archive/tasks-history.md` | 已完成任务的详细记录 |
| `inbox/` | 临时输入池（想法、截图、参考资料），处理后删除源文件 |

各文件的完整格式与归档规则见 [references/formats.md](references/formats.md)，写入前必须先读。

## 初始化

`.daily_reflection/` 不存在时，运行：

```bash
bash <skill目录>/scripts/init.sh
```

脚本幂等，不覆盖已有文件。之后若项目根目录有 `CLAUDE.md` 且未提及 `.daily_reflection`，追加一段说明（模板见 formats.md 末尾）。

## 加载时行为

SessionStart hook 已自动把状态注入上下文（见文末 Hooks 节），无需手动读取。若上下文中没有 `[daily-reflection]` 状态行且 `.daily_reflection/context-sync.json` 存在，手动读取并输出一行：`📊 {phase} | 进度 {progress} | 待办 {n} 项 | 下一步：{next_focus}`。

## 早省

**触发**："早省"、"做计划"、"今日计划"。

1. **Git 检查**（按 daily-git-check 三段式）：`git status` + `git fetch --all`；当前分支对比 `origin/<同名分支>`（远程分支不存在则报"未推送远程"，禁止报"无更新"）；非默认分支时顺带对比 `origin/HEAD`
2. **Issue 检查**：`gh issue list --state open --limit 20`；无 gh CLI 或远程非 GitHub → 静默跳过
3. 读 context-sync.json，输出今日计划：
   ```
   📝 今日计划 - <日期>
   目标：<next_focus>　阶段：<phase>
   任务：<pending_tasks>
   Open Issues：<N 个，新增/长期未回应高亮>
   已知陷阱：<active_findings>
   ```
4. 处理 inbox（见下文，必须）
5. 更新 `last_session`，在 daily-status.md 早省 checklist 打勾

## 中省

**触发**："记录一下"、"写日志"、"中省"。仅在用户触发时执行，不要主动打断。

1. 读 `recent-changes.log` 和 `corrections.log`（hook 实时捕获的证据，见文末）
2. 对 corrections.log 里每条纠正，结合对话上下文写出：**问题 → 根因 → 怎么解决 → 教训**；打转警告（⚠️ 行）同样分析
3. 教训属于反复出现的陷阱 → 经用户确认后进 `active_findings`
4. 文件轨迹去重后更新 `recent_changes`（保留最近 5 个），然后**清空两个 log**

## 晚省

**触发**："晚省"、"今日结束"。若当天未早省，先提示补早省。

1. 处理 inbox（必须）
2. 若今天没做过中省，先按中省流程处理两个 log（证据不会因延迟而丢失）
3. `git log --since="<今天 00:00>" --oneline` 回顾今日提交
4. 更新 context-sync.json：`last_session`、`progress`、`pending_tasks`（移除已完成）、`next_focus`
5. `active_findings` > 8 条 → 归档最老 3 条到 `archive/findings-history.md`
6. 询问是否有新决策 → 追加到 decisions.md 活跃区
7. 在 daily-status.md 晚省 checklist 打勾

## 决策记录

**触发**："决策记录"、"ADR"，或检测到重大变更（删除 3+ 文件的模块、核心依赖变更、入口文件改动超 20 行）——重大变更在 commit 后立即记录，不等晚省。

1. 收集：标题、约束（对代码的规则）、原因
2. 追加到 decisions.md 活跃区，格式见 formats.md
3. 活跃区 > 8 条 → 最老 3 条移到 `archive/decisions-history.md`

## Inbox 处理

早省/晚省必须执行，其他时候用户说"处理 inbox"时执行。

1. 读取内容，识别类型：bug / feature / question / reference / idea
2. 归类记录：需求/bug → `pending_tasks`；决策 → decisions.md；陷阱 → `active_findings`；参考资料 → 提取摘要
3. **删除源文件**——inbox 只存"待处理"

## 错误捕捉

区分两类错误：

- **临时错误**（构建失败、依赖缺失、单次 typo）→ 不入 `active_findings`，解决即可
- **反复出现的陷阱**（框架限制、路径问题、已知 bug 模式）→ 经用户确认后追加到 `active_findings`

## commit 提醒

用户说"完成了"/"做好了"时，检查 `git status`；有未提交修改则询问是否 commit（遵循项目 commit 规范，不强制）。

## 时间戳

统一用 `get-current-time` skill；不可用时降级 `Get-Date -Format "yyyy-MM-dd HH:mm"`。

## Hooks（自动捕获层）

三个全局 hook 配置在 `~/.claude/settings.json`，仅在项目存在 `.daily_reflection/context-sync.json` 时工作，否则静默退出：

| Hook | 脚本 | 捕获内容 |
|------|------|---------|
| SessionStart | `scripts/session-start.js` | 把阶段/进度/待办/下一步/inbox 数量注入会话上下文 |
| PostToolUse（Edit\|Write\|MultiEdit\|NotebookEdit） | `scripts/log-change.js` | 项目内文件轨迹 → `recent-changes.log`；同文件 10 分钟改 5+ 次记打转警告 |
| UserPromptSubmit | `scripts/log-correction.js` | 匹配纠正词（不对/错了/重来/回退/撤销/返工等）的用户消息原文 → `corrections.log` |

分工：hook 负责**实时抓证据**（确定性、不依赖自觉），agent 在中省/晚省负责**读证据写叙事**（问题→根因→教训）。log 是缓冲，中省/晚省处理后清空。
