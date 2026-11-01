---
name: model-eval-cli
description: Model Eval CLI 集成与应用指南。用于将 model-eval 评估框架集成到机器学习项目中，包括配置 model-eval.json、创建测试用例、运行评估测试、查看反馈与可视化报告。触发场景：(1) 需要评估 ML 模型性能 (2) 集成评估框架到现有项目 (3) 创建测试用例和管理反馈 (4) 启动 Web Dashboard 查看可视化报告
---

# Model Eval CLI 集成与应用

## ⚠️ 铁律：禁止修改原始项目代码

**只允许修改 CLI 相关文件，禁止修改原始项目中的任何代码和配置文件。**

**允许修改的范围**：
- `model_eval_wrapper.py` — CLI wrapper 钩子函数
- `model-eval.json` — CLI 配置文件
- `.model-eval-viz.json` — 可视化配置（已迁移到 `.model-eval/{env}/viz.json`，按环境独立）
- `.model-eval/` — CLI 生成的数据目录
- `model-eval-cli/` 源代码 — CLI 本身的代码（如果有权限）

**禁止修改的范围**：
- 原始项目的数据处理代码（`src/weiqiao/task/task_*.py`）
- 原始项目的配置文件（`src/weiqiao/config/**/*.json`、`src/weiqiao/config/**/*.csv`）
- 原始项目的模型代码（`src/weiqiao/model/*.py`）
- 原始项目的工具函数（`src/weiqiao/util/*.py`）

**违反铁律的后果**：
- 会导致原始项目行为改变，可能引入 Bug
- 破坏 CLI 与原始项目的隔离性
- 用户需要手动 revert 被错误修改的文件

**正确做法**：
- 如果发现问题在原始项目中，应向用户报告，让用户决定是否修复
- CLI wrapper 只负责调用原始项目的函数，不应改变其行为

---

## Overview

Model Eval CLI 是一个机器学习评估工具，提供无侵入式的模型效果评估环境。通过简单的配置文件，即可将评估能力集成到现有 ML 项目中。

## 快速开始

### 前置条件：必须 Clone 项目（重要）

> **使用 Dashboard 的必要条件**：model-eval-cli 的前端代码（Next.js）存放在独立的 `model_eval_cli` 项目中，**pip 安装后无法获取前端代码**。

因此，无论是否发布到 PyPI，**必须 Clone 项目到本地**才能启动 Dashboard：

```bash
# 1. Clone 项目（获取前端代码）
git clone https://github.com/your-repo/model_eval_cli.git C:\path\to\model_eval_cli

# 2. 在寄生项目中安装（仅后端 + CLI）
cd /path/to/your-project
uv pip install -e C:\path\to\model_eval_cli
```

**关键点**：
| 组件 | 安装方式 | 是否必须 clone |
|------|----------|----------------|
| 后端 (CLI + API) | `pip install` 或 `uv pip install -e` | ❌ 不需要 |
| 前端 (Next.js Dashboard) | **必须 clone 项目到本地** | ✅ 必须 |

### 启动位置选择（重要）

**启动位置**：

```bash
# 在寄生项目根目录启动
cd /path/to/your-project
model-eval start
```

**可视化配置说明**：
- 可视化配置按环境独立存储，路径为 `.model-eval/{env}/viz.json`
- 旧版 `.model-eval-viz.json`（项目根目录）仍兼容，优先使用环境内配置
- 启动时自动加载当前环境的可视化配置

### 项目初始化与依赖管理（重要）

**如果项目还没有使用 uv 管理**（没有 pyproject.toml），必须先初始化：

```bash
# 1. 检查项目是否已有 pyproject.toml
ls pyproject.toml 2>/dev/null || echo "No pyproject.toml found"

# 2. 如果有 requirements.txt，先读取内容
cat requirements.txt

# 3. 创建 pyproject.toml（将 requirements.txt 的依赖转为 uv 格式）
# 示例 pyproject.toml:
cat > pyproject.toml << 'EOF'
[project]
name = "your-project"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "pandas",
    "scipy",
    "loguru",
    # 从 requirements.txt 复制其他依赖
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
index-url = "https://pypi.tuna.tsinghua.edu.cn/simple"
EOF

# 4. 同步依赖并生成 uv.lock
uv sync

# 5. 后续安装新包必须使用 uv add
uv add <package-name>     # 添加生产依赖
uv add --dev <package>    # 添加开发依赖
```

**为什么必须用 uv 管理**：
- `uv.lock` 保证团队环境一致
- `uv sync` 可快速同步环境
- 避免依赖缺失导致运行时错误（如 pandas 未安装）

**注意**：寄生项目不要用 `uv add` 添加 model-eval-cli，用的是 `uv pip install -e`（见下方 Step 1）。

### Step 0: 环境检查与准备（重要）

**在安装 model-eval-cli 之前，必须先检查环境**：

```bash
# 1. 确认当前目录是目标项目（寄生项目）根目录
pwd
# 应该显示如: /c/Users/17625/Documents/Gitlab/weiqiao-on-pipe

# 2. 检查 .python-version 文件（model-eval-cli 需要 Python >= 3.10）
cat .python-version
# 如果版本 < 3.10，需要修改

# 3. 检查是否存在虚拟环境
ls -la .venv 2>/dev/null || echo "No .venv found"

# 4. 检查 home 目录是否有空的 pyproject.toml（会干扰 uv 运行）
ls -la ~/pyproject.toml
# 如果文件存在且为空，删除它
rm ~/pyproject.toml
```

**Python 版本要求**：
- model-eval-cli 要求 `Python >= 3.10`
- 如果项目 `.python-version` 指定的是 3.9 或更低版本，需要修改

```bash
# 修改 .python-version 为 3.11 或更高
echo "3.11.13" > .python-version
```

### Step 1: 创建虚拟环境并安装

```bash
# 在目标项目根目录下执行：

# 1. 删除旧虚拟环境（如果存在且 Python 版本不匹配）
rm -rf .venv

# 2. 创建新虚拟环境（会自动使用 .python-version 中的版本）
uv venv .venv

# 3. 激活并安装 model-eval-cli
uv pip install -e C:\path\to\model_eval_cli

# 或使用 uv run 直接运行（不需要手动激活）
uv run model-eval --help
```

**关键检查清单**：
- [ ] 当前目录是目标项目根目录（不是 model_eval_cli 目录）
- [ ] `.python-version` 指定 Python >= 3.10
- [ ] 虚拟环境 `.venv` 存在且 Python 版本正确
- [ ] `~/pyproject.toml` 不存在或已删除
- [ ] myauth 已安装（如果使用认证功能，见下方 Step 1.5）
- [ ] 安装成功后运行 `uv run model-eval validate` 验证

### Step 1.5: 安装 myauth（认证功能必选）

**如果需要登录认证功能，必须安装 myauth**：

```bash
# 1. Clone myauth 到本地（与 model_eval_cli 同级目录）
cd C:\Users\17625\Documents\GitHub
git clone https://github.com/your-repo/my-auth.git

# 2. 在寄生项目中安装 myauth（注意 [dev] 包含 aiosqlite 等必要依赖）
cd /path/to/your-project
uv pip install -e C:\Users\17625\Documents\GitHub\my-auth[dev]

# 3. 验证安装
uv run python -c "from myauth import AuthFramework; print('OK')"
```

**为什么需要 [dev]**：
- myauth 的 `aiosqlite`（SQLite 异步支持）在 dev 依赖中
- 不加 `[dev]` 会导致认证功能无法正常工作

**配置 .env 文件**（项目根目录）：

```bash
# JWT 配置（必填，至少32字符）
JWT_SECRET=your-secret-key-at-least-32-characters

# 数据库配置（可选，默认 SQLite）
DATABASE_URL=sqlite:///myauth.db

# 管理员账户
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=admin123

# 钉钉登录配置
DINGTALK_ENABLED=true
DINGTALK_APP_KEY=your-app-key
DINGTALK_APP_SECRET=your-app-secret
DINGTALK_REDIRECT_URI=http://localhost:3939/auth/dingtalk/callback
```

