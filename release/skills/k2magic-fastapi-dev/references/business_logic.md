# 业务逻辑组织指南

## 核心原则

### 分层架构

1. **`k2magic_service.py`** → 纯粹封装 K2Magic SDK，不包含业务逻辑
2. **`data_service.py`** → 提供通用的数据获取方法（如 `query_by_type`、`query_by_repo_name`）
3. **`endpoints/*.py`** → 实现特定 API 的业务逻辑（数值转换、逻辑判断、数据组装）

## data_service.py - 通用数据提供者

### ✅ 应该写的

- `query_by_type(query_type, devices, ...)` → 根据配置查询数据
- `query_by_repo_name(repo, devices, ...)` → 直接查询指定仓库
- 基础的数据合并（按配置的 concat/merge）
- 降级策略实现

### ❌ 不应该写的

- 特定 API 的数值转换（如温度单位转换）
- 特定 API 的逻辑判断（如状态过滤）
- 特定 API 的数据组装（如添加衍生字段）

**原则**：保持通用性！`data_service` 像一个"数据快递员"，只负责把数据送到，不关心数据的具体用途。

## endpoints/*.py - 特定业务实现者

### ✅ 应该写的

- 接收请求参数
- 调用 `data_service` 获取原始数据
- **数值转换**：格式化、单位转换、数据清洗
- **逻辑判断**：根据条件过滤、分类、状态判断
- **数据组装**：添加衍生字段、合并多次查询
- **业务规则**：权限检查、业务验证
- 格式化响应

**原则**：endpoint 是"业务大厨"，拿到原材料（数据）后，加工成最终的菜品（响应）。

## 实际示例：温度监控功能

### ❌ 错误做法

```python
# app/services/data_service.py - ❌ 不推荐

async def query_temperature_with_business_logic(
    self,
    devices: List[str],
    start_time: str,
    end_time: str,
    convert_to_fahrenheit: bool = False,
    threshold: float = 100.0
):
    """❌ 不推荐：这种特定业务逻辑不应该放在 data_service 中"""
    df = await self.query_by_type(...)
    
    # ❌ 特定业务：单位转换
    if convert_to_fahrenheit:
        df['temperature'] = df['temperature'] * 9/5 + 32
    
    # ❌ 特定业务：标记异常
    df['is_abnormal'] = df['temperature'] > threshold
    
    return df
```

**问题**：
1. 这个方法只能用于温度监控这一个特定场景
2. `data_service` 变得臃肿，充满各种特定业务逻辑
3. 不符合单一职责原则

### ✅ 正确做法

#### 步骤1：data_service.py 只提供通用方法

```python
# app/services/data_service.py - ✅ 推荐

async def query_by_type(
    self,
    query_type: str,
    devices: List[str],
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    columns: List[str] = ['*'],
    limit: Optional[int] = None
) -> Tuple[pd.DataFrame, str, float, bool]:
    """
    通用的查询方法
    
    不包含任何特定业务逻辑，只负责：
    1. 根据配置查询数据
    2. 合并数据
    3. 返回原始结果
    """
    # ... 实现通用查询逻辑 ...
    return merged_df, "k2magic", elapsed, fallback_used
```

#### 步骤2：在 endpoint 中实现业务逻辑

```python
# app/api/v1/endpoints/monitor.py - ✅ 推荐

@router.post("/temperature", response_model=BaseResponse[dict])
async def monitor_temperature(
    devices: list[str],
    start_time: str,
    end_time: str,
    convert_to_fahrenheit: bool = False,
    threshold: float = 100.0,
    data_service: DataService = Depends(get_data_service)
):
    """温度监控接口"""
    # ✅ 步骤1：调用通用服务获取原始数据
    data, source, query_time, fallback = await data_service.query_by_type(
        query_type="device_temperature",
        devices=devices,
        start_time=start_time,
        end_time=end_time
    )
    
    if data.empty:
        return BaseResponse(success=True, message="无数据", data={})
    
    # ✅ 步骤2：业务逻辑 - 单位转换（特定于这个API）
    if convert_to_fahrenheit and 'unit' in data.columns:
        mask = data['unit'] == 'C'
        if mask.any():
            data.loc[mask, 'temperature'] = data.loc[mask, 'temperature'] * 9/5 + 32
            data.loc[mask, 'unit'] = 'F'
    
    # ✅ 步骤3：业务逻辑 - 异常检测（特定于这个API）
    if 'temperature' in data.columns:
        data['is_abnormal'] = data['temperature'] > threshold
        abnormal_count = data['is_abnormal'].sum()
    else:
        abnormal_count = 0
    
    # ✅ 步骤4：业务逻辑 - 统计计算（特定于这个API）
    summary = {
        'total_records': len(data),
        'abnormal_count': int(abnormal_count),
        'avg_temperature': float(data['temperature'].mean()) if 'temperature' in data.columns else None,
        'threshold': threshold
    }
    
    # ✅ 步骤5：生成响应
    return BaseResponse(
        success=True,
        message=f"温度监控完成",
        data={
            'summary': summary,
            'details': data.to_dict('records')[:100]
        }
    )
```

