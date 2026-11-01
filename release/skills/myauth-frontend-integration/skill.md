---
name: myauth-frontend-integration
description: My-Auth 前端集成指南。当需要将 my-auth 认证框架集成到 Next.js 前端项目时使用此 skill。包括 UI/UX 设计指导、AuthContext 配置、API 适配、登录注册页面、个人资料页面等完整实现。必须配合 ui-ux-pro-max skill 使用进行页面设计。
---

# My-Auth 前端集成

## 设计风格定位

**产品类型**: SaaS 内部工具 / 技能市场
**风格关键词**: 专业、简洁、现代、企业级
**行业**: 企业内部工具 / 技能交易平台

---

## Step 1: UI/UX 设计准备

使用 `ui-ux-pro-max` skill 获取设计指导：

```bash
# 搜索产品设计风格
python3 "${CLAUDE_SKILL_DIR}/scripts/search.py" "saas dashboard" --domain product

# 搜索配色方案
python3 "${CLAUDE_SKILL_DIR}/scripts/search.py" "professional enterprise" --domain color

# 搜索字体
python3 "${CLAUDE_SKILL_DIR}/scripts/search.py" "modern clean" --domain typography
```

**本项目设计特点**（参考 skill market 现有设计）：
- 主色调: Slate (石板灰) + 品牌蓝
- 卡片式布局，带 subtle 阴影
- 渐变背景: `bg-gradient-to-b from-slate-50 to-slate-100`
- 圆角: `rounded-lg` / `rounded-xl`
- 间距: `max-w-md` (登录) / `max-w-4xl` (个人中心)
- 过渡: `transition-colors duration-200`

---

## Step 2: 前置依赖

```bash
npm install axios js-cookie
npm install lucide-react  # 图标库
```

**已使用的 shadcn/ui 组件**：
- Button, Card, Input, Label
- Tabs, TabsList, TabsTrigger, TabsContent
- DropdownMenu

---

## Step 3: 环境配置

`.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## Step 4: API 适配 (lib/api.ts)

### 关键点
- my-auth 后端路由前缀为 `/api/auth`，不是 `/auth`
- 钉钉登录 URL 字段: `auth_url` (不是 `url`)
- 钉钉回调参数: 兼容 `code` 和 `authCode`

```typescript
// lib/api.ts

const AUTH_BASE_URL = process.env.NEXT_PUBLIC_API_URL?.replace('/api/v1', '') || 'http://localhost:8000';

const authAxios = axios.create({
  // 加上 /api 前缀，后端路由为 /api/auth/*
  baseURL: AUTH_BASE_URL + '/api',
  headers: { 'Content-Type': 'application/json' },
});