**依赖关系图**：
```
model-eval-cli (必须 clone)
    ↓ 依赖
myauth (认证功能需要 clone)
    ↓ 依赖
寄生项目 (uv pip install -e)
```

### 依赖同步问题（重要）

当更新 model_eval_cli 源码后，需要同步更新寄生项目的虚拟环境：

```bash
# 1. 首先停止正在运行的 model-eval 进程

# 2. 重新安装 model-eval-cli（使用 --force-reinstall）
uv pip install -e C:\path\to\model_eval_cli --force-reinstall

# 3. 检查并安装缺失的依赖
# 测试导入是否正常
uv run python -c "from myauth import AuthFramework; print('OK')"

# 如果导入失败，安装缺失的依赖
# 注意：myauth 的 aiosqlite 在 dev 依赖中，需要加 [dev]
uv pip install -e C:\path\to\my-auth[dev]
```

**依赖检查流程**：
1. 运行 `uv run python -c "import 模块名"` 检查各模块是否可导入
2. 如果导入失败，查找并安装缺失的包
3. 对于 my-auth，需要安装 `[dev]` 依赖（包含 aiosqlite 等）

### Step 2: 创建配置文件

在项目根目录创建 `model-eval.json`:

```json
{
  "project_type": "python",
  "hooks": {
    "predict": "project:predict",
    "get_curve_data": "project:get_curve_data",
    "generate_smart_report": "project:generate_smart_report",
    "env_management": "project:EnvManagementProvider",
    "pipeline_config": "project:PipelineConfigProvider",
    "model_config": "project:ModelConfigProvider"
  }
}
```

**注意：** 配置应保持简洁，不需要 `capabilities.supported_tasks` 等空字段。`generate_smart_report` 为**必须配置**的钩子，集成时 skill 会帮助 build 占位实现，后续可通过 `/smart-report-builder` skill 升级为真实实现。

**系统钩子说明**：
| 钩子 | 用途 | 类型 |
|------|------|------|
| `predict` | 模型推理 | 函数 |
| `get_curve_data` | 获取曲线数据 | 函数 |
| `generate_smart_report` | 智能报告生成 | 函数 |
| `env_management` | 环境管理（list/get/set） | Provider 类 |
| `pipeline_config` | 数据清洗/特征工程配置 | Provider 类 |
| `model_config` | 模型训练配置 | Provider 类 |

### Step 3: 验证配置

```bash
model-eval validate
```

### Step 4: 运行推理测试

```bash
model-eval run '{"input": "test data"}'
```

## 核心API接口说明

Dashboard 前端会调用以下 API，理解这些接口有助于正确实现 wrapper：

### ⚠️ 重要：API 返回格式约定

**API 响应统一格式**：model-eval-cli 的 API 会自动包装响应：

```json
{
  "success": true,
  "data": <wrapper函数返回值>
}
```

**关键规则**：
- `get_curve_data` 应直接返回**数组** `[{...}, {...}]`，而不是包装对象
- API 会将数组包装为 `{"success": true, "data": [...]}`
- 前端期望 `response.data` 是数组，可直接用于图表渲染
- ⚠️ **特别注意**：如果返回的对象中包含 `data` 字段（即使是数组），API 会将其二次包装成 `{"success": true, "data": {"data": [...]}}`，导致前端无法访问

**错误示例**（踩坑记录）：
```python
# ❌ 错误：返回包含 'data' 键的字典
def get_curve_data(...):
    return {'data': [...], 'case_path': '...'}
# API 响应: {"success": true, "data": {"data": [...], "case_path": "..."}}
# 前端访问 response.data[0] 会失败，因为 data 是对象不是数组

# ✅ 正确：直接返回数组（API 会自动包装）
def get_curve_data(...):
    return [...]
# API 响应: {"success": true, "data": [...]}  # 正确！
# 前端访问 response.data[0] 成功获取第一条数据
```

**说明**：如果需要在返回数据中携带额外信息（如 `case_path`），应通过其他方式传递（如后续的 predict 接口依赖该信息时，从 params 或 raw_input 中获取），而不是放在 get_curve_data 的返回值中。

### 1. `/api/curves/fields` - 获取可用字段列表

- 用途：前端下拉菜单选择 X/Y 轴字段
- 调用方式：`get_curve_data(params={"time_range": "1h"})`
- **要求**：当没有传 `device_id` 时，应返回默认设备的字段
- 返回格式：
```json
[{"field": "k_ts", "label": "时间"}, {"field": "电压", "label": "电压"}]
```

### 2. `/api/curves/data` - 获取曲线数据（重点）

- 用途：渲染图表数据
- 调用方式：`get_curve_data(x_axis, y_axis, params)`
- params 常见参数：
  - `device_id`: 设备ID（必填）
  - `profile`: 厂区（可选）
  - `model_type`: 模型类型（可选）

**返回值要求**：

```python
def get_curve_data(x_axis=None, y_axis=None, params=None):
    """
    获取曲线数据

    Args:
        x_axis: X轴字段名（可选，用于提示但不影响返回数据）
        y_axis: Y轴字段名（可选，用于提示但不影响返回数据）
        params: 参数字典
            - device_id: 设备ID（必填）
            - profile: 厂区（可选）
            - model_type: 模型类型（可选）

    Returns:
        list: 数据点数组，每个元素是一条完整记录
              [{"k_ts": "2025-10-07 09:00:00", "potVolt": 3990, ...}, ...]
    """
    # 加载数据
    df = pd.read_csv(data_file)

    # 直接返回完整数据（所有列）
    return df.to_dict(orient='records')  # 返回数组，不要包装！
```

**为什么返回全量数据**：
1. 前端需要根据 series 配置提取多个字段
2. 数据标注时需要查看完整数据
3. 简化后端逻辑，不需要维护字段过滤

### 3. `/api/predict` - 执行推理

- 用途：运行模型预测

### 4. `/api/viz/model-formats` - 获取模型输出格式

- 用途：前端 AnnotationModal 标注时显示预期输出的字段表单
- 调用方式：自动调用，无需手动配置
- **依赖**：`PredictProvider.OUTPUT_SCHEMA` 类属性（详见下方"OUTPUT_SCHEMA"部分）

### 5. `/api/test/run` - 异步执行测试（重要）

- 用途：运行测试用例
- **注意**：此 API 是**异步非阻塞**的，调用后立即返回 `test_run_id`，测试在后台执行
- 前端通过轮询 `/api/test-runs/{run_id}` 获取实时进度

### 6. `/api/preview/config` - 预览配置变更

- 用途：预览节点配置变更后的输出差异
- 调用方式：`POST /api/preview/config`，请求体 `{node_id, old_config, new_config}`
- 依赖：config provider 的 `preview` 方法
- 返回：新旧配置的输出对比结果

### 7. `/api/preview/comparisons` - 待讨论对比结果管理

- **POST** `/api/preview/comparisons` - 暂存对比结果
  - 请求体：`{node_id, old_config, new_config, old_output, new_output, sample_data, note}`
  - 状态默认为 `pending`

- **GET** `/api/preview/comparisons` - 列出所有对比结果摘要
  - 返回：`[{id, node_id, note, status, comment_count, created_at}, ...]`

- **GET** `/api/preview/comparisons/{id}` - 获取单个对比详情

- **PATCH** `/api/preview/comparisons/{id}` - 更新状态或备注
  - 请求体：`{status, note}`

- **POST** `/api/preview/comparisons/{id}/comments` - 添加评论
  - 请求体：`{text, author}`

- **DELETE** `/api/preview/comparisons/{id}` - 删除对比结果

**状态流转**：`pending` → `annotated`（添加评论） → `tested`（保存配置并发起测试）

### 8. `/api/config/save` - 保存节点配置

- 用途：将讨论确认后的配置保存到项目
- 调用方式：`POST /api/config/save`，请求体 `{node_id, config}`
- 依赖：config provider 的 `save` 方法

### get_curve_data 函数设计原则

1. **参数设计**：
   - 实时模式：需要 `device_id` + `time_range`
   - 离线模式：只需要 `device_id`（自动匹配案例）

