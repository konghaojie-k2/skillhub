# Phase 1: 数据准备 (Data Preparation)

## 目的

对原始数据进行清洗、处理和特征工程，为后续模型训练做准备。

## 数据清洗

### 1.1 去噪

常用方法：
- **移动平均**: `df.rolling(window=5).mean()`
- **卡尔曼滤波**: 用于实时去噪
- **低通滤波**: 去除高频噪声

```python
# 示例：移动平均去噪
def denoise_moving_avg(data: pd.DataFrame, columns: list, window: int = 5) -> pd.DataFrame:
    result = data.copy()
    for col in columns:
        if col in result.columns:
            result[col] = result[col].rolling(window=window, center=True).mean()
    return result
```

### 1.2 空值填充

| 方法 | 适用场景 | 代码 |
|------|----------|------|
| 前向填充 | 时序数据 | `df.fillna(method='ffill')` |
| 线性插值 | 趋势数据 | `df.interpolate(method='linear')` |
| 均值填充 | 随机缺失 | `df.fillna(df.mean())` |
| KNN填充 | 复杂模式 | `from sklearn.impute import KNNImputer` |

### 1.3 异常值处理

```python
def handle_outliers(data: pd.DataFrame, column: str, method: str = 'iqr') -> pd.DataFrame:
    """
    异常值处理

    方法:
    - iqr: 四分位距法
    - zscore: Z-score法
    - isolation_forest: 孤立森林
    """
    result = data.copy()

    if method == 'iqr':
        Q1 = result[column].quantile(0.25)
        Q3 = result[column].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        result[column] = result[column].clip(lower, upper)

    elif method == 'zscore':
        from scipy import stats
        z_scores = np.abs(stats.zscore(result[column]))
        result = result[z_scores < 3]

    return result
```

## 工况切分

### 2.1 阈值法

适用于有明确工况边界的场景：

```python
def segment_by_threshold(data: pd.DataFrame, signal: str, thresholds: dict) -> pd.DataFrame:
    """
    基于阈值的工况切分

    参数:
    - signal: 工况信号 (如 rpm)
    - thresholds: 阈值字典 {"stop": 100, "low_load": 800}
    """
    result = data.copy()
    conditions = []

    # 排序阈值确保正确匹配
    sorted_thresholds = sorted(thresholds.items(), key=lambda x: x[1])

    for i, (name, value) in enumerate(sorted_thresholds):
        if i == 0:
            cond = result[signal] <= value
        else:
            prev_value = sorted_thresholds[i-1][1]
            cond = (result[signal] > prev_value) & (result[signal] <= value)
        conditions.append((name, cond))

    # 最后一个工况
    last_value = sorted_thresholds[-1][1]
    conditions.append(('high_load', result[signal] > last_value))

    # 创建工况列
    result['condition'] = 'unknown'
    for name, cond in conditions:
        result.loc[cond, 'condition'] = name

    return result
```

### 2.2 聚类法

适用于工况边界不明确的场景：

```python
def segment_by_clustering(data: pd.DataFrame, signal: str, n_clusters: int = 3) -> pd.DataFrame:
    """
    基于聚类的工况切分

    使用 K-Means 或 DBSCAN 自动发现工况
    """
    from sklearn.cluster import KMeans
    import numpy as np

    X = data[signal].values.reshape(-1, 1)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    data['condition'] = kmeans.fit_predict(X)

    # 按工况均值排序并重命名
    means = data.groupby('condition')[signal].mean().sort_values()
    mapping = {old: new for new, old in enumerate(means.index)}
    data['condition'] = data['condition'].map(mapping)

    return data
```

### 2.3 规则法

适用于有专家知识的场景：

```python
def segment_by_rules(data: pd.DataFrame, rules: list) -> pd.DataFrame:
    """
    基于专家规则的工况切分

    rules 示例:
    [
        {"name": "startup", "condition": "rpm > 0 and rpm < 100"},
        {"name": "running", "condition": "rpm >= 100 and rpm < 800"},
        {"name": "high_load", "condition": "rpm >= 800"}
    ]
    """
    result = data.copy()
    result['condition'] = 'unknown'

    for rule in rules:
        mask = eval(rule["condition"], {"__builtins__": {}}, result.to_dict('series'))
        result.loc[mask, 'condition'] = rule["name"]

    return result
```

