# 查询配置管理指南

## 配置文件格式

查询配置使用 TOML 格式，位于 `config/query_config.toml`。

## 基本结构

### 单个仓库查询

```toml
[device_status]
query_type = "device_status"
merge_strategy = "concat"

[[device_status.repos]]
repo_name = "device_status_repo"
columns = ["*"]
required = true
```

### 多仓库合并查询

```toml
[device_comprehensive]
query_type = "device_comprehensive"
merge_strategy = "merge"
merge_key = "device_id"

[[device_comprehensive.repos]]
repo_name = "device_status_repo"
columns = ["device_id", "status", "last_update"]
required = false

[[device_comprehensive.repos]]
repo_name = "device_history_repo"
columns = ["device_id", "timestamp", "value", "metric"]
required = true

[[device_comprehensive.repos]]
repo_name = "device_info_repo"
columns = ["device_id", "name", "location", "type"]
required = false
```

## 配置字段说明

### 查询类型配置

- `query_type`: 查询类型标识符（唯一）
- `merge_strategy`: 合并策略
  - `"concat"`: 简单拼接（默认）
  - `"merge"`: 按key合并（类似SQL JOIN）
- `merge_key`: 合并键（当 `merge_strategy="merge"` 时必填）

### 仓库配置

- `repo_name`: 仓库名称（对应 K2Assets 仓库）
- `columns`: 要查询的列列表
  - `["*"]`: 查询所有列
  - `["col1", "col2"]`: 查询指定列
- `required`: 是否必需
  - `true`: 必需，查询失败会抛出异常
  - `false`: 可选，查询失败会跳过

## 合并策略详解

### concat（拼接）

简单地将多个仓库的数据拼接在一起：

```toml
[device_history]
query_type = "device_history"
merge_strategy = "concat"

[[device_history.repos]]
repo_name = "device_history_repo1"
columns = ["*"]
required = true

[[device_history.repos]]
repo_name = "device_history_repo2"
columns = ["*"]
required = false
```

**结果**：两个仓库的数据会按行拼接，列会合并（相同列名会保留）。

### merge（合并）

按指定的key合并多个仓库的数据：

```toml
[device_comprehensive]
query_type = "device_comprehensive"
merge_strategy = "merge"
merge_key = "device_id"

[[device_comprehensive.repos]]
repo_name = "device_status_repo"
columns = ["device_id", "status"]
required = true

[[device_comprehensive.repos]]
repo_name = "device_info_repo"
columns = ["device_id", "name", "location"]
required = false
```

**结果**：按 `device_id` 合并，类似 SQL 的 LEFT JOIN。

## 使用示例

### 1. 添加新的查询类型

在 `config/query_config.toml` 中添加：

```toml
[temperature_monitor]
query_type = "temperature_monitor"
merge_strategy = "concat"

[[temperature_monitor.repos]]
repo_name = "temperature_repo"
columns = ["device_id", "timestamp", "temperature", "unit"]
required = true
```

### 2. 在代码中使用

```python
# 自动根据配置查询
data, source, query_time, fallback = await data_service.query_by_type(
    query_type="temperature_monitor",
    devices=["device001", "device002"],
    start_time="2024-01-01T00:00:00",
    end_time="2024-01-02T00:00:00"
)
```

### 3. 获取查询类型列表

```python
query_types = data_service.query_config_service.list_query_types()
# 返回: ["device_status", "device_history", "device_comprehensive", ...]
```

## QueryConfigService 使用

### 获取配置

```python
from app.services.query_config import QueryConfigService

config_service = QueryConfigService()
config = config_service.get_config("device_history")

if config:
    print(f"查询类型: {config.query_type}")
    print(f"合并策略: {config.merge_strategy}")
    print(f"仓库数量: {len(config.repos)}")
```

### 列出所有查询类型

```python
query_types = config_service.list_query_types()
for query_type in query_types:
    print(query_type)
```

## 最佳实践

1. **命名规范**：使用下划线命名，如 `device_history`、`temperature_monitor`
2. **列选择**：尽量指定具体列，避免使用 `["*"]` 以提高性能
3. **必需仓库**：将核心数据仓库设置为 `required=true`
4. **合并键**：使用 merge 策略时，确保所有仓库都有合并键对应的列
5. **配置验证**：启动时验证配置文件的正确性

## 配置验证

系统会在启动时自动验证配置：

- 检查必需的字段是否存在
- 验证仓库配置格式
- 检查合并键是否存在（当使用 merge 策略时）

## 常见问题

### Q: 如何修改查询列？

A: 修改配置文件中对应仓库的 `columns` 字段，重启服务生效。

### Q: 如何添加新的仓库？

A: 在对应查询类型的 `repos` 数组中添加新的仓库配置。

### Q: merge 策略的合并键不存在怎么办？

A: 确保所有仓库都包含合并键对应的列，否则合并会失败。

### Q: 如何禁用某个仓库？

A: 将 `required` 设置为 `false`，或直接删除该仓库配置。