2. **默认值处理**：
   - 当 `device_id` 未提供时，应有默认值（避免前端调用失败）

3. **返回值格式**（重要）：

```python
def get_curve_data(x_axis=None, y_axis=None, params=None):
    # ... 获取数据逻辑 ...

    # ✅ 正确：直接返回数组
    return df.to_dict(orient='records')

    # ❌ 错误：不要返回包装对象
    # return {'data': [...], 'case_path': '...'}
```

**注意**：API 会自动包装响应为 `{"success": true, "data": <返回值>}`，所以 wrapper 函数应直接返回数组。

4. **时间格式**：
   - k_ts 字段应为字符串格式：`YYYY-MM-DD HH:MM:SS`
   - 或 Unix 时间戳（单位ms）+ 时区处理

## 认证系统

### 概述

Model Eval CLI 内置 my-auth 认证框架，支持：
- 用户登录/注册
- JWT 令牌认证
- DingTalk OAuth 第三方登录

### 认证配置

**.env 文件（推荐）**

在项目根目录创建 `.env` 文件配置认证参数：

```bash
# JWT 配置（必填，至少32字符）
JWT_SECRET=your-secret-key-at-least-32-characters

# 数据库配置（可选，默认 SQLite）
DATABASE_URL=sqlite:///myauth.db

# 管理员账户
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=admin123

# 钉钉登录配置
DINGTALK_ENABLED=true
DINGTALK_APP_KEY=your-app-key
DINGTALK_APP_SECRET=your-app-secret
DINGTALK_REDIRECT_URI=http://localhost:3939/auth/dingtalk/callback
```

**注意**：myauth 会自动读取 `.env` 文件，无需额外配置。

### project_type

| 类型 | 说明 |
|------|------|
| `python` | Python 函数推理 |
| `http` | HTTP API 推理 |

### hooks

自定义钩子函数:

```json
{
  "hooks": {
    "predict": "module.path:function_name",
    "get_curve_data": "module.path:get_data_func",
    "generate_smart_report": "module.path:generate_smart_report_func",
    "env_management": "module.path:EnvManagementProvider",
    "pipeline_config": "module.path:PipelineConfigProvider",
    "model_config": "module.path:ModelConfigProvider"
  }
}
```

### pipeline_config / model_config provider（配置验证提供者）

**用于配置验证页面**：当用户在 Dashboard 的"配置验证"页面查看和修改节点配置时，调用此 provider。

**拆分设计**：
- `pipeline_config`：数据清洗 + 特征工程节点
- `model_config`：模型推理节点（nb, v, f, al, superheat）

两个 provider 继承相同的读写逻辑，但 `list_nodes()` 返回不同的节点列表。

**必须实现的方法**：

```python
class ConfigProvider:
    """配置提供者，用于配置验证页面的读写操作"""

    def list_nodes(self) -> list:
        """列出所有可配置节点（用于 /api/nodes 接口）

        Returns:
            list: 节点列表，每个节点至少包含 id、name 字段
                  [{"id": "nb", "name": "下料间隔模型", "type": "model"}, ...]
        """
        return []

    def get_config(self, node_id: str) -> dict:
        """获取指定节点的当前配置

        Args:
            node_id: 节点ID

        Returns:
            dict: 当前配置内容（JSON 可序列化）
        """
        return {"param1": "value1", ...}

    def get_schema(self, node_id: str) -> dict:
        """获取指定节点的配置字段说明（Schema）

        Args:
            node_id: 节点ID

        Returns:
            dict: {
                "description": "模型配置说明",
                "fields": {
                    "field_name": {
                        "label": "显示名称",
                        "type": "number|string|boolean|array|object",
                        "description": "字段说明（可选）",
                        "default": "默认值（可选）"
                    }
                }
            }
        """
        return {"description": "", "fields": {}}

    def save(self, node_id: str, config: dict) -> bool:
        """保存指定节点的配置

        Args:
            node_id: 节点ID
            config: 新配置内容

        Returns:
            bool: 是否保存成功
        """
        return True

    def get_compare_data(self) -> list:
        """获取用于预览配置变更效果的样本数据（可选方法）

        Returns:
            list: 数据样本列表，用于 preview 的对比展示
        """
        return []

    def preview(
        self,
        node_id: str,
        old_config: dict,
        new_config: dict,
        compare_data: list,
    ) -> dict:
        """预览配置变更效果

        Args:
            node_id: 节点ID
            old_config: 当前配置
            new_config: 新配置
            compare_data: 对比用数据样本

        Returns:
            dict: {
                "old_output": {...},  # 旧配置输出
                "new_output": {...},  # 新配置输出
                "diff": {...}         # 差异信息（可选）
            }
        """
        return {"old_output": {}, "new_output": {}}
```

**配置示例**：

```json
{
  "project_type": "python",
  "hooks": {
    "predict": "model_eval_wrapper:predict",
    "get_curve_data": "model_eval_wrapper:get_curve_data",
    "pipeline_config": "model_eval_wrapper:PipelineConfigProvider",
    "model_config": "model_eval_wrapper:ModelConfigProvider"
  }
}
```

### env_management provider（环境管理提供者）

**用于多环境切换**：当项目需要支持多个环境（如不同厂区、不同部署环境）时，配置此 provider。

**必须实现的方法**：

```python
class EnvManagementProvider:
    """环境管理提供者，用于多环境切换"""

    def list_envs(self) -> list:
        """列出所有可用环境

        Returns:
            list: 环境名称列表，如 ["lv1p3", "lv3p2", "lv5p3"]
        """
        return []

    def get_current(self) -> str:
        """获取当前激活的环境

        Returns:
            str: 当前环境名称
        """
        return ""

    def set_current(self, env_name: str) -> str:
        """切换当前环境

        Args:
            env_name: 环境名称

        Returns:
            str: 切换后的环境名称
        """
        return env_name
```

**配置示例**：

```json
{
  "project_type": "python",
  "hooks": {
    "predict": "model_eval_wrapper:predict",
    "get_curve_data": "model_eval_wrapper:get_curve_data",
    "env_management": "model_eval_wrapper:EnvManagementProvider"
  }
}
```

**前端交互**：
1. Dashboard 顶部导航栏显示 EnvSelector 组件
2. 用户选择环境后，前端自动刷新页面加载新环境数据
3. 所有数据按当前环境隔离存储

### generate_smart_report 函数（智能报告生成钩子）

> **用于智能报告功能**：当用户在 Dashboard 的"智能报告"页面生成报告时，调用此钩子函数。

**⚠️ 重要：返回格式协议**

> **状态字段必须是 `"completed"` 或 `"failed"`，不是 `"success"`**

API 会检查返回状态是否为 `"completed"` 来判断报告是否生成成功：

```python
# API 代码逻辑（api.py:1785-1800）
if result.get("status") == "completed":
    update_smart_report(..., status="completed", ...)
else:
    update_smart_report(..., status="failed", ...)
```

如果返回 `"success"` 而不是 `"completed"`，会被判定为失败！

**函数签名**：

```python
def generate_smart_report(base_run_id: str, test_run_id: str, report_id: str = None) -> dict:
    """
    生成智能报告

    Args:
        base_run_id: 基准测试记录 ID
        test_run_id: 测试对象记录 ID
        report_id: 报告记录 ID（用于生成唯一文件名）

    Returns:
        dict: {
            "status": "completed" | "failed",  # ⚠️ 必须是 completed，不是 success！
            "pdf_path": str | None,      # PDF 文件相对路径（相对于项目根目录）
            "error_message": str | None   # 错误信息（status 为 failed 时）
        }
    """
```

**典型实现流程**：