## 特征工程

### 3.1 时域特征

```python
def extract_time_domain_features(data: pd.DataFrame, column: str, window_size: int = 100) -> pd.DataFrame:
    """提取时域特征"""
    features = pd.DataFrame(index=data.index)

    # 滑动窗口统计
    rolling = data[column].rolling(window=window_size)

    features[f'{column}_mean'] = rolling.mean()
    features[f'{column}_std'] = rolling.std()
    features[f'{column}_max'] = rolling.max()
    features[f'{column}_min'] = rolling.min()
    features[f'{column}_peak'] = rolling.max() - rolling.min()  # 峰峰值
    features[f'{column}_rms'] = np.sqrt(rolling.apply(lambda x: np.mean(x**2)))  # 均方根
    features[f'{column}_skew'] = rolling.skew()
    features[f'{column}_kurt'] = rolling.apply(lambda x: x.kurtosis())

    return features
```

### 3.2 频域特征

```python
def extract_frequency_features(data: pd.DataFrame, column: str, sampling_rate: int = 1000) -> pd.DataFrame:
    """提取频域特征"""
    from scipy.fft import fft, fftfreq

    features = pd.DataFrame(index=data.index)

    # 计算FFT
    n = len(data)
    yf = fft(data[column].values)
    xf = fftfreq(n, 1/sampling_rate)[:n//2]

    # 频域特征
    power = 2.0/n * np.abs(yf[0:n//2])

    features[f'{column}_spectral_centroid'] = np.sum(xf * power) / np.sum(power)
    features[f'{column}_spectral_energy'] = np.sum(power**2)
    features[f'{column}_dominant_freq'] = xf[np.argmax(power)]

    return features
```

### 3.3 工况特征

```python
def extract_condition_features(data: pd.DataFrame, condition_column: str) -> pd.DataFrame:
    """提取工况相关特征"""
    features = pd.DataFrame(index=data.index)

    # 工况持续时间
    features['condition_duration'] = data.groupby(condition_column).cumcount()

    # 工况变化标记
    features['condition_change'] = (data[condition_column] != data[condition_column].shift(1)).astype(int)

    # 工况占比
    condition_ratio = data[condition_column].value_counts(normalize=True)
    for cond in condition_ratio.index:
        features[f'is_{cond}'] = (data[condition_column] == cond).astype(int)

    return features
```

## 数据准备配置示例

```yaml
# config/data_prep.yaml
data_prep:
  # 数据清洗配置
  cleaning:
    denoise:
      method: moving_avg
      window: 5

    missing_value:
      method: interpolation
      strategy: linear

    outliers:
      method: iqr
      threshold: 1.5

  # 工况切分配置
  segmentation:
    method: threshold  # threshold / clustering / rules
    signal: rpm
    thresholds:
      stop: 100
      low_load: 800
    min_duration: 5min  # 最小工况持续时间

  # 特征工程配置
  features:
    time_domain:
      - mean
      - std
      - max
      - min
      - rms
      - skewness
      - kurtosis

    frequency:
      - spectral_centroid
      - spectral_energy
      - dominant_freq

    condition:
      - duration
      - change
      - ratio
```

## 询问话术

```
⚙️ 数据准备配置：

【数据清洗】
- 去噪方法：移动平均 (window=5)
- 空值填充：线性插值
- 异常值处理：IQR法 (threshold=1.5)

【工况切分】
- 方法：阈值法
- 工况信号：rpm
- 阈值：stop(0-100), low_load(100-800), high_load(800+)
- 最小持续时间：5分钟

【特征工程】
- 时域特征：均值、标准差、最大值、峰峰值、RMS
- 频域特征：谱质心、谱能量、主频率

[确认/修改] 这个配置符合你的需求吗？
```
