#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一启动脚本 - 同时启动 LangGraph 和 FastAPI

Usage:
    python start_unified.py

This script starts both services concurrently:
- LangGraph dev server on port 2024
- FastAPI server on port 8000
"""
import asyncio
import sys

async def start_langgraph():
    """启动 LangGraph dev server (端口 2024)"""
    from langgraph.cli.api import start

    print("🚀 启动 LangGraph dev server...")
    try:
        await start(
            host="127.0.0.1",
            port=2024,
            grpc=False
        )
    except KeyboardInterrupt:
        print("\n⏹️  LangGraph 已停止")

async def start_fastapi():
    """启动 FastAPI (端口 8000)"""
    import uvicorn

    # 创建 FastAPI 应用
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(title="Agent API")

    # CORS 配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def root():
        return {"message": "Agent API is running", "services": {"langgraph": "http://localhost:2024", "fastapi": "http://localhost:8000"}}

    @app.get("/health")
    async def health():
        return {"status": "ok", "langgraph": "running", "fastapi": "running"}

    # TODO: 添加你的业务路由
    # @app.post("/api/your-endpoint")
    # async def your_handler(data: dict):
    #     return {"result": "success"}

    print("🚀 启动 FastAPI server...")
    try:
        config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=8000,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
    except KeyboardInterrupt:
        print("\n⏹️  FastAPI 已停止")

async def main():
    """同时启动两个服务"""
    print("=" * 60)
    print("🎯 Agent 应用统一启动")
    print("=" * 60)
    print(f"📍 LangGraph: http://localhost:2024")
    print(f"📍 FastAPI:   http://localhost:8000")
    print(f"📍 前端:     http://localhost:3000")
    print("=" * 60)
    print()

    langgraph_task = asyncio.create_task(start_langgraph())
    fastapi_task = asyncio.create_task(start_fastapi())

    await asyncio.gather(langgraph_task, fastapi_task)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 所有服务已停止")
        sys.exit(0)
