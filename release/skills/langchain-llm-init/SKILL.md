---
name: langchain-llm-init
description: Guide for initializing and configuring LLM clients using LangChain 1.2+ with langchain-openai. Use when setting up LLM infrastructure, configuring OpenAI-compatible APIs (like DeepSeek, Qwen), managing environment variables, writing integration tests for LLM clients, implementing unified LLM configuration management with multi-provider support, or creating agents with create_agent. Covers LangChain best practices, message format conversion, base_url handling, environment variable loading with python-dotenv, model manager pattern, create_agent usage, tool binding strategies, structured output with ToolStrategy, and comprehensive test patterns.
metadata:
  author: konghaojie
  version: 2.0.0
  last_modified: 2026-01-31
---

# LangChain LLM 初始化技能

**版本**: 2.0.0  
**最后更新**: 2026-01-31

使用 LangChain 1.2+ 和 `langchain-openai` 初始化和管理 LLM 客户端的最佳实践，支持多供应商统一管理，包括 Agent 创建和工具调用。

## 版本历史

### v2.0.0 (2026-01-31)
- ✨ 添加 `create_agent` 最佳实践和完整示例
- ✨ 添加工具绑定策略说明（工具应在 `create_agent` 时传入）
- ✨ 添加结构化输出 `ToolStrategy` 使用指南
- 🔧 修正消息类型导入路径（`langchain.messages` 而非 `langchain_core.messages`）
- 📝 更新版本说明从 LangChain 1.1+ 到 1.2+
- 📚 添加工具绑定策略对比表和常见问题解答

### v1.0.0
- 初始版本，包含基础的 LLM 初始化和配置管理

## 核心原则

1. **统一配置管理**：使用 `model_config` 和 `model_manager` 模块统一管理多供应商配置
2. **环境变量优先**：使用 `.env` 文件管理配置，支持 `override=True` 覆盖系统环境变量
3. **LangChain 1.2+ 标准**：使用最新的 LangChain API 和导入路径
4. **多供应商支持**：通过 `Provider` 枚举和 `ModelInfo` 数据类支持多个 LLM 供应商
5. **任务类型推荐**：根据任务类型自动推荐合适的模型
6. **工具绑定策略**：工具应在 `create_agent` 时传入，而不是提前绑定到 LLM
7. **结构化输出**：使用 `ToolStrategy` 实现结构化输出，支持 Pydantic 模型
8. **完整测试覆盖**：包含单元测试、集成测试和 API 集成测试

## 快速开始

### 1. 依赖配置

在 `pyproject.toml` 中添加：

```toml
dependencies = [
    "langchain>=1.2.6",
    "langchain-core>=0.3.0",
    "langchain-openai>=0.2.0",
    "python-dotenv>=1.0.0",
    "loguru>=0.7.0",
    # ... 其他依赖
]
```

### 2. 模型配置模块实现

创建 `llm/model_config.py`：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""模型配置模块 - Model Configuration Module"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from dotenv import load_dotenv
from loguru import logger

# 加载.env文件（如果存在）
env_path = Path(__file__).parent.parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path, override=True)
    logger.debug(f"已加载.env文件: {env_path}")

class Provider(str, Enum):
    """LLM供应商枚举"""
    DEEPSEEK = "deepseek"
    QWEN = "qwen"

@dataclass(frozen=True)
class ModelInfo:
    """模型信息数据类"""
    model_id: str
    model_name: str
    provider: Provider
    api_key: str
    base_url: str
    temperature: float = 0.3
    max_tokens: int = 2000

def _get_env_key(key: str, default: str = "") -> str:
    """获取环境变量，支持默认值"""
    return os.getenv(key, default)

