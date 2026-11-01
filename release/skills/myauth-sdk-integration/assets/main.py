#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
My-Auth SDK 集成模板

使用方法：
1. 复制此文件到你的项目
2. 修改配置（JWT_SECRET 等）
3. 运行：uv run python main.py

首次运行会自动创建 SQLite 数据库和管理员账户
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

# 导入 myauth
from myauth import AuthFramework, init_config, CurrentUser, User


# ========== 配置 ==========

# 方式1: 从 config.toml 加载配置
# settings = init_config("config.toml")

# 方式2: 直接配置（推荐用于快速开始）
class Settings:
    # JWT 配置（必填，至少32字符）
    jwt_secret = "your-secret-key-change-in-production-min-32-chars"

    # 数据库配置（可选，默认 SQLite）
    database_url = "sqlite:///myauth.db"

    # 管理员账户（可选）
    admin_email = "admin@example.com"
    admin_password = "admin123"

    # Redis（可选，用于 Token 黑名单）
    redis_url = None


settings = Settings()


# ========== 初始化 AuthFramework（模块级别）==========

auth = AuthFramework(
    db_url=settings.database_url,
    secret=settings.jwt_secret,
    admin_email=settings.admin_email,
    admin_password=settings.admin_password,
    redis_url=settings.redis_url,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    await auth.init(app)

    # 保存到 app 状态，供路由使用
    app.state.auth = auth

    print(f"✅ MyAuth 初始化完成")
    print(f"   数据库: {settings.database_url}")
    print(f"   管理员: {settings.admin_email}")

    yield

    # 关闭时清理
    await auth.close()


# ========== 创建应用 ==========

app = FastAPI(
    title="My API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== 依赖获取 ==========

def get_auth():
    return app.state.auth


# ========== 路由示例 ==========

@app.get("/")
async def root():
    return {"message": "欢迎使用", "docs": "/docs"}


@app.get("/public")
async def public():
    """公开接口，无需登录"""
    return {"message": "这是公开接口"}


@app.get("/profile")
async def profile(user: User = CurrentUser):
    """需要登录"""
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "roles": user.roles
    }


@app.get("/admin/users")
async def list_users(auth=Depends(get_auth), user: User = CurrentUser):
    """需要 admin 角色"""
    if "admin" not in user.roles:
        from fastapi import HTTPException
        raise HTTPException(403, "需要 admin 角色")

    users = await auth.identity.list_all_users()
    return {"users": users}


@app.get("/finance/report/{report_id}")
async def get_report(
    report_id: str,
    auth=Depends(get_auth),
    user: User = CurrentUser
):
    """需要 finance 角色"""
    from fastapi import HTTPException

    # 使用依赖检查
    if "finance" not in user.roles and "admin" not in user.roles:
        raise HTTPException(403, "需要 finance 角色")

    return {"report_id": report_id, "content": "财务报告内容"}


# ========== 回调示例 ==========

@auth.on_register
def on_register(user: User):
    """用户注册后触发"""
    print(f"📝 新用户注册: {user.email} ({user.name})")


@auth.on_login
async def on_login(user: User):
    """用户登录后触发"""
    print(f"🔐 用户登录: {user.email}")


# ========== 启动 ==========

if __name__ == "__main__":
    import uvicorn

    print("""
    🚀 启动服务

    访问以下地址：
    - API: http://localhost:8000
    - 文档: http://localhost:8000/docs

    默认管理员：
    - 邮箱: admin@example.com
    - 密码: admin123
    """)

    uvicorn.run(app, host="0.0.0.0", port=8000)
