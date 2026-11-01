#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速初始化LLM客户端的脚本
用于快速验证LLM配置和客户端是否正常工作
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from autoy.llm import (
    get_llm,
    chat,
    get_model_info,
    list_models,
    list_available_models,
    Provider,
    get_recommended_model,
    is_model_available,
)
from loguru import logger
from langchain_core.messages import HumanMessage


def main():
    """初始化并测试LLM客户端"""
    try:
        # 1. 列出所有模型
        logger.info("正在列出所有可用模型...")
        all_models = list_models()
        logger.info(f"所有模型: {all_models}")
        
        # 2. 按供应商列出模型
        deepseek_models = list_models(Provider.DEEPSEEK)
        logger.info(f"DeepSeek模型: {deepseek_models}")
        
        qwen_models = list_models(Provider.QWEN)
        logger.info(f"Qwen模型: {qwen_models}")
        
        # 3. 获取模型信息
        logger.info("正在获取模型信息...")
        info = get_model_info("deepseek-chat")
        if info:
            logger.info(f"模型信息:")
            logger.info(f"  - Model ID: {info.model_id}")
            logger.info(f"  - Provider: {info.provider.value}")
            logger.info(f"  - Base URL: {info.base_url}")
            logger.info(f"  - Temperature: {info.temperature}")
            logger.info(f"  - Max Tokens: {info.max_tokens}")
        
        # 4. 检查模型可用性
        logger.info("正在检查模型可用性...")
        available = is_model_available("deepseek-chat")
        logger.info(f"deepseek-chat 可用: {available}")
        
        if not available:
            logger.warning("模型不可用，请检查API密钥配置")
            logger.warning("需要设置 DEEPSEEK_API_KEY 或 OPENAI_API_KEY 环境变量")
            return 1
        
        # 5. 获取推荐模型
        logger.info("正在获取推荐模型...")
        recommended = get_recommended_model("coldstart")
        logger.info(f"coldstart任务推荐模型: {recommended}")
        
        # 6. 初始化LLM客户端
        logger.info("正在初始化LLM客户端...")
        llm = get_llm("deepseek-chat")
        
        if not llm:
            logger.error("无法初始化LLM客户端")
            logger.error("请检查API密钥配置")
            return 1
        
        logger.info("LLM客户端初始化成功")
        
        # 7. 测试基础调用
        logger.info("正在测试基础API调用...")
        response = llm.invoke([HumanMessage(content="Say 'Hello, World!' in one sentence.")])
        
        logger.info("API调用成功:")
        logger.info(f"  - Response: {response.content}")
        
        # 8. 测试便捷函数
        logger.info("正在测试便捷函数...")
        chat_response = chat("你好", model_id="deepseek-chat")
        if chat_response:
            logger.info(f"  - Chat Response: {chat_response}")
        
        # 9. 测试任务类型推荐
        logger.info("正在测试任务类型推荐...")
        llm_by_task = get_llm(task_type="coldstart")
        if llm_by_task:
            logger.info("通过任务类型获取LLM成功")
            response = llm_by_task.invoke([HumanMessage(content="Test message")])
            logger.info(f"  - Response: {response.content[:50]}...")
        
        # 10. 列出可用模型
        logger.info("正在列出可用模型...")
        available_models = list_available_models()
        logger.info(f"可用模型: {available_models}")
        
        logger.info("所有测试通过！")
        return 0
        
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
