# Phase 0: 前置条件检查 (Pre-Flight Check)

## 目的

在开始分析前，系统性地确认所有必要前提条件是否存在。**必须调用检查工具/脚本执行实际验证，而非仅靠问答**。

## 检查清单

### 1. 数据可用性检查

| 检查项 | 要求 | 严重程度 |
|--------|------|----------|
| 数据文件是否存在 | CSV/Excel/数据库连接 | 🔴 严重 |
| 数据格式是否可读 | 支持的格式 | 🔴 严重 |
| 数据量是否足够 | 建议 > 1000 行 | 🟡 中等 |
| 时间范围是否合理 | 建议 > 7 天 | 🟡 中等 |
| 缺失值比例是否可接受 | < 10% | 🟡 中等 |

### 2. 设备信息检查

| 检查项 | 要求 | 严重程度 |
|--------|------|----------|
| 设备类型是否明确 | 离心泵/电机/压缩机... | 🔴 严重 |
| 设备 ID/名称是否已定义 | 唯一标识 | 🟡 中等 |
| 设备层级结构是否已知 | 部件列表 | 🟡 中等 |
| 测点-部件映射是否已知 | 映射关系 | 🟡 中等 |

### 3. 测点类型检查

| 检查项 | 要求 | 严重程度 |
|--------|------|----------|
| 观测量 (target) 是否已识别 | 健康指标 | 🟡 中等 |
| 因子量 (factors) 是否已识别 | 工况参数 | 🟡 中等 |
| target-factor 映射关系是否已知 | 建模关系 | 🟡 中等 |
| 关键测点的物理意义是否明确 | 领域知识 | 🟢 可选 |

### 4. 业务规则检查

| 检查项 | 要求 | 严重程度 |
|--------|------|----------|
| 报警阈值是否已知 | 或可从历史数据学习 | 🟢 可选 |
| 工况定义是否明确 | 停机/低负载/高负载 | 🟡 中等 |
| 工况切分方法是否已选择 | threshold/clustering/rule | 🟡 中等 |
| 领域知识库是否存在 | 根因分析用 | 🟢 可选 |

### 5. 环境准备检查

| 检查项 | 要求 | 严重程度 |
|--------|------|----------|
| Python 环境是否就绪 | Python 3.9+ | 🔴 严重 |
| 依赖库是否安装 | pandas/sklearn/xgboost... | 🔴 严重 |
| 输出目录是否可写 | 写入权限 | 🔴 严重 |

## 检查脚本使用

### 调用方式

```python
# 方式 1: 命令行调用
from phm_tools import run_preflight_check

result = run_preflight_check(
    user_input={
        "device_type": "centrifugal_pump",
        "device_id": "pump_001",
        "hierarchy": {...}
    },
    data_file="pump_data.csv",
    output_dir="./phm_pump_001"
)

# 方式 2: 直接调用各检查脚本
from phm_tools.check_data import check_data_availability
from phm_tools.check_device import check_device_info
from phm_tools.check_metrics import check_metric_types
from phm_tools.check_env import check_environment
```

### 检查结果处理

| 缺失项 | 严重程度 | 处理策略 |
|--------|----------|----------|
| 数据文件 | 🔴 严重 | 无法继续，请用户提供 |
| 设备类型 | 🔴 严重 | 无法继续，请用户确认 |
| 部件列表 | 🟡 中等 | 基于领域知识推荐，用户确认 |
| 测点类型 | 🟡 中等 | 基于数据分析推荐，用户确认 |
| 报警阈值 | 🟢 可选 | 从历史数据学习或采用默认值 |
| 知识库 | 🟢 可选 | 生成默认知识库，用户补充 |

## 询问话术示例

```
🔍 前置条件检查开始...

【数据检查】✅ 通过
- 数据文件：pump_data.csv (存在)
- 数据量：100,000 行 (充足)
- 时间范围：11 天 (合理)
- 缺失值：2.3% (可接受)

【设备信息】⚠️ 部分缺失
- 设备类型：离心泵 ✅
- 设备 ID: pump_001 ✅
- 部件列表：❌ 缺失 → 需要确认
- 测点-部件映射：❌ 缺失 → 需要确认

【测点类型】⚠️ 部分缺失
- 观测量：❌ 缺失 → 需要确认
- 因子量：❌ 缺失 → 需要确认
- target-factor 映射：❌ 缺失 → 需要确认

【业务规则】⚠️ 部分缺失
- 报警阈值：可从历史数据学习 ✅
- 工况定义：❌ 缺失 → 需要确认

【环境检查】✅ 通过
- Python 3.11 ✅
- 依赖库：pandas/sklearn/xgboost ✅
- 输出目录：./phm_pump_001/ ✅

━━━━━━━━━━━━━━━━━━━━━━━
📋 检查结果：部分缺失 (可继续)

需要补充的信息：
1. 设备有哪些部件？
2. 每个测点归属哪个部件？
3. 哪些测点是观测量？哪些是因子量？
4. 工况如何定义？(停机/低负载/高负载的阈值)

我将引导你逐步确认这些信息。准备好了吗？
```

## 详细检查函数

### check_data.py

```python
def check_data_availability(file_path: str) -> Dict:
    """
    数据可用性检查工具

    执行:
    - 文件是否存在
    - 格式是否可读 (尝试读取)
    - 数据量统计
    - 时间范围分析
    - 缺失值计算
    - 异常值检测

    返回:
    {
        "passed": bool,
        "file_exists": True,
        "row_count": 100000,
        "time_range": ("2026-03-01", "2026-03-11"),
        "missing_ratio": 0.023,
        "issues": ["temperature 有 2.3% 缺失"],
        "recommendations": ["建议插值填充 temperature"]
    }
    """
    pass
```

### check_device.py

```python
def check_device_info(user_input: dict, data: pd.DataFrame) -> Dict:
    """
    设备信息检查工具

    执行:
    - 设备类型确认
    - 设备 ID 确认
    - 基于领域知识推荐部件列表
    - 测点-部件映射推荐

    返回:
    {
        "passed": bool,
        "device_type": "centrifugal_pump",
        "device_id": "pump_001",
        "recommended_hierarchy": {...},
        "missing": ["部件列表", "测点-部件映射"],
        "recommendations": ["建议确认部件列表"]
    }
    """
    pass
```

### check_metrics.py

```python
def check_metric_types(data: pd.DataFrame, device_type: str) -> Dict:
    """
    测点类型分析工具 - 智能推荐观测量和因子量

    执行:
    - 基于领域知识推荐
    - 相关性分析
    - 变化模式分析
    - 生成 target-factor 映射建议

    返回:
    {
        "recommended_targets": [...],
        "recommended_factors": [...],
        "correlation_matrix": {...},
        "target_factor_mapping": {...}
    }
    """
    pass
```

### check_env.py

```python
def check_environment(output_dir: str) -> Dict:
    """
    环境准备检查工具

    执行:
    - Python 版本检查
    - 依赖库检查
    - 输出目录权限检查

    返回:
    {
        "passed": bool,
        "python_version": "3.11.0",
        "dependencies": {...},
        "output_dir_writable": True
    }
    """
    pass
```

### preflight_check.py

```python
def run_preflight_check(user_input: dict, data_file: str, output_dir: str) -> Dict:
    """
    Phase 0 前置条件检查 - 统一入口

    调用上述所有检查脚本，生成综合报告

    返回:
    {
        "passed": bool,
        "checks": {...},
        "summary": "...",
        "next_steps": [...]
    }
    """
    pass
```
