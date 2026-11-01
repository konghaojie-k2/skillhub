---
name: inline-visualizer
description: 在对话流中内嵌渲染 SVG 插画、流程图、架构图、示意图、数据图表、UI mockup、交互式控件。基于 read_me + show_widget 两个内置工具。触发词：画一个、画张图、画个插画、可视化、流程图、架构图、示意图、时序图、对比表、思维导图、illustration、diagram、chart、draw、visualize、show me。注意产出只在对话内嵌显示、不生成文件；需要导出成文件（PPT/Word/网页）请改用 tencent-pptx / html-to-docx / 发布为应用。
agent_created: true
---

# Inline Visualizer — 对话内嵌可视化

用 SVG / HTML 片段直接在对话里渲染视觉内容。**不产出文件**。

## 两个工具

| 工具 | 作用 |
|------|------|
| `read_me` | 加载设计规范模块，拿到 CSS 变量、色阶、字体、尺寸约束。**出图前必调** |
| `show_widget` | 真正渲染。传原始 SVG 或 HTML 片段 |

模块参数：`diagram` / `chart` / `art` / `mockup` / `interactive`，可传数组一次加载多个（如 `["diagram","chart"]`）。

调用 `show_widget` 需三个参数：`title`（同语言、可区分）、`widget_code`（代码片段）、`loading_messages`（JSON 字符串数组，1–4 条，每条约 5 字）。

## 模块怎么选

| 场景 | 模块 |
|------|------|
| 概念讲解、流程、架构、状态机、对比 | `diagram` |
| 数据趋势、占比、对比图表 | `chart` |
| 纯插画、氛围场景、装饰图形 | `art` |
| 表单、界面原型、UI 布局 | `mockup` |
| 可调参数的交互控件、模拟器 | `interactive` |

## 触发时机

用户明说"画/展示/可视化"时直接出图。以下情况**主动**出图：

- 教学类请求（讲概念、解释原理）—— 图比纯文字有效得多
- 对比两个方案 / 架构设计 / 解释系统结构
- 用户丢来一个可视物件的名词（"对比表""状态机""时序图"），物件本身就是请求

**复杂主题拆成多个 `show_widget`**，每个图之间用一段文字串起来，不要连续堆叠无文字的图。

---

## 硬约束（违反会渲染异常）

**画布**
- SVG 根：`viewBox="0 0 680 H"` + `width="100%"`。**680 不能改**，所有坐标以它为准
- `H` = 最底部元素 y + 20，不要拍脑袋猜
- 安全区 x 40–640、y 40–(H−40)；背景透明（宿主提供底色）
- 一次调用一个 SVG

**禁用**
- 渐变、阴影、模糊、发光、霓虹（流式渲染会闪，用纯色分层代替）
- `<!-- -->` 和 `/* */` 注释（浪费 token 且打断流式渲染）
- emoji（用 CSS 形状或 SVG path）
- `position: fixed`、`<!DOCTYPE>` / `<html>` / `<head>` / `<body>`
- 旋转文字
- 字号 < 11px
- 字重只允许 400 / 500，**禁止 600 / 700**
- 容器深色背景（外层必须透明）

**排版**
- h1 15px / h2 14px / h3 13px，全部 weight 500；正文 13px weight 400，行高 1.6
- 一律 sentence case，禁止 Title Case 和全大写
- `<style>` 块控制在 15 行内；优先 inline `style="..."`，控件要在流式过程中就长得对

**可访问性**
- SVG：`role="img"` + `<title>` / `<desc>` 作为**最先的子元素**
- HTML：开头加视觉隐藏的 `<h2 class="sr-only">` 一句话摘要

**文字放响应里，图里只放视觉。** 解释、说明、总结都写在 `show_widget` 外面。

## 流式渲染顺序

- **HTML**：`<style>` → 内容 → `<script>`（放最后）
- **SVG**：`<defs>` → 立刻接视觉元素

## 配色

9 个色阶 × 7 级（50 最浅 → 900 最深，400 中间调，600 描边，800/900 文字）：

| 色阶 | 50 | 100 | 200 | 400 | 600 | 800 | 900 |
|------|----|-----|-----|-----|-----|-----|-----|
| c-purple | #EEEDFE | #CECBF6 | #AFA9EC | #7F77DD | #534AB7 | #3C3489 | #26215C |
| c-teal | #E1F5EE | #9FE1CB | #5DCAA5 | #1D9E75 | #0F6E56 | #085041 | #04342C |
| c-coral | #FAECE7 | #F5C4B3 | #F0997B | #D85A30 | #993C1D | #712B13 | #4A1B0C |
| c-pink | #FBEAF0 | #F4C0D1 | #ED93B1 | #D4537E | #993556 | #72243E | #4B1528 |
| c-gray | #F1EFE8 | #D3D1C7 | #B4B2A9 | #888780 | #5F5E5A | #444441 | #2C2C2A |
| c-blue | #E6F1FB | #B5D4F4 | #85B7EB | #378ADD | #185FA5 | #0C447C | #042C53 |
| c-green | #EAF3DE | #C0DD97 | #97C459 | #639922 | #3B6D11 | #27500A | #173404 |
| c-amber | #FAEEDA | #FAC775 | #EF9F27 | #BA7517 | #854F0B | #633806 | #412402 |
| c-red | #FCEBEB | #F7C1C1 | #F09595 | #E24B4A | #A32D2D | #791F1F | #501313 |

**主题配色公式**
- 浅色主题：50 填充 + 600 描边 + **800 标题 / 600 副标题**
- 深色主题：800 填充 + 200 描边 + **100 标题 / 200 副标题**