## 何时可以在 data_service 中添加业务逻辑？

**如果业务逻辑满足以下条件，可以考虑放在 `data_service.py` 中**：

1. **被多个 endpoint 共享** - 不是某一个特定API独有的
2. **相对通用** - 是数据层的责任，不是业务展示层的责任
3. **数据处理相关** - 而不是业务规则或展示逻辑

**示例：可以接受的 data_service 业务方法**：

```python
# app/services/data_service.py

# ✅ 可以接受：这个方法可能被多个不同的endpoint使用
async def query_with_time_aggregation(
    self,
    query_type: str,
    devices: List[str],
    start_time: str,
    end_time: str,
    interval: str = '1H'  # 时间聚合间隔
) -> pd.DataFrame:
    """
    带时间聚合的查询（可能被多个场景使用）
    
    这是一个相对通用的功能：
    - 温度监控可能需要按小时聚合
    - 压力监控可能需要按小时聚合
    - 流量监控可能需要按小时聚合
    """
    # 获取原始数据
    df, _, _, _ = await self.query_by_type(...)
    
    # 时间聚合（这是相对通用的数据处理）
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        df = df.groupby('device_id').resample(interval).mean().reset_index()
    
    return df
```

**但是！** 如果只有一个特定的endpoint使用，请直接在endpoint中实现。

## 架构决策流程图

```
我需要实现一个功能
    ↓
是否只是改配置?
    ├─ 是 → 修改 query_config.toml
    └─ 否 → 是否需要获取数据?
            ├─ 是 → 是通用的数据获取吗?
            │       ├─ 是 → 在 data_service.py 中添加通用方法
            │       └─ 否 → 是特定 API 的业务逻辑?
            │               ├─ 是 → 在 endpoints/*.py 中实现业务逻辑
            │               └─ 否 → 是否被多个 API 共享?
            │                       ├─ 是 → 创建业务服务类
            │                       └─ 否 → 在 endpoints/*.py 中实现
            └─ 否 → 在 endpoints/*.py 中实现纯业务逻辑
```

## 快速参考表

| 功能类型 | 写在哪里 | 示例 |
|---------|---------|------|
| 查询类型配置 | `query_config.toml` | 仓库名称、列配置、合并策略 |
| 通用数据获取 | `data_service.py` | query_by_type、query_by_repo_name |
| 数值转换 | `endpoints/*.py` | 单位转换、格式化、数据清洗 |
| 逻辑判断 | `endpoints/*.py` | 条件过滤、分类、状态判断 |
| 数据组装 | `endpoints/*.py` | 添加衍生字段、合并查询结果 |
| 基础数据合并 | `data_service.py` | concat/merge（按配置） |
| 共享业务逻辑 | `services/business/*.py` | 被多个endpoint使用的复杂逻辑 |
| SDK封装 | `k2magic_service.py` | K2Magic特定方法 |

## 总结

遵循以下原则，可以让代码更清晰、更易维护：

1. **`data_service.py`** = **数据快递员** → 只负责送数据，不管数据用途
2. **`endpoints/*.py`** = **业务大厨** → 拿到原材料后，按特定需求加工
3. **保持通用性** → 如果一个方法只能用于一个特定场景，它不应该在 `data_service` 中
4. **避免过度设计** → 不要提前创建"可能会用到"的通用方法
5. **代码复用** → 如果多个endpoint有相同逻辑，再考虑提取到 `data_service` 或创建业务服务类

这样的架构使得：
- ✅ `data_service.py` 保持精简，职责清晰
- ✅ `endpoints/*.py` 包含完整的业务逻辑，易于理解和测试
- ✅ 新增功能时更灵活，不需要频繁修改 `data_service`
- ✅ 代码更符合单一职责原则
