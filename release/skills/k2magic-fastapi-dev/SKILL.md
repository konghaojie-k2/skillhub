---
name: k2magic-fastapi-dev
description: 使用 K2Magic SDK 读取公司产品数据并开发 FastAPI 接口的完整指南。当需要：(1) 集成 K2Magic SDK 访问 K2Assets 仓库数据，(2) 开发 FastAPI REST API 接口，(3) 实现数据服务层和降级策略，(4) 配置查询类型和多仓库数据合并时使用此技能。
---

# K2Magic FastAPI 开发指南

## 概述

本技能提供使用 K2Magic SDK 访问 K2Assets 仓库数据，并基于 FastAPI 开发 REST API 的完整工作流程。涵盖从 SDK 集成、服务封装、API 开发到降级策略的完整实现。

## 快速开始

### 1. 安装 K2Magic

使用 UV 安装（推荐）：
```powershell
uv add k2magic pandas
```

或使用 pip：
```bash
pip install k2magic pandas
```

### 2. 配置连接

在 `.env` 文件中配置 K2Magic 连接 URL：
```env
K2MAGIC_CONNECTION_URL=k2assets+repo://username:password@host/{repo}?tenant=tenant_name
K2MAGIC_REST=True
K2MAGIC_TIMEOUT=30
```

**重要**：URL 中必须包含 `{repo}` 占位符，实际调用时会替换为具体的仓库名称。

### 3. 基本使用

```python
from app.services.k2magic_service import K2MagicService

# 初始化服务
k2magic_service = K2MagicService()

# 查询仓库数据
df = await k2magic_service.get_repo_data_by_time(
    repo='device_history',
    k_devices=['device001', 'device002'],
    start_time='2024-01-01T00:00:00',
    end_time='2024-01-02T00:00:00',
    columns=['*'],
    limit=1000
)
```

## K2Magic SDK 集成

### 服务封装模式

创建 `app/services/k2magic_service.py` 封装 K2Magic SDK：

```python
from k2magic.k2_dataframe_db import K2DataFrameDB
from app.core.config import settings

class K2MagicService:
    def __init__(self):
        self.connection_url_template = settings.k2magic_connection_url
        self._clients: Dict[str, Any] = {}  # 缓存客户端实例
    
    def _get_client(self, repo: str):
        """获取指定repo的客户端实例（带缓存）"""
        if repo in self._clients:
            return self._clients[repo]
        
        connection_url = self.connection_url_template.format(repo=repo)
        client = K2DataFrameDB(connection_url, rest=self.rest)
        self._clients[repo] = client
        return client
    
    async def get_repo_data_by_time(
        self,
        repo: str,
        k_devices: List[Union[str, int]],
        start_time: Optional[Union[str, datetime]] = None,
        end_time: Optional[Union[str, datetime]] = None,
        columns: List[str] = ['*'],
        limit: Optional[int] = None,
        desc: bool = False
    ) -> pd.DataFrame:
        """通过时间范围读取仓库数据"""
        client = self._get_client(repo)
        devices = [str(k) for k in k_devices]
        
        df = client.get_repo_data(
            columns=columns,
            start_time=start_time,
            end_time=end_time,
            devices=devices,
            limit=limit,
            desc=desc
        )
        return df
```

### 关键要点

1. **客户端缓存**：为每个 repo 创建独立的客户端实例并缓存，避免重复创建
2. **URL 占位符**：连接 URL 使用 `{repo}` 占位符，调用时动态替换
3. **设备ID转换**：将设备ID统一转换为字符串列表
4. **返回值**：直接返回 pandas DataFrame，便于后续处理

## FastAPI 接口开发

### 项目结构

```
app/
├── api/
│   └── v1/
│       ├── router.py          # 路由汇总
│       └── endpoints/
│           ├── query.py        # 查询接口
│           └── health.py       # 健康检查
├── services/
│   ├── k2magic_service.py     # K2Magic SDK 封装
│   ├── data_service.py        # 数据服务层（降级逻辑）
│   └── query_config.py        # 查询配置管理
├── models/
│   ├── requests.py            # 请求模型
│   └── responses.py           # 响应模型
└── main.py                    # 应用入口
```

### 创建查询接口

在 `app/api/v1/endpoints/query.py` 中：