```python
def generate_smart_report(base_run_id: str, test_run_id: str, report_id: str = None) -> dict:
    # 1. 加载测试记录数据
    from model_eval_cli.execution.storage import TestRunStorage
    storage = TestRunStorage()
    base_run = storage.get(base_run_id)
    test_run = storage.get(test_run_id)

    # 2. 对比分析两个测试结果
    # ... 自定义报告逻辑 ...

    # 3. 生成 PDF 报告（按环境隔离存储）
    # PDF 文件名使用 report_id 保证唯一性：{report_id}.pdf
    # 路径通过 get_data_root() 自动解析为 .model-eval/{env}/smart-reports/
    from model_eval_cli.config.paths import get_data_root
    data_root = get_data_root()
    pdf_path = str(data_root / "smart-reports" / f"{report_id}.pdf")
    # ... PDF 生成逻辑 ...

    return {
        "status": "completed",
        "pdf_path": pdf_path
    }
```

**占位实现**（CLI 默认提供）：

如果未配置此钩子，CLI 会返回引导提示，建议用户使用 `/smart-report-builder` skill 完成集成。

**配置示例**：

```json
{
  "hooks": {
    "predict": "model_eval_wrapper:predict",
    "get_curve_data": "model_eval_wrapper:get_curve_data",
    "generate_smart_report": "model_eval_wrapper:generate_smart_report"
  }
}
```

### predict OUTPUT_SCHEMA（重要）

> **用于 AnnotationModal 标注表单**：Dashboard 的标注模态框通过读取 `PredictProvider.OUTPUT_SCHEMA` 类属性，自动生成预期输出字段的结构化表单，不再解析 docstring。

**⚠️ 重要：OUTPUT_SCHEMA 设计必须与用户交互确认**

在编写 `OUTPUT_SCHEMA` 之前，必须与用户确认实际的业务需求：

```
Step 1: 询问用户
  "predict 函数返回哪些字段？每个字段的含义和类型是什么？"

Step 2: 根据用户回答，确认字段列表
  例如：
  - action: 动作类型 (string, 如 "+1" / "-1" / "0")
  - model_type: 模型类型 (string)
  - confidence_score: 置信度 (float)

Step 3: 确认后编写 OUTPUT_SCHEMA
```

```python
class PredictProvider:
    """模型预测 Provider"""

    OUTPUT_SCHEMA = {
        "fields": [
            {
                "name": "action",
                "type": "string",
                "description": "动作类型",
                "enum_values": [
                    {"value": "+1", "label": "增加"},
                    {"value": "-1", "label": "减少"},
                    {"value": "0", "label": "保持"},
                ],
            },
            {
                "name": "confidence_score",
                "type": "float",
                "description": "置信度",
            },
        ],
        "model_types": ["nb", "v", "f", "al", "superheat"],
    }

    def predict(self, input_data: dict) -> dict:
        """执行模型预测"""
        # ... 预测逻辑 ...
        return {"action": "+1", "confidence_score": 0.95}
```

**`OUTPUT_SCHEMA` 结构说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `fields` | list | 输出字段列表，每个字段包含 `name`、`type`、`description`，可选 `enum_values` |
| `enum_values` | list | 枚举值列表，每个元素包含 `value` 和 `label`，用于下拉选择 |
| `model_types` | list | 支持的模型类型列表，如 `["nb", "v", "f", "al", "superheat"]` |

**支持的模型类型**（重要）：`model_types` 在 `OUTPUT_SCHEMA` 中定义，无需单独的 `SUPPORTED_MODELS` 模块级变量。

**注意**：`OUTPUT_SCHEMA` 是类属性，不是实例属性或 docstring。后端通过 `getattr(provider_class, "OUTPUT_SCHEMA", None)` 读取。

### PARAMS_SCHEMA（曲线数据参数定义）

> **用于前端动态生成筛选器**：Dashboard 的曲线数据筛选器通过读取 `CurveDataProvider.PARAMS_SCHEMA` 类属性自动生成，不再解析 docstring。

```python
class CurveDataProvider:
    """曲线数据 Provider"""

    PARAMS_SCHEMA = [
        {
            "name": "source",
            "type": "string",
            "label": "查询模式",
            "description": "realtime=实时查询ODS, offline=读取本地案例CSV",
            "default": "offline",
        },
        {
            "name": "device_id",
            "type": "string",
            "label": "槽号",
            "description": "设备ID",
            "required": True,
        },
        {
            "name": "start_time",
            "type": "string",
            "label": "开始时间",
            "description": "ISO格式时间",
        },
        {
            "name": "end_time",
            "type": "string",
            "label": "结束时间",
            "description": "ISO格式时间",
        },
        {
            "name": "profile",
            "type": "string",
            "label": "厂区",
            "description": "如 lv1p3, lv3p2",
        },
        {
            "name": "case_dir",
            "type": "string",
            "label": "案例目录",
            "description": "离线模式下精确指定案例路径",
        },
    ]

    def get_curve_data(self, x_axis=None, y_axis=None, params=None):
        """获取曲线数据"""
        # ... 数据获取逻辑 ...
        return df.to_dict(orient='records')
```

**`PARAMS_SCHEMA` 结构说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 参数名（对应 params 字典的 key） |
| `type` | string | 参数类型：`string`、`number`、`boolean`、`datetime` |
| `label` | string | 前端显示标签 |
| `description` | string | 参数说明 |
| `default` | any | 默认值（可选） |
| `required` | boolean | 是否必填（可选） |

**注意**：`PARAMS_SCHEMA` 是类属性，不是 docstring。后端通过 `getattr(provider_class, "PARAMS_SCHEMA", None)` 读取。

### case_index

用于离线模式下的案例索引:

```json
{
  "case_index": {
    "root": ".model-eval/{env}/cases",
    "pattern": "{profile}/{device_id}/{start_time}_{end_time}"
  }
}
```

> **注意**：案例索引路径会自动按当前环境解析。实际存储在 `.model-eval/{current_env}/cases/` 下。

## CLI 命令

### validate

验证配置文件:

```bash
model-eval validate
```

### run

运行推理测试:

```bash
model-eval run '{"input": "data"}'
```

### start

启动 Web Dashboard:

```bash
model-eval start
# 指定端口
model-eval start --backend-port 2525 --frontend-port 3939
# 指定项目路径
model-eval start -p /path/to/project
```

### curves

列出可用字段:

```bash
model-eval curves
```

### env

环境管理（多环境切换）:

```bash
# 列出所有可用环境
model-eval env list

# 查看当前环境
model-eval env current

# 切换环境
model-eval env set lv3p2
```

**注意**：环境管理依赖 `env_management` hook 配置。切换环境后，所有数据（反馈、测试用例、测试记录等）自动隔离。

### feedback

反馈管理:

```bash
# 提交反馈
model-eval feedback submit <file> -d "反馈描述" -t tag1 -t tag2

# 列出反馈
model-eval feedback list -t tag1
```

### 对照组（Control Groups）

对照组是从案例全集（`.model-eval/{env}/cases`）中选择的一部分案例集合，用于模型评估对比。

**存储结构**（按环境隔离）：
- 对照组存储路径: `.model-eval/{env}/control-groups/{group_id}.json`
- 每个对照组包含一个案例列表 (`cases` 字段)
- 索引文件: `.model-eval/{env}/control-groups/index.json`

**对照组数据模型**：
```python
class ControlGroup(BaseModel):
    id: str                      # 对照组 ID
    name: str                    # 名称
    description: str | None      # 描述
    status: "draft" | "active" | "archived"  # 状态
    tags: list[str]              # 标签
    cases: list[CaseRef]         # 案例列表
    created_at: datetime         # 创建时间
    updated_at: datetime         # 更新时间
    creator: str                 # 创建者

class CaseRef(BaseModel):
    profile: str                 # 厂区/环境标识
    device_id: str               # 设备 ID
    case_id: str                 # 案例时间戳 (如 "20251004_093000")

class FilterParams(BaseModel):
    """嵌入在 Feedback.raw_input 和 TestCase.raw_input 中的过滤参数"""
    source: str | None           # 查询模式: realtime|offline
    device_id: str               # 槽号
    start_time: str | None       # 开始时间（可选）
    end_time: str | None         # 结束时间（可选）
    profile: str | None          # 厂区（可选）
    case_dir: str | None         # 案例目录路径（离线模式）
```

**批量转测试用例（重要）**：

