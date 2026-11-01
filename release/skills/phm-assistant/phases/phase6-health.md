# Phase 6: 健康评分 (Health Score)

## 目的

基于偏差分析结果，计算部件和设备的健康评分，生成预警信号。

## 健康评分体系

### 评分层次

```
设备层 (Equipment Score)
  └── 部件层 (Component Score)
        └── 测点层 (Metric Score)
```

### 评分计算

```python
class HealthScoreCalculator:
    def __init__(self, hierarchy: dict):
        self.hierarchy = hierarchy

    def calc_metric_score(self, metric: str, deviation_result: dict) -> float:
        """
        计算测点健康分

        基于偏差结果计算单个测点的健康分
        - 正常: 1.0
        - 异常: 0.0 ~ 1.0
        """
        if deviation_result["anomaly_ratio"] == 0:
            return 1.0
        elif deviation_result["anomaly_ratio"] < 0.1:
            return 0.8
        elif deviation_result["anomaly_ratio"] < 0.3:
            return 0.5
        else:
            return 0.2

    def calc_component_score(self, component: str, metric_scores: dict) -> float:
        """
        计算部件健康分

        聚合部件下所有测点的健康分
        """
        if component not in self.hierarchy["components"]:
            return 1.0

        config = self.hierarchy["components"][component]
        metrics = config.get("metrics", [])

        # 获取该部件下所有测点的分数
        scores = [metric_scores.get(m, 1.0) for m in metrics if m in metric_scores]

        if not scores:
            return 1.0

        # 使用加权平均
        return np.mean(scores)

    def calc_equipment_score(self, component_scores: dict) -> float:
        """
        计算设备健康分

        加权聚合所有部件的健康分
        """
        total_weight = 0
        weighted_sum = 0

        for comp, config in self.hierarchy["components"].items():
            weight = config.get("weight", 0)
            score = component_scores.get(comp, 1.0)

            weighted_sum += weight * score
            total_weight += weight

        if total_weight == 0:
            return 1.0

        return weighted_sum / total_weight

    def calc_overall_score(self, metric_deviations: dict) -> dict:
        """
        计算综合健康分
        """
        # 1. 计算测点分
        metric_scores = {
            m: self.calc_metric_score(m, d)
            for m, d in metric_deviations.items()
        }

        # 2. 计算部件分
        component_scores = {
            comp: self.calc_component_score(comp, metric_scores)
            for comp in self.hierarchy["components"]
        }

        # 3. 计算设备分
        equipment_score = self.calc_equipment_score(component_scores)

        return {
            "equipment_score": equipment_score,
            "component_scores": component_scores,
            "metric_scores": metric_scores
        }
```

## 预警触发

### 预警规则

```python
class AlarmTrigger:
    def __init__(self, config: dict):
        self.config = config

    def check(self, health_scores: dict, history: list = None) -> dict:
        """
        检查是否触发预警

        返回:
        - alarm_level: normal / warning / alarm
        - triggers: 触发的规则列表
        """
        triggers = []
        alarm_level = "normal"

        equipment_score = health_scores["equipment_score"]
        component_scores = health_scores["component_scores"]

        # 规则1: 设备健康分低于阈值
        threshold = self.config.get("alarm_threshold", 0.6)
        if equipment_score < threshold:
            triggers.append({
                "rule": "low_equipment_score",
                "message": f"设备健康分 {equipment_score:.2f} 低于阈值 {threshold}"
            })
            alarm_level = "alarm"

        # 规则2: 关键部件分数低
        for comp, score in component_scores.items():
            if self.is_critical_component(comp):
                if score < 0.5:
                    triggers.append({
                        "rule": "critical_component_low",
                        "message": f"关键部件 {comp} 健康分 {score:.2f} 过低"
                    })
                    alarm_level = "alarm"

        # 规则3: 连续下降趋势
        if history and len(history) >= 3:
            recent_scores = [h["equipment_score"] for h in history[-3:]]
            if all(recent_scores[i] > recent_scores[i+1] for i in range(len(recent_scores)-1)):
                if recent_scores[-1] < recent_scores[0] - 0.1:
                    triggers.append({
                        "rule": "degradation_trend",
                        "message": "设备健康分持续下降"
                    })
                    if alarm_level == "normal":
                        alarm_level = "warning"

        # 规则4: 部件分数低于预警阈值
        warning_threshold = self.config.get("warning_threshold", 0.8)
        for comp, score in component_scores.items():
            if score < warning_threshold and alarm_level == "normal":
                triggers.append({
                    "rule": "component_warning",
                    "message": f"部件 {comp} 健康分 {score:.2f} 低于预警阈值"
                })
                alarm_level = "warning"

        return {
            "alarm_level": alarm_level,
            "triggers": triggers,
            "recommendations": self.generate_recommendations(alarm_level, triggers)
        }

    def is_critical_component(self, component: str) -> bool:
        """判断是否关键部件"""
        return self.config.get("critical_components", []).count(component) > 0

    def generate_recommendations(self, alarm_level: str, triggers: list) -> list:
        """生成建议"""
        recommendations = []

        if alarm_level == "alarm":
            recommendations.append("建议立即安排检修")
            recommendations.append("加强设备监控频率")

        if alarm_level in ["warning", "alarm"]:
            recommendations.append("准备备件")

        for trigger in triggers:
            if "轴承" in trigger.get("message", ""):
                recommendations.append("检查轴承润滑状态")
            elif "振动" in trigger.get("message", ""):
                recommendations.append("检查设备对中和平衡")

        return recommendations
```