```python
from fastapi import APIRouter, Depends, HTTPException
from app.models.requests import DataQueryRequest
from app.models.responses import BaseResponse, QueryResponse
from app.services.data_service import DataService

router = APIRouter(prefix="/query", tags=["数据查询"])

@router.post("", response_model=BaseResponse[QueryResponse])
async def query_data(
    query_req: DataQueryRequest,
    data_service: DataService = Depends(get_data_service)
):
    """数据查询接口"""
    # 执行查询（自动处理降级）
    data, source, query_time, fallback = await data_service.query_by_type(
        query_type=query_req.query_type,
        devices=query_req.devices,
        start_time=query_req.start_time,
        end_time=query_req.end_time,
        columns=query_req.columns,
        limit=query_req.limit
    )
    
    # 转换为字典列表
    data_list = data.to_dict('records') if not data.empty else []
    
    return BaseResponse(
        success=True,
        message=f"查询成功 - 类型: {query_req.query_type}, 数据源: {source}",
        data=QueryResponse(
            total=len(data_list),
            data=data_list,
            source=source,
            query_time=query_time,
            fallback=fallback
        )
    )
```

### 依赖注入模式

使用 FastAPI 的依赖注入管理服务实例：

```python
# app/core/dependencies.py
from app.services.k2magic_service import K2MagicService
from app.services.database_service import DatabaseService
from app.services.data_service import DataService

def get_data_service() -> DataService:
    """获取数据服务实例"""
    k2magic = K2MagicService()
    database = DatabaseService()
    return DataService(k2magic, database)
```

### 应用生命周期管理

在 `app/main.py` 中使用 `lifespan` 管理服务：

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化服务
    k2magic_service = K2MagicService()
    database_service = DatabaseService()
    data_service = DataService(k2magic_service, database_service)
    
    await k2magic_service.connect()
    await database_service.connect()
    
    app.state.data_service = data_service
    
    yield
    
    # 关闭时清理资源
    await k2magic_service.disconnect()
    await database_service.disconnect()

app = FastAPI(lifespan=lifespan)
```

## 数据服务层设计

### 降级策略实现

`data_service.py` 实现自动降级逻辑：

```python
class DataService:
    async def query_repo_by_time(
        self,
        repo: str,
        k_devices: List[Union[str, int]],
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        **kwargs
    ) -> Tuple[pd.DataFrame, str, float, bool]:
        """查询仓库数据（带降级逻辑）"""
        try:
            # 优先使用 K2Magic
            data = await asyncio.wait_for(
                self.k2magic.get_repo_data_by_time(...),
                timeout=self.fallback_timeout
            )
            return data, "k2magic", elapsed, False
        except (asyncio.TimeoutError, Exception) as e:
            # 降级到数据库
            if self.fallback_enabled:
                app_logger.warning(f"K2Magic失败，降级到数据库: {e}")
                data = await self._query_database(...)
                return data, "database", elapsed, True
            else:
                raise
```

### 查询类型配置

使用 TOML 配置文件管理查询类型（`config/query_config.toml`）：

```toml
[device_history]
query_type = "device_history"
merge_strategy = "concat"

[[device_history.repos]]
repo_name = "device_history_repo"
columns = ["*"]
required = true

[device_comprehensive]
query_type = "device_comprehensive"
merge_strategy = "merge"
merge_key = "device_id"

[[device_comprehensive.repos]]
repo_name = "device_status_repo"
columns = ["device_id", "status"]
required = false

[[device_comprehensive.repos]]
repo_name = "device_history_repo"
columns = ["device_id", "timestamp", "value"]
required = true
```

### 多仓库数据合并

`query_by_type` 方法自动处理多仓库查询和合并：

```python
async def query_by_type(
    self,
    query_type: str,
    devices: List[str],
    **kwargs
) -> Tuple[pd.DataFrame, str, float, bool]:
    """根据查询类型查询数据"""
    config = self.query_config_service.get_config(query_type)
    
    # 查询所有repo
    repo_dataframes = []
    for repo_config in config.repos:
        df, _, _, fallback = await self.query_repo_by_time(
            repo=repo_config.repo_name,
            k_devices=devices,
            **kwargs
        )
        repo_dataframes.append((df, repo_config.repo_name))
    
    # 根据合并策略合并数据
    if config.merge_strategy == "merge":
        merged_df = pd.merge(...)  # 按key合并
    else:
        merged_df = pd.concat(...)  # 简单拼接
    
    return merged_df, "k2magic", elapsed, fallback_used
