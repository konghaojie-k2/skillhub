# Phase 2: 数据分析 (Data Analysis)

## 目的

基于数据分析和领域知识，智能推荐测点类型和建模策略。

## 数据分析流程

### 2.1 基础统计分析

```python
def basic_statistics(data: pd.DataFrame) -> dict:
    """基础统计分析"""
    stats = {
        "row_count": len(data),
        "column_count": len(data.columns),
        "time_range": {
            "start": str(data.index.min()),
            "end": str(data.index.max()),
            "days": (data.index.max() - data.index.min()).days
        },
        "columns": {}
    }

    for col in data.columns:
        stats["columns"][col] = {
            "dtype": str(data[col].dtype),
            "missing_ratio": data[col].isnull().mean(),
            "unique_count": data[col].nunique(),
            "mean": data[col].mean() if data[col].dtype in ['int64', 'float64'] else None,
            "std": data[col].std() if data[col].dtype in ['int64', 'float64'] else None,
            "min": data[col].min() if data[col].dtype in ['int64', 'float64'] else None,
            "max": data[col].max() if data[col].dtype in ['int64', 'float64'] else None,
        }

    return stats
```

### 2.2 相关性分析

```python
def correlation_analysis(data: pd.DataFrame) -> dict:
    """相关性分析"""
    import numpy as np

    numeric_cols = data.select_dtypes(include=[np.number]).columns
    corr_matrix = data[numeric_cols].corr()

    return {
        "correlation_matrix": corr_matrix.to_dict(),
        "strong_correlations": find_strong_correlations(corr_matrix)
    }


def find_strong_correlations(corr_matrix: pd.DataFrame, threshold: float = 0.7) -> list:
    """找出强相关对"""
    strong = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i+1, len(corr_matrix.columns)):
            corr = corr_matrix.iloc[i, j]
            if abs(corr) > threshold:
                strong.append({
                    "col1": corr_matrix.columns[i],
                    "col2": corr_matrix.columns[j],
                    "correlation": corr
                })
    return sorted(strong, key=lambda x: abs(x["correlation"]), reverse=True)
```

### 2.3 变化模式分析

```python
def change_pattern_analysis(data: pd.DataFrame) -> dict:
    """变化模式分析"""
    import numpy as np

    patterns = {}

    for col in data.columns:
        if data[col].dtype in ['int64', 'float64']:
            # 计算变化率
            diff = data[col].diff().dropna()
            patterns[col] = {
                "mean_change": diff.mean(),
                "std_change": diff.std(),
                "max_change": diff.max(),
                "min_change": diff.min(),
                "zero_ratio": (diff == 0).mean(),  # 稳定信号
                "changing_ratio": (diff != 0).mean()  # 变化信号
            }

    return patterns
```

## 智能推荐策略

### 3.1 领域知识规则