## 评分配置

```yaml
# config/health_score.yaml
health_score:
  # 评分方法
  method: weighted_avg  # weighted_avg / min / custom

  # 阈值配置
  thresholds:
    alarm: 0.6      # 报警阈值
    warning: 0.8    # 预警阈值

  # 部件评分规则
  component:
    # 聚合方法: mean / min / weighted
    aggregation: mean

    # 关键部件列表
    critical:
      - bearing
      - seal

  # 设备评分规则
  equipment:
    # 聚合方法: weighted_avg / min
    aggregation: weighted_avg

  # 预警触发规则
  trigger:
    rules:
      - name: low_score
        condition: "equipment_score < alarm_threshold"
        level: alarm

      - name: critical_component
        condition: "critical_component_score < 0.5"
        level: alarm

      - name: degradation_trend
        condition: "score_trend < -0.1"
        level: warning

      - name: component_warning
        condition: "component_score < warning_threshold"
        level: warning
```

## 知识库配置

```yaml
# config/knowledge_base.yaml
knowledge_base:
  # 异常模式定义
  patterns:
    vibration_high:
      symptoms: ["振动值超过阈值"]
      possible_causes:
        - "轴承磨损"
        - "转子不平衡"
        - "对中不良"
        - "螺栓松动"
      recommendations:
        - "检查轴承状态"
        - "进行动平衡校正"
        - "检查对中情况"
        - "紧固螺栓"

    temperature_high:
      symptoms: ["温度超过阈值"]
      possible_causes:
        - "润滑不良"
        - "冷却故障"
        - "过载运行"
        - "环境温度高"
      recommendations:
        - "检查润滑油位"
        - "检查冷却系统"
        - "降低负载"
```

## 询问话术

```
📊 健康评分配置：

【评分体系】
- 测点分 → 部件分 → 设备分
- 分数范围：0.0 ~ 1.0

【阈值设置】
- 正常：> 0.8
- 预警：0.6 - 0.8
- 报警：< 0.6

【关键部件】(故障影响大)
- 轴承：权重 0.5
- 密封：权重 0.3
- 电机：权重 0.2

【触发规则】
- 健康分 < 0.6 → 报警
- 关键部件 < 0.5 → 报警
- 连续 3 周期下降 → 预警

[确认/修改]
```

## 诊断分析

### 部件定位

```python
def locate_component(health_scores: dict) -> list:
    """定位异常部件"""
    anomalies = []

    for comp, score in health_scores["component_scores"].items():
        if score < 0.5:
            anomalies.append({
                "component": comp,
                "score": score,
                "severity": "critical" if score < 0.3 else "warning"
            })

    return sorted(anomalies, key=lambda x: x["score"])
```

### 指标定位

```python
def locate_metric(component: str, health_scores: dict, hierarchy: dict) -> list:
    """定位异常测点"""
    metrics = hierarchy["components"][component].get("metrics", [])
    anomalies = []

    for metric in metrics:
        score = health_scores["metric_scores"].get(metric, 1.0)
        if score < 0.8:
            anomalies.append({
                "metric": metric,
                "score": score
            })

    return sorted(anomalies, key=lambda x: x["score"])
```

### 根因分析

```python
def diagnose(anomalies: list, knowledge_base: dict) -> dict:
    """基于知识库进行根因分析"""
    diagnosis = []

    for anomaly in anomalies:
        # 匹配知识库中的异常模式
        for pattern in knowledge_base.get("patterns", {}).values():
            # 简化匹配逻辑
            diagnosis.append({
                "anomaly": anomaly,
                "possible_causes": pattern.get("possible_causes", []),
                "recommendations": pattern.get("recommendations", [])
            })

    return diagnosis
```
