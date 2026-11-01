# K2Magic SDK 集成详细指南

## K2Magic 简介

K2Magic 是由 K2data 开发的数据分析工具包，用于简化 Python 中对 K2Assets 仓库的访问操作。

- **核心类**: `k2magic.k2_dataframe_db.K2DataFrameDB`
- **特点**: 基于 pandas DataFrame，专门用于 K2Assets 仓库数据访问
- **支持方式**: 支持 REST API 和原生连接方式

## K2Assets 仓库连接

### 连接 URL 格式

```
k2assets+repo://username:password@host/{repo}?tenant=tenant_name
```

**示例**:
```
k2assets+repo://test:password123@192.168.32.239/{repo}?tenant=test
```

**重要**：URL 中必须包含 `{repo}` 占位符，实际调用时会替换为具体的仓库名称。

### REST API 模式

默认启用 REST API 模式（`rest=True`），这种方式：
- ✅ 性能更好
- ✅ 网络开销更小
- ✅ 推荐在生产环境使用

## 服务封装实现

### 基本结构

```python
from k2magic.k2_dataframe_db import K2DataFrameDB
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import pandas as pd

class K2MagicService:
    def __init__(self):
        self.connection_url_template = settings.k2magic_connection_url
        self.rest = settings.k2magic_rest
        self._clients: Dict[str, Any] = {}  # 客户端缓存
```

### 客户端缓存机制

为每个 repo 创建独立的客户端实例并缓存：

```python
def _get_client(self, repo: str):
    """获取指定repo的客户端实例（带缓存）"""
    if repo in self._clients:
        return self._clients[repo]
    
    # 构建连接URL，替换 {repo} 占位符
    connection_url = self.connection_url_template.format(repo=repo)
    
    # 创建新的客户端实例
    client = K2DataFrameDB(connection_url, rest=self.rest)
    self._clients[repo] = client
    
    return client
```

### 主要查询方法

#### 1. 通过时间范围读取仓库数据

```python
async def get_repo_data_by_time(
    self,
    repo: str,
    k_devices: List[Union[str, int]],
    start_time: Optional[Union[str, datetime]] = None,
    end_time: Optional[Union[str, datetime]] = None,
    columns: List[str] = ['*'],
    limit: Optional[int] = None,
    desc: bool = False,
    **kwargs
) -> pd.DataFrame:
    """通过时间范围读取仓库数据（最常用的方法）"""
    client = self._get_client(repo)
    devices = [str(k) for k in k_devices]
    
    df = client.get_repo_data(
        columns=columns,
        start_time=start_time,
        end_time=end_time,
        devices=devices,
        limit=limit,
        desc=desc,
        **kwargs
    )
    
    return df
```

**参数说明**：
- `repo`: 仓库名称（如：`device_history`、`device_status`）
- `k_devices`: 设备ID列表（字符串或整数）
- `start_time` / `end_time`: 时间范围（字符串格式或 datetime 对象）
- `columns`: 要查询的列，`['*']` 表示所有列
- `limit`: 返回结果数量限制
- `desc`: 是否降序排列，默认False（升序）

**返回值**：pandas DataFrame

## 错误处理

### 库未安装检测

```python
try:
    from k2magic.k2_dataframe_db import K2DataFrameDB
    K2MAGIC_AVAILABLE = True
except ImportError:
    K2MAGIC_AVAILABLE = False
    app_logger.warning("K2Magic库未安装，将使用降级模式")
```

### 异常处理

```python
try:
    df = client.get_repo_data(...)
except Exception as e:
    app_logger.error(f"K2Magic读取仓库数据失败: repo={repo}, error={e}")
    raise
```

## 性能优化

### 1. 客户端缓存

为每个 repo 缓存客户端实例，避免重复创建连接。

### 2. 合理设置参数

- **时间范围**：避免查询过大的时间跨度
- **limit 参数**：限制返回结果数量
- **columns 参数**：只查询需要的列，避免 `['*']`
- **设备过滤**：通过 `k_devices` 只查询需要的设备

### 3. 启用 REST API

设置 `K2MAGIC_REST=True` 获得更好性能。

## 日志记录

### 日志格式

```python
app_logger.info(
    f"K2Magic读取成功 - repo={repo}, devices={len(devices)}, "
    f"start_time={start_time}, end_time={end_time}, "
    f"耗时={elapsed:.3f}s, 结果数={len(df)}, columns={columns}"
)
```

### 日志内容

- 仓库名称
- 设备数量
- 时间范围
- 查询耗时
- 结果数量
- 查询列

## 测试方法

### 连接测试

```python
async def test_connection():
    service = K2MagicService()
    await service.connect()
    
    df = await service.get_repo_data_by_time(
        repo='device_history',
        k_devices=['device001'],
        start_time='2024-01-01T00:00:00',
        end_time='2024-01-02T00:00:00',
        limit=10
    )
    print(f"✅ 查询成功，返回 {len(df)} 条记录")
    print(df.head())
```

## 常见问题

### Q1: 连接失败

**检查项**：
1. 连接URL格式是否正确（包含 `{repo}` 占位符）
2. K2Assets 服务是否可访问
3. 用户名密码是否正确
4. K2Magic 库是否已安装
5. Tenant 配置是否正确

### Q2: 仓库不存在或查询失败

**检查项**：
1. 仓库名称拼写正确
2. 仓库权限和访问权限
3. 使用 K2Assets 管理工具确认仓库存在

### Q3: 返回数据为空

**检查项**：
1. 时间范围是否正确（时区问题）
2. 设备ID是否存在
3. 仓库中是否有该时间段的数据
