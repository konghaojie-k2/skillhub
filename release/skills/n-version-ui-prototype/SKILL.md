---
name: n-version-ui-prototype
description: 'Generate N versions of self-contained HTML UI prototypes for a BDD feature or design requirement, with each version meaningfully different in positioning/layout/interaction and annotated with BDD scenario coverage. Use when user says "出 3 版原型" / "做 N 版对比" / "探索 UI 设计" / "做多版 UI" / "UI prototype" / "原 N 多个版本", or wants to evaluate alternative UIs before committing to one. Output: N HTML files in `docs/prototypes/` with placeholder colors, each annotated with which BDD scenarios it satisfies (✓ / ⚠️ / ❌).'
---

# N Version UI Prototype

## When to Use

- User has a BDD feature file or design requirement, wants to explore N UI options
- User says "出 3 版原型" / "做多版 UI" / "explore layouts" / "compare approaches"
- Before committing to one UI design, want to walk through BDD scenarios against multiple versions
- **Not for**: Single targeted UI fix (just edit the file), or production-quality designs (use `frontend-design` skill)

## Parameters

When invoking this skill, the user can specify:

| Param | Default | 含义 |
|-------|---------|------|
| `count` | 3 | 要生成的版本数 |
| `output_dir` | `docs/prototypes/` | HTML 文件输出目录 |
| `name_prefix` | derived from BDD/PB name | 文件名前缀 |
| `interaction_state_count` | 1-3 | 每个版本展示的交互状态数（如 initial / 追问 / 多次追问）|

用户典型触发：
- "出 3 版原型" → count=3, 1 个状态
- "做 5 版 UI 探索" → count=5
- "用侧边栏方案出 3 个状态" → count=1, 3 个状态

## Workflow

### Step 1: 读输入 + 确定设计维度

读 BDD feature 文件或设计需求。识别：
- 核心 UI 元素是什么（浮层？侧边栏？按钮？卡片？）
- 用户会怎么交互（一次性？追问？切换？多选？）
- BDD 场景列表（每个 prototype 都要 walk through）

读 `references/design-dimensions.md` 选 N 个**有意义不同的维度组合**：
- 位置（position）：inline-right / inline-below / sidebar-right / bottom-drawer
- 宽度（width）：200-240 / 280-320 / 360-400
- 交互（interaction）：always-on / cue-first / hover-preview / progressive
- 密度（density）：minimal / compact / normal / dense
- 视觉权重（visual）：subtle / normal / prominent

**关键规则**：N 个版本必须各自在**至少一个核心维度**不同（不是颜色微调）。详细 anti-pattern 见 `references/design-dimensions.md`。

### Step 2: 生成 N 个 HTML 文件

**复制** `assets/prototype-template.html` 作为骨架，按每个版本的设计维度填充：

- 替换 `{VERSION_NAME}` / `{VERSION_TAGLINE}` / `{ALGORITHM_DESC}`
- 替换 `{PROS}` / `{CONS}` / `{BDD_VERDICT}`
- 替换 `{SIDEBAR_OR_PANEL}` 为该版本的浮层 / 侧边栏 DOM
- 调整 CSS（`{VERSION_NAME}` 特定的浮层定位/宽度）
- 改 `body` 结构支持 N 个状态（grid 布局或 page sections）

每个文件保存为 `<output_dir>/<name_prefix>-<version>.html`，例如：
- `docs/prototypes/pb1-panel-v1-anchor-right.html`
- `docs/prototypes/pb1-panel-v2-smart-floating.html`
- `docs/prototypes/pb1-panel-v3-below-cursor.html`

### Step 3: 标注 BDD 走查

读 `references/bdd-walking-checklist.md` 学标注格式。

每个 prototype 的 `.header` 必须包含：
- BDD verdict block（✓/⚠️/❌）
- 每个 BDD 场景的覆盖说明
- reasoning（为什么满足 / 不满足）