对照组可批量转换为 TestCase，但**必须满足以下条件**：
- 每个案例的 `case_meta.json` 中必须有 `expected_output`（预期输出）
- 每个案例的 `case_meta.json` 中必须有 `model_type`（模型类型）
- **缺失任一字段的案例会被跳过**，并提示用户前往标注

```
批量转换流程：
1. 用户点击"批量转测试"
2. 后端读取每个 CaseRef 对应的 case_meta.json
3. 检查 model_type 和 expected_output 是否存在
4. 缺失的案例跳过，返回跳过列表给用户
5. 满足条件的案例生成 TestCase（raw_input 含 case_dir 和 filterParams.device_id）
```

**⚠️ 关键约束**：Feedback 本身**不能直接**转换为 TestCase，必须经过 Annotation 标注（生成 `expected_output`）后才能转换。即：**Feedback → Annotation → TestCase**，不存在 Feedback → TestCase 的直连路径。

**⚠️ 待标注反馈限制**：`pending` 状态的 Feedback 不允许添加到 ControlGroup。只有 `annotated` 状态的反馈才能被选中并加入对照组。

**API 端点**：
| 端点 | 说明 |
|------|------|
| `GET /api/cases` | 列出所有可用案例（用于选择） |
| `GET /api/control-groups` | 列出对照组 |
| `POST /api/control-groups` | 创建对照组（包含案例列表） |
| `PATCH /api/control-groups/{id}` | 更新对照组 |
| `POST /api/control-groups/{id}/cases` | 添加案例到对照组 |
| `POST /api/control-groups/{id}/cases/remove` | 从对照组移除案例 |
| `DELETE /api/control-groups/{id}` | 删除对照组 |
| `GET /api/control-groups/{id}/export` | 导出案例列表为 CSV |
| `POST /api/control-groups/{id}/convert-to-testcases` | 批量转为测试用例 |

**前端交互**：
1. Dashboard 显示案例全集列表
2. 用户通过多选创建对照组
3. 对照组详情页可添加/移除案例
4. 点击"批量转测试"按钮，校验后生成 TestCase
5. 导出功能生成案例列表 CSV

### testcase

测试用例管理:

```bash
# 创建测试用例
model-eval testcase create <input.json> <expected.json> -l label1 --status active

# 列出测试用例
model-eval testcase list --status active -l label1
```

### test

测试执行:

```bash
# 运行单个测试用例
model-eval test run <testcase_id>

# 运行所有活跃测试用例
model-eval test run --all

# 指定执行策略
model-eval test run --all --strategy parallel --max-workers 4
```

策略选项:
- `sequential`: 顺序执行
- `parallel`: 并行执行
- `adaptive`: 自适应执行

## 集成模式

### 模式 1: Python 函数集成

适用于本地 Python 项目:

```python
# your_project/inference.py
def predict(input_data: dict) -> dict:
    """推理函数"""
    # your inference logic
    return {"result": "output"}

# model-eval.json
{
  "project_type": "python",
  "hooks": {
    "predict": "your_project.inference:predict"
  }
}
```

### 如何包装项目中已有的推理函数

在项目中创建包装文件（如 `model_eval_wrapper.py`），步骤如下：

**Step 1: 搜索项目中已有的技术资产**

使用 Glob 和 Grep 工具搜索：

```bash
# 1. 搜索推理函数
grep -r "def.*predict" src/predict/
grep -r "def.*predict" src/

# 2. 搜索数据读取函数
grep -r "def read_" src/data_interface/
grep -r "def get_" src/data_interface/

# 3. 查找完整的数据处理流程（如果有）
ls -la src/link_all_task.py

# 4. 查看测试数据目录结构（用于离线模式）
ls tests/
ls tests/logical/ 2>/dev/null || echo "无logical目录"
```

**Step 2: 与用户确认技术方案**

根据搜索结果，与用户确认以下内容：

1. **推理函数确认**
   - 列出找到的预测函数及其路径
   - 询问用户使用哪个函数作为 predict 钩子

2. **数据获取方式确认**
   - 列出找到的数据读取函数
   - 询问数据来源：实时API / 离线文件 / 混合

3. **实时数据访问确认（重要）**
   - 询问：「运行评估时，能否访问实时数据源？」
   - 选项：
     - A: 可以访问实时数据 → 生成实时数据获取逻辑
     - B: 不能访问实时，但有本地离线数据 → 生成离线数据读取逻辑
     - C: 两者都没有 → 提示无法获取数据

**Step 3: 根据确认结果生成代码**

根据用户选择，生成对应的 wrapper 代码：

- **实时数据模式**：调用数据读取函数获取实时数据
- **离线数据模式**：从本地文件读取数据
- **混合模式**：优先实时，失败则降级离线

**model-eval.json 保持简洁通用：**
```json
{
  "project_type": "python",
  "hooks": {
    "predict": "project:predict",
    "get_curve_data": "project:get_curve_data"
  }
}
```

### 模式 2: HTTP API 集成

适用于远程模型服务:

```json
{
  "project_type": "http",
  "capabilities": {
    "endpoint": "http://localhost:8000/predict"
  }
}
```

### 模式 3: 工厂函数模式

适用于需要初始化项目实例的场景:

```python
# your_project/__init__.py
class Project:
    def __init__(self):
        self.model = load_model()

    def predict(self, input_data):
        return self.model.predict(input_data)

def get_project_instance():
    return Project()
```

```json
{
  "project_type": "python",
  "hooks": {
    "predict": "project:predict",
    "get_curve_data": "project:get_curve_data"
  }
}
```

## 数据存储

项目数据存储在 `.model-eval/` 目录，**按当前环境隔离**：

```
.model-eval/
└── {current_env}/              # 当前激活的环境，如 lv1p3
    ├── config/                 # 配置缓存
    ├── feedback/               # 反馈数据
    ├── testcases/              # 测试用例（独立文件 + index.json）
    ├── test-runs/              # 测试运行记录（独立文件 + index.json）
    ├── comparisons/            # 待讨论对比结果（独立文件 + index.json）
    ├── results/                # 测试结果（已弃用，使用 test-runs）
    ├── reports/                # 生成报告
    ├── smart-reports/          # 智能报告（PDF）
    ├── annotations/            # 标注数据
    ├── control-groups/         # 对照组数据
    ├── cases/                  # 离线案例索引
    ├── viz.json                # 可视化配置（按环境独立）
    └── logs/                   # 运行日志
```

**环境隔离说明**：
- 所有 storage 模块通过 `get_data_root()` 自动解析当前环境路径
- 切换环境后，只能看到该环境的数据
- 已有数据自动迁移到默认环境目录

**路径工具**（`model_eval_cli/config/paths.py`）：
```python
from model_eval_cli.config.paths import get_data_root, get_viz_config_path

# 获取当前环境的数据根目录
# 返回: .model-eval/{current_env}/
data_root = get_data_root()

# 获取当前环境的可视化配置路径
# 返回: .model-eval/{current_env}/viz.json
viz_path = get_viz_config_path()
```

**存储模式**：testcases、test-runs、comparisons 均采用相同的存储模式：
- 每个记录独立文件：`{id}.json`
- 索引文件：`index.json`
- 避免单文件过大导致的读写性能问题

### 待讨论对比结果（Comparisons）

配置验证页面暂存的对比讨论数据：

```bash
# 存储位置（按环境隔离）
.model-eval/{env}/comparisons/
├── index.json              # 索引：["abc123", "def456", ...]
├── abc123.json             # 单个对比详情
└── def456.json
```

**对比结果状态**：
- `pending`: 待讨论（刚暂存）
- `annotated`: 已标注（添加了评论）
- `tested`: 已测试（已保存配置并发起测试）

**前端展示**：在"测试库"页面的"待讨论用例"子标签页中查看和管理。

## 最佳实践

### 1. 测试用例组织

按功能模块组织测试用例:

```bash
# 创建带标签的测试用例
model-eval testcase create input.json expected.json -l classification -l fast
```

### 2. 持续评估

使用 CI/CD 集成:

```bash
# 在 CI 中运行所有测试
model-eval test run --all --strategy parallel
```

### 3. 反馈循环

