# Phase 3: 工况切分 (Working Condition Segmentation)

## 目的

将连续运行数据分割为不同的工况段，用于后续的模型训练和偏差分析。

## 工况类型

### 稳态工况

| 工况 | 特征 | 示例 |
|------|------|------|
| 停机 | 转速=0 或极低 | 启动前、检修时 |
| 待机 | 低转速、低负载 | 预备运行 |
| 正常运行 | 稳定转速和负载 | 满负荷运行 |
| 高负荷 | 高转速、高负载 | 峰值工况 |
| 变载 | 负载变化 | 调峰运行 |

### 暂态工况

| 工况 | 特征 | 持续时间 |
|------|------|----------|
| 启动 | 转速从0上升 | 数秒~数分钟 |
| 停机 | 转速下降到0 | 数秒~数分钟 |
| 升降负荷 | 负载快速变化 | 数秒~数分钟 |

## 工况切分方法

### 1. 阈值法

适用于有明确工况边界的场景：

```python
class ThresholdSegmenter:
    def __init__(self, signal: str, thresholds: dict, min_duration: int = 300):
        """
        参数:
        - signal: 工况信号名称
        - thresholds: 阈值字典 {"工况名": 阈值}
        - min_duration: 最小持续时间(秒)
        """
        self.signal = signal
        self.thresholds = thresholds
        self.min_duration = min_duration

    def segment(self, data: pd.DataFrame) -> pd.DataFrame:
        """执行工况切分"""
        result = data.copy()

        # 按阈值划分工况
        conditions = []
        sorted_thresholds = sorted(self.thresholds.items(), key=lambda x: x[1])

        for i, (name, value) in enumerate(sorted_thresholds):
            if i == 0:
                cond = result[self.signal] <= value
            else:
                prev = sorted_thresholds[i-1][1]
                cond = (result[self.signal] > prev) & (result[self.signal] <= value)
            conditions.append((name, cond))

        # 最高工况
        last_val = sorted_thresholds[-1][1]
        conditions.append(('high_load', result[self.signal] > last_val))

        # 创建工况列
        result['condition'] = 'unknown'
        for name, cond in conditions:
            result.loc[cond, 'condition'] = name

        # 过滤过短工况
        result = self._filter_short_conditions(result)

        return result

    def _filter_short_conditions(self, data: pd.DataFrame) -> pd.DataFrame:
        """过滤持续时间过短的工况"""
        # 计算工况持续采样点数
        # 假设采样频率为1Hz，min_duration秒对应min_duration个点

        result = data.copy()
        condition_changes = result['condition'] != result['condition'].shift(1)
        result['condition_id'] = condition_changes.cumsum()

        # 统计每个工况段的持续点数
        condition_counts = result.groupby('condition_id').size()
        short_conditions = condition_counts[condition_counts < self.min_duration].index

        # 将短工况标记为过渡态
        result.loc[result['condition_id'].isin(short_conditions), 'condition'] = 'transient'

        return result
```

### 2. 聚类法

适用于工况边界不明确的场景：

```python
class ClusteringSegmenter:
    def __init__(self, signals: list, n_clusters: int = 3, method: str = 'kmeans'):
        """
        参数:
        - signals: 用于聚类的信号列表
        - n_clusters: 工况数量
        - method: 聚类方法 (kmeans/dbscan)
        """
        self.signals = signals
        self.n_clusters = n_clusters
        self.method = method

    def segment(self, data: pd.DataFrame) -> pd.DataFrame:
        """执行工况切分"""
        from sklearn.cluster import KMeans, DBSCAN

        X = data[self.signals].values

        if self.method == 'kmeans':
            model = KMeans(n_clusters=self.n_clusters, random_state=42)
            labels = model.fit_predict(X)
        else:  # dbscan
            model = DBSCAN(eps=0.5, min_samples=10)
            labels = model.fit_predict(X)

        # 按工况均值排序并重命名
        result = data.copy()
        result['condition'] = labels

        means = result.groupby('condition')[self.signals[0]].mean().sort_values()
        mapping = {old: new for new, old in enumerate(means.index)}
        result['condition'] = result['condition'].map(mapping)

        return result
```

### 3. 规则法

适用于有专家知识的场景：

```python
class RuleBasedSegmenter:
    def __init__(self, rules: list):
        """
        参数:
        - rules: 专家规则列表
          [
            {"name": "startup", "conditions": ["rpm > 0", "rpm < 100"]},
            {"name": "running", "conditions": ["rpm >= 100", "rpm < 800"]}
          ]
        """
        self.rules = rules

    def segment(self, data: pd.DataFrame) -> pd.DataFrame:
        """执行工况切分"""
        result = data.copy()
        result['condition'] = 'unknown'

        for rule in self.rules:
            # 组合条件
            condition_str = " and ".join(rule["conditions"])
            try:
                mask = eval(condition_str, {"__builtins__": {}}, result.to_dict('series'))
                result.loc[mask, 'condition'] = rule["name"]
            except Exception as e:
                print(f"Warning: Failed to evaluate rule {rule['name']}: {e}")

        return result
```

## 工况配置示例

```yaml
# config/segmentation.yaml
segmentation:
  # 切分方法: threshold / clustering / rules
  method: threshold

  # 方法-specific 配置
  threshold:
    signal: rpm  # 工况信号
    thresholds:
      stop: 100          # 停机: 0-100 rpm
      low_load: 800     # 低负载: 100-800 rpm
      # high_load: 800+  # 高负载: 800+ rpm
    min_duration: 300   # 最小持续时间(秒)

  clustering:
    signals: [rpm, load, pressure]
    n_clusters: 3
    method: kmeans  # kmeans / dbscan

  rules:
    - name: startup
      conditions:
        - "rpm > 0"
        - "rpm < 100"
    - name: running
      conditions:
        - "rpm >= 100"
        - "rpm < 800"
    - name: high_load
      conditions:
        - "rpm >= 800"
```

## 询问话术

```
⚙️ 工况切分配置：

【检测到】rpm 信号适合做工况切分

【方法选择】
请选择工况切分方法：

1. 阈值法 (推荐 - 你有明确的工况边界)
   - 需要定义每个工况的阈值
   - 简单直观，易于解释

2. 聚类法 (自动发现 - 工况边界不明确)
   - 使用 K-Means 自动聚类
   - 需要指定工况数量

3. 规则法 (专家知识)
   - 基于专家规则定义
   - 需要领域知识

【阈值法配置示例】
阈值：
  - stop: 0-100 rpm (停机)
  - low_load: 100-800 rpm (低负载)
  - high_load: 800+ rpm (高负载)

最小工况持续时间：5 分钟 (过滤过短片段)

[确认/修改] 你想用哪种方法？
[修改] 你有不同阈值定义吗？
```
