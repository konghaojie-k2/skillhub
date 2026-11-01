---
name: project-init
description: |
  项目初始化工具集。用于快速初始化 Python 项目，包括：uv 项目创建、.gitignore 优化、清华镜像源配置、基础文件夹结构生成。
  触发条件：(1) 创建新 Python 项目 (2) 需要配置 uv 环境 (3) 需要生成项目基础结构 (4) 需要优化 gitignore
---

# Project Init - 项目初始化工具

## 快速开始

### 1. 初始化 uv 项目

```bash
# 创建项目目录并进入
mkdir my-project && cd my-project

# 使用 uv 初始化（交互式）
uv init

# 或使用模板
uv init --template package my-project
```

### 2. 配置镜像源

在 `pyproject.toml` 中添加：

```toml
[tool.uv]
index-url = "https://pypi.tuna.tsinghua.edu.cn/simple"

[[tool.uv.index]]
name = "tsinghua"
url = "https://pypi.tuna.tsinghua.edu.cn/simple"
explicit = true
```

或全局配置 `~/.config/uv/uv.toml`：

```toml
index-url = "https://pypi.tuna.tsinghua.edu.cn/simple"
```

### 3. 生成 .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
dist/
*.egg-info/

# Virtual Environment
.venv/
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp

# Testing
.pytest_cache/
.coverage

# Environment
.env
*.local

# Database
*.db
*.sqlite

# Logs
*.log

# OS
.DS_Store
Thumbs.db
```

### 4. 基础文件夹结构

#### 单模块 Python 项目
```
project/
├── src/               # 源代码
│   └── __init__.py
├── tests/            # 测试
├── docs/             # 文档
├── scripts/          # 脚本
├── config/           # 配置
└── data/             # 数据文件
```

#### 前后端分离项目（推荐）
```
project/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── api/routes/     # API 路由
│   │   ├── core/           # 核心模块 (config, database, security)
│   │   ├── models/         # SQLAlchemy 模型
│   │   ├── schemas/        # Pydantic 验证模型
│   │   └── services/       # 业务逻辑
│   ├── alembic/            # 数据库迁移
│   ├── scripts/            # 脚本
│   ├── tests/              # 测试
│   ├── pyproject.toml      # uv 项目配置
│   └── .env                # 环境变量
│
├── frontend/               # Next.js 前端
│   ├── app/               # Next.js 14 App Router
│   ├── components/        # React 组件
│   ├── contexts/          # React Context
│   ├── lib/               # 工具库
│   ├── types/             # TypeScript 类型
│   ├── package.json
│   └── tailwind.config.ts
│
├── docs/                  # 项目文档
├── .gitignore
├── CLAUDE.md              # 项目说明 (Claude Code)
└── README.md
```

#### FastAPI 后端详细结构
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI 应用入口
│   ├── api/
│   │   └── routes/        # API 端点
│   │       ├── auth.py    # 认证
│   │       ├── skills.py  # 技能
│   │       └── ...
│   ├── core/
│   │   ├── config.py     # 配置
│   │   ├── database.py   # 数据库连接
│   │   ├── security.py   # 安全工具
│   │   └── ...
│   ├── models/           # SQLAlchemy 模型
│   │   ├── user.py
│   │   ├── skill.py
│   │   └── ...
│   ├── schemas/          # Pydantic 模型
│   └── services/         # 业务逻辑
│       ├── gitlab.py
│   │   ├── dingtalk.py
│   │   └── ...
│├── alembic/              # 数据库迁移
│   └── versions/
├── scripts/              # 工具脚本
├── tests/                # 测试
│   ├── unit/
│   ├── integration/
│   └── factories/        # 测试工厂
├── pyproject.toml
├── uv.lock
└── .env
```

#### Next.js 前端详细结构
```
frontend/
├── app/                   # Next.js 14 App Router
│   ├── (auth)/           # 认证路由组
│   ├── (dashboard)/     # 仪表盘路由组
│   ├── api/              # API 代理
│   ├── layout.tsx        # 根布局
│   └── page.tsx          # 首页
│
├── components/
│   ├── ui/               # shadcn/ui 组件
│   ├── forms/            # 表单组件
│   └── features/         # 功能组件
│
├── contexts/             # React Context
├── lib/                   # 工具函数
│   ├── api.ts            # API 客户端
│   ├── utils.ts
│   └── auth.ts
│
├── types/                # TypeScript 类型定义
├── hooks/                # 自定义 Hooks
├── public/               # 静态资源
├── package.json
├── tailwind.config.ts
├── tsconfig.json
└── next.config.js
```

## 常用命令

```bash
# 安装依赖
uv add <package>
uv add -d <package>  # 开发依赖

# 安装可编辑模式
uv pip install -e .

# 运行脚本
uv run python script.py

# 创建虚拟环境
uv venv
uv venv --python 3.11
```

## Windows 注意事项

- 使用正斜杠 `/` 代替反斜杠 `\`（如 `cd path/to/project`）
- 配置 Python UTF-8 编码：创建 `sitecustomize.py`

## 架构模式建议

### 数据库模型
- 使用 SQLAlchemy 2.0 风格（异步支持）
- 使用 `UUIDMixin` 和 `TimestampMixin`
- 模型使用 UUID 主键而非自增 ID

### API 设计
- RESTful 风格端点
- 使用 Pydantic 进行请求/响应验证
- 统一的错误响应格式

### 前后端通信
- 前端使用 TanStack Query 管理服务端状态
- 使用 Server Components 减少客户端 JavaScript
- API 代理避免 CORS 问题

### 服务抽象
- Queue、Cache、Ranking 等服务使用接口抽象
- 开发环境使用内存实现，生产环境可切换到 Redis