正确的反馈流转路径：**Feedback → Annotation → TestCase**

1. 通过 Dashboard 查看曲线或测试结果
2. 提交有问题的案例作为 **Feedback**（状态为 `pending`）
3. 对 Feedback 进行 **Annotation** 标注（填写 `expected_output`、`model_type` 等），状态变为 `annotated`
4. 标注后的 Annotation 可转换为 **TestCase**
5. 运行 TestCase 验证模型效果
6. 迭代改进模型

**⚠️ 注意**：`pending` 状态的 Feedback 不能直接转为 TestCase，也不能加入 ControlGroup。必须先完成标注。

### 4. 测试运行实时进度（重要）

后端 `/api/test/run` 是异步非阻塞的，前端需要轮询获取进度：

```typescript
// 前端轮询示例
const [pollingRunId, setPollingRunId] = useState<string | null>(null)

useEffect(() => {
  if (!pollingRunId) return
  const pollInterval = setInterval(async () => {
    const response = await fetch(`/api/test-runs/${pollingRunId}`)
    const data = await response.json()
    if (data.success) {
      const testRun = data.data
      // 更新测试运行状态
      setTestRuns(prev => prev.map(run => run.id === testRun.id ? testRun : run))
      // 测试完成时停止轮询
      if (testRun.status === 'completed' || testRun.status === 'failed') {
        setPollingRunId(null)
      }
    }
  }, 2000)  // 每2秒轮询一次
  return () => clearInterval(pollInterval)
}, [pollingRunId])
```

### 5. 图表标题增强

可视化图表标题应包含设备ID和其他筛选参数，使用 `filterValues`（包含默认值）而非 `filterParams`（仅非默认值）：

```typescript
const buildTitle = () => {
  let titleText = chart.title || ''

  // 添加设备ID
  if (filterValues.device_id) {
    titleText += ` - 槽${filterValues.device_id}`
  }

  // 添加其他筛选参数（排除时间参数）
  const timeParams = ['start_time', 'end_time', 'time_range', 'x_axis', 'y_axis', 'device_id']
  filters.forEach((filter) => {
    const value = filterValues[filter.name]
    if (value && !timeParams.includes(filter.name)) {
      const label = filter.label || filter.name
      titleText += ` - ${label}: ${value}`
    }
  })
  return titleText
}
```

## 离线数据模式案例索引设计

### 背景与问题

在工业场景中，模型推理需要多种数据源（设备配置、日报、工艺参数、量测记录等）。离线模式下存在以下挑战：

1. **数据关联困难**：测试用例中的曲线数据（get_curve_data）需要与推理数据（predict）关联
2. **案例定位不精确**：如何根据测试用例的过滤条件找到对应的离线案例
3. **数据源分散**：推理需要11-12个不同的数据表

### 解决方案：案例索引目录

创建案例索引目录，统一管理曲线数据和推理数据的引用：

```
.model-eval/{env}/cases/
└── {profile}/              # 厂区，如 lv1
    └── {device_id}/       # 设备ID，如 3813
        └── {case_id}/    # 案例ID，如 202511251200_202512251145
            ├── case_meta.json
            ├── curve/
            │   └── ref.json        # 曲线数据引用
            └── predict/
                └── {model_type}/  # nb/v/f
                    └── ref.json    # 推理数据引用（11-12个表）
```

**ref.json 结构**：
```json
// curve/ref.json - 只包含电压数据
{
  "source_file": "tests/logical/lv1/nb/case_data_3813_20251225_120000/3813_电压2分钟_xxx.csv.zip"
}

// predict/nb/ref.json - 包含全部推理数据
{
  "pot_config": {"table_name_cn": "槽配置", "source_file": "..."},
  "daily_report": {"table_name_cn": "日报", "source_file": "..."},
  "voltage_2min": {"table_name_cn": "电压2分钟", "source_file": "..."},
  "measure_data": {"table_name_cn": "量测记录", "source_file": "..."},
  ...
}
```

### 配置文件

在 `model-eval.json` 中添加 `case_index` 配置：

```json
{
  "project_type": "python",
  "hooks": {
    "predict": "model_eval_wrapper:al_predict",
    "get_curve_data": "model_eval_wrapper:get_curve_data"
  },
  "case_index": {
    "root": ".model-eval/{env}/cases",
    "pattern": "{profile}/{device_id}/{start_time}_{end_time}"
  }
}
```

### 完整集成 Workflow

#### Phase 1: 离线数据准备

```
用户已有离线数据目录（如 tests/logical/）

     ↓

Step 1: 询问用户数据位置
  "请告诉我你的离线数据存放在哪个目录？"

     ↓

Step 2: 查看并确认目录结构
  命令: ls -la tests/logical/
  确认: 厂区目录、模型类型子目录、案例命名格式

     ↓

Step 3: 生成案例索引
  扫描离线数据 → 创建 .model-eval/{env}/cases/ 索引目录
  结构: .model-eval/{env}/cases/{profile}/{device_id}/{case_id}/
        ├── case_meta.json
        ├── curve/
        │   └── ref.json
        └── predict/{model_type}/
            └── ref.json
```

#### Phase 2: 参数设计（关键交互点）

```
Step 1: 查看实际案例索引目录
  命令: ls -la .model-eval/{env}/cases/

     ↓

Step 2: 分析真实目录层级
  例如: .model-eval/{env}/cases/lv1p3/3615/20251010_090000/
  分析: 第一层=profile, 第二层=device_id, 第三层=case_id

     ↓

Step 3: 【交互确认】询问用户
  "你的案例索引结构是 {profile}/{device_id}/{case_id}/

   我建议 get_curve_data 的 params 包含：
   - profile: 厂区
   - device_id: 设备ID
   - case_id: 案例ID

   这个设计是否符合你的业务场景？是否需要调整？"

     ↓

Step 4: 根据用户反馈调整
  用户确认后 → 实现 wrapper 代码
  用户有调整 → 更新参数设计后重新确认
```

#### Phase 3: 实现 wrapper 代码

```
get_curve_data 实现:
  1. 从 params 提取参数
  2. 根据参数拼接案例路径
  3. 读取 curve/ref.json 获取数据文件路径
  4. 加载数据并返回数组（不要包装对象！）

predict 实现:
  1. 从 raw_input.filterParams 提取参数
  2. 调用 get_case_by_device_and_time() 查找案例
  3. 读取 predict/{model_type}/ref.json 获取推理数据
  4. 执行推理返回结果
```

#### Phase 4: 运行时流程

```
┌─────────────────────────────┐
│  前端 Dashboard             │
│  用户选择设备、时间等筛选条件 │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  调用 /api/curves/data      │
│  params: {device_id, ...}   │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  get_curve_data(params)     │
│  1. 查找案例索引目录         │
│  2. 读取 ref.json           │
│  3. 加载数据文件             │
│  4. 返回数组                 │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│  前端渲染图表               │
│  response.data 直接用于渲染  │
└─────────────────────────────┘
```

#### 关键原则总结

| 阶段 | 原则 |
|------|------|
| 数据准备 | 先确认用户数据位置，再生成索引 |
| 参数设计 | **基于真实目录结构，交互确认** |
| 代码实现 | 返回数组，不要包装对象 |
| 可视化 vs 推理 | 可视化不需要 model_type，推理需要 |

---

### 集成前数据准备（详细步骤）

**在改造 wrapper 代码之前，必须先确认现有离线数据的存储位置**。按以下步骤与用户确认：

#### Step 1: 询问用户数据位置

请告诉我你的离线数据存放在哪个目录？
例如：tests/logical/、data/cases/ 或其他自定义路径

#### Step 2: 确认目录结构

根据用户回答，检查并确认：
1. 离线数据根目录：{用户回答的路径}
2. 厂区目录：lv1p3, lv3p2 还是有其他命名？
3. 模型类型子目录：nb/, v/, f/ 还是其他？
4. 案例数据格式：case_data_{device_id}_{timestamp} 还是其他？

#### Step 3: 实现案例索引生成函数并执行

**实现 generate_case_index 函数**（在 wrapper 中实现）：

