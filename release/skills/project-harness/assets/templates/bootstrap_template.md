# Bootstrap Protocol - 新项目初始化向导

> 本文件是新项目首次进入时的初始化开关。Agent 进入时发现此文件存在，应执行以下流程。

---

## 初始化流程

### 第 1 步：收集用户信息

请向人类收集以下信息：

```text
请提供以下信息以完成项目初始化：
1. user_id（用于 AI 识别您的身份，建议使用简短英文，如 'kong'）
2. name（您的姓名或称呼）
3. role（您在项目中的角色，如 '技术负责人'、'项目经理'、'工程师'）
4. 项目中文名称（用于生成 project_cn 字段）
5. 项目英文名称（用于生成 project 字段）
```

### 第 2 步：创建用户上下文

1. 基于 `_template.json` 创建 `.project/user-contexts/{user_id}.json`
2. 填入收集到的用户信息
3. 更新 `index.json`，添加新用户到 `users` 列表
4. 设置 `default_user` 为新用户的 `user_id`

### 第 3 步：初始化项目状态

1. 更新 `.project/project-state.json`：
   - 设置 `project` 和 `project_cn`
   - 设置 `current_phase`（默认为 `presales`）
   - 设置 `last_update` 为当前日期
   - 清空 `active_threads` 和 `pending_decisions`

### 第 4 步：创建必要的空文件

确保以下文件存在（如不存在则创建）：

- `.project/memory/user-profile.md`
- `.project/memory/decision-log.md`
- `.project/memory/feedback-log.md`

### 第 5 步：生成状态报告

执行 Agent 自检清单的步骤 1-5，向人类汇报项目初始状态。

### 第 6 步：删除本文件

**重要**：初始化完成后，删除 `.project/bootstrap.md`，标志着项目已完成初始化。

---

## 初始化完成标志

初始化完成后，向人类汇报：

```text
【初始化完成】
- 项目名称：{project_cn}
- 当前阶段：{current_phase}
- 用户身份：{name}（{role}）
- Harness 结构已建立，请开始协作。

建议下一步：
1. 在项目根目录创建 CLAUDE.md（项目宪法）
2. 将已有资料放入 90-inbox/，由 Agent 协助归档
```

---

## 重要约束

- 本文件只在首次进入时执行一次，完成后立即删除。
- 若用户没有提供完整的 user_id/name/role，不要猜测，直接追问。
- 所有文件使用 UTF-8 编码。