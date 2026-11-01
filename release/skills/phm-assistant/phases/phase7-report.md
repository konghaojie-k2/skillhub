# Phase 7: 诊断报告 (Diagnostic Report)

## 目的

生成完整的诊断报告，包括数据分析结果、异常定位、根因分析和改进建议。

## 报告结构

### 1. 执行摘要

```python
def generate_executive_summary(health_scores: dict, diagnosis: dict) -> str:
    """生成执行摘要"""
    equipment_score = health_scores["equipment_score"]

    if equipment_score >= 0.8:
        status = "✅ 正常"
        summary = "设备运行状态良好，各项指标正常。"
    elif equipment_score >= 0.6:
        status = "⚠️ 预警"
        summary = "设备存在轻微异常，建议关注。"
    else:
        status = "🚨 报警"
        summary = "设备存在严重异常，建议立即检修。"

    return f"""
## 执行摘要

| 指标 | 状态 |
|------|------|
| 设备健康分 | {equipment_score:.2f} ({status}) |
| 异常部件数 | {len([s for s in health_scores['component_scores'].values() if s < 0.6])} |
| 异常测点数 | {len([s for s in health_scores['metric_scores'].values() if s < 0.6])} |

{summary}
"""
```

### 2. 详细分析

```python
def generate_detailed_analysis(health_scores: dict, metric_deviations: dict) -> str:
    """生成详细分析"""
    lines = ["## 详细分析\n"]

    # 部件分析
    lines.append("### 部件健康状态\n")
    lines.append("| 部件 | 健康分 | 状态 |")
    lines.append("|------|--------|------|")

    for comp, score in health_scores["component_scores"].items():
        if score >= 0.8:
            status = "✅ 正常"
        elif score >= 0.6:
            status = "⚠️ 预警"
        else:
            status = "🚨 报警"

        lines.append(f"| {comp} | {score:.2f} | {status} |")

    # 测点分析
    lines.append("\n### 测点偏差分析\n")
    lines.append("| 测点 | 偏差率 | 状态 |")
    lines.append("|------|--------|------|")

    for metric, deviation in metric_deviations.items():
        ratio = deviation.get("out_ratio", 0)
        if ratio < 0.1:
            status = "✅ 正常"
        elif ratio < 0.3:
            status = "⚠️ 预警"
        else:
            status = "🚨 报警"

        lines.append(f"| {metric} | {ratio:.1%} | {status} |")

    return "\n".join(lines)
```

### 3. 根因分析

```python
def generate_root_cause_analysis(diagnosis: dict) -> str:
    """生成根因分析"""
    lines = ["## 根因分析\n"]

    for item in diagnosis:
        anomaly = item.get("anomaly", {})
        causes = item.get("possible_causes", [])

        lines.append(f"### {anomaly.get('component', anomaly.get('metric', 'Unknown'))}")
        lines.append(f"**可能原因:**")
        for cause in causes:
            lines.append(f"- {cause}")

    return "\n".join(lines)
```

### 4. 改进建议

```python
def generate_recommendations(alarm_triggers: list, knowledge_base: dict) -> str:
    """生成改进建议"""
    lines = ["## 改进建议\n"]

    # 基于触发器的建议
    for trigger in alarm_triggers:
        lines.append(f"### {trigger.get('rule', 'Unknown')}")
        lines.append(trigger.get("message", ""))

    # 基于知识库的建议
    lines.append("\n### 维护建议")
    lines.append("- 定期巡检关键部件")
    lines.append("- 建立设备健康档案")
    lines.append("- 优化运行参数")

    return "\n".join(lines)
```

## 报告输出格式

### Markdown 格式

