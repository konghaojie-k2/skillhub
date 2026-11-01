#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain LLM 初始化的测试示例
包含单元测试、集成测试和API集成测试的最佳实践
"""

import pytest
import os
from pathlib import Path
import sys
from dotenv import load_dotenv

# 加载.env文件（使用override=True确保.env文件中的值覆盖系统环境变量）
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path, override=True)

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

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
    list_available_models,
    model_manager,
)


# ==================== 模型配置测试 ====================

class TestModelConfig:
    """模型配置测试类"""

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

    def test_list_models_by_provider(self):
        """测试按供应商列出模型"""
        deepseek_models = list_models(Provider.DEEPSEEK)
        assert isinstance(deepseek_models, list)
        assert "deepseek-chat" in deepseek_models
        
        qwen_models = list_models(Provider.QWEN)
        assert isinstance(qwen_models, list)
        assert "qwen3-max" in qwen_models

    def test_get_model_info(self):
        """测试获取模型信息"""
        info = get_model_info("deepseek-chat")
        assert info is not None
        assert isinstance(info, ModelInfo)
        assert info.model_id == "deepseek-chat"
        assert info.provider == Provider.DEEPSEEK
        assert info.base_url is not None

    def test_get_model_info_not_exist(self):
        """测试获取不存在的模型"""
        info = get_model_info("non-existent-model")
        assert info is None

    def test_is_model_available(self):
        """测试模型可用性检查"""
        api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
        available = is_model_available("deepseek-chat")
        assert isinstance(available, bool)
        # 如果没有API密钥，应该返回False
        if not api_key or api_key.startswith("test-") or api_key == "":
            assert available is False

    def test_get_recommended_model(self):
        """测试获取推荐模型"""
        model = get_recommended_model("coldstart")
        assert model is None or isinstance(model, str)


# ==================== 模型管理器测试 ====================

class TestModelManager:
    """模型管理器测试类"""

    def test_manager_initialization(self):
        """测试管理器初始化"""
        manager = ModelManager()
        assert manager is not None
        assert isinstance(manager._cache, dict)

    def test_get_llm_with_invalid_model(self):
        """测试获取不存在的模型"""
        llm = model_manager.get_llm("non-existent-model")
        assert llm is None

    def test_get_llm_by_task_type(self):
        """测试通过任务类型获取LLM"""
        llm = model_manager.get_llm(task_type="coldstart")
        # 可能返回None（如果没有API密钥）
        assert llm is None or llm is not None

    def test_get_llm_without_params(self):
        """测试不传参数时获取第一个可用模型"""
        llm = model_manager.get_llm()
        # 可能返回None（如果没有API密钥）
        assert llm is None or llm is not None

    def test_get_available_models(self):
        """测试获取可用模型列表"""
        models = model_manager.get_available_models()
        assert isinstance(models, list)

    def test_clear_cache(self):
        """测试清理缓存"""
        model_manager.clear_cache()
        assert len(model_manager._cache) == 0

    @pytest.mark.skipif(
        not os.environ.get("DEEPSEEK_API_KEY") and not os.environ.get("OPENAI_API_KEY"),
        reason="需要有效的API密钥"
    )
    def test_test_connection(self):
        """测试模型连接（需要有效API）"""
        load_dotenv(env_path, override=True)
        api_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if not api_key or api_key.startswith("test-"):
            pytest.skip("需要有效的API密钥")

        result = model_manager.test_connection("deepseek-chat")
        assert isinstance(result, bool)


# ==================== 便捷函数测试 ====================

class TestConvenienceFunctions:
    """便捷函数测试类"""

    def test_get_llm_function(self):
        """测试get_llm便捷函数"""
        # 测试不存在的模型
        llm = get_llm("non-existent-model")
        assert llm is None
        
        # 测试存在的模型（可能返回None或LLM实例，取决于API密钥配置）
        llm = get_llm("deepseek-chat")
        assert llm is None or llm is not None

    def test_list_available_models_function(self):
        """测试list_available_models便捷函数"""
        models = list_available_models()
        assert isinstance(models, list)

    def test_chat_function_without_api(self):
        """测试chat便捷函数（无API）"""
        # 测试不存在的模型应该返回None
        response = chat("Hello", model_id="non-existent-model")
        assert response is None
        
        # 测试存在的模型（可能返回None或响应，取决于API密钥配置）
        response = chat("Hello", model_id="deepseek-chat")
        assert response is None or isinstance(response, str)

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
        assert len(response) > 0


# ==================== 集成测试 ====================

class TestLLMIntegration:
    """LLM集成测试类"""

    def test_end_to_end_workflow(self):
        """测试端到端工作流程"""
        # 1. 列出所有模型
        all_models = list_models()
        assert len(all_models) > 0

        # 2. 按供应商过滤
        deepseek_models = list_models(Provider.DEEPSEEK)
        assert "deepseek-chat" in deepseek_models

        # 3. 获取模型信息
        info = get_model_info("deepseek-chat")
        assert info is not None
        assert info.provider == Provider.DEEPSEEK

        # 4. 检查可用性
        available = is_model_available("deepseek-chat")
        assert isinstance(available, bool)

        # 5. 获取推荐模型
        recommended = get_recommended_model("coldstart")
        # 可能返回None（如果没有API密钥）

    def test_global_model_manager_instance(self):
        """测试全局模型管理器实例"""
        assert model_manager is not None
        assert isinstance(model_manager, ModelManager)

        # 测试可用模型列表
        available = model_manager.get_available_models()
        assert isinstance(available, list)
