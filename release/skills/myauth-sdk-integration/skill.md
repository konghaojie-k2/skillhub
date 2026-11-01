---
name: myauth-sdk-integration
description: My-Auth SDK 完整集成指南。当需要将 my-auth 认证授权框架集成到新的 FastAPI 项目时使用此 skill。包括环境准备、配置步骤、数据库初始化、完整代码示例。
---

# My-Auth SDK 集成

## 前置要求

- Python 3.10+
- FastAPI 项目
- uv 包管理器

## 集成步骤

### 1. 获取并安装 SDK

**方式一：从源码安装（推荐，内网项目）**

```bash
# 克隆 SDK 仓库
git clone https://gitlab.kstonedata.k2/Konghaojie/my-auth.git /path/to/my-auth

# 在你的项目中安装
cd your-project
uv pip install -e /path/to/my-auth
```

**方式二：从包管理器安装（需先发布到私有仓库）**

```bash
uv add my-auth
```

### 2. 配置环境变量

在项目根目录创建 `.env` 文件：

```bash
# JWT 配置（必填，至少32字符）
JWT_SECRET=your-production-secret-key-min-32-characters

# 数据库配置（可选，默认 SQLite）
DATABASE_URL=sqlite:///myauth.db

# 钉钉登录配置（可选）
DINGTALK_ENABLED=true
DINGTALK_APP_KEY=your_app_key
DINGTALK_APP_SECRET=your_app_secret
DINGTALK_REDIRECT_URI=http://localhost:3000/auth/dingtalk/callback
```

### 3. 创建配置文件

在项目根目录创建 `config.toml` 文件：

```toml
[app]
name = "My API"
version = "0.1.0"
debug = false

[jwt]
access_token_expire = 30
refresh_token_expire = 1440

[database]
pool_size = 5

[cors]
origins = ["http://localhost:3000"]

# 管理员账户（可选）
admin_email = "admin@example.com"
admin_password = "admin123"
```

### 4. 集成代码

```python
# main.py
import os
from fastapi import FastAPI
from myauth import AuthFramework, init_config

app = FastAPI()

# 加载配置（优先级：环境变量 > config.toml > 默认值）
auth_config = init_config("config.toml")

# 初始化认证框架
auth = AuthFramework(
    db_url=auth_config.database_url,
    secret=auth_config.jwt_secret,
    use_sqlite=True,
    admin_email=auth_config.admin_email,
    admin_password=auth_config.admin_password,
    # 钉钉配置（可选）
    dingtalk_app_key=os.getenv("DINGTALK_APP_KEY"),
    dingtalk_app_secret=os.getenv("DINGTALK_APP_SECRET"),
    dingtalk_enabled=os.getenv("DINGTALK_ENABLED", "false").lower() == "true",
)

# 启动时初始化
@app.on_event("startup")
async def startup():
    await auth.init(app)

# 关闭时清理
@app.on_event("shutdown")
async def shutdown():
    await auth.close()
```

### 5. 使用权限控制

详细用法见 `references/usage.md`

## 配置说明

### 环境变量（敏感信息）
- `JWT_SECRET` - JWT 密钥（至少32字符）
- `DATABASE_URL` - 数据库连接 URL
- `DINGTALK_APP_KEY` - 钉钉 App Key
- `DINGTALK_APP_SECRET` - 钉钉 App Secret
- `DINGTALK_ENABLED` - 是否启用钉钉登录

### config.toml（非敏感配置）
- `jwt.access_token_expire` - 访问令牌过期时间（分钟）
- `jwt.refresh_token_expire` - 刷新令牌过期时间（分钟）
- `cors.origins` - 允许的跨域来源
- `app.name` - 应用名称
- `app.version` - 应用版本
- `app.debug` - 调试模式
- `admin_email` - 管理员邮箱
- `admin_password` - 管理员密码

## 重要提示

- 首次启动会自动创建 SQLite 数据库文件
- 首次启动会自动创建管理员账户
- 确保 `.env` 文件中的 `JWT_SECRET` 至少 32 个字符
