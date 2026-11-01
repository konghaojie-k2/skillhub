---
name: tauri-icon
description: 为 Tauri 2 项目（Windows / macOS / Linux / iOS / Android）生成全套应用图标。流程：SVG 源文件 → cairosvg 渲染 1024×1024 PNG → `cargo tauri icon` 生成所有平台资源 → 校验 ICO 帧数。触发词："tauri 图标"、"做 ICO"、"app icon"、"换图标"、"cargo tauri icon"。
---

# tauri-icon

Tauri 2 项目做应用图标的完整管线。设计稿是 SVG，输出包含 `icon.ico` / `icon.icns` / `icon.png` / 各尺寸 PNG / iOS / Android 资源。

---

## 流程（三步）

### 1. 准备 1024×1024 PNG 源文件

设计稿交付的是 SVG（矢量、可改色）。但 Tauri 要求源文件是 **1024×1024 PNG**（像素确定、跨平台一致）。所以第一步用 cairosvg 一次性渲染：

```bash
python -c "
import cairosvg
cairosvg.svg2png(
    url='src-tauri/icons/app-icon.svg',
    write_to='src-tauri/icons/app-icon.png',
    output_width=1024,
    output_height=1024,
)
"
```

### 2. 用 `cargo tauri icon` 生成全套资源

```bash
cargo tauri icon src-tauri/icons/app-icon.png
```

这一条命令会生成：

- `icon.ico`（Windows，多帧 ICO）
- `icon.icns`（macOS）
- `icon.png`（256×256）
- `32x32.png` / `64x64.png` / `128x128.png` / `128x128@2x.png`（Windows）
- `Square*.png` / `StoreLogo.png`（Windows Store）
- `ios/` / `android/`（移动端资源）

> 走 `tauri.conf.json` 里 `bundle.icon` 引用的所有 PNG 都从同一份源文件生成，不会出现"时间炸弹"PNG。

### 3. 校验 ICO

```python
from PIL import Image
img = Image.open('src-tauri/icons/icon.ico')
print('ICO frames:', sorted(img.ico.sizes()))
```

正常应该有 6 帧：`[(16,16), (24,24), (32,32), (48,48), (64,64), (256,256)]`。

---

## 文件约定

```
src-tauri/icons/
├── app-icon.svg      # 设计稿（唯一手写文件）
├── app-icon.png      # cairosvg 一次性生成（1024×1024）
├── icon.ico          # tauri icon 生成
├── icon.icns         # tauri icon 生成
├── icon.png          # tauri icon 生成
└── 32x32.png / 64x64.png / 128x128.png / 128x128@2x.png  # tauri icon 生成
```

**不要手写脚本**（cairosvg + Pillow 拼 ICO），交给 `cargo tauri icon`。

---

## 常见错误

| 症状 | 原因 | 解决 |
|------|------|------|
| ICO 只有 1 帧 | 自己用 Pillow 写 ICO 时没把最大帧放第一 | 改用 `cargo tauri icon` |
| 部分 PNG 还是旧版本 | 自己脚本漏更新了 `tauri.conf.json` 引用的某个 PNG | 改用 `cargo tauri icon`，一次全生 |
| 小尺寸图标糊 | 手写脚本用 Pillow 在小画布上 `ImageDraw` 像素 | 改用 `cargo tauri icon`，工具内部用 `image` crate 做高质量缩放 |
| `tauri icon` 报输入无效 | 源文件不是 1024×1024 或没有 alpha 通道 | 检查 PNG 尺寸和 mode |
