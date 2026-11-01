# Phase 5: 偏差分析 (Deviation Analysis)

## 目的

基于训练好的基准模型，计算实时数据与基准的偏差，判断设备健康状态。

## 偏差分析原理

```
基准模型: y_pred = f(factors)

偏差计算:
- 偏差 = y_actual - y_pred
- 偏差率 = (y_actual - y_pred) / y_pred

判断标准:
- 正常: 偏差在允许范围内 (±δ)
- 异常: 偏差超出允许范围
```

## 动态阈值计算

### 1. 简单阈值法

```python
def simple_threshold(predictions: np.ndarray, actual: np.ndarray, delta: float = 0.15) -> dict:
    """
    简单阈值法

    参数:
    - predictions: 预测值
    - actual: 实际值
    - delta: 允许偏差率 (默认 15%)
    """
    deviation = actual - predictions
    deviation_ratio = deviation / (predictions + 1e-8)

    # 计算阈值
    upper_limit = predictions * (1 + delta)
    lower_limit = predictions * (1 - delta)

    # 判断是否异常
    is_anomaly = (actual > upper_limit) | (actual < lower_limit)

    return {
        "upper_limit": upper_limit,
        "lower_limit": lower_limit,
        "deviation": deviation,
        "deviation_ratio": deviation_ratio,
        "is_anomaly": is_anomaly,
        "anomaly_ratio": is_anomaly.mean()
    }
```

### 2. SPC (统计过程控制) 法

```python
def spc_threshold(predictions: np.ndarray, actual: np.ndarray, n_std: float = 3.0) -> dict:
    """
    SPC 统计过程控制法

    使用历史偏差的均值和标准差计算控制限
    """
    deviation = actual - predictions

    # 计算统计量
    mean_deviation = deviation.mean()
    std_deviation = deviation.std()

    # 计算控制限
    UCL = mean_deviation + n_std * std_deviation  # 上控制限
    LCL = mean_deviation - n_std * std_deviation  # 下控制限

    # 判断是否异常
    is_anomaly = (deviation > UCL) | (deviation < LCL)

    return {
        "mean": mean_deviation,
        "std": std_deviation,
        "UCL": UCL,
        "LCL": LCL,
        "deviation": deviation,
        "is_anomaly": is_anomaly,
        "anomaly_ratio": is_anomaly.mean()
    }
```

### 3. 滑动窗口法

```python
def sliding_window_threshold(predictions: np.ndarray, actual: np.ndarray,
                            window_size: int = 100, n_std: float = 3.0) -> dict:
    """
    滑动窗口法

    使用滑动窗口计算动态阈值，适应工况变化
    """
    deviation = actual - predictions
    is_anomaly = np.zeros(len(deviation), dtype=bool)

    for i in range(window_size, len(deviation)):
        # 计算窗口内的统计量
        window = deviation[i-window_size:i]
        mean = window.mean()
        std = window.std()

        # 判断当前点
        if abs(deviation[i] - mean) > n_std * std:
            is_anomaly[i] = True

    return {
        "deviation": deviation,
        "is_anomaly": is_anomaly,
        "anomaly_ratio": is_anomaly.mean()
    }
```

## 指标偏差计算

### 偏差指标定义

```python
def calculate_deviation_metrics(predictions: np.ndarray, actual: np.ndarray) -> dict:
    """计算偏差指标"""
    deviation = actual - predictions
    deviation_ratio = deviation / (predictions + 1e-8)

    return {
        # 绝对偏差
        "bias": deviation.mean(),
        "bias_abs": np.abs(deviation).mean(),

        # 相对偏差
        "out_ratio": (np.abs(deviation_ratio) > 0.15).mean(),  # 超限比例

        # 方差
        "variance": deviation.var(),

        # 最大偏差
        "max_deviation": deviation.max(),
        "min_deviation": deviation.min(),

        # 趋势
        "trend": np.polyfit(range(len(deviation)), deviation, 1)[0]
    }
```

### 多指标综合偏差

```python
def calculate_equipment_deviation(metric_deviations: dict, hierarchy: dict) -> dict:
    """
    计算设备综合偏差

    参数:
    - metric_deviations: {metric_name: deviation_result}
    - hierarchy: 设备层级配置
    """
    component_scores = {}

    # 按部件聚合
    for component, config in hierarchy["components"].items():
        metrics = config.get("metrics", [])
        metric_scores = []

        for metric in metrics:
            if metric in metric_deviations:
                # 使用偏差率作为异常指标 (越低越好)
                score = 1 - min(metric_deviations[metric]["out_ratio"], 1.0)
                metric_scores.append(score)

        if metric_scores:
            component_scores[component] = np.mean(metric_scores)

    # 计算设备总分
    total_weight = sum(c["weight"] for c in hierarchy["components"].values())
    equipment_score = sum(
        component_scores.get(c, 0.5) * hierarchy["components"][c]["weight"]
        for c in hierarchy["components"]
    ) / total_weight

    return {
        "component_scores": component_scores,
        "equipment_score": equipment_score
    }
```

## 报警规则配置

```yaml
# config/alarm_rules.yaml
threshold:
  # 偏差阈值
  delta: 0.15  # 允许 15% 偏差

  # 评价规则: simple / spc / sliding_window
  evaluation_rule: spc

  # SPC 参数
  spc:
    n_std: 3.0  # 3倍标准差

  # 滑动窗口参数
  sliding_window:
    window_size: 100
    n_std: 3.0

# 评分配置
scoring:
  # 健康分阈值
  alarm_threshold: 0.6
  warning_threshold: 0.8

  # 聚合方法: weighted_avg / min / custom
  aggregation_method: weighted_avg

  # 触发规则
  trigger:
    - condition: "health_score < alarm_threshold"
      action: "alarm"
    - condition: "health_score < warning_threshold"
      action: "warning"
    - condition: "health_score_trend < -0.1"
      action: "degradation_warning"
```

## 询问话术

```
🚨 预警规则配置：

【偏差阈值】
- 允许偏差 δ = 15%
- 计算方式: |actual - predicted| / predicted

【评价规则】
1. 简单阈值 (推荐)
   - 固定阈值 ±15%
   - 简单直观

2. SPC (统计过程控制)
   - 基于历史偏差的均值和标准差
   - 自适应工况变化

3. 滑动窗口
   - 使用滑动窗口计算动态阈值
   - 适合长期运行设备

【健康分阈值】
- 正常：> 0.8
- 预警：0.6 - 0.8
- 报警：< 0.6

【关键部件权重】
- 轴承：0.5 (关键)
- 密封：0.3
- 其他：0.2

【触发规则】
- 健康分 < 0.6 → 预警
- 连续 3 个周期下降 → 预警
- 关键部件 < 0.5 → 预警

[确认/修改]
```
