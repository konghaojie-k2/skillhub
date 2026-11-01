# LangGraph + Agent Chat UI Integration Guide

Complete walkthrough for integrating LangGraph backend with Agent Chat UI frontend.

## Architecture Overview

```
┌────────────────────────────────────────────────┐
│  Agent Chat UI (Port 3000)                     │
│  - ✅ Original chat interface (Thread)         │
│  - 🚀 Custom business pages (useStream)        │
│  - 📡 LangGraph SDK integration                │
└───────────────┬────────────────────────────────┘
                │
        ┌───────┴────────┐
        │                │
        ▼                ▼
┌──────────────┐  ┌─────────────┐
│  FastAPI     │  │  LangGraph  │
│  Port 8000   │  │  Port 2024  │
│  Business    │  │  Agent      │
│  Logic       │  │  Execution  │
└──────────────┘  └─────────────┘
```

## Port Allocation

| Service | Port | Purpose |
|---------|------|---------|
| Agent Chat UI | 3000 | Next.js frontend |
| FastAPI | 8000 | Business API, file operations |
| LangGraph | 2024 | Agent execution, state management |

## Complete Setup Steps

### Step 1: Backend Setup

**1.1 Create project structure:**

```bash
mkdir your-agent-app
cd your-agent-app
mkdir backend
cd backend
```

**1.2 Create `pyproject.toml`:**

```toml
[project]
name = "your-agent-app"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "langgraph",
    "langchain",
    "langchain-openai",
    "langchain-core",
    "fastapi",
    "uvicorn[standard]",
    "python-multipart",
    "pydantic",
    "python-dotenv",
]

[tool.uv]
dev-dependencies = []

[[tool.uv.index]]
name = "tsinghua"
url = "https://pypi.tuna.tsinghua.edu.cn/simple"
default = true
```

**1.3 Create `.env`:**

```bash
# Required
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1/

# Or for DeepSeek
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1/
```

**1.4 Create `langgraph.json`:**

```json
{
  "dependencies": ["."],
  "graphs": {
    "demo_agent": "src/agents/demo_agent/graph.py:graph"
  },
  "env": ".env"
}
```

**1.5 Create agent structure:**

```bash
mkdir -p src/agents/demo_agent
```

Create `src/agents/demo_agent/state.py`:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from langgraph.graph import MessagesState

class DemoState(MessagesState):
    """Demo agent state"""
    pass
```

Create `src/agents/demo_agent/tools.py`:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from langchain_core.tools import tool
import time

@tool
def greet_user(name: str) -> str:
    """向用户打招呼"""
    return f"你好，{name}！很高兴见到你。"

@tool
def get_current_time() -> str:
    """获取当前时间"""
    return f"当前时间是：{time.strftime('%Y-%m-%d %H:%M:%S')}"

@tool
def calculate(expression: str) -> str:
    """计算数学表达式"""
    try:
        result = eval(expression)
        return f"{expression} = {result}"
    except:
        return f"无法计算：{expression}"
```

Create `src/agents/demo_agent/graph.py`:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from .tools import greet_user, get_current_time, calculate

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
tools = [greet_user, get_current_time, calculate]
graph = create_react_agent(llm, tools)
```

**1.6 Create `start_unified.py`:**

See template in `assets/backend/start_unified.py`

**1.7 Install and run:**

```bash
cd backend
uv sync
uv run python start_unified.py
```

### Step 2: Frontend Setup

**2.1 Get Agent Chat UI:**

Clone from GitHub or copy from existing installation:

```bash
cd ..
git clone https://github.com/langchain-ai/agent-chat-ui frontend
# OR copy existing agent-chat-ui directory
```

**2.2 Configure environment:**

Create `frontend/.env.local`:

```env
# LangGraph
NEXT_PUBLIC_API_URL=http://localhost:2024
NEXT_PUBLIC_ASSISTANT_ID=demo_agent

# FastAPI
NEXT_PUBLIC_FASTAPI_URL=http://localhost:8000
```

**2.3 Option A - Use original chat (minimal):**

No changes needed! `frontend/src/app/page.tsx` already has `<Thread />` component.

**2.4 Option B - Add custom page:**

Create `frontend/src/app/demo/page.tsx`:

```typescript
"use client";

import { useState } from "react";
import { useStream } from "@langchain/langgraph-sdk/react";

