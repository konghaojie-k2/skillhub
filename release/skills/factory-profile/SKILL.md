---
name: factory-profile
description: 多工厂画像对比工作流。输入 N 个工厂的 state CSV + setpoint zip，输出 5 维度画像、对比判定、待工艺方确认的问题清单。当用户提到"对比工厂画像""多厂对比""工厂 portrait""portrait 对比"时触发。
---

# Factory Profile: 多工厂画像对比

## 用途

对 N 个工厂, 用统一画像方法提取每厂的"状态 / 行为 / 物理影响"分布, 然后两两对比, 输出"两厂是否同质"的统计判定 + 给工艺方的待办问题。

**核心价值**: 回答"同一套 AI 模型能不能跨厂推广"——这是 AI 工厂模型部署前的必做分析。

## 何时使用

- AI 模型计划在多个厂推广, 想知道哪些厂可以共享模型 / 哪些要 per-factory 适配
- 工艺方想了解两厂的操作风格和物理机制差异
- 工厂间发生异常, 想对比画像定位差异

## 输入

每个工厂需要 2 个数据源:
1. **状态数据**: `<profile>_state_vars.csv`, 列名约定见下
2. **干预数据**: `<profile>_prod_dws_setpoint_change_<date_range>.zip` 内含 CSV

**列名约定** (11 个状态变量):
```
k_device, k_ts, 温度, 分子比, 实际氟盐加料量, 下料量,
电压残差, 针振, 吸出铝量, 基准下料间隔,
工作电压, 效应电压, 浓度（斜率）
```
前 2 列是 ID 和时间, 后 11 列是特征。

**干预数据列**:
```
k_device, k_ts, k_sp, delta, direction
```
k_sp 是动作类型 (下料间隔 / 设定电压 / 氟盐重量 / 计划出铝)

## Workflow (5 步)

按顺序执行, 每步输出 JSON, 供下一步使用。

### 步骤 1: 状态画像

**脚本**: `experiments/factory-profile/06_state_profile.py`
**改这里换数据**:
```python
DATA_SOURCES = {
    "factory_a": {
        "state_csv": Path(r"path/to/factory_a_state_vars.csv"),
    },
    "factory_b": {
        "state_csv": Path(r"path/to/factory_b_state_vars.csv"),
    },
}
```
**输出**: `output/<factory>_state_profile.json`, 含:
- `marginal`: 11 变量分布 (mean/std/percentiles/skewness)
- `quality`: 每变量 flag (usable / suspect / unusable)
- `correlation`: 11x11 相关矩阵
- `time_windows`: 按月切分的子画像
- `data_issues`: 稀疏/缺失月检测

### 步骤 2: 行为画像 (含转移链)

**脚本**: `experiments/factory-profile/07_action_profile.py`
**输出**: `output/<factory>_action_profile.json`, 含:
- `action_freq`: 动作频率分布
- `action_delta`, `action_direction`: 调整幅度和方向
- `transition_matrix`: 4x4 P(next|prev)
- `conditional_chains`: P(next | prev, var, low/high 桶) (88 cells)
- `interval_dist`, `daily_intensity`: 节奏统计
- `time_windows`, `data_issues`

### 步骤 3: 状态变化 (纯描述)

**脚本**: `experiments/factory-profile/08_result_profile.py`
**输出**: `output/<factory>_result_profile.json`, 含:
- `by_action.<action>.delta_by_var.<var>`: 后 3d - 前 3d 窗口均值差
- **不下"好/坏"判定**, 只描述事实
- `time_windows`, `data_issues`

### 步骤 4: 画像对比

**脚本**: `experiments/factory-profile/09_compare.py`
**自动**: 找出所有工厂对, 两两对比
**输出**: `output/<factory_a>_<factory_b>_comparison.json`, 含 5 维度对比:
- `marginal`: per-var 效应大小 (|Δmean|/pooled_std)
- `quality`: 两厂 flag 矩阵
- `correlation`: top 5 相关差异对
- `action.action_freq_diff`, `chain_diff`: 动作差异 + 转移差异
- `drift`: 月度样本数同步性
- `effect`: per (动作, 变量) 物理影响差异

### 步骤 5: 综合判定

**脚本**: `experiments/factory-profile/10_synthesize.py`
**输出**: `output/<pair>_synthesis.json`, 含:
- `overall.verdict`: 总体判定 (相同/部分相同/不同)
- `per_dimension`: 5 维各自判定
- `top_5_evidence`: 跨维度最强证据
- `data_quality`: 排除变量 + 稀疏月 + 可信度

判定阈值 (统计约定):
- marginal: same ≥80%, suspect 50-80%, different <50%
- structure: same <0.2, suspect 0.2-0.5, different >0.5
- behavior: same |Δfreq|<5%, suspect 5-15%, different >15%
- chains: same L1<0.10, suspect 0.10-0.20, different >0.20
- effect: same 0-4 不同对, suspect 5-14, different ≥15

总体: 1 维"不同"→部分相同; ≥2 维"不同"→不同; 否则"相同"

## 最终报告 (手写)

**不要用脚本生成**。脚本只能拼数据, 报告需要叙事+数据论证, **手工打磨**。

**报告位置**: `output/<pair>_report.md`