```markdown
# 设备健康诊断报告

**设备:** pump_001 (离心泵)
**生成时间:** 2026-03-17 10:30:00
**分析周期:** 2026-03-01 ~ 2026-03-17

---

## 执行摘要

| 指标 | 状态 |
|------|------|
| 设备健康分 | 0.72 (⚠️ 预警) |
| 异常部件数 | 1 |
| 异常测点数 | 2 |

设备存在轻微异常，建议关注轴承组件状态。

---

## 详细分析

### 部件健康状态

| 部件 | 健康分 | 状态 |
|------|--------|------|
| bearing | 0.58 | 🚨 报警 |
| seal | 0.85 | ✅ 正常 |
| motor | 0.92 | ✅ 正常 |

### 测点偏差分析

| 测点 | 偏差率 | 状态 |
|------|--------|------|
| vibration_x | 32% | 🚨 报警 |
| vibration_y | 18% | ⚠️ 预警 |
| bearing_temp | 8% | ✅ 正常 |

---

## 根因分析

### bearing (轴承)

**可能原因:**
- 轴承磨损
- 润滑不良
- 安装不当

---

## 改进建议

### 报警规则触发

- **low_equipment_score**: 设备健康分 0.72 低于阈值 0.6

### 维护建议

1. 建议立即安排检修
2. 检查轴承润滑状态
3. 准备备件
4. 加强设备监控频率

---

**报告生成:** PHM Assistant v0.2.0
```

### JSON 格式

```json
{
  "report": {
    "device_id": "pump_001",
    "device_type": "centrifugal_pump",
    "generated_at": "2026-03-17T10:30:00Z",
    "analysis_period": {
      "start": "2026-03-01",
      "end": "2026-03-17"
    }
  },
  "summary": {
    "equipment_score": 0.72,
    "status": "warning",
    "anomaly_components": 1,
    "anomaly_metrics": 2
  },
  "component_scores": {
    "bearing": 0.58,
    "seal": 0.85,
    "motor": 0.92
  },
  "metric_deviations": {
    "vibration_x": {"out_ratio": 0.32, "status": "alarm"},
    "vibration_y": {"out_ratio": 0.18, "status": "warning"},
    "bearing_temp": {"out_ratio": 0.08, "status": "normal"}
  },
  "diagnosis": [
    {
      "component": "bearing",
      "possible_causes": ["轴承磨损", "润滑不良", "安装不当"],
      "recommendations": ["检查轴承状态", "检查润滑系统", "重新安装"]
    }
  ],
  "recommendations": [
    "建议立即安排检修",
    "检查轴承润滑状态",
    "准备备件"
  ]
}
```

## 生成代码结构

```python
# report_generator.py
class ReportGenerator:
    def __init__(self, config: dict):
        self.config = config

    def generate(self, health_scores: dict, metric_deviations: dict,
                 diagnosis: dict, alarm_triggers: list) -> str:
        """生成完整报告"""

        sections = [
            self.generate_header(),
            self.generate_executive_summary(health_scores),
            self.generate_detailed_analysis(health_scores, metric_deviations),
            self.generate_root_cause_analysis(diagnosis),
            self.generate_recommendations(alarm_triggers),
            self.generate_footer()
        ]

        return "\n\n".join(sections)

    def save(self, content: str, format: str = "markdown"):
        """保存报告"""
        if format == "markdown":
            with open("report.md", "w", encoding="utf-8") as f:
                f.write(content)
        elif format == "json":
            # 转换为 JSON
            pass
```

## 询问话术

```
📊 诊断报告生成中...

【报告内容预览】

1. 执行摘要
   - 设备健康分: 0.72 (⚠️ 预警)
   - 异常部件: 轴承
   - 异常测点: vibration_x, vibration_y

2. 详细分析
   - 部件健康状态表格
   - 测点偏差分析表格

3. 根因分析
   - 轴承: 可能是轴承磨损/润滑不良

4. 改进建议
   - 建议立即安排检修
   - 检查轴承润滑状态

报告将保存为:
├── report.md (Markdown 格式)
└── report.json (JSON 格式)

[确认] 报告生成完成
[导出] 需要其他格式吗？
```

## 输出文件结构

```
phm_pump_001/
├── data_prep.py          # 数据准备模块
├── model_training.py     # 模型训练模块
├── deviation_analysis.py  # 偏差分析模块
├── health_score.py       # 健康评分模块
├── diagnosis.py          # 诊断分析模块
├── report_generator.py   # 报告生成模块
├── main.py              # 主入口
├── config/
│   ├── device_config.yaml
│   ├── hierarchy.yaml
│   ├── model.yaml
│   ├── alarm_rules.yaml
│   ├── health_score.yaml
│   └── knowledge_base.yaml
├── requirements.txt
└── README.md            # 部署文档
```
