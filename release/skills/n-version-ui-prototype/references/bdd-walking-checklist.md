# BDD Walking Checklist

> How to annotate each prototype with BDD scenario coverage.

## Header Annotation Format

Each prototype's `.header` block must include a BDD walking verdict:

```html
<div class="verdict verdict-good">BDD 走查: 
  ✓ Scenario 1: 含项目上下文 | 
  ✓ Scenario 5: 不遮挡 | 
  ⚠️ Scenario 4: 5s 内显示 (定位算法略慢) | 
  ✓ Scenario 2: 返回 3-4 个追问
</div>
```

## Verdict Symbols

| Symbol | 含义 | CSS class |
|--------|------|-----------|
| ✓ | 完全满足 | `.verdict-good` (绿色) |
| ⚠️ | 部分满足 / 风险 | `.verdict-warn` (黄色) |
| ❌ | 不满足 | `.verdict-bad` (红色) |

## BDD Scenarios to Cover (typical for AI 解释 / AI 浮层类)

For an inline-float or sidebar prototype, walk through these:

| Scenario | 验证点 | 常见 fail |
|----------|--------|----------|
| 选中文字得上下文解释 | LLM 响应包含项目关键词 | LLM 不调用 context |
| 解释返回 3-4 个推荐追问 | chips 数量 | 解析失败 |
| LLM 响应非 JSON 时降级 | 提示正常 + 不报错 | 抛错给用户 |
| 直调 LLM 延迟 < 5s | 视觉感知 | spawn node 太慢 |
| 浮层不与选区重叠 | boundingRect 检查 | 浮层超出视口 |
| 默认 cue 模式（Cornell）| 首次显示 1 行 | 默认就是完整解释 |
| 追问 LLM 知道前情 | previousQA 入 prompt | 丢失历史 |
| tab 切换浮层关闭 | 监听 activeTab 变化 | 浮层残留 |
| 浮层超出视口重定位 | smart positioning | 无 fallback |

## Why BDD Walking Matters

1. **避免纯美学对比** — BDD 走查把"好看"和"对错"分开
2. **量化优势** — "v2 满足 4/5 个场景" 比 "v2 更好看" 更有信息量
3. **指导实现** — TDD 可以针对⚠️ 项补测试

## Format for Multi-State Prototypes

When prototype shows 状态 1 / 2 / 3 (e.g., initial / 追问 / 多次追问), annotate each state:

```html
<!-- State 1: 首次响应 -->
<div class="stage-col">
  <h3>State 1 · 首次响应</h3>
  <span class="bdd-tag bdd-good">Scenario 1 ✓</span>
  ...
</div>

<!-- State 2: 1 次追问 -->
<div class="stage-col">
  <h3>State 2 · 1 次追问后</h3>
  <span class="bdd-tag bdd-good">Scenario 2 ✓ · 追问展开</span>
  ...
</div>
```

This makes it clear which states satisfy which scenarios without reading code.

## Verdict Block Style

```css
.verdict-good { color: #047857; }
.verdict-warn { color: #b45309; }
.verdict-bad  { color: #b91c1c; }
.bdd-tag { 
  display: inline-block;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 3px;
  margin-left: 4px;
}
.bdd-good { background: #d1fae5; color: #065f46; }
.bdd-warn { background: #fef3c7; color: #92400e; }
.bdd-bad  { background: #fee2e2; color: #991b1b; }
```