```

## 业务逻辑组织

### 分层原则

1. **`k2magic_service.py`**：纯粹封装 K2Magic SDK，不包含业务逻辑
2. **`data_service.py`**：提供通用的数据获取方法（如 `query_by_type`）
3. **`endpoints/*.py`**：实现特定 API 的业务逻辑（数值转换、逻辑判断、数据组装）

### 示例：温度监控接口

```python
@router.post("/temperature")
async def monitor_temperature(
    devices: list[str],
    start_time: str,
    end_time: str,
    threshold: float = 100.0,
    data_service: DataService = Depends(get_data_service)
):
    """温度监控接口"""
    # 1. 调用通用服务获取原始数据
    data, source, query_time, fallback = await data_service.query_by_type(
        query_type="device_temperature",
        devices=devices,
        start_time=start_time,
        end_time=end_time
    )
    
    # 2. 业务逻辑 - 单位转换
    if 'unit' in data.columns:
        mask = data['unit'] == 'C'
        data.loc[mask, 'temperature'] = data.loc[mask, 'temperature'] * 9/5 + 32
    
    # 3. 业务逻辑 - 异常检测
    data['is_abnormal'] = data['temperature'] > threshold
    
    # 4. 生成响应
    return BaseResponse(
        success=True,
        data={
            'summary': {
                'total': len(data),
                'abnormal_count': int(data['is_abnormal'].sum())
            },
            'details': data.to_dict('records')
        }
    )
```

## 配置管理

### 环境变量配置

使用 Pydantic Settings 管理配置（`app/core/config.py`）：

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    k2magic_connection_url: str
    k2magic_rest: bool = True
    k2magic_timeout: int = 30
    fallback_enabled: bool = True
    fallback_timeout: int = 5
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
```

## 错误处理和日志

### 日志记录

使用 loguru 记录详细日志：

```python
from app.core.logger import app_logger

app_logger.info(
    f"K2Magic读取成功 - repo={repo}, devices={len(devices)}, "
    f"耗时={elapsed:.3f}s, 结果数={len(df)}"
)
```

### 错误处理

```python
try:
    df = await k2magic_service.get_repo_data_by_time(...)
except ImportError:
    app_logger.error("K2Magic库未安装")
    raise
except Exception as e:
    app_logger.error(f"K2Magic查询失败: {e}")
    # 触发降级逻辑
    raise
```

## 测试和验证

### 健康检查接口

```python
@router.get("/health")
async def health_check(
    data_service: DataService = Depends(get_data_service)
):
    """健康检查"""
    status = await data_service.check_data_sources()
    return {
        "status": "healthy" if all(status.values()) else "degraded",
        "data_sources": status
    }
```

### 测试查询

```python
# 测试脚本
async def test_query():
    service = K2MagicService()
    df = await service.get_repo_data_by_time(
        repo='device_history',
        k_devices=['device001'],
        start_time='2024-01-01T00:00:00',
        end_time='2024-01-02T00:00:00',
        limit=10
    )
    print(f"查询成功，返回 {len(df)} 条记录")
```

## 参考资源

- **K2Magic SDK 集成**：详见 `references/k2magic_integration.md`
- **FastAPI 开发模式**：详见 `references/fastapi_patterns.md`
- **业务逻辑组织**：详见 `references/business_logic.md`
- **查询配置管理**：详见 `references/query_config.md`

## 常见问题

### Q: 连接失败怎么办？

A: 检查：
1. 连接 URL 格式是否正确（包含 `{repo}` 占位符）
2. K2Assets 服务是否可访问
3. 用户名密码是否正确
4. K2Magic 库是否已安装

### Q: 如何禁用降级策略？

A: 在 `.env` 中设置 `FALLBACK_ENABLED=False`

### Q: 如何添加新的查询类型？

A: 在 `config/query_config.toml` 中添加新配置，系统会自动识别

### Q: 多仓库数据如何合并？

A: 在配置中设置 `merge_strategy` 和 `merge_key`，系统会自动处理