如果是多状态 prototype（同一文件展示 1/2/3 个状态），每个状态块也要标 `.bdd-good` / `.bdd-warn` / `.bdd-bad` tag。

### Step 4: 总结到对话

输出给用户时，简要说明：
- N 个文件路径
- 每版核心差异（用 1 句话）
- BDD 走查结果（每版的✓/⚠️/❌）
- **不给评分**——让用户自己选

## Bundled Resources

### `assets/prototype-template.html`
可复制的 HTML 模板，含：
- 占位色 CSS 变量（灰/白/浅蓝/暖黄）
- 通用元素样式（panel、cue 模式、Q/A 块、chips、按钮）
- Header 标注格式
- 替换占位符：`{VERSION_NAME}`, `{VERSION_TAGLINE}`, `{ALGORITHM_DESC}`, `{PROS}`, `{CONS}`, `{BDD_VERDICT}`, `{SIDEBAR_OR_PANEL}`

### `references/design-dimensions.md`
5 个核心维度的可选值 + 选择规则 + anti-patterns。生成 N 版前必读。

### `references/bdd-walking-checklist.md`
BDD 走查标注格式 + verdict 符号 + 多状态标注示例。生成标注前必读。

## 占位色规则

**绝对不要**纠结配色。统一使用：
- 页面背景 `#f5f5f7`
- 卡片白 `#fff`
- 软底 `#f9fafb`
- Cornell cue 暖色 `#fefce8` / `#fbbf24`
- 蓝（链接/问题）`#1e40af` / `#eff6ff`
- 灰（按钮/默认）`#6b7280` / `#d1d5db`
- 警告 `#b45309` / `#fef3c7`

**统一配色在最终方案选定后**做，不在原型阶段。

## Examples

### Example 1: 3 版浮层（用户："出 3 版浮层原型"）

读 BDD feature `sprint6_explain_conversation.feature`：
- Scenario 1-5: 选中文字、解释、追问、延迟、不遮挡

读 `design-dimensions.md` 选 3 个不同组合：
- v1: `inline-float-right` + 280px + `always-on` + `normal` density
- v2: `inline-float-smart` + 280px + `always-on` + `normal` density
- v3: `inline-float-below` + 280px + `always-on` + `subtle` visual

生成 3 个 HTML 文件，每版 header 标注 BDD 走查。

### Example 2: 1 版侧边栏 + 3 个状态（用户："用侧边栏方案出 3 个状态"）

读 BDD feature + design doc：
- 选 `sidebar-right` + 360px + `cue-first` interaction
- 单个 HTML 含 3 个状态：cue 模式 / 展开 / 收起
- 每个状态块标注 BDD walking verdict

### Example 3: 5 版 UI 探索（用户："做 5 版 UI"）

读 BDD + 设计约束：
- 5 个版本在 5 个维度上都不同：
  - v1: inline-float-right, 280px, always-on, normal
  - v2: inline-float-smart, 280px, always-on, normal
  - v3: sidebar-right, 360px, cue-first, normal
  - v4: bottom-drawer, 100%, hover-preview, dense
  - v5: modal-centered, 480px, always-on, prominent

输出 5 个文件。

## Anti-Patterns to Avoid

- **N 版只是颜色不同**（红/蓝/绿）→ 浪费 token
- **N 版只是宽度不同**（280/320/360px）→ 同一版本
- **不写 BDD 走查** → 用户无法客观选
- **纠结配色** → 原型阶段用占位色
- **单个 HTML 写完 5 版** → 用户无法并排对比
- **生成的 HTML 不能独立打开** → 必须自包含（inline CSS/HTML）
- **跳过 references/ 文档** → 容易产出同质版本

## Quick Validation

生成完 N 版后自检：
- [ ] 每个文件能直接在浏览器打开（无外部依赖）
- [ ] 每版的 BDD 走查都在 .header 里
- [ ] 至少一个核心维度上版本之间有差异
- [ ] 占位色一致（不混用其他调色板）
- [ ] 包含至少 1 个交互状态（initial / 追问 / 展开）
