# My-Auth SDK 详细使用指南

## 初始化参数

```python
AuthFramework(
    db_url: str,              # 数据库连接字符串
    secret: str,               # JWT 密钥（至少32字符）
    admin_email: str = None,   # 管理员邮箱
    admin_password: str = None, # 管理员密码
    dingtalk_enabled: bool = False,   # 启用钉钉登录
    dingtalk_app_key: str = None,    # 钉钉 AppKey
    dingtalk_app_secret: str = None, # 钉钉 AppSecret
    dingtalk_redirect_uri: str = None, # 回调地址
    max_agents_per_user: int = 5,     # 每个用户最大 Agent 数量
)
```

## 数据库连接

支持多种数据库：

| 数据库 | 连接字符串 |
|--------|-----------|
| SQLite | `sqlite:///myauth.db` |
| PostgreSQL | `postgresql://user:pass@localhost:5432/myauth` |

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| JWT_SECRET | 是 | JWT 签名密钥，至少32字符 |
| DATABASE_URL | 否 | 数据库连接字符串 |
| ADMIN_EMAIL | 否 | 管理员邮箱 |
| ADMIN_PASSWORD | 否 | 管理员密码 |
| REDIS_URL | 否 | Redis 连接（用于 Token 黑名单） |
| DINGTALK_ENABLED | 否 | 启用钉钉登录 |
| DINGTALK_APP_KEY | 否 | 钉钉 AppKey |
| DINGTALK_APP_SECRET | 否 | 钉钉 AppSecret |

## 权限控制

### 1. 必须登录

```python
from myauth import CurrentUser

@app.get("/profile")
async def profile(user: User = CurrentUser):
    return {"name": user.name, "email": user.email}
```

### 2. 可选登录

```python
from myauth import optional_user

@app.get("/dashboard")
async def dashboard(user=Depends(optional_user)):
    if user:
        return {"welcome": user.name}
    return {"message": "请登录"}
```

### 3. 角色检查

> ⚠️ `require_role` / `require_roles` 必须在 `auth.init(app)` 之后才能使用。

```python
# 单角色
@app.get("/admin")
async def admin(user=Depends(auth.require_role("admin"))):
    return {"admin": True}

# 多角色（满足任一即可）
@app.get("/manager")
async def manager(user=Depends(auth.require_roles(["admin", "manager"]))):
    return {"manager": True}

# 或者使用从 myauth 导入的 @require 装饰器
from myauth import require

@app.get("/hr/employees")
@require("hr:employee", "read")
async def hr_employees(request, user: User = CurrentUser):
    return {"employees": [...]}
```

### 4. 资源权限

```python
@app.get("/finance/report/{id}")
async def report(id: str, user=Depends(auth.require("finance:report", "read"))):
    return {"report_id": id}
```

## 回调事件

```python
@auth.on_register
def after_register(user):
    """用户注册后触发"""
    print(f"新用户: {user.email}")

@auth.on_login
async def after_login(user):
    """用户登录后触发"""
    print(f"用户登录: {user.email}")
```

## 角色权限

| 角色 | 权限 |
|------|------|
| admin | *:* (所有权限) |
| finance | finance:* |
| employee | 仅自己的资源 |

## Agent API Key

```python
# 创建 Agent
@app.post("/agents")
async def create_agent(data: CreateAgentRequest, user=CurrentUser):
    agent = await auth.agent.create_agent(
        owner_id=user.id,
        name=data.name,
        role=data.role,
        expires_days=30
    )
    return {"api_key": agent["api_key"]}  # 只返回一次！

# 使用 API Key 访问
@app.get("/api/data")
async def get_data(user=CurrentUser):
    # Agent 或用户都可以访问
    return {"data": "..."}
```

## 钉钉登录

```python
# 获取授权 URL
@app.get("/auth/dingtalk/url")
async def get_dingtalk_url():
    auth_url = auth.dingtalk_login.generate_auth_url()
    return {"auth_url": auth_url}

# 回调处理
@app.post("/auth/dingtalk/callback")
async def dingtalk_callback(code: str):
    tokens = await auth.dingtalk_login.login(code)
    return tokens
```
