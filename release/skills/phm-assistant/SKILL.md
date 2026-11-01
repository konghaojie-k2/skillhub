---
name: phm-assistant
description: 'PHM（故障预测与健康管理）算法 Setup 助手。交互式生成可部署的 PHM 算法代码框架，支持数据清洗、工况切分、模型训练、偏差分析、健康评分、诊断报告等模块。输出 Python 代码 + YAML 配置，而非实时数据处理。'
version: 0.2.0
last_updated: 2026-03-17
changelog:
  - "v0.2.0: 拆分为多文件结构，新增 phm_tools 工具集"
  - "v0.1.1: 删除重复的 Step 2，添加版本信息"
  - "v0.1.0: 初始版本"
metadata:
  {
    "openclaw": { "emoji": "🏭", "requires": { "anyBins": ["python"] } },
    "domain": "industrial-iot",
    "interaction_mode": "interactive",
    "output_type": "deployable_code"
  }
---

# PHM 助手 - 故障预测与健康管理算法 Setup 助手

## 技能定位

| 维度 | 定位 |
|------|------|
| **角色** | 算法代码生成助手，而非实时数据处理系统 |
| **输入** | 离线数据样本 + 设备信息 + 业务需求 |
| **输出** | **可部署的 PHM 算法代码** + 配置文件 |
| **交互** | 交互式，每步确认后继续 |
| **场景** | 离线数据分析、算法框架搭建 |

## 核心流程 (7 阶段)

```
Phase 0: 前置条件检查 ⭐ (Pre-Flight Check)
  ├── 数据可用性检查 (文件/格式/数据量)
  ├── 设备信息检查 (类型/层级/映射)
  ├── 测点类型检查 (观测量/因子量)
  ├── 业务规则检查 (阈值/工况定义)
  └── 环境准备检查 (Python/依赖/输出目录)

Phase 1: 数据准备 (DataPreparation)
  ├── 数据清洗 (去噪、填充、异常值)
  ├── 工况切分 ⭐ (threshold/clustering/rule)
  ├── 工况识别 (暂态/稳态)
  └── 特征工程 (时域、频域、工况特征)

Phase 2: 基准模型训练 (BaselineTraining)
  ├── 工况选择器 (单/多工况)
  ├── 模型训练 (sklearn/xgboost/pytorch)
  ├── 模型评估 (R²/F1/MAPE)
  └── 模型打包 (pkl + config.yaml)

Phase 3: 偏差分析 (DeviationAnalysis)
  ├── 动态阈值计算 (UL/LL)
  ├── 指标偏差计算 (out_ratio/bias/variance)
  └── 指标评价 (简单阈值/SPC)

Phase 4: 综合评价 (ComprehensiveEval) ⭐
  ├── 部件评分 (指标分 → 部件分) - 基于 hierarchy 配置
  ├── 设备评分 (部件分 → 设备分) - 加权聚合
  └── 预警触发 (pre_alarm)

Phase 5: 诊断分析 (DiagnosticAnalysis) ⭐
  ├── 部件定位 (反查异常部件) - 基于 hierarchy 映射
  ├── 指标定位 (反查异常指标) - 定位到具体测点
  └── 根因分析 (LLM + 知识库)

Phase 6: 代码生成 ⭐
  ├── 生成 Python 模块
  ├── 生成 YAML 配置
  ├── 生成 requirements.txt
  └── 生成部署文档
```

## 使用场景

**适合使用**：
- [ ] 需要为工业设备搭建 PHM 算法框架
- [ ] 有离线数据样本，需要分析并生成代码
- [ ] 需要可部署、可维护的算法代码
- [ ] 需要交互式定制每个环节

**不适合使用**：
- [ ] 需要实时处理数据流
- [ ] 已有成熟的 PHM 平台只需调用 API
- [ ] 只需一次性分析报告而非代码
- [ ] 需要后台大数据处理能力

## Phase 0: 前置条件检查

**详细说明**: 见 [phases/phase0-check.md](phases/phase0-check.md)

**所需工具/脚本**:
```
phm_tools/
├── check_data.py          # 数据可用性检查脚本
├── check_device.py        # 设备信息检查脚本
├── check_metrics.py       # 测点类型分析脚本
├── check_env.py           # 环境准备检查脚本
└── preflight_check.py     # 统一入口 (调用上述脚本)
```

