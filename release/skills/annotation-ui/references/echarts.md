# ECharts 图表配置

## 基础折线图

```tsx
import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts-for-react';

const option: EChartsOption = {
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'cross' }
  },
  legend: {
    data: ['温度', '压力', '能耗']
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'time',
    boundaryGap: false
  },
  yAxis: {
    type: 'value'
  },
  series: [
    {
      name: '温度',
      type: 'line',
      smooth: true,
      data: [
        ['2024-01-01 10:00', 850],
        ['2024-01-01 10:10', 860],
        ['2024-01-01 10:20', 870]
      ],
      markPoint: {
        data: [
          { type: 'max', name: '最大值' },
          { type: 'min', name: '最小值' }
        ]
      },
      markLine: {
        data: [
          { yAxis: 900, name: '阈值' }
        ]
      }
    }
  ]
};

<ReactECharts option={option} style={{ height: 400 }} />
```

## 多测点叠加

```tsx
const option: EChartsOption = {
  tooltip: { trigger: 'axis' },
  legend: { data: ['测点1', '测点2', '测点3'] },
  xAxis: { type: 'time' },
  yAxis: { type: 'value' },
  series: [
    { name: '测点1', type: 'line', data: [...] },
    { name: '测点2', type: 'line', data: [...] },
    { name: '测点3', type: 'line', data: [...] }
  ]
};
```

## 区间标注

```tsx
const option: EChartsOption = {
  // ... 基础配置
  series: [{
    type: 'line',
    data: [...],
    markArea: {
      itemStyle: { color: 'rgba(255, 173, 177, 0.4)' },
      data: [
        [
          { xAxis: '2024-01-01 10:00' },
          { xAxis: '2024-01-01 11:00' }
        ]
      ]
    }
  }]
};
```

## 点标注

```tsx
const option: EChartsOption = {
  series: [{
    type: 'line',
    data: [...],
    markPoint: {
      symbol: 'pin',
      symbolSize: 50,
      data: [
        { coord: ['2024-01-01 10:30', 880], value: '异常' }
      ]
    }
  }]
};
```

## 交互式点击事件

```tsx
const handleChartClick = (params: any) => {
  console.log('点击位置:', params);
  // 获取点击的坐标
  const { value, axisValue } = params;
  // 创建点标注
};

<ReactECharts
  option={option}
  onEvents={{ 'click': handleChartClick }}
/>
```

## 高级功能

### 缩放状态保持

当用户放大图表后添加标注点时，图表会重置到初始缩放状态。解决方案：

```tsx
import { useRef, useEffect } from 'react';

// 保存图表实例和缩放状态
const chartInstanceRef = useRef<any>(null);
const zoomStateRef = useRef<any>(null);

// 监听图表缩放状态变化并保存（保存所有轴的缩放状态）
useEffect(() => {
  if (chartInstanceRef.current) {
    const chart = chartInstanceRef.current;
    const handleDataZoom = () => {
      const option = chart.getOption();
      zoomStateRef.current = {
        xAxis: option.dataZoom?.[0] ? {
          start: option.dataZoom[0].start,
          end: option.dataZoom[0].end
        } : null,
        yAxisLeft: option.dataZoom?.[1] ? {
          start: option.dataZoom[1].start,
          end: option.dataZoom[1].end
        } : null,
        yAxisRight: option.dataZoom?.[3] ? {
          start: option.dataZoom[3].start,
          end: option.dataZoom[3].end
        } : null,
      };
    };
    chart.on('dataZoom', handleDataZoom);
    return () => {
      chart.off('dataZoom', handleDataZoom);
    };
  }
}, []);

// 当 annotations 变化时，恢复缩放状态（恢复所有轴）
useEffect(() => {
  if (chartInstanceRef.current && zoomStateRef.current) {
    setTimeout(() => {
      const chart = chartInstanceRef.current;
      if (chart && zoomStateRef.current) {
        // 恢复 X 轴缩放
        if (zoomStateRef.current.xAxis) {
          chart.dispatchAction({
            type: 'dataZoom',
            dataIndex: 0,
            start: zoomStateRef.current.xAxis.start,
            end: zoomStateRef.current.xAxis.end,
          });
        }
        // 恢复左 Y 轴缩放
        if (zoomStateRef.current.yAxisLeft) {
          chart.dispatchAction({
            type: 'dataZoom',
            dataIndex: 1,
            start: zoomStateRef.current.yAxisLeft.start,
            end: zoomStateRef.current.yAxisLeft.end,
          });
        }
        // 恢复右 Y 轴缩放
        if (zoomStateRef.current.yAxisRight) {
          chart.dispatchAction({
            type: 'dataZoom',
            dataIndex: 3,
            start: zoomStateRef.current.yAxisRight.start,
            end: zoomStateRef.current.yAxisRight.end,
          });
        }
      }
    }, 50);
  }
}, [annotations]);

// 获取图表实例
const onChartReady = (chart: any) => {
  chartInstanceRef.current = chart;
};

<ReactECharts
  option={option}
  onChartReady={onChartReady}
  onEvents={{ 'click': handleChartClick }}
/>
```

### 增量更新标注点（保持缩放状态）

关键原则：`chartOption` 的 `useMemo` 依赖**不要包含** `annotations`，避免每次添加标注都触发整个图表重新渲染。

