# Prototype Design Dimensions

> When generating N prototype versions, each version should differ in **at least one** of these dimensions meaningfully. Don't just tweak colors or sizes.

## Core Dimensions

### 1. **Position**（位置）
Where the UI element lives relative to the main content.

| 位置 | 描述 | 适用场景 |
|------|------|---------|
| `inline-float-right` | 浮在选区右侧 | 短选区、宽视口 |
| `inline-float-below` | 浮在选区下方 | tooltip 类提示 |
| `inline-float-smart` | 智能避让（4 种 fallback）| robust 默认 |
| `sidebar-right` | 右侧固定栏 | 频繁追问 / 累积历史 |
| `sidebar-left` | 左侧固定栏 | 写作类工具 |
| `bottom-drawer` | 底部抽屉 | 移动端 / 内容优先 |
| `modal-centered` | 居中模态框 | 重要决策（不推荐用于解释）|

### 2. **Width**（宽度）
How much horizontal space the UI takes.

| 宽度 | 视口占比 | 适合 |
|------|---------|------|
| 极窄 | 200-240px | Cornell cue / 最小信息 |
| 窄 | 280-320px | 浮层 / 单次对话 |
| 中 | 360-400px | 侧边栏 / 完整解释 |
| 宽 | 50%+ | 详情页 / 多视图 |

### 3. **Interaction Model**（交互模式）
How the user reveals more info.

| 模式 | 默认状态 | 展开方式 |
|------|---------|---------|
| `always-on` | 全部可见 | 滚动 |
| `cue-first` (Cornell) | cue（1 行） | 点"展开"→ 完整 |
| `hover-preview` | 不显示 | hover 显示 tooltip |
| `click-expand` | 摘要 | 点展开完整 |
| `progressive-disclosure` | 多层折叠 | 逐层展开 |

### 4. **Information Density**（信息密度）
How much is shown at once.

| 密度 | 适用 |
|------|------|
| `minimal` (1-2 行) | cue / 提示 |
| `compact` (3-5 行) | 单次解释 |
| `normal` (5-10 行) | 解释 + 短追问 |
| `dense` (10+ 行) | 完整对话流 |

### 5. **Visual Weight**（视觉权重）
How prominent the UI feels.

| 权重 | 实现 |
|------|------|
| `subtle` | 浅色 / 细边 / 半透明 |
| `normal` | 标准白底 + 阴影 |
| `prominent` | 高饱和度 / 重阴影 / 大圆角 |

## How to Choose Dimensions for Each Version

When user says "出 3 版", pick 3 meaningfully different combinations:

| Version | Position | Width | Interaction | Visual | 为什么不同 |
|---------|----------|-------|-------------|--------|-----------|
| v1 | inline-float-right | 窄 (280px) | always-on | normal | 极简浮层 |
| v2 | sidebar-right | 中 (360px) | cue-first | normal | Cornell 自测 |
| v3 | inline-float-smart | 窄 (280px) | always-on | subtle | 智能避让变体 |

**核心规则**：每版的差异必须是**用户能感知的行为差异**，不是颜色/字体的微调。

## Common BDD Walking Checklist

For each prototype, annotate the .header with:

```
BDD 走查:
  ✓ Scenario 1: 选中文字得到含项目上下文的解释
  ✓ Scenario 5: 浮层不与选区矩形重叠
  ⚠️ Scenario 4: 5 秒内显示首次解释（定位算法复杂 → 略慢）
  ✓ Scenario 2: 解释返回 3-4 个推荐追问
```

Use:
- ✓ = 完全满足
- ⚠️ = 部分满足 / 风险
- ❌ = 不满足

## Anti-Patterns to Avoid

- **三版只是颜色不同**（v1 红 / v2 蓝 / v3 绿）→ 没意义
- **三版只是宽度不同**（v1 280px / v2 320px / v3 360px）→ 同一版本
- **三版只改文案/示例** → 实际是同一 UI

正确做法：**每个版本必须改变至少一个核心维度**（位置/宽度/交互/密度/权重）。
