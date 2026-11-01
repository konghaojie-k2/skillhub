# 工作流指南

本文件详细说明 Harness 和 AutoResearch 的工作流程。

---

## 目录

1. [项目初始化流程](#项目初始化流程)
2. [Agent 自检流程](#agent-自检流程)
3. [Inbox 工作流](#inbox-工作流)
4. [决策记录流程](#决策记录流程)
5. [量化评估迭代流程](#量化评估迭代流程)

---

## 项目初始化流程

### 使用脚本初始化

```bash
cd <skill-path>
uv run scripts/init_project.py --name "项目名称" --path ./项目目录 --description "项目描述"
```

### 手动初始化

1. 创建目录结构：
   - `.project/`
   - `.project/user-contexts/`
   - `.project/memory/`
   - `.project/memory/session-summaries/`
   - `00-meta/`
   - `00-meta/decisions/`
   - `00-meta/queries/`
   - `90-inbox/`
   - `99-archive/`

2. 创建核心文件：
   - `.project/project-state.json`（从模板复制）
   - `.project/bootstrap.md`（从模板复制）
   - `.project/agent-checklist.md`（从模板复制）
   - `.project/user-contexts/_template.json`
   - `.project/user-contexts/index.json`

3. Agent 进入时自动执行 bootstrap 流程

---

## Agent 自检流程

每次对话开始时，Agent 执行以下自检：

### Step 0: 检查初始化开关

```
if exists(.project/bootstrap.md):
    执行 Bootstrap Protocol
    删除 bootstrap.md
else:
    继续标准自检
```

### Step 1: 加载上下文

```
读取 project-state.json → 获取全局状态
读取 user-contexts/index.json → 获取用户注册表
识别当前用户 → 读取对应个人上下文文件
读取 memory/*.md → 获取增量知识
```

### Step 2: 扫描 Inbox

```
列出 90-inbox/ 内容
if inbox 有文件:
    向人类汇报：文件名、摘要、建议归档位置
```

### Step 3: 检查变更

```
git diff --name-only HEAD~3..HEAD
识别新增 .md 文件
if 发现技术决策变更:
    提议创建/更新 ADR
```

### Step 4: 检查线程

```
遍历 active_threads
if last_update > 7天:
    标记为 stale，提醒人类
if next_action 为空:
    提议补充后续计划
```

### Step 5: 主动汇报

使用标准模板汇报项目状态。

---

## Inbox 工作流

### 入口

人类将原始材料（会议记录、截图、草稿）放入 `90-inbox/`。

### Agent 处理

1. 发现 inbox 有新文件
2. 分析内容：
   - 文件类型（会议记录、决策记录、参考资料等）
   - 关键信息提取
   - 归档位置建议
3. 向人类提议：
   ```
   发现 inbox 新文件：{文件名}
   内容摘要：{摘要}
   建议归档位置：{位置}
   关联线程：{线程名}
   
   是否执行归档？
   ```
4. 人类确认后移动文件

### 归档规则

归档位置由项目 `CLAUDE.md` 定义。常见映射：

| 文件类型 | 归档位置（示例） | 说明 |
|---------|----------|------|
| 会议记录 | `10-presales/` 或对应阶段目录 | 根据项目阶段选择 |
| 技术决策 | `00-meta/decisions/ADR-XXXX.md` | 框架层（通用） |
| 参考资料 | `40-studies/` 或 `50-attachments/` | 项目层（取决于项目定义） |
| 历史文档 | `99-archive/` | 框架层（通用） |

**Agent 执行归档前**：先读取项目 `CLAUDE.md` 确认目录结构，再提议归档位置。

---

## 决策记录流程

### ADR 格式

```markdown
# ADR-XXXX: {决策标题}

## 背景

{描述问题背景、约束条件、触发因素}

## 考虑的选项

1. **选项 A**: {描述}
   - 优点：...
   - 缺点：...
2. **选项 B**: {描述}
   - 优点：...
   - 缺点：...

## 决策结果

选择：{选项}

## 理由

{为什么选择这个选项}

## 后果

- 正面：...
- 负面：...
- 风险：...

## 相关文件

- {相关文件路径}
```

### 创建流程

1. Agent 发现技术讨论涉及决策
2. 提议创建 ADR：
   ```
   本次讨论涉及技术决策：{决策内容}
   建议创建 ADR：ADR-XXXX-{标题}.md
   
   是否创建？
   ```
3. 人类确认后创建
4. 更新 `decision-log.md`
5. 更新 `project-state.json` 的 `pending_decisions`

---

## 量化评估迭代流程

### AutoResearch 框架

用于需要量化评估的迭代优化任务。

### 使用方式

```python
from autoresearch import AutoResearch

ar = AutoResearch(
    evaluate_func=evaluate,        # 评估函数，返回分数
    target_score=100,              # 目标分数
    max_iterations=50,             # 最大迭代次数
    backup_files=['target.md'],    # 需备份的文件
    experiment_func=experiment     # 实验函数，执行优化
)

results = ar.run()
```

### 典型场景

1. **代码重构**：评估代码质量指标，自动重构
2. **性能优化**：评估性能指标，自动调优
3. **格式规范化**：评估格式合规性，自动修复
4. **文档优化**：评估文档质量，自动改进

### 与 Harness 整合

1. 实验开始前：在 `project-state.json` 创建线程
2. 每次迭代后：更新线程状态
3. 实验结束后：
   - 写入 `memory/session-summaries/`
   - 如有决策，创建 ADR
   - 更新 `project-state.json`