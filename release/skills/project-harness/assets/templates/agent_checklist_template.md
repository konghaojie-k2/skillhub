# Agent 自检清单

> 每次进入本项目时，请按以下顺序执行自检，然后主动向人类汇报状态。

---

## 步骤 0：检查初始化开关（必读）

- [ ] 读取 `CLAUDE.md`
- [ ] **检查 `.project/bootstrap.md` 是否存在**
- [ ] 若存在，执行 Bootstrap Protocol（按 `bootstrap.md` 引导新用户完成初始化，创建个人上下文，更新 `index.json`，最后**删除 `bootstrap.md`**）
- [ ] 初始化完成后，继续执行步骤 1

## 步骤 1：加载上下文（必读）

- [ ] 读取 `.project/project-state.json`
- [ ] 读取 `.project/user-contexts/index.json`（用户注册表）
- [ ] 识别当前用户身份；读取对应的 `.project/user-contexts/{username}.json`
- [ ] 若用户无个人上下文文件，基于 `_template.json` 主动为其创建并告知
- [ ] 读取 `.project/memory/*.md`（按修改时间降序）
- [ ] 确定 `current_phase` 和 `active_threads`

---

## 步骤 2：扫描 inbox

- [ ] 列出 `90-inbox/` 中的文件
- [ ] 若 `inbox_items > 0`，向人类汇报：文件名、内容摘要、建议归档位置
- [ ] 若 `inbox_items == 0`，无需汇报

---

## 步骤 3：检查项目变更

- [ ] 运行 `git diff --name-only HEAD~3..HEAD`（或最近 3 个 commit）
- [ ] 识别新增的 `.md` 文件或重大修改
- [ ] 判断是否有新的技术决策、方案变更、限制条件调整
- [ ] 若有，提议创建或更新 ADR（`00-meta/decisions/`）

---

## 步骤 4：检查活跃线程状态

- [ ] 遍历 `active_threads`
- [ ] 对 `last_update` 超过 7 天的线程，标记为 `stale` 并提醒人类
- [ ] 对 `next_action` 为空的线程，提议补充后续计划
- [ ] 汇报本周最值得关注的 1-2 个线程

---

## 步骤 5：主动汇报（标准模板）

用以下格式向人类汇报：

```text
【项目状态速览】
- 当前阶段：[phase]
- 活跃线程数：[N] 个，其中 [M] 个需要关注
- 最近更新：[日期]
- inbox 状态：[N] 个待处理 / 空
- 本周建议优先处理：[线程名称]
```

---

## 步骤 6：对话意图识别与实时状态同步（必须）

### 6A. 实时意图识别与记录（对话中执行）

Agent 在对话中实时检测用户意图。当检测到以下信号时，**立即记录**，无需等到会话结束：

| 类型 | 触发信号（关键词） | 处理方式 |
|------|-------------------|---------|
| 新功能请求 | "添加"、"实现"、"支持"、"能不能"、"希望有"、"需要" + 功能描述 | 立即创建线程，告知用户 |
| Bug 修复请求 | "修复"、"bug"、"报错"、"崩溃"、"失效"、"不对" + 症状描述 | 立即创建线程，告知用户 |
| 修改/重构 | "改成"、"重构"、"优化"、"调整"、"改一下" + 组件名 | 立即创建线程，告知用户 |
| 技术决策 | "决定"、"用"、"选型"、"选"、"方案" + 对比/选择语境 | 立即追加到 decision-log，告知用户 |

**线程创建规则**：
1. 扫描 `project-state.json` 的 `active_threads`，取最大 T-XXX 编号 +1 作为新 ID
2. 新线程格式：`{"id": "T-XXX", "name": "功能描述", "status": "open", "last_update": "YYYY-MM-DD", "next_action": "待实现"}`
3. 写入前检查：若已有同名/同关键词线程，更新其 `last_update` 而非新建
4. 告知用户：`已记录为新线程 T-XXX：功能描述`

**决策记录规则**：
1. 追加到 `memory/decision-log.md`，格式沿用现有模板
2. 告知用户：`已记录到决策日志：决策标题`

### 6B. Session Summary 生成（上下文压缩时触发 / 手动触发）

**本流程已封装为 `/session-summary` skill，可直接调用。**

**触发时机**（满足其一即可）：
1. 系统提示"上下文已被压缩"
2. 对话轮次明显增长（>40 轮）
3. 用户主动说"总结一下"、"记录会话"、"session summary"

**执行步骤**：

1. **回顾对话内容**，提取关键信息：
   - 本次会话创建/更新了哪些线程
   - 做出了什么技术决策
   - 用户有什么待确认事项
   - 完成了什么代码修改
2. **创建 summary 文件**：`.project/memory/session-summaries/YYYY-MM-DD_HH-MM.md`

   格式：
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

3. **更新 `user-contexts/{username}.json` 的 `recent_sessions`**（保留最近 10 条）

**约束**：
- summary 不超过 30 行
- 无需用户确认，自动生成
- 文件名用 `YYYY-MM-DD_HH-MM.md`，冲突时加 `-2`、`-3`

### 6C. 会话自然结束时的收尾

当用户明确表示会话结束（"先这样"、"好了"、转入无关话题），执行：
- [ ] 更新 `project-state.json` 的 `last_update` 字段
- [ ] 若本次会话未生成过 summary，检查是否需要补生成（有产出但未压缩上下文的情况）

---

## 重要约束

- **模式 A（修订）**：
  - **任务记录**（新线程创建/更新）：用户已明确表达需求时，**直接写入**，无需额外确认。
  - **技术决策记录**：讨论中已明确的决策，**直接追加**到 decision-log。
  - **Session summary**：自动生成，无需确认。
  - **其他变更**（删除线程、修改历史决策、变更项目阶段）：仍遵循先提议后确认。
- 个人上下文文件 `user-contexts/{username}.json` 可由对应用户直接更新，Agent 协助整理。
- 不要猜测人类的意图。不确定时，直接问。
- 所有中文文件使用 UTF-8 编码。
