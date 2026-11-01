---
name: api-best-practices
description: API 最佳实践指南，用于 FastAPI + Next.js 全栈项目的 API 开发、集成和调试。触发场景：(1) 创建新的 API 端点 (2) 调试 API 调用问题 (3) 集成前端与后端 (4) 配置 API 代理
---

# API 最佳实践

## 概述

本 skill 提供 FastAPI 后端与 Next.js 前端集成时的 API 开发规范和调试方法，确保前后端 API 路径统一，避免 404、CORS 等常见问题。

## 核心原则：统一 /api 前缀

**所有 API 必须带 /api 前缀**，这是前后端集成的黄金法则。

```
前端调用: /api/auth/login      →  后端路由: /api/auth/login
前端调用: /api/agents          →  后端路由: /api/agents
前端调用: /api/users           →  后端路由: /api/users
```

## 1. 路径命名规范

### 必遵守规则

| 规则 | 正确示例 | 错误示例 |
|------|----------|----------|
| 必须带 /api 前缀 | `/api/auth/login` | `/auth/login` |
| 避免重复前缀 | `/api/auth` (router 自带) | `/api/api/auth` |
| 使用复数名词 | `/api/users` | `/api/user` |
| 蛇形命名 | `/api/test-cases` | `/api/testCases` |

### 前端 API_BASE 配置

```typescript
// .env.local
NEXT_PUBLIC_API_BASE=

// 使用空字符串，通过 Next.js 代理
const API_URL = ''
fetch(`${API_URL}/api/auth/login`, ...)
```

## 2. 后端路由定义

### FastAPI 正确写法

```python
from fastapi import APIRouter

# 正确：router 自带 /api 前缀
router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login")
async def login(data: UserLogin):
    return {"access_token": "xxx", "token_type": "bearer"}

# 完整路径: POST /api/auth/login ✓
```

### 常见错误

```python
# 错误 1: router 没有 /api 前缀
router = APIRouter(prefix="/auth", tags=["auth"])
# 结果: POST /auth/login ✗

# 错误 2: 路由函数又加了 /api
@router.post("/api/login")
# 结果: POST /api/api/login ✗

# 错误 3: 与 app.include_router 重复
app.include_router(router, prefix="/api")
router = APIRouter(prefix="/api/auth")
# 结果: POST /api/api/auth ✗
```

### 检查后端路由

```bash
# 启动后端后访问 docs
http://localhost:2525/docs

# 或用 curl 查看路由
curl http://localhost:2525/openapi.json | jq '.paths'
```

## 3. 前端调用规范

### Next.js 代理配置 (next.config.js)

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:2525/api/:path*',
      },
    ]
  },
}
module.exports = nextConfig
```

### 前端调用方式

```typescript
// 方式 1: 使用空字符串 (推荐)
// 环境变量 NEXT_PUBLIC_API_BASE=
const API_URL = ''

// 方式 2: 直接使用 /api
const response = await fetch('/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
})
```

### AuthContext 示例

```typescript
// 登录
const login = async (email: string, password: string) => {
  const res = await fetch(`${API_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  })
  const data = await res.json()
  // 存储 token
  document.cookie = `access_token=${data.access_token}; path=/`
}

// 获取用户信息
const fetchProfile = async () => {
  const res = await fetch(`${API_URL}/api/auth/me`)
  return await res.json()  // 直接是 User 对象，不是 {data: User}
}
```

## 4. 调试方法

### 调试流程：后端 → 代理 → 前端

#### Step 1: 验证后端 API

```bash
# 1. 启动后端
cd my-auth && uvicorn myauth.main:app --reload --port 2525

# 2. 直接调用后端 (绕过代理)
curl -X POST http://localhost:2525/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"123456"}'

# 3. 检查返回
```

#### Step 2: 验证 Next.js 代理

```bash
# 1. 启动前端
cd frontend && npm run dev

# 2. 通过代理调用
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"123456"}'

# 3. 如果返回 404，检查 next.config.js 的 rewrites 配置
```

#### Step 3: 验证前端

```javascript
// 浏览器控制台
// 检查网络请求
fetch('/api/auth/login', ...)

// 检查是否正确转发到 http://localhost:2525/api/auth/login
```

### 快速验证命令

```bash
# 后端是否正常
curl http://localhost:2525/api/auth/me

# 代理是否工作
curl http://localhost:3000/api/auth/me

# OpenAPI 文档
http://localhost:2525/docs
```

## 5. 常见问题排查

### 问题 1: 404 Not Found

| 原因 | 排查 |
|------|------|
| 前端调用路径没有 /api | 检查前端代码: `/api/auth/login` |
| 后端 router 缺少 /api 前缀 | 检查: `APIRouter(prefix="/api/xxx")` |
| 代理配置错误 | 检查 next.config.js rewrites |
| 代理目标端口错误 | 确认后端实际端口 |

**排查命令**:
```bash
# 对比前后端路径
echo "前端调用: /api/auth/login"
curl -s http://localhost:2525/openapi.json | jq '.paths | keys'
```

### 问题 2: CORS 跨域错误

**原因**: 未配置 CORS 或使用代理时仍配置了 CORS

**解决**: 使用 Next.js 代理时，后端不必配置 CORS

```python
# 后端 (使用代理时可选配置)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
)

# 或者完全依赖 Next.js 代理，不配置 CORS
```

### 问题 3: 返回格式不一致

| 后端返回 | 前端解析 |
|----------|----------|
| `{"access_token": "xxx"}` | `data.access_token` ✓ |
| `{"data": {"access_token": "xxx"}}` | `data.data.access_token` ✗ |

**原则**: 后端直接返回数据对象，前端按需解析

```python
# 正确：直接返回
@router.post("/login")
async def login(data: UserLogin):
    return {"access_token": "xxx", "token_type": "bearer"}

# 错误：套一层 data
return {"data": {"access_token": "xxx"}}
```

### 问题 4: Cookie 未保存

```typescript
// 登录成功后设置 cookie
document.cookie = `access_token=${data.access_token}; path=/; max-age=${60*60*24}`

// 读取 cookie
const token = document.cookie.split('access_token=')[1]?.split(';')[0]
```

## 6. 快速检查清单

### 开发新 API 时

- [ ] 后端 router 使用 `/api/xxx` 前缀
- [ ] 前端调用使用 `/api/xxx` 路径
- [ ] next.config.js 包含代理配置
- [ ] 重启后端服务
- [ ] 重启前端服务

### 调试 API 时

- [ ] 后端是否正常启动？
- [ ] 直接调用后端是否成功？
- [ ] 通过代理调用是否成功？
- [ ] 路径是否一致（都有 /api）？
- [ ] 端口是否正确？

### 上线前检查

- [ ] 所有 API 都有 /api 前缀
- [ ] 无硬编码的完整 URL
- [ ] next.config.js 代理配置正确
- [ ] 生产环境 API 地址配置正确

## 7. 参考配置

### 完整项目结构示例

```
my-project/
├── backend/
│   ├── main.py
│   └── routers/
│       └── auth.py          # APIRouter(prefix="/api/auth")
├── frontend/
│   ├── next.config.js        # rewrites 代理配置
│   ├── .env.local           # NEXT_PUBLIC_API_BASE=
│   └── app/
│       └── api/
│           └── auth/
│               └── login/
│                   └── page.tsx
```

### 环境变量

```bash
# .env.local (前端)
NEXT_PUBLIC_API_BASE=

# .env (后端)
DATABASE_URL=sqlite:///./db.sqlite
SECRET_KEY=your-secret-key
```