**报告结构 (9 节)**:

### 1. 结论 (3-4 句)
```
## 结论

**两厂在数据上判为「<overall>」。**

5 维判定: <逐维 判定>, ...

直接含义: 同一套 AI 模型<能否跨厂>。
```

### 2. 论点 1: 动作选择与节奏
- **1 张表**: 动作 / lv3p2 频率 / lv5p3 频率 / 差 / 判定
- **备注**: 干预节奏 + 快反比例 + 含义

### 3. 论点 2: 物理机制
- **1 张表**: 变量对 / r_lv3p2 / r_lv5p3 / Δr / 判定 (top 5)
- **备注**: 最显著对的方向相反 + 含义

### 4. 论点 3: 物理影响
- **1 张表**: 动作→变量 / Δ_lv3p2 / Δ_lv5p3 / 差 / 判定 (top 5)
- **备注**: 总差异对数 + 含义

### 5. 论点 4: 状态输入
- **1 张表**: 11 变量 / μ / σ / 可信度
- **备注**: 效应电压异常 + 含义

### 6. 论点 5: 链
- **2 张表**: 完整 4x4 转移矩阵 + 一个条件链具体 cell
- **关键观察**: 从数据里读出 2-3 条事实 (无叙事铺垫)

### 7. 数据质量
- 整体可信度
- 排除变量 (列表)
- 稀疏月 (列表)

### 8. 工艺方需确认的 5 个问题
针对异常点和关键差异, 列 5 个具体问题。

### 9. 重要声明
- 报告基于统计约定, 不含工艺知识
- 工艺含义 = 统计结论 + 工艺知识

## 报告写作原则

1. **数据论证, 不叙事铺垫**: 不要"普通 AI 只看...实际工艺里..."这类话, 直接展示数据让结论站住
2. **表格放事实, 备注放解读**: 数据 → 表格, 解释 → 备注
3. **不用"a 厂 b 厂"**: 用真实厂名 (lv3p2 / lv5p3)
4. **专业语气**: 不要"师傅""动手脚""嫌弃"等口语
5. **不改变事实**: 数字、判定、结论都来自 10_synthesize 输出, 不擅自修改

## 复用方法

**换数据** (新一组工厂):
1. 改 06/07/08 顶部的 `DATA_SOURCES`
2. 跑 `uv run python 06_state_profile.py` → `07` → `08` → `09` → `10`
3. **手写新报告**, 按上述 9 节结构
4. 报告保存为 `output/<新厂对>_report.md`

**判定阈值调整**: 改 `10_synthesize.py` 顶部常量

**新增维度**: 现状 5 维固定, 不建议添加; 如需添加, 应同步改 06/07/08/09/10 五个脚本

## 关联脚本

- 06: `experiments/factory-profile/06_state_profile.py`
- 07: `experiments/factory-profile/07_action_profile.py`
- 08: `experiments/factory-profile/08_result_profile.py`
- 09: `experiments/factory-profile/09_compare.py`
- 10: `experiments/factory-profile/10_synthesize.py`

## 业务背景参考

本 skill 的画像差异只有叠加工艺知识才能形成"可执行的工艺结论"，但工艺事实不内嵌在脚本里。原始资料放在外部 Markdown，路径如下：

- `C:\Users\17625\Desktop\项目资料\wq\doc\电解铝业务与数据背景_kimi_v2.md` — 数据集说明 + 工艺机制 + 11 变量含义
- `C:\Users\17625\Desktop\项目资料\wq\doc\铝电解工艺故障诊断事理知识体系.md` — 故障演变与工况扰动事理

精简后可直接被画像/报告引用的"业务事实子集"在：

- `references/business-context.md` — 字段管控区间、延迟时间尺度、控制输入 vs 状态输出、关键耦合、缺失率业务解释、跨厂注意事项

### 各资料对应到 skill 步骤的指引

| 步骤 | 涉及资料章节 | 用途 |
|------|--------------|------|
| 06 状态画像 | 业务背景第 1.1/2.4/3 节、事理知识一/二/三节 | 变量分类、缺失率业务解释（分子比 3/4 天采样）、状态时窗匹配（短时窗 vs 长时窗）|
| 07 行为画像 | 业务背景第 2.3/2.5 节 | 4 个动作归类（基准下料间隔/氟盐/出铝/设定电压为控制输入），节奏判读用工艺延迟时间尺度 |
| 08 状态变化 | 业务背景第 2.5.7 节、事理知识三节 | 默认 pre/post 3d 窗口与"设定电压偏快/氟盐中速/出铝偏慢"对照；效应/换极扰动期识别 |
| 09/10 判定 | 业务背景第 1.2/5.4 节 | 跨电流等级直接比较的注意事项、效应电压在 lv5p3 的异常可信度判定 |
| 报告写作 | 全文 | 备注里加"业务含义"小段：差异是工艺上的什么含义 |

**改动画像脚本的边界**：业务知识以"元数据"形式注入（meta.business_context 字段），不修改 5 维度的统计计算逻辑，确保判定阈值与历史输出一致。

**复用**：换数据源（其他铝厂、铜厂、钢厂等）时，业务知识需要重新整理；可直接复用 references/ 的目录结构与事实抽取模板。
