# FastAPI 开发模式指南

## 项目结构

```
app/
├── api/
│   └── v1/
│       ├── router.py          # 路由汇总
│       └── endpoints/
│           ├── query.py       # 查询接口
│           └── health.py       # 健康检查
├── services/
│   ├── k2magic_service.py    # K2Magic SDK 封装
│   ├── data_service.py       # 数据服务层
│   └── query_config.py       # 查询配置管理
├── models/
│   ├── requests.py           # 请求模型
│   └── responses.py          # 响应模型
├── core/
│   ├── config.py             # 配置管理
│   ├── dependencies.py        # 依赖注入
│   └── logger.py             # 日志配置
└── main.py                   # 应用入口
```

## 路由组织

### 路由汇总（router.py）

```python
from fastapi import APIRouter
from app.api.v1.endpoints import health, query, demo

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(query.router)
api_router.include_router(demo.router)
```

### 端点定义（endpoints/query.py）

```python
from fastapi import APIRouter, Depends, HTTPException
from app.core.dependencies import get_data_service
from app.services.data_service import DataService

router = APIRouter(prefix="/query", tags=["数据查询"])

@router.post("", response_model=BaseResponse[QueryResponse])
async def query_data(
    query_req: DataQueryRequest,
    data_service: DataService = Depends(get_data_service)
):
    """数据查询接口"""
    # 实现逻辑
    pass
```

## 依赖注入

### 服务依赖（core/dependencies.py）

```python
from app.services.k2magic_service import K2MagicService
from app.services.database_service import DatabaseService
from app.services.data_service import DataService

def get_data_service() -> DataService:
    """获取数据服务实例"""
    k2magic = K2MagicService()
    database = DatabaseService()
    return DataService(k2magic, database)
```

### 在端点中使用

```python
@router.post("/query")
async def query_data(
    query_req: DataQueryRequest,
    data_service: DataService = Depends(get_data_service)
):
    # 使用 data_service
    pass
```

## 应用生命周期

### 使用 lifespan 管理

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化服务
    k2magic_service = K2MagicService()
    database_service = DatabaseService()
    data_service = DataService(k2magic_service, database_service)
    
    await k2magic_service.connect()
    await database_service.connect()
    
    app.state.k2magic_service = k2magic_service
    app.state.database_service = database_service
    app.state.data_service = data_service
    
    yield
    
    # 关闭时清理资源
    await k2magic_service.disconnect()
    await database_service.disconnect()

app = FastAPI(lifespan=lifespan)
```

## 请求和响应模型

### 请求模型（models/requests.py）

```python
from pydantic import BaseModel, Field
from typing import Optional, List

class DataQueryRequest(BaseModel):
    query_type: str = Field(..., description="查询类型")
    devices: List[str] = Field(..., description="设备ID列表")
    start_time: Optional[str] = Field(None, description="开始时间")
    end_time: Optional[str] = Field(None, description="结束时间")
    columns: Optional[List[str]] = Field(None, description="查询列")
    limit: Optional[int] = Field(None, description="结果数量限制")
```

### 响应模型（models/responses.py）

```python
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, List, Any

T = TypeVar('T')

class BaseResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: Optional[T] = None

class QueryResponse(BaseModel):
    total: int
    data: List[dict]
    source: str
    query_time: float
    fallback: bool
```

## 错误处理

### HTTP 异常

```python
from fastapi import HTTPException

@router.post("/query")
async def query_data(query_req: DataQueryRequest):
    try:
        # 业务逻辑
        pass
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        app_logger.error(f"查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### 业务错误处理

```python
try:
    data, source, query_time, fallback = await data_service.query_by_type(...)
except ValueError as e:
    # 查询类型不存在等业务错误
    app_logger.error(f"查询参数错误: {e}")
    raise HTTPException(status_code=400, detail=str(e))
```

## 中间件

### CORS 中间件

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 自定义中间件

```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        app_logger.info(f"{request.method} {request.url} - {process_time:.3f}s")
        return response

app.add_middleware(LoggingMiddleware)
```

## 配置管理

### 使用 Pydantic Settings

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "SNPRI API"
    api_prefix: str = "/api/v1"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    k2magic_connection_url: str
    k2magic_rest: bool = True
    k2magic_timeout: int = 30
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
```

## 日志配置

### 使用 loguru

```python
from loguru import logger
import sys

logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="INFO"
)
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    rotation="500 MB",
    retention="7 days",
    level="INFO"
)

app_logger = logger
```

## API 文档

### Swagger UI

FastAPI 自动生成 API 文档：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 自定义文档

```python
app = FastAPI(
    title="SNPRI API",
    version="0.1.0",
    description="基于FastAPI的接口框架",
    docs_url="/docs",
    redoc_url="/redoc"
)
```

## 启动应用

### 使用 uvicorn

```python
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
```

### 命令行启动

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 最佳实践

1. **路由组织**：按功能模块组织路由，使用 `APIRouter` 汇总
2. **依赖注入**：使用 FastAPI 的依赖注入管理服务实例
3. **生命周期管理**：使用 `lifespan` 管理服务启动和关闭
4. **模型验证**：使用 Pydantic 模型进行请求和响应验证
5. **错误处理**：统一错误处理，返回清晰的错误信息
6. **日志记录**：记录关键操作和错误信息
7. **配置管理**：使用环境变量和 Pydantic Settings 管理配置
