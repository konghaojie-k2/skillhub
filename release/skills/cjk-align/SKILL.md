---
name: cjk-align
description: 修复网页/Markdown 预览中"含中文的 ASCII 线框图/表格/对齐注释"错位或溢出裁切的问题。核心算法：canvas 实测拉丁与 CJK 字宽 → letter-spacing 补偿使 CJK 恒占 2 列 → 过宽代码块等比缩小字号。当用户遇到代码块里 ASCII 图右边框漂移、对不齐、被裁切、出现横向滚动条，或要在自己项目（Web 应用、文档站、Tauri/Electron 应用）中集成此修复时使用。
---

# CJK Align — 代码块中西文混排等宽对齐

## 问题本质

等宽代码块字体栈（JetBrains Mono / Consolas / ...）**不含 CJK 字形**，中文回退到系统字体（微软雅黑等）。回退字体的中文字宽 ≠ 2 × 拉丁等宽字宽，而 ASCII 线框图是按「中文 = 2 列」绘制的：

```
行宽误差 = (cjk实际宽度 − 2×拉丁宽度) × 该行中文字数
```

中文越多的行漂移越远（阶梯状错位），最宽行超出容器即被 `overflow` 裁切。**不同环境回退字体不同，偏差方向都可能不同**（可能偏宽也可能偏窄）——所以必须实测，不能写死。

## 算法（四步）

1. **实测字宽**：canvas `measureText`，用目标元素的 computed font 字符串，测 `'0'×20` 和 `'中'×10` 取平均 → `latin`、`cjk`
2. **补偿量**：`diff = 2×latin − cjk`；`|diff| < 0.3px` 视为已对齐（零侵入，装了 Sarasa Mono 等 2:1 字体时自动跳过）
3. **包 span**：TreeWalker 遍历文本节点，连续 CJK 段包 `<span class="cjk-align">`，`letter-spacing = diff/fontSize em`。**必须用 em 不用 px**——字号变化时补偿自动等比跟随
4. **过宽自适应**：`scrollWidth > clientWidth` 时 `fontSize ×= (usable/content)` 等比缩小，下限 9px（再小宁可保留滚动条）

## 集成方法

```html
<script src="scripts/cjk-align.js"></script>
<script>
  // 在代码块 DOM 就绪、语法高亮（Prism/highlight.js）之后调用
  CJKAlign.apply(container);  // container 为包含 pre code 的祖先元素
</script>
```

```css
pre code .cjk-align { letter-spacing: var(--cjk-letter-spacing, 0px); }
```

模块为 UMD（浏览器挂 `window.CJKAlign`，Node 可 `require` 测纯函数）。复制 `scripts/cjk-align.js` 进目标项目即可，零依赖。

### 接入检查清单

- [ ] 在语法高亮**之后**调用（TreeWalker 能穿透高亮 span；高亮若在之后会冲掉 span）
- [ ] CSS 变量 `--cjk-letter-spacing` 由 JS 设在 `code` 元素上，继承到 span
- [ ] 跳过 `pre.mermaid` 等非文本代码块（模块已内置）
- [ ] 复制/下载功能走 `textContent` 即不受 span 影响（innerHTML 才会带 span）

## 坑（都是实测踩过的）

- **padding 不参与字号缩放**：过宽判断必须 `scrollWidth − paddingH` 对 `clientWidth − paddingH`，否则留残差溢出
- **scrollWidth 整数取整 + 滚动条抖动**：可用宽度再减 2px 安全余量
- **全角字符也要算 CJK**：正则须覆盖 `，。（）：；`、全角空格 U+3000、全角 ASCII（U+FF00–FF60）
- **盒线字符 `─│┌┐▼` 不算 CJK**：它们由 Latin 等宽字体提供，占 1 列，不要包 span
- **`/g` 正则复用要重置 `lastIndex`**（或每次新建 RegExp）

## 验证

用 Playwright 在真实浏览器断言，不要"看一眼觉得对了"：

```bash
uv run --no-project --with playwright python scripts/verify_alignment.py <page.html> [--selector "pre code"]
```

`page.html` 需含 `<pre><code>` 块并引入 `cjk-align.js`。脚本断言：

- 每行渲染宽度 ≈ 设计列数 × 拉丁字宽（CJK 计 2 列；容差与行宽成正比，吸收亚像素取整）
- apply 后横向溢出 ≤ 2px
- apply 后偏差必须小于 apply 前

退出码 0 = PASS。页面应至少包含一行纯 ASCII 宽行（如线框图顶边框）作为字宽基准。

## 纯函数 API（可单测，DOM 无关）

| 函数 | 说明 |
|---|---|
| `containsCJK(text)` | 是否含 CJK/全角字符 |
| `splitRuns(text)` | 切分为 `[{text, cjk}]` 段 |
| `computeLetterSpacing(latinW, cjkW)` | px 补偿值，已对齐返回 null |
| `computeFitFontSize(contentW, usableW, fontPx, minPx)` | 自适应新字号，无需缩放返回 null |
| `pxToEm(diffPx, fontSizePx)` | px → em 换算 |