```python
DOMAIN_RULES = {
    "centrifugal_pump": {
        "likely_targets": ["vibration", "bearing_temp", "seal_pressure", "flow_deviation"],
        "likely_factors": ["rpm", "load", "flow_rate", "inlet_pressure", "outlet_pressure"],
        "critical_metrics": {
            "vibration": {"component": "bearing", "alarm_threshold": 10.0, "unit": "mm/s"},
            "bearing_temp": {"component": "bearing", "alarm_threshold": 80.0, "unit": "°C"},
            "seal_pressure": {"component": "seal", "alarm_threshold": 5.0, "unit": "bar"}
        }
    },
    "motor": {
        "likely_targets": ["winding_temp", "vibration", "current", "power_factor"],
        "likely_factors": ["load", "rpm", "ambient_temp", "voltage"],
        "critical_metrics": {
            "winding_temp": {"component": "stator", "alarm_threshold": 120.0, "unit": "°C"},
            "vibration": {"component": "bearing", "alarm_threshold": 7.0, "unit": "mm/s"}
        }
    },
    "compressor": {
        "likely_targets": ["discharge_temp", "oil_temp", "vibration", "pressure_ratio"],
        "likely_factors": ["rpm", "load", "inlet_temp", "cooling_water_flow"],
        "critical_metrics": {
            "discharge_temp": {"component": "cylinder", "alarm_threshold": 180.0, "unit": "°C"},
            "oil_temp": {"component": "lubrication", "alarm_threshold": 70.0, "unit": "°C"}
        }
    }
}


def recommend_metric_types(data: pd.DataFrame, device_type: str) -> dict:
    """基于领域知识推荐测点类型"""
    import numpy as np

    recommendations = {
        "targets": [],
        "factors": [],
        "target_factor_mapping": {}
    }

    # 获取领域规则
    rules = DOMAIN_RULES.get(device_type, {})
    likely_targets = rules.get("likely_targets", [])
    likely_factors = rules.get("likely_factors", [])
    critical_metrics = rules.get("critical_metrics", {})

    # 匹配测点
    columns_lower = {c.lower(): c for c in data.columns}

    # 推荐观测量
    for target in likely_targets:
        for pattern, col in columns_lower.items():
            if target in pattern:
                recommendations["targets"].append({
                    "metric": col,
                    "confidence": 0.9 if target in critical_metrics else 0.7,
                    "reason": f"{device_type} 关键健康指标",
                    "component": critical_metrics.get(target, {}).get("component"),
                    "alarm_threshold": critical_metrics.get(target, {}).get("alarm_threshold")
                })

    # 推荐因子量
    for factor in likely_factors:
        for pattern, col in columns_lower.items():
            if factor in pattern:
                recommendations["factors"].append({
                    "metric": col,
                    "type": "operating_condition",
                    "confidence": 0.8,
                    "reason": "影响观测量的工况参数"
                })

    # 相关性分析增强推荐
    numeric_cols = data.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 1:
        corr_matrix = data[numeric_cols].corr()

        # 为每个观测量找强相关因子
        for target in recommendations["targets"]:
            target_col = target["metric"]
            if target_col in corr_matrix.columns:
                strong_factors = []
                for factor in recommendations["factors"]:
                    factor_col = factor["metric"]
                    if factor_col in corr_matrix.columns:
                        corr = abs(corr_matrix.loc[target_col, factor_col])
                        if corr > 0.5:
                            strong_factors.append({
                                "factor": factor_col,
                                "correlation": corr
                            })

                if strong_factors:
                    recommendations["target_factor_mapping"][target_col] = sorted(
                        strong_factors, key=lambda x: x["correlation"], reverse=True
                    )[:5]

    return recommendations
```

### 3.2 推荐输出格式

```python
def format_recommendations(recommendations: dict) -> str:
    """格式化推荐结果为话术"""

    output = "⭐ 智能推荐 (基于领域知识 + 数据分析):\n\n"

    # 观测量推荐
    output += "【推荐 1】目标量识别:\n"
    for target in recommendations["targets"]:
        status = "✅" if target["confidence"] > 0.8 else "❌"
        output += f"{status} {target['metric']} → 观测量\n"
        output += f"   理由：{target['reason']}\n"
        if target.get("component"):
            output += f"   建议部件：{target['component']}\n"

    # 因子量推荐
    output += "\n【推荐 2】因子量识别:\n"
    for factor in recommendations["factors"]:
        output += f"❌ {factor['metric']} → 因子量 ({factor['type']})\n"
        output += f"   理由：{factor['reason']}\n"

    # 映射关系
    if recommendations["target_factor_mapping"]:
        output += "\n【推荐 3】目标量-因子量映射:\n"
        for target, factors in recommendations["target_factor_mapping"].items():
            factor_names = [f["factor"] for f in factors]
            output += f"{target} ← {', '.join(factor_names)}\n"

    return output
```

## 分析示例

```
📊 我来分析一下你的数据样本...

基础分析:
- 数据量：100,000 行 (2026-03-01 ~ 2026-03-11)
- 测点：vibration, temperature, pressure, rpm
- 缺失值：temperature 有 2.3% 缺失
- 异常值：vibration 检测到 15 个离群点

⭐ 智能推荐 (基于领域知识 + 数据分析):

【推荐 1】目标量识别:
根据测点特性和领域知识，建议：
✅ vibration (振动) → 观测量
   理由：旋转机械关键健康指标，常用于故障诊断
   建议部件：bearing (轴承)

✅ bearing_temp (轴承温度) → 观测量
   理由：直接反映轴承健康状态，有明确报警阈值
   建议部件：bearing (轴承)

❌ rpm (转速) → 因子量 (工况参数)
   理由：转速变化会影响振动水平，是典型的工况因子

❌ pressure (压力) → 因子量 (工况参数)
   理由：系统压力影响密封性能，是工况因子

【推荐 2】目标量-因子量映射关系:
基于物理机理和相关性分析：

vibration ← rpm, load, bearing_temp
  理由：
  - rpm 与振动强相关 (相关系数=0.72)
  - 转速变化引起离心力变化，影响振动
  - 温度升高可能导致轴承间隙变化

bearing_temp ← rpm, load, ambient_temp
  理由：
  - 转速和负载影响轴承摩擦生热
  - 环境温度影响散热

[确认/修改] 这个推荐符合你的设备实际情况吗？
[修改] 你有不同的理解或额外的领域知识吗？
```
