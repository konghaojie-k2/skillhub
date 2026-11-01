# Phase 4: 模型训练 (Model Training)

## 目的

基于历史数据训练基准预测模型，用于计算实时偏差。

## 设备层级结构详解

### 为什么需要层级结构？

```
问题：如何从"振动大"这个测点异常，定位到"轴承磨损"这个部件故障？

答案：通过层级映射关系

测点层 (Metrics)          部件层 (Components)        设备层 (Equipment)
    ↓                           ↓                          ↓
vibration_x ───────────→ 轴承 (bearing) ──────────→ pump_001
vibration_y ───────────→                        (离心泵)
bearing_temp  ───────────→
```

### 层级配置的作用

| 作用 | 说明 | 示例 |
|------|------|------|
| **部件评分** | 聚合部件下所有测点分数 | 轴承分 = mean(vibration_x, vibration_y, bearing_temp) |
| **设备评分** | 加权聚合部件分数 | 设备分 = 0.5×轴承 + 0.3×密封 + 0.2×电机 |
| **故障定位** | 从设备报警反推到部件 | 设备分低 → 轴承分低 → vibration_x 异常 |
| **根因分析** | 结合知识库定位原因 | 振动大 → 轴承磨损 → 建议更换 |

### 层级配置示例

```yaml
# config/hierarchy.yaml
hierarchy:
  # 层级深度：2 层 (设备→部件) 或 4 层
  depth: 2

  components:
    bearing:
      name: 轴承
      weight: 0.5  # 关键部件权重
      level: 1
      parent: null
      metrics: [vibration_x, vibration_y, bearing_temp]
      critical: true

    seal:
      name: 密封
      weight: 0.3
      level: 1
      parent: null
      metrics: [seal_pressure, leakage_rate]
      critical: false

    motor:
      name: 电机
      weight: 0.2
      level: 1
      parent: null
      metrics: [motor_current, motor_temp, rpm]
      critical: false
```

### 复杂结构示例 (4 层)

```yaml
# 复杂设备 (4 层): 设备 → 子系统 → 组件 → 零件 → 测点
hierarchy:
  depth: 4

  components:
    drive_end:
      name: 驱动端
      weight: 0.6
      level: 2
      parent: null
      children: [bearing_assembly, coupling]

    bearing_assembly:
      name: 轴承组件
      weight: 0.7
      level: 3
      parent: drive_end
      children: [front_bearing, rear_bearing]

    front_bearing:
      name: 前轴承
      weight: 1.0
      level: 4
      parent: bearing_assembly
      metrics: [vibration_x]
      critical: true
```

## 测点类型区分

### 观测量 (Target Metrics)

**识别特征**:
- 反映设备健康状态的关键参数
- 通常有明确的报警阈值
- 数据波动可能反映故障
- 示例：vibration (振动), temperature (温度)

### 因子量 (Factor Metrics)

**类型**:
- 工况参数：rpm, load, flow_rate
- 环境参数：ambient_temp, humidity
- 控制参数：valve_position, frequency

### Target-Factor 映射

```yaml
# config/metrics.yaml
model:
  metrics:
    targets:
      vibration_x:
        component: bearing
        description: "X 向振动"
        unit: "mm/s"
        alarm_threshold: 10.0

      bearing_temp:
        component: bearing
        description: "轴承温度"
        unit: "°C"
        alarm_threshold: 80.0

    factors:
      rpm:
        description: "转速"
        unit: "rpm"
        type: "operating_condition"

      load:
        description: "负载"
        unit: "%"
        type: "operating_condition"

  # 目标量 → 因子量映射
  target_factor_mapping:
    vibration_x: [rpm, load, bearing_temp]
    bearing_temp: [rpm, load, ambient_temp]
```

## 模型训练

### 模型选择

| 模型 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| XGBoost | 精度高，可解释性好 | 需调参 | 推荐首选 |
| RandomForest | 训练快，不易过拟合 | 精度一般 | 快速原型 |
| LSTM | 适合时序依赖 | 需大量数据 | 复杂时序 |
| LinearRegression | 简单，可解释 | 精度低 | 基线模型 |

### 训练代码示例

```python
class ModelTrainer:
    def __init__(self, config: dict):
        self.config = config
        self.models = {}

    def train(self, data: pd.DataFrame, target: str, factors: list) -> dict:
        """训练模型"""
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import r2_score, mean_absolute_percentage_error
        import xgboost as xgb

        # 准备数据
        X = data[factors].dropna()
        y = data.loc[X.index, target]

        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # 训练 XGBoost
        model = xgb.XGBRegressor(
            max_depth=6,
            learning_rate=0.1,
            n_estimators=100,
            random_state=42
        )

        model.fit(X_train, y_train)

        # 评估
        y_pred = model.predict(X_test)
        metrics = {
            "r2": r2_score(y_test, y_pred),
            "mape": mean_absolute_percentage_error(y_test, y_pred)
        }

        # 保存模型
        self.models[target] = {
            "model": model,
            "factors": factors,
            "metrics": metrics
        }

        return metrics
```

### 模型配置

```yaml
# config/model.yaml
model:
  type: xgboost
  params:
    max_depth: 6
    learning_rate: 0.1
    n_estimators: 100
    min_child_weight: 1
    subsample: 0.8
    colsample_bytree: 0.8

  # 交叉验证配置
  cv:
    n_folds: 5
    scoring: r2

  # 评估指标
  metrics:
    - r2
    - mape
    - rmse
```

## 询问话术

```
🤖 模型训练配置：

【目标量】vibration (预测振动)
【因子量】temperature, pressure, rpm

【模型类型选择】

1. XGBoost (推荐，精度高，可解释性好)
   - 适合结构化数据
   - 可输出特征重要性

2. RandomForest (训练快，不易过拟合)
   - 适合快速原型
   - 不易过拟合

3. LSTM (适合时序依赖强的场景)
   - 适合长期依赖
   - 需要更多数据

4. LinearRegression (基线模型)
   - 最简单
   - 可解释性好

【训练配置】
- 交叉验证：5 折
- 评估指标：R², MAPE, RMSE

[确认/修改] 选择哪个模型？
```

## 层级结构确认话术

```
🏗️ 设备层级结构配置：

关键问题：测点 → 部件 → 设备 的映射关系

⚠️ 注意：设备层级可能是多层的，需要灵活确认：

简单结构 (2 层):
设备 → 部件 → 测点

复杂结构 (4 层):
设备 → 子系统 → 组件 → 零件 → 测点

示例 (复杂结构):
离心泵 (pump_001)
└── 驱动端 (drive_end) [子系统，权重：0.6]
    ├── 轴承组件 (bearing_assembly) [组件，权重：0.7]
    │   ├── 前轴承 (front_bearing) [零件]
    │   │   └── vibration_x (X 向振动)
    │   └── 后轴承 (rear_bearing) [零件]
    │       └── vibration_y (Y 向振动)
    └── 联轴器 (coupling) [组件，权重：0.3]
        └── alignment (对中偏差)

[确认] 你的设备是简单结构还是复杂结构？
[确认] 需要分几层？每层的名称是什么？
[确认] 每个测点归属哪个部件？
```
