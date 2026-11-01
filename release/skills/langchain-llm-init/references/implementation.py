#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain LLM 初始化的完整实现示例
包含模型配置管理和模型管理器的最佳实践
支持多供应商统一管理
"""

# ==================== 模型配置模块实现 ====================

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


# ==================== 模型管理器实现 ====================

from typing import Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

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


# ==================== 使用示例 ====================

if __name__ == "__main__":
    # 示例1：直接指定模型
    llm = get_llm("deepseek-chat")
    if llm:
        response = llm.invoke([HumanMessage(content="Hello")])
        print(f"Response: {response.content}")
    
    # 示例2：根据任务类型自动推荐
    llm = get_llm(task_type="coldstart")
    if llm:
        response = llm.invoke([HumanMessage(content="Analyze this data")])
        print(f"Response: {response.content}")
    
    # 示例3：使用便捷函数
    response = chat("你好", model_id="deepseek-chat")
    if response:
        print(f"Chat response: {response}")
    
    # 示例4：自定义参数
    llm = get_llm("deepseek-chat", temperature=0.5, max_tokens=1000)
    if llm:
        response = llm.invoke([HumanMessage(content="Tell me a joke")])
        print(f"Response: {response.content}")
    
    # 示例5：JSON格式输出
    llm = get_llm("deepseek-chat", temperature=0.3)
    if llm:
        llm_with_json = llm.bind(response_format={"type": "json_object"})
        response = llm_with_json.invoke([
            SystemMessage(content="You are a helpful assistant"),
            HumanMessage(content="Return a JSON object with key 'status' and value 'ok'")
        ])
        import json
        result = json.loads(response.content)
        print(f"JSON response: {result}")