1. 扫描用户确认的数据目录（如 `tests/logical/{profile}/data/{model_type}/case_data_*`）
2. 解析目录名获取 device_id 和 case_id
3. 生成 `.model-eval/{env}/cases/{profile}/{device_id}/{case_id}/` 索引目录
4. 生成以下文件：
   - `case_meta.json`：案例元信息
   - `curve/ref.json`：曲线数据引用
   - `predict/{model_type}/ref.json`：推理数据引用

**函数签名示例**：

```python
def generate_case_index(data_root: str, cases_root: str = None,
                       profile: str = None, model_type: str = None, dry_run: bool = False):
    """生成案例索引

    Args:
        data_root: 离线数据根目录（与用户确认）
        cases_root: 案例索引根目录（默认自动解析为 .model-eval/{env}/cases）
        profile: 厂区过滤
        model_type: 模型类型过滤
        dry_run: True 则只打印预览
    """
```

**执行**：
```python
from model_eval_wrapper import generate_case_index

# 先 dry-run 预览
generate_case_index(data_root='tests/logical', dry_run=True)

# 确认后执行
generate_case_index(data_root='tests/logical')
```

#### Step 4: Agent 验证并改造 wrapper

Agent 验证索引生成成功后，按照下方"函数设计原则"改造 wrapper 代码。

---

### 函数设计原则

#### get_curve_data 数据查找流程（重要）

**必须使用案例索引目录查找数据**，而不是直接从 tests/logical 目录读取：

```
1. 查找 .model-eval/{env}/cases/{profile}/{device_id}/ 目录
2. 遍历案例目录，读取 case_meta.json
3. 从 case_meta.json 中获取 source_case_dir
4. 使用 source_case_dir 加载实际数据文件
```

**错误做法**（直接读取 tests/logical 目录）：
```python
# 错误：绕过了案例索引系统
data_dir = os.path.join(OFFLINE_DATA_ROOT, profile, model_type)
case_dirs = glob.glob(os.path.join(data_dir, 'case_data_*'))
```

**正确做法**（使用案例索引）：
```python
# 正确：从 .model-eval/{env}/cases/ 读取案例索引（通过 get_data_root 自动解析）
from model_eval_cli.config.paths import get_data_root
cases_root = str(get_data_root() / 'cases')
profile_dir = os.path.join(cases_root, profile, device_id)
for case_dir in os.listdir(profile_dir):
    meta_file = os.path.join(case_dir, 'case_meta.json')
    with open(meta_file) as f:
        meta = json.load(f)
    source_dir = meta['source_case_dir']  # 从索引获取数据路径
```

**case_meta.json 格式**：
```json
{
  "device_id": "3615",
  "profile": "lv1p3",
  "case_id": "20251010_090000",
  "model_type": "nb",
  "source_case_dir": "tests/logical/lv1p3/data/nb/case_data_3615_20251010_090000"
}
```

#### 案例搜索函数实现

**⚠️ 重要：时间范围匹配**

案例搜索需要区分两个时间概念：
- **case_id（k_job_start_time）**：作业开始时间，如 `20251026_040000`
- **数据时间范围**：电压2分钟数据的起止时间，如 `2025-10-23 04:00:00 ~ 2025-10-26 03:45:00`

**用户在可视化界面选择的是数据时间范围**，搜索时需要判断用户选择的时间范围是否与案例的数据时间范围有交集（可能被包含、可能有交叉、也可能完全匹配）。

**curve/ref.json 需要添加时间范围**：

```json
{
  "电压2分钟": {
    "source_file": "tests/logical/.../3410_电压2分钟_2025-10-23-04-00-00_2025-10-26-03-45-00.csv.zip",
    "table_name_cn": "电压2分钟",
    "data_start_time": "2025-10-23 04:00:00",
    "data_end_time": "2025-10-26 03:45:00"
  }
}
```

**搜索逻辑**：检查 `[user_start, user_end]` 是否与 `[data_start, data_end]` 有交集。

**需要实现两个搜索函数**：

**1. `get_offline_case_list_by_index` - 按索引获取案例列表**

```python
def get_offline_case_list_by_index(profile: str, model_type: str, device_id: str = None):
    """获取案例列表（使用案例索引）

    Args:
        profile: 厂区，如 'lv1p3'
        model_type: 模型类型，如 'nb'
        device_id: 设备ID（可选，用于过滤）

    Returns:
        list: 案例信息列表，按时间倒序排列
        [
            {'case_path': '.model-eval/{env}/cases/lv1p3/3615/20251010_090000',
             'source_dir': 'tests/logical/lv1p3/data/nb/case_data_3615_20251010_090000',
             'device_id': '3615', 'case_id': '20251010_090000'},
            ...
        ]
    """
    from model_eval_cli.config.paths import get_data_root
    cases_root = str(get_data_root() / 'cases')
    profile_dir = os.path.join(cases_root, profile)
    cases = []

    for device_dir in os.listdir(profile_dir):
        if device_id and device_dir != device_id:
            continue
        for case_dir in os.listdir(os.path.join(profile_dir, device_dir)):
            meta_file = os.path.join(profile_dir, device_dir, case_dir, 'case_meta.json')
            if os.path.exists(meta_file):
                meta = json.load(open(meta_file))
                if meta.get('model_type') == model_type:
                    cases.append({
                        'case_path': os.path.join(cases_root, profile, device_dir, case_dir),
                        'source_dir': meta.get('source_case_dir'),
                        'device_id': device_dir,
                        'case_id': case_dir
                    })

    return sorted(cases, key=lambda x: x['case_id'], reverse=True)
```

**2. `get_case_by_device_and_time` - 按数据时间范围查找案例**

```python
def get_case_by_device_and_time(profile: str, device_id: str, start_time: str = None, end_time: str = None):
    """根据数据时间范围查找案例路径

    用户在可视化界面选择数据时间范围，查找包含该时间范围数据的案例。
    时间范围匹配规则：[user_start, user_end] 与 [data_start, data_end] 有交集即可。

    Args:
        profile: 厂区
        device_id: 设备ID
        start_time: 用户选择的开始时间（数据时间，格式 YYYY-MM-DD HH:MM:SS）
        end_time: 用户选择的结束时间（数据时间，格式 YYYY-MM-DD HH:MM:SS）

    Returns:
        str: 案例路径 或 None（返回第一个匹配的案例）
    """
    from datetime import datetime

    # 如果没有传时间，返回最新案例
    if not start_time or not end_time:
        for model_type in SUPPORTED_MODELS.keys():
            cases = get_offline_case_list_by_index(profile, model_type, device_id)
            if cases:
                return cases[0]['case_path']
        return None

    user_start = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
    user_end = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')

    for model_type in SUPPORTED_MODELS.keys():
        cases = get_offline_case_list_by_index(profile, model_type, device_id)
        for case in cases:
            # 读取 curve/ref.json 获取数据时间范围
            ref_file = os.path.join(case['case_path'], 'curve', 'ref.json')
            if os.path.exists(ref_file):
                ref = json.load(open(ref_file))
                for table_name, table_info in ref.items():
                    if 'data_start_time' in table_info and 'data_end_time' in table_info:
                        data_start = datetime.strptime(table_info['data_start_time'], '%Y-%m-%d %H:%M:%S')
                        data_end = datetime.strptime(table_info['data_end_time'], '%Y-%m-%d %H:%M:%S')
                        # 检查时间范围是否有交集
                        if user_start <= data_end and user_end >= data_start:
                            return case['case_path']
    return None
```

**使用场景**：
- `get_offline_case_list_by_index`：获取某设备的所有案例列表
- `get_case_by_device_and_time`：按数据时间范围查找案例（返回第一个匹配的）

**搜索函数实现**：

`get_case_by_device_and_time` 按数据时间范围匹配案例：

