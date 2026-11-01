---
name: chart-viz-generator
description: 图表可视化配置生成器。通过上传图表截图，AI 识别图表元素，自动生成 .model-eval-viz.json 配置文件，并提供 matplotlib 图片预览。触发场景：(1) 需要快速创建可视化配置 (2) 根据截图生成图表 JSON (3) 预览生成的图表效果
---

# Chart Visualization Config Generator

根据图表截图，AI 识别后生成可视化配置 JSON，并提供图片预览功能。

## 核心功能

1. **图片识别** - 分析图表截图，提取图表元素
2. **JSON 生成** - 输出符合 .model-eval-viz.json 格式的配置
3. **图片预览** - 使用 matplotlib 生成图表预览图片

## 使用方式

### 基本流程

```
1. 用户提供图表截图（粘贴或上传）
2. AI 分析图片，识别图表元素
3. 生成 JSON 配置文件
4. 生成 matplotlib 图片预览
```

### Skill 触发词

- "生成图表配置"
- "根据图片生成可视化配置"
- "创建图表 JSON"
- "预览图表效果"

## 输入要求

### 图片格式

支持：
- PNG、JPG、JPEG、WebP
- 剪贴板粘贴
- 文件拖拽

### 图片内容

支持的图表类型：
- 折线图 (line)
- 柱状图 (bar)
- 散点图 (scatter)
- 面积图 (area)
- 多轴图表（双 Y 轴）

## 输出格式

### JSON 配置

生成的配置符合 .model-eval-viz.json 标准：

```json
{
  "version": "1.0",
  "description": "图表描述",
  "charts": [{
    "id": "chart-xxx",
    "title": "图表标题",
    "type": "line",
    "x_axis": { "field": "字段名", "label": "X轴" },
    "y_axis": { "field": "字段名", "label": "Y轴", "min": 0, "max": 100 },
    "series": [{
      "point_name": "数据字段",
      "label": "图例",
      "color": "#1f38f4",
      "y_axis_index": 0,
      "type": "line",
      "line_style": "solid"
    }],
    "annotations": []
  }],
  "global_settings": {
    "theme": "dark",
    "chart_height": 500
  }
}
```

### HTML 预览

生成独立 HTML 文件，包含：
- pyechart 图表渲染
- 模拟数据展示
- 可导出分享

## AI 识别内容

AI 会识别以下元素：

| 元素 | 说明 |
|------|------|
| 图表类型 | line, bar, scatter, area |
| X 轴 | 字段名、标签、范围 |
| Y 轴 | 字段名、标签、范围（支持双轴） |
| 数据系列 | 名称、颜色、线型、类型 |
| 标注 | 阈值线、区域、关键点 |

## 输出目录结构

所有生成的文件默认保存到 `.chart-viz/output/` 目录：

```
project-root/
├── .chart-viz/
│   └── output/
│       ├── chart_preview_20260325_105030.png    # 生成的图表图片
│       ├── .model-eval-viz.generated.json       # 生成的配置 JSON
│       └── chart_preview.html                   # HTML 预览文件（可选）
```

### 生成脚本位置

项目根目录下的脚本（由 skill 自动生成）：

| 脚本 | 用途 |
|------|------|
| `chart_viz_image.py` | 生成图表图片预览 |
| `chart_viz_preview.py` | 生成 HTML 预览（可选） |

### 使用方式

```bash
# 生成图片预览（默认保存到 .chart-viz/output/）
uv run python chart_viz_image.py <config.json>

# 指定自定义输出路径
uv run python chart_viz_image.py <config.json> /path/to/output.png
```

## 使用示例

### 示例 1：简单折线图

**输入**：一张显示温度变化的折线图截图

**AI 识别结果**：
- 图表类型：line
- X 轴：时间
- Y 轴：温度 (°C)
- 数据系列：温度曲线

**输出 JSON**：
```json
{
  "charts": [{
    "title": "温度变化趋势",
    "type": "line",
    "x_axis": { "field": "timestamp", "label": "时间" },
    "y_axis": { "field": "temperature", "label": "温度 (°C)" },
    "series": [{
      "point_name": "temperature",
      "label": "温度",
      "color": "#1f38f4",
      "type": "line",
      "line_style": "solid"
    }]
  }]
}
```

### 示例 2：双轴图表

**输入**：一张同时显示产量和成本的图表

**AI 识别结果**：
- 图表类型：line（双轴）
- 左 Y 轴：产量
- 右 Y 轴：成本
- 数据系列：产量曲线、成本曲线

## 配置 Schema

详细字段定义见 `config-schema.json`：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| version | string | 是 | 配置版本 |
| description | string | 否 | 图表描述 |
| charts | array | 是 | 图表数组 |
| global_settings | object | 否 | 全局设置 |

### Chart 对象

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | 唯一标识 |
| title | string | 是 | 图表标题 |
| type | string | 是 | 图表类型 |
| x_axis | object | 是 | X 轴配置 |
| y_axis | object | 是 | Y 轴配置 |
| y_axis2 | object | 否 | 右 Y 轴配置 |
| series | array | 是 | 数据系列 |
| annotations | array | 否 | 标注配置 |

## 预览功能

### 生成预览

```python
from pyechartgen import generate_html

# 根据 JSON 配置生成 HTML
html = generate_html(config_json, sample_data)
html.save("chart_preview.html")
```

### 模拟数据

预览使用模拟数据，自动根据配置生成：
- 时间序列：自动生成日期序列
- 数值序列：自动生成合理范围的数值

## 文件位置

Skill 文件存放：

```
C:\Users\17625\.claude\skills\chart-viz-generator\
├── SKILL.md                 # 本文件
├── config-schema.json       # 配置 Schema 定义
├── prompt.md                # AI 识别 prompt 模板
└── examples/                # 示例配置
    └── dual-axis-chart.json # 双轴图表示例
```

项目中的生成脚本（由 skill 自动创建）：

```
project-root/
├── chart_viz_image.py       # 图片生成脚本
└── .chart-viz/              # 输出目录
    └── output/              # 生成的图表图片
```

## 依赖

- matplotlib（用于生成图片预览）
- Python >= 3.10

## 注意事项

1. **图片质量**：上传清晰的图表截图，识别更准确
2. **字段推断**：AI 会根据图表内容推断字段名，可根据实际情况调整
3. **数据绑定**：生成的配置需与实际数据字段绑定才能用于生产环境
4. **预览**：预览使用模拟数据，仅用于验证配置格式正确性
