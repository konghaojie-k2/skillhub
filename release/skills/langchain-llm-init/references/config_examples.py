#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境变量配置示例
展示如何配置不同场景的LLM客户端
"""

# ==================== .env 文件示例 ====================

"""
# LLM API配置
# DeepSeek API密钥（优先使用）
# 获取方式：https://platform.deepseek.com/
DEEPSEEK_API_KEY=your-deepseek-api-key-here

# DeepSeek API基础URL（可选，默认：https://api.deepseek.com）
DEEPSEEK_BASE_URL=https://api.deepseek.com

# 或使用OPENAI_API_KEY作为DeepSeek的备用（如果DEEPSEEK_API_KEY未设置）
OPENAI_API_KEY=your-api-key-here

# Qwen API密钥（可选）
# 获取方式：https://dashscope.console.aliyun.com/
QWEN_API_KEY=your-qwen-api-key-here

# Qwen API基础URL（可选，默认：https://dashscope.aliyuncs.com/compatible-mode/v1）
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
"""

# ==================== 使用示例 ====================

from autoy.llm import get_llm, chat, get_model_info, list_models, Provider
from langchain_core.messages import HumanMessage, SystemMessage

# 示例1：直接指定模型（推荐）
llm = get_llm("deepseek-chat")
if llm:
    response = llm.invoke([HumanMessage(content="Hello, how are you?")])
    print(response.content)

# 示例2：根据任务类型自动推荐模型
llm = get_llm(task_type="coldstart")  # 自动选择适合coldstart任务的模型
if llm:
    response = llm.invoke([HumanMessage(content="Analyze this data")])
    print(response.content)

# 示例3：使用便捷函数
response = chat("你好", model_id="deepseek-chat")
if response:
    print(response)

# 示例4：自定义温度参数
llm = get_llm("deepseek-chat", temperature=0.5, max_tokens=1000)
if llm:
    response = llm.invoke([HumanMessage(content="Tell me a joke")])
    print(response.content)

# 示例5：使用系统消息
llm = get_llm("deepseek-chat")
if llm:
    response = llm.invoke([
        SystemMessage(content="You are a helpful assistant"),
        HumanMessage(content="What is Python?")
    ])
    print(response.content)

# 示例6：JSON格式输出
llm = get_llm("deepseek-chat", temperature=0.3)
if llm:
    llm_with_json = llm.bind(response_format={"type": "json_object"})
    response = llm_with_json.invoke([
        SystemMessage(content="You are a helpful assistant"),
        HumanMessage(content="Return a JSON object with key 'status' and value 'ok'")
    ])
    import json
    result = json.loads(response.content)
    print(result)  # {"status": "ok"}

# 示例7：列出所有可用模型
all_models = list_models()
print(f"所有模型: {all_models}")

# 示例8：按供应商列出模型
deepseek_models = list_models(Provider.DEEPSEEK)
print(f"DeepSeek模型: {deepseek_models}")

qwen_models = list_models(Provider.QWEN)
print(f"Qwen模型: {qwen_models}")

# 示例9：获取模型信息
info = get_model_info("deepseek-chat")
if info:
    print(f"模型ID: {info.model_id}")
    print(f"供应商: {info.provider.value}")
    print(f"Base URL: {info.base_url}")
    print(f"默认温度: {info.temperature}")

# 示例10：检查模型可用性
from autoy.llm import is_model_available

available = is_model_available("deepseek-chat")
print(f"deepseek-chat 可用: {available}")

# 示例11：获取推荐模型
from autoy.llm import get_recommended_model

recommended = get_recommended_model("coldstart")
print(f"coldstart任务推荐模型: {recommended}")
