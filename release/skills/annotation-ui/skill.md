---
name: annotation-ui
description: |
  交互式标注UI组件和后端API。用于创建案例、可视化数据、添加标注（点标注、区间标注、绘制标注）、管理标注、添加评论讨论。
  适用于需要构建数据标注和管理系统的场景。
---

# Annotation UI Skill

## 功能概述

本技能提供交互式标注UI组件和后端API，用于：
- 创建和管理案例
- 可视化数据图表
- 交互式标注（点标注、区间标注、绘制标注）
- 评论和讨论功能
- **缩放状态保持**（放大后添加标注不重置缩放）
- **增量更新标注**（不丢失原有曲线）
- **点击空白处添加标注**（支持任意位置标注）

## 技术栈

- **前端**: React + TypeScript + Tailwind CSS + **ECharts** (`echarts-for-react`)
- **后端**: FastAPI + Pydantic
- **存储**: JSON文件（可扩展为数据库）

## ECharts 图表组件

```tsx
import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts-for-react';

// 基础折线图示例
const chartOption: EChartsOption = {
  tooltip: { trigger: 'axis' },
  legend: { data: ['温度', '压力'] },
  xAxis: { type: 'time', data: [] },
  yAxis: { type: 'value' },
  series: [
    { name: '温度', type: 'line', data: [] },
    { name: '压力', type: 'line', data: [] }
  ]
};

<ReactECharts option={chartOption} style={{ height: 400 }} />
```

详见 [references/echarts.md](references/echarts.md)

## 快速开始

### 1. 后端API

```python
from fastapi import FastAPI
from app.api.case_routes import router as case_router

app = FastAPI()
app.include_router(case_router)
```

### 2. 前端组件

```tsx
import { CaseWorkspace } from './components/CaseWorkspace';
import { FeatureChart } from './components/FeatureChart';
```

### 3. 核心类型定义

详见 [references/types.md](references/types.md)

### 4. API接口

详见 [references/api.md](references/api.md)

## 核心概念

### 案例 (Case)

- **状态**: draft → active → resolved → archived
- **包含**: 设备列表、测点、时间范围、图表数据、标注、评论

### 标注 (Annotation)

- **类型**:
  - `point`: 点标注 {x, y}
  - `range`: 区间标注 {start_x, end_x}
  - `drawing`: 自由绘制 {points: [{x, y}]}
- **属性**: id, case_id, type, point_name, position, content, color, created_by, created_at

#### 缩放状态保持

**问题**：当用户放大图表后添加标注点，图表会重置到初始缩放状态

**解决方案**：
1. 使用 `useRef` 保存图表实例和缩放状态
2. 监听 `dataZoom` 事件保存缩放状态
3. 添加标注后使用 `dispatchAction` 恢复缩放状态

详见 [references/echarts.md](references/echarts.md#缩放状态保持)

#### 增量更新标注

**问题**：增量更新时只传标注系列，覆盖了原有的曲线数据

**解决方案**：
1. `chartOption` 的 `useMemo` 依赖**不要包含** `annotations`
2. 增量更新时过滤并保留原有系列，只更新标注系列
3. 使用 `lazyUpdate: true` 延迟更新

详见 [references/echarts.md](references/echarts.md#增量更新标注点保持缩放状态)

#### 点击空白处添加标注

支持点击图表空白区域添加标注点：

1. 使用 `chart.getZr()` 获取 zrender 实例
2. 监听 zrender 的 `click` 事件
3. 使用 `convertFromPixel` 将像素坐标转换为逻辑坐标
4. 找到最近的数据点并添加标注

详见 [references/echarts.md](references/echarts.md#点击空白处添加标注)

### 评论 (DiscussionComment)

- 支持回复
- 支持关联标注
- 可标记为已解决

## 参考文件

- [types.md](references/types.md) - 数据类型定义
- [api.md](references/api.md) - API接口文档
- [schemas.md](references/schemas.md) - Pydantic数据模型
- [echarts.md](references/echarts.md) - ECharts图表配置
