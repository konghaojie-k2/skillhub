---
name: iconforge
description: 为项目生成全套桌面图标。流程：询问偏好 → 读取项目代码提取品牌色/关键词 → 调用 canvas-design/brand-guidelines 设计图标 → 多尺寸组图输出。触发词："生成图标"、"icon"、"ico"、"应用图标"、"app icon"、"换图标"。
---

# iconforge

为项目从零设计并生成全套桌面图标（.ico / .icns / 多尺寸 PNG / favicon）。

---

## 流程（四步）

### Step 1: 询问用户偏好

必须先和用户确认以下信息（用 AskUserQuestion，一次性问完）：

1. **目标项目路径** — 要生成哪个项目的图标？默认当前工作目录
2. **图标风格** — 极简线性 / 渐变现代 / 扁平纯色 / 拟物 / 3D / 手绘
3. **图标类型** — 纯符号 logo / 项目名首字母 / 图形+文字组合
4. **色彩偏好** — 跟随项目品牌色（推荐）/ 自定义主色和辅色
5. **参考方向** — 有没有喜欢的参考？（Material Design / SF Symbols / macOS Big Sur / 自定义描述）

> 不要跳过这一步直接生成。用户可能第一次用，需要引导。

### Step 2: 读取项目代码

运行项目分析，提取品牌信息：

```bash
cd C:\cc-project\iconforge
uv run iconforge analyze "<项目路径>"
```

从输出 JSON 中获取：
- `name` — 项目名（用于图标文案、文件命名）
- `description` — 项目用途（影响图标隐喻）
- `primary_color` / `secondary_color` — 品牌色（如有）
- `keywords` — 关键词（如 "music", "AI", "image"）
- `tech_stack` — 技术栈（可能影响风格：Tauri 偏现代、FastAPI 偏简洁）
- `has_existing_logo` — 是否已有 logo（如有，优先基于现有 logo 优化而非从零设计）

**如果 `primary_color` 为空**，从 `description` 和 `keywords` 推断：
- music/audio → 紫蓝渐变
- AI/ML → 科技蓝/深紫
- photo/image → 暖色/橙粉
- tool/cli → 灰绿/极简黑白
- game → 鲜艳撞色

### Step 3: 调用设计 Skill 生成图标 SVG

基于 Step 1-2 的结果，按以下优先级调用设计 skill：

#### 3a. brand-guidelines（如有品牌色）
如果项目有明确的 primary_color + secondary_color，先调用 brand-guidelines 确定色彩体系、字体、图标风格方向。

#### 3b. canvas-design（主设计）
传入以下约束，让 canvas-design 生成 SVG 图标：
- **尺寸**: 1024×1024
- **风格**: 用户选的风格 + 品牌色
- **用途**: 桌面图标（需要在 16×16 缩小时仍可辨识，避免过细线条）
- **背景**: 圆角矩形（squircle）或纯透明
- **输出**: 单个 SVG 文件，保存到项目 `assets/` 或 `src-tauri/icons/`

> 关键约束：告诉 canvas-design "这是一个桌面应用图标，要经得起缩放到 16×16。线条不能太细（至少 2px），负空间要足够，颜色对比度要高。"

#### 3c. ui-ux-pro-max（可读性校验）
可选：用 ui-ux-pro-max 检查图标在多尺寸下的可读性。

### Step 4: 多尺寸组图输出

设计稿 SVG 确认后，用 iconforge CLI 渲染全部尺寸：

```bash
cd C:\cc-project\iconforge
uv run iconforge generate <icon.svg> -o <项目路径>/assets/icons/ --name <项目名> --platform all
```

输出：

```
assets/icons/
├── <name>.ico          # Windows（16/32/48/256）
├── <name>.icns         # macOS（32~1024，含 @2x）
├── favicon.ico         # Web favicon（16/32/48）
├── <name>-16.png
├── <name>-32.png
├── <name>-48.png
├── <name>-64.png
├── <name>-128.png
├── <name>-180.png      # Apple Touch
├── <name>-192.png      # Android/PWA
├── <name>-256.png
├── <name>-512.png      # PWA Splash
└── <name>-1024.png     # 原始尺寸
```

> 如果目标项目是 **Tauri** 项目且存在 `src-tauri/icons/`，则用 `cargo tauri icon` 代替（Tauri 有额外的移动端资源需求）。

---

## 各项目类型的特殊处理

| 项目类型 | 图标输出位置 | 特殊处理 |
|----------|-------------|---------|
| Python (pyproject.toml) | `assets/icons/` | 标准 pipeline |
| Node.js (package.json) | `public/icons/` 或 `assets/icons/` | 标准 pipeline |
| Tauri (tauri.conf.json) | `src-tauri/icons/` | 用 `cargo tauri icon` 代替 iconforge generate |
| Web 前端 | `public/` | 额外生成 `favicon.ico` + `apple-touch-icon.png` + `manifest.json` 引用 |

---

## 尺寸判断标准

图标缩小后是否可读？检查清单：
- [ ] 16×16：图形轮廓仍可辨识，不糊成一团
- [ ] 32×32：细节开始可见
- [ ] 48×48：windows 任务栏清晰
- [ ] 256×256：完整细节
- [ ] 圆角是否在缩小后仍有视觉意义？

如果 16×16 不可读，通知用户并提供两个选项：
1. 简化图标（去掉细节，只留核心轮廓）
2. 为小尺寸单独提供简化版

---

## iconforge CLI 依赖

确保 `C:\cc-project\iconforge` 已 `uv sync`，且安装了 cairosvg：

```bash
cd C:\cc-project\iconforge
uv sync
uv pip install cairosvg
```