export default function DemoPage() {
  const [input, setInput] = useState("");

  const { submitMessage, messages } = useStream({
    apiUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:2024",
    assistantId: process.env.NEXT_PUBLIC_ASSISTANT_ID || "demo_agent",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    submitMessage({ content: input });
    setInput("");
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Agent Demo</h1>

        <div className="bg-white rounded-lg shadow p-6 mb-6 max-h-96 overflow-y-auto">
          {messages.map((msg, i) => (
            <div key={i} className={`mb-4 ${msg.role === "user" ? "text-right" : "text-left"}`}>
              <div className={`inline-block px-4 py-2 rounded-lg ${
                msg.role === "user" ? "bg-blue-600 text-white" : "bg-gray-100"
              }`}>
                {typeof msg.content === "string" ? msg.content : JSON.stringify(msg.content)}
              </div>
            </div>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="输入消息..."
            className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button type="submit" className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            发送
          </button>
        </form>
      </div>
    </div>
  );
}
```

**2.5 Install and run:**

```bash
cd frontend
pnpm install
pnpm dev
```

Access at http://localhost:3000

### Step 3: Test Integration

**3.1 Check services:**

- LangGraph Studio: http://localhost:2024
- FastAPI Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

**3.2 Test agent:**

Navigate to http://localhost:3000/demo and try:
- "你好，我是小明" → Calls greet_user
- "现在几点了？" → Calls get_current_time
- "2+3 等于多少？" → Calls calculate

**3.3 Check streaming:**

Messages should appear in real-time as agent thinks and responds.

## Adding FastAPI Business Endpoints

In `start_unified.py` or separate FastAPI app:

```python
from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/upload")
async def upload_file(file: UploadFile):
    # Business logic
    return {"filename": file.filename, "status": "uploaded"}

@app.get("/api/data")
async def get_data():
    # Business logic
    return {"data": [...]}
```

Frontend calls:

```typescript
const response = await fetch('http://localhost:8000/api/upload', {
  method: 'POST',
  body: formData,
});
```

## Switching Agents

### Backend: Add multiple agents to `langgraph.json`:

```json
{
  "dependencies": ["."],
  "graphs": {
    "agent_a": "src/agents/agent_a/graph.py:graph",
    "agent_b": "src/agents/agent_b/graph.py:graph",
    "agent_c": "src/agents/agent_c/graph.py:graph"
  },
  "env": ".env"
}
```

### Frontend: Switch via assistantId:

```typescript
// Static (environment variable)
NEXT_PUBLIC_ASSISTANT_ID=agent_b

// Dynamic (state)
const [agentId, setAgentId] = useState("agent_a");
const { submitMessage } = useStream({ assistantId: agentId });

// User selection
<select value={agentId} onChange={(e) => setAgentId(e.target.value)}>
  <option value="agent_a">Agent A</option>
  <option value="agent_b">Agent B</option>
</select>
```

## Troubleshooting

### Backend Issues

**Port already in use:**
```bash
# Find and kill process
netstat -ano | findstr :2024
taskkill /PID <PID> /F
```

**Agent not found:**
- Check graph name in `langgraph.json` matches assistantId
- Restart backend after adding new agents

**LLM errors:**
- Verify API keys in `.env`
- Check `OPENAI_BASE_URL` if using non-OpenAI provider

### Frontend Issues

**Can't connect to agent:**
- Verify `NEXT_PUBLIC_API_URL` matches backend port 2024
- Check browser console for CORS errors
- Ensure backend is running

**Messages not streaming:**
- Check LangGraph dev server is running (not just FastAPI)
- Verify SSE/EventSource support in browser

**Environment variables not working:**
- Restart dev server after changing `.env.local`
- Check variable name format (NEXT_PUBLIC_* required)

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Assistant not found" | Wrong assistantId | Match langgraph.json graph name |
| "ECONNREFUSED" | Backend not running | Start backend services |
| CORS error | Missing CORS config | Add CORS middleware to FastAPI |
| "Module not found" | Missing dependencies | Run `uv sync` or `pnpm install` |

## Best Practices

1. **Use uv for Python** - Fast package management with mirror support
2. **Use pnpm for Node** - Faster installs, better disk space
3. **Keep agents simple** - Start with `create_react_agent`, customize later
4. **Implement proper error handling** - Try/except in tools, error boundaries in React
5. **Use TypeScript** - Type safety prevents many bugs
6. **Implement retry logic** - Network calls can fail
7. **Add logging** - Use loguru for backend, console.log for frontend
8. **Test incrementally** - Test each agent, each endpoint before moving on
9. **Use environment variables** - Never hardcode URLs or keys
10. **Document your tools** - Tool descriptions guide agent behavior

## Next Steps

- **Custom agents**: See [agent-patterns.md](agent-patterns.md)
- **Frontend patterns**: See [frontend-patterns.md](frontend-patterns.md)
- **Production deployment**: Consider Docker, cloud hosting, authentication
- **Monitoring**: Add logging, metrics, error tracking
- **Testing**: Write tests for agents, API endpoints, and components
