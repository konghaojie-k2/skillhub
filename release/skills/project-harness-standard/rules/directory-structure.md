# 通用目录架构

适用于任何采用 Project Harness 的项目。

## 核心目录

```
{project-root}/
├── .project/                    # AI 运行时与共享状态
│   ├── project-state.json       # 全局项目状态
│   ├── agent-checklist.md       # Agent 自检清单
│   ├── user-contexts/           # 个人 AI 上下文
│   └── memory/                  # 增量知识
│
├── 00-meta/                     # 跨阶段知识（LLM Wiki）
│   ├── glossary.md              # 术语表
│   ├── stakeholders.md          # 关键人员
│   ├── decisions/               # ADR（架构决策记录）
│   └── queries/                 # FAQ
│
├── 10-{phase1}/                 # 阶段 1（如售前/需求）
├── 20-{phase2}/                 # 阶段 2（如实施/开发）
├── 30-{phase3}/                 # 阶段 3（如运维/运营）
│
├── 40-studies/                  # 研究、学习、实验
│
├── 50-attachments/              # 附件与资产
│   ├── INDEX.md                 # 总索引（必填）
│   └── {category}/              # 按用途分类的子目录
│
├── 90-inbox/                    # 待处理原始输入
├── 99-archive/                  # 归档文档
│
├── CONTRIBUTING.md              # 项目规范定义（必填）
└── CLAUDE.md                    # 项目宪法（可选）
```

## 编号规则

| 编号前缀 | 用途 |
|----------|------|
| `00-` | 元知识（跨阶段通用） |
| `10-` ~ `30-` | 项目阶段（按时间/生命周期排序） |
| `40-` | 研究/探索（非生产代码） |
| `50-` | 附件/资产 |
| `90-` | 临时/待处理 |
| `99-` | 归档 |

## 扩展规则

- 阶段目录名可自定义（如 `10-presales`、`20-implementation`）
- `50-attachments/` 下的子目录由项目 `CONTRIBUTING.md` 定义
- 新增阶段目录需符合编号范围，避免与现有编号冲突
