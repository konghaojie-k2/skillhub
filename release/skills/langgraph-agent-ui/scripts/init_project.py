#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangGraph + Agent Chat UI Project Initializer

Usage:
    python init_project.py <project-name> [--path <output-directory>]

Example:
    python init_project.py my-agent-app
    python init_project.py my-agent-app --path ~/projects
"""
import sys
import os
from pathlib import Path
import shutil

# Template files content (these would normally be loaded from assets/)
PYPROJECT_TOML = """[project]
name = "PROJECT_NAME"
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
"""

LANGGRAPH_JSON = """{
  "dependencies": ["."],
  "graphs": {
    "AGENT_NAME": "src/agents/AGENT_FOLDER/graph.py:graph"
  },
  "env": ".env"
}
"""

ENV_TEMPLATE = """# LLM Configuration
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1/
"""

START_UNIFIED = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
from langgraph.cli.api import start
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

async def start_langgraph():
    print("🚀 启动 LangGraph dev server...")
    await start(host="127.0.0.1", port=2024, grpc=False)

async def start_fastapi():
    app = FastAPI(title="AGENT_TITLE API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def root():
        return {"message": "AGENT_TITLE is running"}

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    print("🚀 启动 FastAPI server...")
    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    print("=" * 60)
    print("🎯 AGENT_TITLE")
    print("=" * 60)
    print(f"📍 LangGraph: http://localhost:2024")
    print(f"📍 FastAPI:   http://localhost:8000")
    print(f"📍 前端:     http://localhost:3000")
    print("=" * 60)
    print()

    await asyncio.gather(
        asyncio.create_task(start_langgraph()),
        asyncio.create_task(start_fastapi())
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\n👋 所有服务已停止")
"""

STATE_PY = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from langgraph.graph import MessagesState

class AGENT_CLASSState(MessagesState):
    \"""AGENT_DESC agent state\"""
    pass
"""

TOOLS_PY = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from langchain_core.tools import tool

@tool
def demo_tool(param: str) -> str:
    \"""示例工具 - 描述工具功能\"""
    return f"处理结果: {param}"
"""

GRAPH_PY = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from .tools import demo_tool

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
tools = [demo_tool]
graph = create_react_agent(llm, tools)
"""

FRONTEND_ENV = """# LangGraph Configuration
NEXT_PUBLIC_API_URL=http://localhost:2024
NEXT_PUBLIC_ASSISTANT_ID=AGENT_NAME

# FastAPI Configuration
NEXT_PUBLIC_FASTAPI_URL=http://localhost:8000
"""


def create_project(project_name: str, base_path: Path = None):
    """
    Create a new LangGraph + Agent Chat UI project

    Args:
        project_name: Name of the project
        base_path: Base directory where project will be created (default: current directory)
    """
    if base_path is None:
        base_path = Path.cwd()

    project_dir = base_path / project_name

    # Check if project already exists
    if project_dir.exists():
        print(f"❌ Error: Project directory already exists: {project_dir}")
        return False

    # Agent naming
    agent_name = f"{project_name.replace('-', '_')}_agent"
    agent_folder = project_name.replace('-', '_')
    agent_class = ''.join(word.capitalize() for word in project_name.split('-'))
    agent_desc = project_name.replace('-', ' ').title()

    print(f"🚀 Creating project: {project_name}")
    print(f"   Location: {project_dir}")
    print()

    try:
        # Create backend structure
        backend_dir = project_dir / "backend"
        src_dir = backend_dir / "src"
        agents_dir = src_dir / "agents" / agent_folder

        # Create directories
        agents_dir.mkdir(parents=True)
        (project_dir / "frontend").mkdir()

        # Backend files
        (backend_dir / "pyproject.toml").write_text(
            PYPROJECT_TOML.replace("PROJECT_NAME", project_name)
        )
        (backend_dir / "langgraph.json").write_text(
            LANGGRAPH_JSON.replace("AGENT_NAME", agent_name).replace("AGENT_FOLDER", agent_folder)
        )
        (backend_dir / ".env").write_text(ENV_TEMPLATE)
        (backend_dir / "start_unified.py").write_text(
            START_UNIFIED.replace("AGENT_TITLE", agent_desc)
        )

        # Agent files
        (agents_dir / "__init__.py").write_text("")
        (agents_dir / "state.py").write_text(
            STATE_PY.replace("AGENT_CLASS", agent_class).replace("AGENT_DESC", agent_desc)
        )
        (agents_dir / "tools.py").write_text(TOOLS_PY)
        (agents_dir / "graph.py").write_text(GRAPH_PY)

        # Frontend files
        frontend_env = FRONTEND_ENV.replace("AGENT_NAME", agent_name)
        (project_dir / "frontend" / ".env.local").write_text(frontend_env)

        print("✅ Project structure created successfully!")
        print()
        print("📁 Created files:")
        print(f"   {backend_dir}/pyproject.toml")
        print(f"   {backend_dir}/langgraph.json")
        print(f"   {backend_dir}/.env")
        print(f"   {backend_dir}/start_unified.py")
        print(f"   {src_dir}/agents/{agent_folder}/state.py")
        print(f"   {src_dir}/agents/{agent_folder}/tools.py")
        print(f"   {src_dir}/agents/{agent_folder}/graph.py")
        print(f"   {project_dir}/frontend/.env.local")
        print()
        print("🎯 Next steps:")
        print(f"   1. cd {project_dir}/backend")
        print("   2. Edit .env with your API keys")
        print("   3. uv sync")
        print("   4. uv run python start_unified.py")
        print()
        print("   5. In another terminal:")
        print(f"   cd {project_dir}/frontend")
        print("   # Copy Agent Chat UI files here, or:")
        print("   git clone <agent-chat-ui-repo> .")
        print("   pnpm install")
        print("   pnpm dev")
        print()
        return True

    except Exception as e:
        print(f"❌ Error creating project: {e}")
        # Cleanup on failure
        if project_dir.exists():
            shutil.rmtree(project_dir)
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python init_project.py <project-name> [--path <output-directory>]")
        print()
        print("Example:")
        print("  python init_project.py my-agent-app")
        print("  python init_project.py my-agent-app --path ~/projects")
        sys.exit(1)

    project_name = sys.argv[1]

    # Parse optional --path argument
    base_path = None
    if len(sys.argv) >= 4 and sys.argv[2] == "--path":
        base_path = Path(sys.argv[3]).expanduser().resolve()

    # Validate project name
    if not project_name.replace('-', '').replace('_', '').isalnum():
        print("❌ Error: Project name must contain only letters, numbers, hyphens, and underscores")
        sys.exit(1)

    success = create_project(project_name, base_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
