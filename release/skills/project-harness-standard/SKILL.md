---
name: project-harness-standard
description: Project Harness 通用工作流标准。提供声明式命令（/archive、/check、/adr），自动执行目录规范检查、文档归档、ADR 创建。具体规则由项目内 CONTRIBUTING.md 定义，skill 框架本身不硬编码项目特定内容。适用于任何采用 Harness 目录结构的项目。
---

# Project Harness Standard

## 核心原则

**框架通用，规范由项目定义。**

- 本 skill 提供通用目录结构、命令接口和验证逻辑
- 每个项目必须在根目录提供 `CONTRIBUTING.md`，定义：
  - 附件分类规则（子目录清单和用途）
  - 文件命名规范（正则表达式）
  - INDEX.md 格式要求
  - 禁止行为清单
- 自动化脚本优先读取项目 `CONTRIBUTING.md`，而非内置硬编码规则

## 前置依赖

- 项目已使用 `project-harness` skill 初始化（或手动创建 Harness 目录结构）
- 项目根目录存在 `CONTRIBUTING.md`
- 项目根目录存在 `00-meta/decisions/`（ADR 存放位置）

## 声明式命令

### /archive {文件路径} [--category {分类}]

将文件归档到项目附件库。

**声明式目标**：文件必须分类存放、命名合规、索引同步、依赖文件同目录。

**执行流程**：
1. 读取 `CONTRIBUTING.md` 获取附件分类规则
2. 若未指定 `--category`，根据文件名/内容推断分类
3. 校验目标目录是否存在（不存在则提议创建）
4. 校验/修正文件命名（添加日期后缀）
5. 更新对应子目录的 `INDEX.md`
6. 移动文件（图片与引用 md 保持同目录）

**输出**：
```
归档完成：
- 目标目录：50-attachments/业务知识/
- 新文件名：Demura基础业务知识_20260421_当前生效.md
- 关联文件：before_demura_20260421.png, after_demura_20260421.png
- INDEX.md 已更新
```

### /check [--scope {范围}]

运行规范验证。

**声明式目标**：项目文件组织符合 CONTRIBUTING.md 定义的所有规则。

**默认范围**：全项目
**可选范围**：`attachments` | `docs` | `adr`

**执行流程**：
1. 读取 `CONTRIBUTING.md`
2. 按范围执行对应检查脚本
3. 报告违规项及修复建议

**输出示例**：
```
规范检查报告：
❌ 50-attachments/ 根目录发现 2 个非法文件（应放入子目录）
   - temp_notes.md → 建议：50-attachments/参考资料/
   - screenshot.png → 建议：50-attachments/调研记录/

❌ 3 个文件命名不符合规范（缺少日期后缀）
   - 项目计划表.xlsx → 建议：项目计划表_20260421.xlsx

✅ INDEX.md 同步检查通过
```

### /adr {标题} [--status {状态}]

创建架构决策记录。

**声明式目标**：ADR 编号递增、格式合规、索引同步、与项目状态关联。

**执行流程**：
1. 读取 `00-meta/decisions/README.md`（获取格式规范模板）
2. 读取 `00-meta/decisions/INDEX.md`（获取现有 ADR 列表，计算下一个编号）
3. 从模板创建 ADR 文件（填充编号、日期、标题）
4. 更新 `00-meta/decisions/INDEX.md`
5. 更新 `.project/memory/decision-log.md`
6. （可选）更新 `project-state.json` 的 pending_decisions

**输出**：
```
ADR 已创建：
- 文件：00-meta/decisions/ADR-0007-规范执行自动化.md
- 状态：proposed（等待人类确认后改为 accepted）
- 决策日志已更新
```

## 项目级配置（CONTRIBUTING.md）

每个项目必须提供 `CONTRIBUTING.md`，至少包含以下章节：

```markdown
## 附件管理规范

### 目录结构
```
50-attachments/
├── INDEX.md          # 总索引（必填）
├── {分类A}/          # 用途描述
├── {分类B}/          # 用途描述
└── ...
```

### 命名规范
- 正则：`.*_\d{8}(_.*)?\.(md|png|...)$`
- 禁止：无日期版本标识的文件

### 索引要求
- 新增/更新/删除附件时，同步维护 INDEX.md
- INDEX.md 格式：表格，含文件名、类型、日期、状态、摘要、关联文档

### 禁止行为
- 根目录直接存放文件
- 新建未定义的旧目录名
- 跨目录引用图片（图片与 md 必须同目录）
```

## 与 project-harness 的关系

| 层级 | skill | 职责 |
|------|-------|------|
| 框架层 | `project-harness` | 初始化目录结构、Agent 自检协议 |
| 标准层 | `project-harness-standard` | 声明式命令、自动化验证、ADR 工作流 |
| 项目层 | `CONTRIBUTING.md` | 具体规范定义（分类、命名、禁止行为） |

## 目录结构

```
project-harness-standard/
├── SKILL.md                    # 本文件
├── rules/
│   ├── directory-structure.md  # 通用目录架构说明
│   ├── attachment-rules.md     # 附件管理通用规则模板
│   └── naming-convention.md    # 命名规范通用模板
└── scripts/
    └── check-compliance.py     # 三层验证脚本（读取项目 CONTRIBUTING.md）
```

## 约束

- **不读取项目外信息**：所有规则以项目根目录 `CONTRIBUTING.md` 为准
- **模式 A 保留**：写入操作（归档、ADR 创建）默认先提议，人类确认后执行
- **可覆盖**：项目可在 `.claude/settings.json` 中禁用特定检查项