```python
def get_case_by_device_and_time(profile: str, device_id: str, start_time: str = None, end_time: str = None):
    """根据数据时间范围查找案例路径

    用户在可视化界面选择数据时间范围，查找包含该时间范围数据的案例。
    时间范围匹配规则：[user_start, user_end] 与 [data_start, data_end] 有交集即可。

    Args:
        profile: 厂区
        device_id: 设备ID
        start_time: 用户选择的开始时间（数据时间）
        end_time: 用户选择的结束时间（数据时间）

    Returns:
        str: 案例路径 或 None（返回第一个匹配的案例）
    """
```

**⚠️ 重要：参数设计必须基于真实目录结构，与用户交互确认**

**不能预设参数模板**，必须按照以下流程：

```
Step 1: 查看用户实际的案例索引目录
  命令: ls -la .model-eval/{env}/cases/（或用户指定的路径）

Step 2: 分析真实目录层级
  例如实际结构: .model-eval/{env}/cases/lv1p3/3615/20251010_090000/
  则参数可能包含: profile=lv1p3, device_id=3615, case_id=20251010_090000

Step 3: 【交互确认】询问用户：
  "你的案例索引结构是 X/X/X，我建议 params 包含：
   - xxx
   - xxx

   这个设计是否符合你的业务场景？是否需要调整？"

Step 4: 根据用户反馈调整后，再实现代码
```

**原则**：
- 可视化（get_curve_data）不需要 `model_type`（曲线数据与模型类型无关）
- 推理（predict）需要 `model_type`（不同模型读取不同数据表）
- 参数应精简，只保留定位案例必需的字段
- **不要预设参数，必须基于真实目录结构**

---

**示例**（仅供参考，实际以用户目录为准）：

```python
def get_curve_data(x_axis=None, y_axis=None, params=None):
    # params 字段定义:
    # - device_id: 电解槽号 (类型: string, 必填)
    # - start_time: 开始时间 (类型: datetime, 可选，精确匹配案例)
    # - end_time: 结束时间 (类型: datetime, 可选)
    # - profile: 厂区 (类型: string, 可选，默认 lv1)
    # - time_range: 时间范围（仅实时模式需要）

    # 如果提供了 start_time，会精确匹配案例
    # 如果未提供，自动匹配最新案例
```

#### 2. get_curve_data 返回值说明

**重要**：`get_curve_data` 必须直接返回数组，不能返回包含额外字段的对象：

```python
# ✅ 正确：直接返回数组
def get_curve_data(x_axis=None, y_axis=None, params=None):
    # ... 获取数据逻辑 ...
    return df.to_dict(orient='records')
```

**case_path 和 case_pattern 的应用场景**：

这两个字段不需要在 `get_curve_data` 返回值中携带。应用流程如下：

1. **可视化阶段**：`get_curve_data(device_id=3813)` → 前端收到曲线数组 → 渲染图表

2. **保存测试用例时**：从 `params` 中提取 `device_id`、`profile`、`model_type` 等，保存为 `raw_input.filterParams`

3. **推理阶段（predict）**：从 `raw_input.filterParams` 获取 `device_id` 等参数，调用 `get_case_by_device_and_time(profile, device_id, target_time)` 重新查找 `case_path`，然后加载推理数据执行预测

```
get_curve_data(params) → 图表渲染
     ↓
测试用例保存: filterParams = {device_id, profile, model_type}
     ↓
predict(input_data) → 从 filterParams 重新查找 case_path → 执行推理
```

**简而言之**：
- `get_curve_data` 只负责返回曲线数据数组
- `case_path` 的查找逻辑在 `predict` 函数中实现（通过 `get_case_by_device_and_time`）

**可视化呈现最佳实践**（重要）：

`get_curve_data` 返回的每条数据应包含可视化配置中 `series` 配置的**所有字段**，而不是只返回 x_axis 和 y_axis：

```python
# 错误：只返回 x_axis 和 y_axis
result_data.append({
    x_axis: str(row[x_axis]),
    y_axis: float(row[y_axis])
})

# 正确：读取 viz 配置，返回 series 中的所有字段
from model_eval_cli.config.paths import get_viz_config_path
series_fields = [x_axis]
viz_config = json.load(open(get_viz_config_path()))
for chart in viz_config['charts']:
    for series in chart['series']:
        if series['point_name'] not in series_fields:
            series_fields.append(series['point_name'])

for _, row in df.iterrows():
    point = {}
    for field in series_fields:
        if field in df.columns:
            point[field] = float(row[field]) if pd.notna(row[field]) else None
    result_data.append(point)
```

**原因**：前端 Dashboard 的 series 配置了多个字段（如 potVolt、settingVolt、potCurrent 等），需要一次性返回所有字段用于图表渲染和数据标注。如果只返回部分字段，前端将无法正确显示图表。

#### 3. al_predict 自动查找案例路径

根据测试用例的过滤条件自动查找案例：

```python
def al_predict(input_data):
    # 从 raw_input 中提取过滤条件
    if 'raw_input' in input_data:
        raw = input_data.get('raw_input', {})
        filter_params = raw.get('filterParams', {})
        device = filter_params.get('device_id')
        start_time = filter_params.get('start_time')  # 可选，精确匹配
        end_time = filter_params.get('end_time')       # 可选
        profile = input_data.get('profile', 'lv1')
        model_type = input_data.get('model_type', 'nb')

    # 自动查找案例路径（支持 start_time 精确匹配）
    case_path = get_case_by_device_and_time(profile, device, target_time=start_time)

    # 加载推理数据
    predict_data = get_predict_data({'case_path': case_path, 'model_type': model_type})

    # 执行推理
    ...
```

**关键点**：
- 如果提供了 start_time，会精确匹配对应时间段的案例
- 如果未提供 start_time，自动查找该设备的最新案例

### 工作流程

```
┌─────────────────┐
│  反馈/标注阶段  │
│ get_curve_data │
│ (device_id=3813)│
│ start_time=xxx │
│ end_time=xxx   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│ 返回曲线数据 + case_path    │
│ {data: [...], case_path: ..}│
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  保存为测试用例             │
│  raw_input.filterParams    │
│  保存 device_id, start_time │
│  end_time (可选)            │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  测试执行阶段               │
│  al_predict(raw_input)    │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  自动查找案例路径           │
│  get_case_by_device_and_  │
│  time(profile, device_id,  │
│  target_time=start_time)   │
│  支持精确匹配或最新案例     │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  加载 predict 数据         │
│  get_predict_data          │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  执行推理，返回结果         │
└─────────────────────────────┘
```

### 参数设计要点

1. **get_curve_data 的 params**（与 case_index pattern 一致）：
   - `device_id`: 电解槽号 (类型: string, 必填)
   - `start_time`: 开始时间 (类型: datetime, 必填)
   - `end_time`: 结束时间 (类型: datetime, 必填)
   - `profile`: 厂区 (类型: string, 可选，默认 lv1p3)

**⚠️ 重要**：
- `start_time` 和 `end_time` 是**必填**参数，用于精确定位案例
- 不需要 `time_range`，实时和离线模式都统一使用 `start_time` 和 `end_time`
- 案例路径格式: `{profile}/{device_id}/{start_time}_{end_time}/`

### 关键点总结

1. **无需修改 CLI**：所有逻辑在 wrapper 函数中实现
2. **配置化**：`case_index` 配置定义目录结构
3. **自动关联**：测试用例只需保存 device_id，自动匹配最新案例
4. **数据分离**：曲线数据（curve）和推理数据（predict）分开引用
5. **参数简化**：params 不需要 start_time/end_time，每个案例对应固定时间点
6. **智能匹配**：根据 device_id 自动查找该设备的最新案例
7. **返回数组**：get_curve_data 直接返回数组，不包装对象，不返回 case_path
8. **OUTPUT_SCHEMA / PARAMS_SCHEMA**：使用显式类属性替代 docstring 解析

## Web Dashboard

> **重要**：启动 Dashboard 之前，必须先 Clone model_eval_cli 项目到本地（见上文「前置条件」部分）。仅 pip 安装无法启动前端。

启动 Dashboard 后访问:

- Frontend: http://localhost:3939
- Backend API: http://localhost:2525

功能:
- 查看测试结果和历史记录
- 管理反馈和标注
- 可视化评估曲线
- 创建和编辑测试用例
- 实时查看测试运行进度