```tsx
// ❌ 错误：chartOption 依赖 annotations，导致添加标注时整个图表重新渲染，缩放状态丢失
const chartOption = useMemo(() => {
  return { /* ... */ };
}, [chart, chartData, annotations]);

// ✅ 正确：chartOption 不依赖 annotations，通过增量更新添加标注
const chartOption = useMemo(() => {
  return { /* ... */ };
}, [chart, chartData]);

// 增量更新标注点（不触发完全重新渲染）
useEffect(() => {
  if (chartInstanceRef.current) {
    const chart = chartInstanceRef.current;
    const currentOption = chart.getOption();
    const currentSeries = currentOption.series || [];

    // 保留原有的非标注系列，只移除旧的标注系列
    const originalSeries = currentSeries.filter((s: any) => s.name !== '标注');

    // 添加新的标注点系列
    const annotationSeries = annotations.map((ann) => ({
      name: '标注',
      type: 'scatter',
      symbol: 'pin',
      symbolSize: 30,
      yAxisIndex: 0,
      data: [[ann.x, 0]],
      itemStyle: { color: ann.color || '#ef4444' },
      label: {
        show: true,
        position: 'top',
        formatter: () => new Date(ann.x).toLocaleString('zh-CN', {
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit'
        }),
        color: '#fff',
        fontSize: 10,
      },
    }));

    // 合并原有系列和标注系列
    chart.setOption({ series: [...originalSeries, ...annotationSeries] }, { lazyUpdate: true });
  }
}, [annotations]);
```

**注意**：增量更新时必须保留原有系列，否则会导致曲线丢失：

```tsx
// ❌ 错误：直接替换 series，导致原有曲线丢失
chart.setOption({ series: annotationSeries }, { lazyUpdate: true });

// ✅ 正确：保留原有曲线，只更新标注点
const originalSeries = currentSeries.filter((s: any) => s.name !== '标注');
chart.setOption({ series: [...originalSeries, ...annotationSeries] }, { lazyUpdate: true });
```

### 点击空白处添加标注

支持点击图表空白区域添加标注点：

```tsx
// 使用 ref 来存储最新的数据和回调
const seriesDataRef = useRef(seriesData);
useEffect(() => {
  seriesDataRef.current = seriesData;
}, [seriesData]);

// 使用 useEffect 直接在 chart 实例上注册 zrender 点击事件
useEffect(() => {
  const timeoutId = setTimeout(() => {
    const chartInstance = chartRef.current?.getEchartsInstance();
    if (!chartInstance) return;

    const zr = chartInstance.getZr();
    if (!zr) return;

    // 注册 zrender 点击事件
    const handler = (e: { offsetX: number; offsetY: number }) => {
      if (e.target) return; // 点击图形时，由 click 事件处理

      const instance = chartRef.current?.getEchartsInstance();
      if (!instance) return;

      // 将像素坐标转换为逻辑坐标
      const pointInGrid = instance.convertFromPixel('grid', [e.offsetX, e.offsetY]);

      if (pointInGrid && pointInGrid[0] !== null) {
        const clickedX = pointInGrid[0];
        const allPoints = Object.values(seriesDataRef.current).flat();

        if (allPoints.length === 0) return;

        // 找到最近的点
        const sortedByDistance = [...allPoints].sort((a, b) =>
          Math.abs(a.x - clickedX) - Math.abs(b.x - clickedX)
        );

        const mainPoint = sortedByDistance[0];
        if (mainPoint?.raw) {
          // 添加标注
          addAnnotation(mainPoint.x, mainPoint.y);
        }
      }
    };

    zr.on('click', handler);

    return () => {
      zr.off('click', handler);
    };
  }, 100);

  return () => clearTimeout(timeoutId);
}, []);
```

### 多Y轴支持

```tsx
const option: EChartsOption = {
  yAxis: [
    {
      type: 'value',
      name: '温度',
      position: 'left',
      axisLabel: { formatter: '{value} °C' }
    },
    {
      type: 'value',
      name: '压力',
      position: 'right',
      axisLabel: { formatter: '{value} MPa' }
    }
  ],
  series: [
    {
      name: '温度',
      type: 'line',
      yAxisIndex: 0,  // 使用第一个 Y 轴
      data: [...]
    },
    {
      name: '压力',
      type: 'line',
      yAxisIndex: 1,  // 使用第二个 Y 轴
      data: [...]
    }
  ]
};
```

## 常用配置

| 配置项 | 说明 |
|--------|------|
| `tooltip` | 提示框 |
| `legend` | 图例 |
| `grid` | 网格 |
| `xAxis/yAxis` | 坐标轴 |
| `series` | 数据系列 |
| `markPoint` | 标记点 |
| `markLine` | 标记线 |
| `markArea` | 标记区域 |
| `dataZoom` | 数据缩放 |

## 最佳实践

1. **保持缩放状态**：使用 `useRef` 保存图表实例和缩放状态
2. **增量更新**：`chartOption` 的 `useMemo` 依赖不要包含 `annotations`
3. **避免曲线丢失**：增量更新时必须保留原有系列数据
4. **性能优化**：使用 `lazyUpdate: true` 延迟更新
5. **多Y轴处理**：通过 `yAxisIndex` 指定系列使用的Y轴