// 请求拦截 - 添加 Token
authAxios.interceptors.request.use((config) => {
  const token = Cookies.get('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// 响应拦截 - 401 跳转登录
authAxios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      Cookies.remove('access_token');
      window.location.href = '/auth/login';
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  login: (email: string, password: string) =>
    authAxios.post('/auth/login', { email, password }),

  register: (data: { email: string; password: string; name: string }) =>
    authAxios.post('/auth/register', data),

  getMe: () => authAxios.get('/auth/me'),
  logout: () => authAxios.post('/auth/logout'),

  // 钉钉 - URL 字段是 auth_url
  getDingTalkUrl: () => authAxios.get('/auth/dingtalk/url'),
  // 钉钉 - 字段是 auth_code
  dingtalkCallback: (code: string, state: string) =>
    authAxios.post('/auth/dingtalk/callback', { auth_code: code, state }),
};
```

---

## Step 5: AuthContext (contexts/AuthContext.tsx)

```typescript
'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { authApi } from '@/lib/api';
import Cookies from 'js-cookie';

interface User {
  id: string;
  email: string;
  name: string;
  roles?: string[];
  avatar?: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  loginWithPassword: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = async () => {
    try {
      const token = Cookies.get('access_token');
      if (!token) { setUser(null); return; }
      const response = await authApi.getMe();
      setUser(response.data);
    } catch { Cookies.remove('access_token'); setUser(null); }
  };

  const login = async (email: string, password: string) => {
    const response = await authApi.login(email, password);
    Cookies.set('access_token', response.data.access_token, { expires: 1 / 24 });
    await refreshUser();
  };

  const logout = async () => {
    try { await authApi.logout(); }
    finally { Cookies.remove('access_token'); setUser(null); }
  };

  useEffect(() => { refreshUser().finally(() => setIsLoading(false)); }, []);

  return (
    <AuthContext.Provider value={{
      user, isLoading, isAuthenticated: !!user,
      login, loginWithPassword: login, logout, refreshUser
    }}>{children}</AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
```

---

## Step 6: 页面设计规范

### 登录页面 (app/auth/login/page.tsx)

**布局**: 垂直居中，单卡片居中
**结构**:
```
┌─────────────────────────────┐
│  [Logo] Skill Market        │  ← 居中 logo + 标题
│  开始探索技能市场             │  ← 副标题
├─────────────────────────────┤
│  [密码登录] [钉钉登录]       │  ← Tabs
├─────────────────────────────┤
│  邮箱 input                  │
│  密码 input                  │
│  [登录按钮]                  │
├─────────────────────────────┤
│  还没有账号？注册            │  ← 链接
└─────────────────────────────┘
```

**设计要点**:
- 背景: `bg-gradient-to-b from-slate-50 to-slate-100`
- 卡片: `max-w-md w-full rounded-lg border bg-card shadow-sm`
- 按钮: `w-full` 填充按钮
- 输入框: 使用 shadcn/ui Input 组件

### 注册页面 (app/auth/register/page.tsx)

结构同登录，添加 name 字段

### 钉钉回调页面

**两个文件**:
1. `/app/auth/dingtalk/callback/page.tsx` - 接收钉钉重定向
2. `/app/auth/callback/page.tsx` - 处理登录逻辑

**设计**: 最小化 - 只有加载动画
```tsx
<div className="min-h-screen flex items-center justify-center">
  <Loader2 className="w-8 h-8 animate-spin" />
  <p>正在登录，请稍候...</p>
</div>
```

### 个人资料页面 (app/profile/page.tsx)

**布局**: 左右分栏
```
┌──────────┬────────────────────────────┐
│          │  个人中心标题              │
│  [头像]   ├────────────────────────────┤
│  用户名   │  [基本信息] [账号安全]     │
│  邮箱    │  ┌──────────────────────┐  │
│          │  │ 用户名: xxx           │  │
│  [菜单]   │  │ 邮箱: xxx@xxx.com    │  │
│  基本信息 │  │ 角色: admin          │  │
│  账号安全 │  └──────────────────────┘  │
└──────────┴────────────────────────────┘
```

**设计要点**:
- 左侧: 用户信息 + 导航菜单
- 右侧: Tab 切换内容区域
- 信息卡片: `p-4 bg-slate-50 rounded-lg`

---

## Step 7: 类型定义 (types/api.ts)

```typescript
export interface User {
  id: string;
  email: string;
  name: string;
  roles: string[];
  department?: string;
  is_active: boolean;
  avatar?: string;
}
```

---

## 重要提示

1. **API 端点**: `/api/auth/*` (后端路由前缀为 `/api/auth`)
2. **钉钉 URL**: 字段名 `auth_url`，不是 `url`
3. **钉钉回调**: 参数可能是 `code` 或 `authCode`，需兼容
4. **Token 存储**: js-cookie，过期时间 1 天
5. **UI 组件**: 优先使用 shadcn/ui，保持设计一致性
6. **图标**: 使用 lucide-react (如 User, Mail, Shield, Loader2)
7. **样式**: 保持与 skill market 现有设计一致
