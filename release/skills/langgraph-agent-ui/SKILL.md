---
name: langgraph-agent-ui
description: Full-stack LangGraph Agent application template with integrated Agent Chat UI frontend. Use when building AI agent applications that require: (1) LangGraph backend with autonomous agent orchestration, (2) Next.js frontend with chat interface, (3) Real-time streaming responses, (4) File upload and data processing capabilities, (5) FastAPI business logic integration. Perfect for data analysis agents, query assistants, workflow automation, and any conversational AI application needing custom UI.
---

# LangGraph + Agent Chat UI Integration

## Overview

Rapidly scaffold full-stack AI agent applications combining LangGraph backend orchestration with Agent Chat UI frontend. Includes pre-configured project structure, unified server startup, and extension patterns for both chat interface and custom business pages.

## Quick Start

Use this skill when user requests:
- "搭建一个 LangGraph agent 应用"
- "创建带聊天界面的 AI agent 项目"
- "Integrate LangGraph with Next.js"
- "Build full-stack agent application"

## Project Structure

```
your-agent-app/
├── backend/
│   ├── langgraph.json          # LangGraph configuration
│   ├── start_unified.py        # Unified startup script
│   ├── pyproject.toml          # Python dependencies
│   └── src/
│       └── agents/
│           └── your_agent/     # Agent definitions
│               ├── graph.py    # Agent workflow
│               ├── tools.py    # Agent tools
│               └── state.py    # Agent state
│
└── frontend/                   # Agent Chat UI extension
    ├── .env.local
    ├── package.json
    └── src/
        ├── app/
        │   ├── page.tsx        # Original chat UI
        │   └── custom/         # Custom pages
        └── lib/
            └── api.ts          # API clients
```

## Port Allocation

| Service | Port | Purpose |
|---------|------|---------|
| Agent Chat UI | 3000 | Frontend Next.js app |
| FastAPI | 8000 | Business logic, file ops, API gateway |
| LangGraph | 2024 | Agent execution, state management |

## Step 1: Initialize Backend

Create backend structure with LangGraph agent:

**1.1 Create `backend/pyproject.toml`:**

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

**1.2 Create `backend/langgraph.json`:**

```json
{
  "dependencies": ["."],
  "graphs": {
    "your_agent": "src/agents/your_agent/graph.py:graph"
  },
  "env": ".env"
}
```

**1.3 Define Agent in `backend/src/agents/your_agent/`:**

- **`state.py`** - Define agent state extending MessagesState
- **`tools.py`** - Define @tool-decorated functions
- **`graph.py`** - Build StateGraph with create_react_agent or custom workflow

See [references/agent-patterns.md](references/agent-patterns.md) for complete examples.

**1.4 Create unified startup `backend/start_unified.py`:**

```python
import asyncio
from langgraph.cli.api import start
import uvicorn

async def main():
    langgraph_task = asyncio.create_task(start(host="127.0.0.1", port=2024, grpc=False))
    fastapi_task = asyncio.create_task(start_fastapi(host="127.0.0.1", port=8000))
    await asyncio.gather(langgraph_task, fastapi_task)
```

Complete template in [assets/backend/start_unified.py](assets/backend/start_unified.py).

**1.5 Install and run:**

```bash
cd backend
uv sync
uv run python start_unified.py
```

## Step 2: Initialize Frontend

**2.1 Get Agent Chat UI base:**

Clone or copy Agent Chat UI template. For new projects, initialize from existing installation.

**2.2 Configure environment in `frontend/.env.local`:**

```env
# LangGraph
NEXT_PUBLIC_API_URL=http://localhost:2024
NEXT_PUBLIC_ASSISTANT_ID=your_agent

# FastAPI
NEXT_PUBLIC_FASTAPI_URL=http://localhost:8000
```

**2.3 Extension options:**

**Option A: Use original Thread component**
- Keep `/src/app/page.tsx` with `<Thread />` component
- Minimal changes, full chat features
- Best for: Chat-first applications

**Option B: Custom UI with useStream hook**
- Create custom pages in `/src/app/*/page.tsx`
- Use `useStream` from `@langchain/langgraph-sdk/react`
- Best for: Business-specific interfaces

See [references/frontend-patterns.md](references/frontend-patterns.md) for code examples.

**2.4 Install and run:**

```bash
cd frontend
pnpm install
pnpm dev
```

Access at http://localhost:3000

## Step 3: Integrate Agents

**3.1 Backend - Define agent tools:**

```python
from langchain_core.tools import tool

@tool
def your_tool(param: str) -> str:
    """Tool description that agent sees."""
    # Implementation
    return result
```

**3.2 Frontend - Connect to agent:**

```typescript
import { useStream } from "@langchain/langgraph-sdk/react";

const { submitMessage, messages } = useStream({
  apiUrl: process.env.NEXT_PUBLIC_API_URL,
  assistantId: process.env.NEXT_PUBLIC_ASSISTANT_ID,
});

submitMessage({ content: "User input" });
```

**3.3 FastAPI - Add business endpoints (optional):**

```python
@app.post("/api/custom-endpoint")
async def custom_handler(data: dict):
    # Business logic
    return {"result": "success"}
```

Frontend calls via: `fetch('${FASTAPI_URL}/api/custom-endpoint', ...)`

## Resources

### references/

- **`agent-patterns.md`** - Complete agent implementation examples (demo_agent with tools)
- **`frontend-patterns.md`** - Frontend extension patterns (Thread vs useStream)
- **`integration-guide.md`** - Comprehensive integration walkthrough

### assets/

- **`backend/`** - Template files: start_unified.py, pyproject.toml, langgraph.json
- **`frontend/`** - Configuration templates: .env.local, api-client.ts

### scripts/

- **`init_project.py`** - Automated project scaffolding script

## Common Patterns

### Switching Between Agents

```typescript
// Dynamic agent selection
const { submitMessage } = useStream({
  assistantId: userSelectedAgent, // "agent_a" or "agent_b"
});
```

### Adding Multiple Agents

1. Create agent directories in `backend/src/agents/`
2. Add entries to `langgraph.json` graphs section
3. Restart backend
4. Frontend switches via assistantId parameter

### Custom Business Pages

1. Create `frontend/src/app/your-page/page.tsx`
2. Use useStream for agent integration
3. Use fetch for FastAPI business endpoints
4. Keep `/page.tsx` for original chat interface

## Troubleshooting

**Backend won't start:**
- Check port 2024 and 8000 availability
- Verify .env has required API keys
- Run `langgraph dev` separately to debug

**Frontend can't connect:**
- Verify NEXT_PUBLIC_API_URL matches backend port 2024
- Check CORS settings in FastAPI
- Browser console for connection errors

**Agent not responding:**
- Verify assistantId matches langgraph.json graph name
- Check LangGraph Studio at http://localhost:2024
- Review agent logs for errors
