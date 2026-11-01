# Agent Implementation Patterns

Complete examples for defining LangGraph agents with different patterns.

## Simple ReAct Agent

The simplest pattern using `create_react_agent`:

### State Definition (`state.py`)

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import TypedDict
from langgraph.graph import MessagesState

class SimpleState(MessagesState):
    """Agent state - extends MessagesState for chat history"""
    pass  # MessagesState provides: messages: list[AnyMessage]
```

### Tools Definition (`tools.py`)

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from langchain_core.tools import tool
import time

@tool
def greet_user(name: str) -> str:
    """向用户打招呼

    Args:
        name: 用户名字
    """
    return f"你好，{name}！很高兴见到你。"

@tool
def get_current_time() -> str:
    """获取当前时间"""
    return f"当前时间是：{time.strftime('%Y-%m-%d %H:%M:%S')}"

@tool
def calculate(expression: str) -> str:
    """计算简单的数学表达式

    Args:
        expression: 数学表达式，如 "2+3" 或 "10*5"
    """
    try:
        result = eval(expression)
        return f"{expression} = {result}"
    except:
        return f"无法计算表达式：{expression}"
```

### Graph Definition (`graph.py`)

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from .tools import greet_user, get_current_time, calculate

# Initialize LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7
)

# Define tools
tools = [greet_user, get_current_time, calculate]

# Build graph using prebuilt React agent
graph = create_react_agent(llm, tools)
```

## Custom Workflow Agent

For more control, build custom workflow with StateGraph:

### State Definition (`state.py`)

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import TypedDict, Annotated
from langgraph.graph import MessagesState
from operator import add

class CustomState(MessagesState):
    """Custom agent state with additional fields"""
    user_input: str
    result: str
    step_count: Annotated[int, add]  # Reducer for counter
```

### Graph Definition (`graph.py`)

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, SystemMessage

from .state import CustomState
from .tools import your_tools

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

# Tool node
tool_node = ToolNode(your_tools)

# Agent node
def call_model(state: CustomState):
    """Call LLM with tools"""
    messages = state["messages"]
    response = llm.bind_tools(your_tools).invoke(messages)
    return {"messages": [response]}

# Routing logic
def should_continue(state: CustomState):
    """Decide whether to call tools or end"""
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END

# Build graph
workflow = StateGraph(CustomState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")

# Compile
graph = workflow.compile()
```

## Agent with System Prompt

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate

# Define system prompt
SYSTEM_PROMPT = """你是一个专业的数据分析助手。
你的职责是帮助用户分析数据、生成报告和提供洞察。

可用的工具：
- greet_user: 向用户打招呼
- get_current_time: 获取当前时间
- calculate: 计算数学表达式

使用工具时，请确保：
1. 工具参数正确
2. 解释工具返回的结果
3. 用友好的语言与用户交流
"""

# Create prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("placeholder", "{messages}"),
])

# Bind prompt to LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
llm_with_prompt = prompt | llm

# Create agent
graph = create_react_agent(llm_with_prompt, tools)
```

## Multi-Agent Workflow

For complex tasks requiring multiple specialized agents:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

# Define shared state
class MultiAgentState(MessagesState):
    current_agent: str
    research_data: str
    analysis_result: str

# Research agent
def research_agent(state: MultiAgentState):
    # Research logic
    return {"research_data": "...", "current_agent": "analyzer"}

# Analysis agent
def analysis_agent(state: MultiAgentState):
    # Analysis logic using research_data
    return {"analysis_result": "...", "current_agent": "reporter"}

# Router
def route_agent(state: MultiAgentState):
    if state["current_agent"] == "researcher":
        return "analysis"
    elif state["current_agent"] == "analyzer":
        return END
    return "research"

# Build multi-agent graph
workflow = StateGraph(MultiAgentState)
workflow.add_node("researcher", research_agent)
workflow.add_node("analyzer", analysis_agent)
workflow.add_conditional_edges("researcher", route_agent)
workflow.add_edge("analyzer", END)
workflow.set_entry_point("researcher")

graph = workflow.compile()
```

## Tool Best Practices

### Input Validation

```python
from pydantic import BaseModel, Field

class CalculateInput(BaseModel):
    expression: str = Field(
        ...,
        description="数学表达式，如 '2+3' 或 '10*5'"
    )

@tool("calculate", args_schema=CalculateInput)
def calculate(expression: str) -> str:
    """安全计算数学表达式"""
    try:
        # Only allow safe characters
        if not all(c in "0123456789+-*/(). " for c in expression):
            return "表达式包含非法字符"
        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"
```

### Error Handling

```python
@tool
def robust_tool(input_data: str) -> str:
    """带有完善错误处理的工具"""
    try:
        # 主逻辑
        result = process(input_data)
        return f"成功: {result}"
    except ValueError as e:
        return f"输入错误: {str(e)}"
    except Exception as e:
        return f"处理失败: {str(e)}"
```

### Async Tools

```python
@tool
async def async_tool(input_data: str) -> str:
    """异步工具，用于 IO 密集型操作"""
    import aiohttp

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.text()
            return data
```

## Common Agent Patterns Reference

| Pattern | Use Case | Complexity |
|---------|----------|------------|
| `create_react_agent` | Simple tool-using agents | Low |
| Custom StateGraph | Complex workflows, custom logic | Medium |
| Multi-agent | Specialized agents collaborating | High |
| Checkpointer | Long-running, stateful conversations | Medium |

## Testing Agents

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
async def test_agent():
    """Test agent with sample inputs"""
    from .graph import graph

    inputs = {
        "messages": [
            ("user", "你好，我是小明")
        ]
    }

    async for chunk in graph.astream(inputs):
        print(chunk)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_agent())
```