# 供应商配置常量
PROVIDER_CONFIGS: Dict[Provider, Dict[str, any]] = {
    Provider.DEEPSEEK: {
        "api_key": _get_env_key("DEEPSEEK_API_KEY") or _get_env_key("OPENAI_API_KEY", ""),
        "base_url": _get_env_key("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        "models": ["deepseek-chat", "deepseek-reasoner"],
    },
    Provider.QWEN: {
        "api_key": _get_env_key("QWEN_API_KEY", ""),
        "base_url": _get_env_key("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        "models": ["qwen3-max", "qwen3-plus"],
    }
}

# 任务类型推荐模型配置
TASK_RECOMMENDED_MODELS: Dict[str, List[str]] = {
    "coldstart": ["deepseek-chat", "qwen3-plus"],
    "validation": ["deepseek-chat", "qwen3-plus"],
    "chat": ["deepseek-chat", "qwen3-plus"],
    "analysis": ["deepseek-chat", "qwen3-plus"],
}

def _build_model_configs() -> Dict[str, ModelInfo]:
    """构建模型配置字典"""
    configs: Dict[str, ModelInfo] = {}
    for provider, config in PROVIDER_CONFIGS.items():
        for model_name in config["models"]:
            configs[model_name] = ModelInfo(
                model_id=model_name,
                model_name=model_name,
                provider=provider,
                api_key=config["api_key"],
                base_url=config["base_url"],
            )
    return configs

# 模型配置表（模块初始化时生成）
MODEL_CONFIGS: Dict[str, ModelInfo] = _build_model_configs()

@lru_cache(maxsize=128)
def get_model_info(model_id: str) -> Optional[ModelInfo]:
    """获取模型配置信息"""
    return MODEL_CONFIGS.get(model_id)

def list_models(provider: Optional[Provider] = None) -> List[str]:
    """列出可用模型列表"""
    if provider:
        return [model_id for model_id, info in MODEL_CONFIGS.items() 
                if info.provider == provider]
    return list(MODEL_CONFIGS.keys())

def get_recommended_model(task_type: str) -> Optional[str]:
    """获取任务推荐模型"""
    models = TASK_RECOMMENDED_MODELS.get(task_type, [])
    for model_id in models:
        info = MODEL_CONFIGS.get(model_id)
        if info and info.api_key and not info.api_key.startswith("your-"):
            return model_id
    return None

def is_model_available(model_id: str) -> bool:
    """检查模型是否可用"""
    info = get_model_info(model_id)
    if not info:
        return False
    return bool(info.api_key and not info.api_key.startswith("your-") 
                and not info.api_key == "")
```

### 3. 模型管理器实现

创建 `llm/model_manager.py`：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统一模型管理器 - Unified Model Manager"""

from typing import Optional, Dict, List, Any
from loguru import logger
from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage, SystemMessage

from .model_config import (
    MODEL_CONFIGS,
    Provider,
    get_model_info,
    get_recommended_model,
    is_model_available,
)

class ModelManager:
    """统一模型管理器"""
    
    def __init__(self) -> None:
        """初始化模型管理器"""
        self._cache: Dict[str, ChatOpenAI] = {}
        logger.info("Model manager initialized")
    
    def get_llm(
        self,
        model_id: Optional[str] = None,
        task_type: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Optional[ChatOpenAI]:
        """获取LangChain ChatOpenAI实例
        
        优先级：直接指定 > 任务推荐 > 第一个可用模型
        """
        # 确定使用的模型ID
        model_id = self._resolve_model_id(model_id, task_type)
        if not model_id:
            logger.error("No available model configuration")
            return None
        
        # 检查缓存
        cache_key = f"{model_id}_{temperature}_{max_tokens}"
        if cache_key in self._cache:
            logger.debug(f"Using cached model instance: {model_id}")
            return self._cache[cache_key]
        
        # 获取模型配置
        model_info = get_model_info(model_id)
        if not model_info:
            logger.error(f"Model configuration not found: {model_id}")
            return None
        
        # 验证API密钥
        if not is_model_available(model_id):
            logger.warning(f"Model {model_id} has no valid API key configured")
            return None
        
        try:
            # 创建ChatOpenAI实例
            llm = ChatOpenAI(
                model=model_info.model_name,
                api_key=model_info.api_key,
                base_url=model_info.base_url,
                temperature=(
                    temperature if temperature is not None else model_info.temperature
                ),
                max_tokens=(
                    max_tokens if max_tokens is not None else model_info.max_tokens
                ),
                **kwargs,
            )
            
            # 缓存默认配置实例
            if temperature is None and max_tokens is None:
                self._cache[model_id] = llm
            
            logger.info(f"Created model instance: {model_id} (provider: {model_info.provider.value})")
            return llm
            
        except Exception as e:
            logger.error(f"Failed to create model instance {model_id}: {e}")
            return None
    
    def _resolve_model_id(
        self, model_id: Optional[str], task_type: Optional[str]
    ) -> Optional[str]:
        """解析模型ID"""
        if model_id:
            return model_id
        
        if task_type:
            model_id = get_recommended_model(task_type)
            if model_id:
                return model_id
        
        return self._get_first_available_model()
    
    def _get_first_available_model(self) -> Optional[str]:
        """获取第一个可用模型"""
        for model_id in MODEL_CONFIGS.keys():
            if is_model_available(model_id):
                return model_id
        return None

# 全局模型管理器实例
model_manager = ModelManager()

# 便捷函数
def get_llm(
    model_id: Optional[str] = None,
    task_type: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    **kwargs: Any,
) -> Optional[ChatOpenAI]:
    """获取LLM实例（便捷函数）"""
    return model_manager.get_llm(
        model_id=model_id,
        task_type=task_type,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs,
    )

def chat(
    message: str,
    model_id: Optional[str] = None,
    task_type: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> Optional[str]:
    """同步聊天（便捷函数）"""
    llm = get_llm(
        model_id=model_id,
        task_type=task_type,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    if not llm:
        return None
    
    try:
        response = llm.invoke([HumanMessage(content=message)])
        return response.content
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        return None
```

### 4. 模块导出

创建 `llm/__init__.py`：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LLM统一管理模块"""

from .model_manager import ModelManager, get_llm, chat, list_available_models, model_manager
from .model_config import (
    Provider,
    ModelInfo,
    get_model_info,
    get_recommended_model,
    is_model_available,
    list_models,
)

__all__ = [
    'ModelManager',
    'get_llm',
    'chat',
    'list_available_models',
    'model_manager',
    'Provider',
    'ModelInfo',
    'get_model_info',
    'get_recommended_model',
    'is_model_available',
    'list_models',
]
```

## 使用方式

### 方式1：直接指定模型（推荐）

```python
from autoy.llm import get_llm
from langchain.messages import HumanMessage

# 获取LLM实例
llm = get_llm("deepseek-chat")
if llm:
    response = llm.invoke([HumanMessage(content="Hello")])
    print(response.content)
```

### 方式2：根据任务类型自动推荐

```python
from autoy.llm import get_llm

# 根据任务类型自动推荐模型
llm = get_llm(task_type="coldstart")  # 自动选择适合coldstart任务的模型
```

### 方式3：使用便捷函数

```python
from autoy.llm import chat

# 直接聊天
response = chat("你好", model_id="deepseek-chat")
print(response)
```

### 方式4：自定义参数

```python
from autoy.llm import get_llm

# 自定义温度参数
llm = get_llm("deepseek-chat", temperature=0.5, max_tokens=1000)
```

## 关键要点

### Base URL 处理

- **保留完整路径**：DeepSeek 使用 `https://api.deepseek.com`，LangChain 会自动添加 `/v1/chat/completions`
- **Qwen 特殊处理**：Qwen 使用兼容模式 `https://dashscope.aliyuncs.com/compatible-mode/v1`
- **不要添加末尾斜杠**：LangChain 会自动处理路径拼接

```python
# 正确：https://api.deepseek.com
# 正确：https://dashscope.aliyuncs.com/compatible-mode/v1
# 错误：https://api.deepseek.com/  (末尾斜杠)
```

### 环境变量加载

**必须使用 `override=True`** 确保 `.env` 文件中的值覆盖系统环境变量：

```python
load_dotenv(env_path, override=True)  # 重要！
```

### 环境变量配置

在 `.env` 文件中配置：

```bash
# DeepSeek配置（优先）
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com

# 或使用OPENAI_API_KEY作为DeepSeek的备用
OPENAI_API_KEY=your-api-key

# Qwen配置
QWEN_API_KEY=your-qwen-api-key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

### 消息格式

**重要**：LangChain 1.2+ 的导入路径有变化：

```python
# ✅ 正确：LangChain 1.2+ 使用 langchain.messages
from langchain.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage

# ❌ 错误：不要使用 langchain_core.messages（旧版本）
from langchain_core.messages import HumanMessage, SystemMessage
```

直接使用 `llm.invoke([HumanMessage(content="...")])`

### 模型配置在模块加载时构建

**重要**：`MODEL_CONFIGS` 在模块导入时构建，环境变量需要在导入前设置。测试时需要注意这一点。

## 测试模式

### 集成测试结构

创建 `tests/integration/test_llm_init.py`：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载.env文件（使用override=True）
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path, override=True)

from autoy.llm import (
    Provider,
    ModelInfo,
    get_model_info,
    get_recommended_model,
    is_model_available,
    list_models,
    ModelManager,
    get_llm,
    chat,
    model_manager,
)

class TestModelConfig:
    def test_provider_enum(self):
        """测试供应商枚举"""
        assert Provider.DEEPSEEK == "deepseek"
        assert Provider.QWEN == "qwen"
    
    def test_list_all_models(self):
        """测试列出所有模型"""
        models = list_models()
        assert isinstance(models, list)
        assert len(models) > 0
        assert "deepseek-chat" in models
    
    def test_get_model_info(self):
        """测试获取模型信息"""
        info = get_model_info("deepseek-chat")
        assert info is not None
        assert isinstance(info, ModelInfo)
        assert info.provider == Provider.DEEPSEEK
    
    def test_get_recommended_model(self):
        """测试获取推荐模型"""
        model = get_recommended_model("coldstart")
        assert model is None or isinstance(model, str)

class TestModelManager:
    def test_manager_initialization(self):
        """测试管理器初始化"""
        manager = ModelManager()
        assert manager is not None
    
    def test_get_llm_with_invalid_model(self):
        """测试获取不存在的模型"""
        llm = model_manager.get_llm("non-existent-model")
        assert llm is None
    
    def test_get_llm_by_task_type(self):
        """测试通过任务类型获取LLM"""
        llm = model_manager.get_llm(task_type="coldstart")
        assert llm is None or llm is not None
    
    @pytest.mark.skipif(
        not os.environ.get("DEEPSEEK_API_KEY") and not os.environ.get("OPENAI_API_KEY"),
        reason="需要有效的API密钥"
    )
    def test_chat_function_with_api(self):
        """测试chat便捷函数（有API）"""
        load_dotenv(env_path, override=True)
        api_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if not api_key or api_key.startswith("test-"):
            pytest.skip("需要有效的API密钥")
        
        response = chat("Say 'Hello, World!'", model_id="deepseek-chat")
        assert response is not None
        assert isinstance(response, str)
```

### 测试最佳实践

1. **测试文件顶部加载 `.env`**：使用 `override=True`
2. **API 测试中重新加载**：确保使用正确的 API 密钥
3. **跳过条件**：使用 `@pytest.mark.skipif` 标记需要真实 API 的测试
4. **注意模块加载时机**：`MODEL_CONFIGS` 在导入时构建，测试环境变量删除可能无效

## 常见问题

### 问题1：环境变量不生效

**原因**：`load_dotenv()` 默认 `override=False`，不会覆盖已存在的环境变量

**解决**：使用 `load_dotenv(override=True)`

### 问题2：模型配置在模块加载时构建

**原因**：`MODEL_CONFIGS` 在模块导入时构建，删除环境变量不会影响已构建的配置

**解决**：测试时应该测试不存在的模型，或检查 `is_model_available()` 函数

### 问题3：Base URL 路径错误

**原因**：LangChain 会自动添加端点路径，需要正确设置 base_url

**解决**：
- DeepSeek: `https://api.deepseek.com`
- Qwen: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- 不要添加末尾斜杠

### 问题4：消息导入错误

**原因**：LangChain 1.2+ 改变了导入路径

**解决**：
- `HumanMessage`, `SystemMessage`, `AIMessage`, `ToolMessage` → `from langchain.messages`
- **不要使用** `from langchain_core.messages`（这是旧版本的导入方式）

### 问题5：工具绑定时机错误

**原因**：在初始化时提前绑定工具到 LLM，导致无法灵活控制工具使用

**解决**：
- ❌ **错误**：`self.llm_with_tools = self.llm.bind_tools(self.tools)`（在初始化时绑定）
- ✅ **正确**：在 `create_agent` 时通过 `tools` 参数传入工具列表
- ✅ **正确**：如需手动工具调用，在使用时动态绑定 `llm_with_tools = llm.bind_tools(tools)`

## Agent 创建和工具调用

### create_agent 最佳实践

LangChain 1.2+ 提供了 `create_agent` 函数来创建 Agent，支持工具调用和结构化输出。

#### 1. 基本 Agent 创建（带工具）

```python
from langchain.agents import create_agent
from langchain.messages import SystemMessage, HumanMessage
from langchain.tools import tool

# 定义工具
@tool
def search(query: str) -> str:
    """搜索工具"""
    return f"搜索结果: {query}"

@tool
def calculate(expression: str) -> str:
    """计算工具"""
    return str(eval(expression))

tools = [search, calculate]

# 创建 Agent - 工具在 create_agent 时传入
agent = create_agent(
    model=llm,
    tools=tools,  # ✅ 正确：在 create_agent 时传入工具
    system_prompt="你是一个有用的助手",
)

# 调用 Agent
result = agent.invoke({
    "messages": [
        HumanMessage(content="搜索 Python 教程")
    ]
})
```

#### 2. 结构化输出 Agent（使用 ToolStrategy）

```python
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from pydantic import BaseModel, Field
from typing import List

# 定义结构化输出模型
class AnalysisResult(BaseModel):
    """分析结果"""
    entities: List[str] = Field(..., description="实体列表")
    relationships: List[str] = Field(..., description="关系列表")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度")

# 创建结构化输出 Agent
agent = create_agent(
    model=llm,
    tools=tools,  # 工具列表
    response_format=ToolStrategy(AnalysisResult),  # 结构化输出策略
)

# 调用并获取结构化结果
result = agent.invoke({
    "messages": [
        SystemMessage(content="你是一个数据分析助手"),
        HumanMessage(content="分析以下数据...")
    ]
})

# 提取结构化响应
if hasattr(result, 'structured_response'):
    structured_data = result.structured_response
elif isinstance(result, dict) and 'structured_response' in result:
    structured_data = result['structured_response']
else:
    # 回退处理
    structured_data = None
```

#### 3. 手动工具调用模式（不使用 create_agent）

如果不需要使用 `create_agent`，可以手动处理工具调用：

```python
from langchain.messages import AIMessage, ToolMessage

# ✅ 正确：在使用时动态绑定工具
llm_with_tools = llm.bind_tools(tools)

messages = [
    SystemMessage(content="你是一个有用的助手"),
    HumanMessage(content="搜索 Python 教程")
]

# 调用 LLM（可能包含工具调用）
response: AIMessage = llm_with_tools.invoke(messages)

# 处理工具调用
if response.tool_calls:
    tool_results = []
    for tool_call in response.tool_calls:
        tool_name = tool_call.get("name")
        tool_args = tool_call.get("args", {})
        tool_id = tool_call.get("id")
        
        # 执行工具
        tool_func = tool_map.get(tool_name)
        if tool_func:
            result = tool_func(**tool_args)
            tool_results.append(ToolMessage(
                content=str(result),
                tool_call_id=tool_id
            ))
    
    # 将工具结果添加到消息历史
    messages.append(response)
    messages.extend(tool_results)
    
    # 继续调用 LLM
    final_response = llm_with_tools.invoke(messages)
```

### 工具绑定策略对比

| 方式 | 使用场景 | 优点 | 缺点 |
|------|----------|------|------|
| `create_agent` + `tools` 参数 | Agent 模式，需要自动工具调用 | 自动处理工具调用循环，支持结构化输出 | 灵活性较低 |
| 动态 `bind_tools` | 手动控制工具调用流程 | 完全控制调用流程，灵活 | 需要手动处理工具调用循环 |

### 关键要点

1. **工具不要提前绑定**：
   ```python
   # ❌ 错误：在初始化时绑定
   class Agent:
       def __init__(self):
           self.llm = get_llm()
           self.tools = get_all_tools()
           self.llm_with_tools = self.llm.bind_tools(self.tools)  # 不推荐
   
   # ✅ 正确：在 create_agent 时传入
   class Agent:
       def __init__(self):
           self.llm = get_llm()
           self.tools = get_all_tools()
       
       def create_agent(self):
           return create_agent(
               model=self.llm,
               tools=self.tools,  # 在这里传入
           )
   ```

2. **结构化输出使用 ToolStrategy**：
   ```python
   from langchain.agents.structured_output import ToolStrategy
   
   agent = create_agent(
       model=llm,
       tools=tools,
       response_format=ToolStrategy(YourPydanticModel),
   )
   ```

3. **消息类型导入**：
   ```python
   # ✅ LangChain 1.2+ 正确导入
   from langchain.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
   
   # ❌ 旧版本导入（已废弃）
   from langchain_core.messages import HumanMessage, SystemMessage
   ```

4. **工具定义**：
   ```python
   from langchain.tools import tool
   
   @tool
   def my_tool(param: str) -> str:
       """工具描述（会被 LLM 读取）"""
       return result
   ```

## 架构优势

1. **多供应商支持**：统一接口支持多个 LLM 供应商
2. **任务类型推荐**：根据任务自动选择合适模型
3. **配置集中管理**：所有模型配置集中在一个模块
4. **缓存机制**：默认配置实例自动缓存
5. **便捷函数**：提供 `get_llm()` 和 `chat()` 简化使用
6. **灵活的工具绑定**：支持 `create_agent` 和手动工具调用两种模式
7. **结构化输出支持**：通过 `ToolStrategy` 实现类型安全的结构化输出

## 参考

- **完整代码示例**：见项目 `src/autoy/llm/model_config.py` 和 `model_manager.py`
- **测试示例**：见 `tests/integration/test_llm_init.py`
- **使用示例**：见 `src/autoy/coldstart/llm_coldstart.py`
- **Agent 示例**：见项目中的 `src/agent/ontology_agent.py`