跟随 `<user_info>` 里的 `IDE Theme` 字段。需要自适应的地方用 CSS 变量（`var(--color-border-secondary)` 等）而非写死颜色。

**颜色类未实现**——`class="c-purple"` 之类不生效，每个形状必须 inline 写 `fill`。

**复杂度预算**：单个盒子副标题 ≤ 5 词；每个图 ≤ 2 个色阶；满宽横向一层 ≤ 4 个盒子（每个约 140px）。

---

## 配方 A · Diagram

- 图表类描边统一 `0.5px`
- 每个作连接线的 `<path>` / `<polyline>` 必须 `fill="none"`
- `<defs>` 里必须放箭头 marker：

```svg
<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5"
    markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke"
      stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
  </marker>
</defs>
```

**预置 class**：`t`（14px 正文）、`ts`（12px 次要）、`th`（14px 500）、`box`（中性矩形）、`node`（可点击带 hover）、`arr`（箭头线）、`leader`（虚线引出线）

**盒宽公式**：`rect_width = max(标题字数 × 7, 副标题字数 × 6) + 24`

**字宽校准**（估算文字占宽用）：

| 用途 | 字数 | 字重 | 字号 | 渲染宽度 |
|------|------|------|------|---------|
| 标题 | 12 | 500 | 14px | ~88px |
| 副标题 | 16 | 400 | 13px | ~104px |
| 正文 | 24 | 400 | 13px | ~156px |
| 说明 | 20 | 400 | 12px | ~120px |

## 配方 B · Chart

用 Chart.js（CDN 白名单内：`cdnjs.cloudflare.com` / `esm.sh` / `cdn.jsdelivr.net` / `unpkg.com`）。

**A 股/中国用户惯例：涨红跌绿**，与欧美相反。货币符号默认 ¥。

## 配方 C · Art（插画）

前两条"硬约束"里禁渐变、禁模糊这两条对插画**同样适用**——深度靠**不透明色块分层**堆出来，不靠特效。

与 diagram 的区别：鼓励填满画布、色彩更奔放、用有机曲线（`<path>` 曲线 / `<ellipse>` / `<circle>`）。

**构图手法**
- 纹理用重复（平行线、点阵、排线），不用滤镜
- 径向对称用 `<g transform="rotate()">` 复制
- 混用多个色阶大类（info 蓝 + success 绿 + warning 琥珀）画面才不单调

### 圆形构图（常用且容易翻车）

用 `clipPath` 把画面裁进圆里，效果好，但**元素坐标必须反算**，否则边上元素被裁掉。

给定圆心 `(cx, cy)` 半径 `r`，在高度 `y` 处的可见半宽：

```
dx = sqrt(r² − (y − cy)²)
可见 x 范围：[cx − dx, cx + dx]
```

**算例**（cx=340, cy=240, r=190，岸线 y=372）：
`dx = sqrt(190² − 132²) = sqrt(36100 − 17424) = sqrt(18676) ≈ 136.7` → x ∈ [203.3, 476.7]
所以底部站立的树只能放在 203–477 之间，放 185 或 512 会被裁掉。

**用 `scripts/arc-fit.py` 算，别手算**：
```bash
python scripts/arc-fit.py 340 240 190 372 388 400 412    # 查多个 y 的可见 x 范围
python scripts/arc-fit.py --rect 340 240 190 185 372 81 68  # 检查矩形是否完整在圆内
```

**多层元素的 y 越往上圆越宽**，所以底部窄、顶部宽，构图时垂直方向要分别核算。

### 绘制顺序（z-order）

后画的盖住先画的。规划顺序，例如夜景：
天空底 → 暮光带 → 极光帘（半透明叠层）→ 月亮 → 星星 → 远山 → 近山 → 湖面 → 倒影 → 前景剪影

**取舍示例**：物理上极光在月亮前面，但让月亮压在极光之上，月亮才是清晰焦点；按物理顺序画月亮会被三层半透明帘子压得发灰。艺术正确性优先于物理正确性。

## 配方 D · Mockup

还原界面原型，注意控件在流式渲染中途就要长得对（优先 inline style）。

## 配方 E · Interactive

`<script>` 放最后。CDN 只能用白名单里的四个。

---

## 常见错误

| 现象 | 原因 | 修法 |
|------|------|------|
| 图形被裁掉一角 | 圆形/异形 clip 下坐标没反算 | 用 arc-fit.py 核算 |
| 流式渲染时闪烁 | 用了渐变/阴影/模糊 | 换纯色分层 |
| 文字溢出盒子 | 没用字宽校准表估算 | 按 `字数×7`（标题）/ `×6`（副标题）反推盒宽 |
| 颜色全黑 | 用了 `class="c-xxx"` 而没写 inline fill | 每个形状 inline 写 `fill` |
| 箭头不显示 | `<path>` 缺 `fill="none"` 或没定义 marker | 补 `fill="none"` + `<defs>` 里加 marker |
| 深色主题看不清 | 写死了颜色 | 改 CSS 变量或按主题配色公式换级 |
| 图里塞了大段文字 | 文字应该放响应正文 | 移到 `show_widget` 外面 |

## 导出成文件

内嵌渲染不落盘。要文件走别的路：
- PPT → `tencent-pptx`
- Word → `html-to-docx`
- 网页/分享链接 → 发布为应用（`workbuddy_sites_deploy`）
- 图片 → `ImageGen`（注意那是 AI 生图，不是 SVG）