**检查流程**: 调用 `phm_tools/preflight_check.py` 执行实际验证

## 交互式引导流程

### Step 1: 设备信息收集

```
🏭 PHM 助手：我来帮你搭建 PHM 算法框架

首先，了解一下你的设备：

1. 设备类型是什么？(如：离心泵、电机、压缩机)
2. 设备 ID/名称是什么？
3. 有哪些关键测点？(如：振动、温度、压力、转速)
4. 采样率是多少？(如：1Hz、10Hz、1kHz)
5. 数据格式是什么？(CSV/Excel/数据库/其他)
```

### Step 1.5: 设备层级结构配置

详细说明: 见 [phases/phase4-model.md](phases/phase4-model.md)

### Step 1.6: 测点类型区分

详细说明: 见 [phases/phase4-model.md](phases/phase4-model.md)

### Step 2: 数据分析

详细说明: 见 [phases/phase2-analysis.md](phases/phase2-analysis.md)

### Step 3: 工况切分配置

详细说明: 见 [phases/phase3-workcond.md](phases/phase3-workcond.md)

### Step 4: 模型配置

详细说明: 见 [phases/phase4-model.md](phases/phase4-model.md)

### Step 5: 报警规则配置

详细说明: 见 [phases/phase5-deviation.md](phases/phase5-deviation.md)

### Step 6: 知识库配置

详细说明: 见 [phases/phase6-health.md](phases/phase6-health.md)

### Step 7: 生成代码

详细说明: 见 [phases/phase7-report.md](phases/phase7-report.md)

## 设备层级结构详解

详细说明: 见 [phases/phase4-model.md](phases/phase4-model.md)

## 决策检查点

每个阶段 Agent 需要询问用户：

### Phase 0: 前置条件检查
- [ ] 数据文件是否存在？格式是否可读？
- [ ] 数据量是否足够？时间范围是否合理？
- [ ] 设备类型是否明确？设备 ID 是什么？
- [ ] 设备层级结构是否已知？(部件列表)
- [ ] 测点 - 部件映射是否已知？
- [ ] 哪些测点是观测量？哪些是因子量？
- [ ] 报警阈值是否已知？工况定义是否明确？
- [ ] Python 环境是否就绪？输出目录是否可写？

### Phase 1: 数据准备
- [ ] 设备类型和关键测点是什么？
- [ ] 采用哪种工况切分方法？
- [ ] 关键工况信号是什么？
- [ ] 数据清洗策略？(空值/异常值处理)

### Phase 2: 模型训练
- [ ] 目标量和因子量是什么？
- [ ] 模型类型选择？
- [ ] 评估指标和阈值？

### Phase 3: 偏差分析
- [ ] 评价规则？(简单阈值/SPC)
- [ ] 允许偏差 δ 是多少？

### Phase 4: 综合评价
- [ ] 聚合方法？(weighted_avg / min / custom)
- [ ] 报警阈值是多少？

### Phase 5: 诊断分析
- [ ] 有领域知识库吗？
- [ ] 需要 LLM 增强根因分析吗？

## 输出代码结构

详细说明: 见 [phases/phase7-report.md](phases/phase7-report.md)

## 工具关联说明

### Agent 如何调用检查工具？

```bash
# 方式 1: 直接运行检查脚本
python phm_tools/preflight_check.py \
  --data pump_data.csv \
  --device-type centrifugal_pump \
  --device-id pump_001 \
  --output-dir ./phm_pump_001

# 方式 2: Agent 调用检查函数
from phm_tools import run_preflight_check
report = run_preflight_check(
    user_input={"device_type": "centrifugal_pump", "device_id": "pump_001"},
    data_file="pump_data.csv",
    output_dir="./phm_pump_001"
)
```

## 扩展计划

- [ ] 支持更多模型后端 (LightGBM, CatBoost)
- [ ] 支持深度学习模型 (LSTM, Transformer)
- [ ] 自动化特征工程
- [ ] 模型自动调参
- [ ] 可视化 Dashboard 生成
