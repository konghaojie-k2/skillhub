# 数据 schema 说明

本文档说明 `.model-eval/test-runs/` 和 `.model-eval/testcases/` 目录下的 JSON 文件结构。LLM 应**动态探索**实际数据字段，而非依赖预设的业务知识。

---

## 核心原则：动态发现

**不要假设**数据中有哪些字段。应该：
1. 先读取 JSON 文件
2. 观察实际存在的字段
3. 根据发现的字段生成分析报告

---

## 一、Test Run 文件结构

**文件路径**: `.model-eval/test-runs/{run_id}.json`

### 常见顶层字段（动态检查）

读取后检查这些字段是否存在：
- `id` - 测试运行ID
- `test_purpose` - 测试目的（可能不存在）
- `tester` - 测试人员（可能不存在）
- `status` - 状态
- `started_at/completed_at` - 时间戳
- `duration_seconds` - 总耗时
- `total_count/passed_count/failed_count/pass_rate` - 统计信息

### Results 数组

每个 result 通常包含：
- `test_case_id` - 关联的测试用例ID
- `is_passed` - 是否通过（true/false）
- `error_message` - 错误信息（失败时）
- `execution_time_ms` - 执行时间
- `actual_output` - **模型输出（对象，字段不固定）**
- `expected_output` - **期望输出（对象，字段不固定）**

**重要**: `actual_output` 和 `expected_output` 的字段因模型而异，必须动态读取。

---

## 二、Test Case 文件结构

**文件路径**: `.model-eval/testcases/{test_case_id}.json`

### 常见字段（动态检查）

- `id` - 测试用例ID
- `model_type` - 模型类型
- `group` - 分组
- `tags` - 标签数组
- `status` - 状态
- `expected_output` - 期望输出（对象）
- `raw_input` - 原始输入（可能包含图表配置和时序数据）

### Raw Input 中的图表数据（如果存在）

如果 `raw_input.chart` 存在：
```json
{
  "chart": {
    "title": "图表标题",
    "x_axis": {"field": "x轴字段", "label": "标签"},
    "y_axis": {"field": "y轴字段", "label": "标签", "min": 最小值, "max": 最大值},
    "series": [
      {
        "point_name": "数据字段名",
        "label": "显示名称",
        "color": "#颜色代码",
        "type": "line/bar",
        "y_axis_index": 0
      }
    ]
  },
  "data": [
    {"timestamp": "2024-01-01 00:00:00", "field1": 100, "field2": 200}
  ]
}
```

**重要**: 图表字段名（如 `point_name`）和数据字段（如 `timestamp`）因业务而异，必须从实际 JSON 中读取。

---

## 三、数据分析方法

### 1. 探索数据字段

```python
# 读取 Test Run
with open(f'.model-eval/test-runs/{run_id}.json', 'r') as f:
    test_run = json.load(f)

# 查看顶层字段
print("顶层字段:", list(test_run.keys()))

# 查看 results 结构
if 'results' in test_run and len(test_run['results']) > 0:
    sample_result = test_run['results'][0]
    print("result 字段:", list(sample_result.keys()))
    
    # 查看 actual_output 字段（因模型而异）
    if 'actual_output' in sample_result:
        print("actual_output 字段:", list(sample_result['actual_output'].keys()))
```

### 2. 统计分析维度

根据发现的字段，从以下维度分析：

| 分析维度 | 需要检查的字段 | 生成的图表 |
|---------|--------------|-----------|
| 整体通过率 | `is_passed` | 饼图/柱状图 |
| 执行性能 | `execution_time_ms` | 分布直方图 |
| 模型置信度 | `actual_output` 中的数值字段 | 分布图/箱线图 |
| 错误类型 | `error_message` | 错误分类饼图 |
| 分组统计 | `model_type`, `group`, `tags` | 分组对比图 |
| 时间趋势 | `started_at`, `execution_time_ms` | 趋势折线图 |

### 3. 动态生成图表

不要预设字段名，而是：

```python
# 错误示例（预设字段）
confidence = result['actual_output']['confidence_score']  # 可能不存在！

# 正确做法（动态检查）
actual = result.get('actual_output', {})
numeric_fields = [k for k, v in actual.items() if isinstance(v, (int, float))]
# 然后选择适合的字段分析
```

---

## 四、报告各章节的数据使用建议

### 测试结论摘要
- **数据来源**: `pass_rate`, `total_count`, `passed_count/failed_count`
- **分析方法**: 对比基准和当前的通过率变化
- **必须包含**: 具体数字（如"通过率从85%下降到70%"）

### 测试概述
- **数据来源**: `test_purpose`, `tester`, `started_at`, `duration_seconds`
- **分析方法**: 总结测试背景和规模

### 测试结果详情
- **数据来源**: `results[]`
- **分析方法**: 
  - 统计通过/失败分布
  - 按 `error_message` 归类错误
  - 如果有分组字段（如 `model_type`），按分组统计
- **必须包含**: 详细数据表格

### 对比分析
- **数据来源**: 两个 Test Run 的对比
- **分析方法**:
  - 对比 `pass_rate`
  - 对比各分组的通过率
  - 如果有数值字段（如置信度），对比分布变化

### 专项分析
- **数据来源**: `actual_output` 中的数值字段
- **分析方法**:
  - 分析数值分布（均值、中位数、异常值）
  - 分析数值与 `is_passed` 的相关性
  - 如果发现规律（如"置信度低的容易失败"），深入分析

### 典型案例分析
- **数据来源**: 失败的 `results[]` 和对应的 `testcases`
- **分析方法**:
  - 选择2-3个有代表性的失败用例
  - 如果有 `raw_input.chart`，渲染时序图
  - 分析失败原因（结合 `error_message` 和 `actual_output`）

### 问题与改进建议
- **数据来源**: 前述分析的结论
- **分析方法**: 归纳发现的问题，给出可操作的改进建议

---

## 五、图表渲染原则

### 必须渲染的图表类型

1. **通过率分布图**
   - 类型: 饼图或柱状图
   - 数据: 通过数 vs 失败数

2. **性能分布图**（如果 `execution_time_ms` 存在）
   - 类型: 直方图
   - 数据: 执行时间分布

3. **数值字段分布图**（如果 `actual_output` 中有数值字段）
   - 类型: 直方图或箱线图
   - 数据: 数值字段的分布

4. **失败用例图表**（如果失败用例有 `raw_input.chart`）
   - 类型: 时序曲线图
   - 数据: 按 `chart` 配置渲染

5. **对比图**（如果提供了基准测试）
   - 类型: 对比柱状图或并排饼图
   - 数据: 当前 vs 基准的关键指标

### 图表渲染步骤

```python
# 1. 读取数据
with open(f'.model-eval/testcases/{test_case_id}.json', 'r') as f:
    testcase = json.load(f)

# 2. 检查是否存在图表配置
raw_input = testcase.get('raw_input', {})
if 'chart' not in raw_input or 'data' not in raw_input:
    print("该用例无图表数据")
    return

chart = raw_input['chart']
data = raw_input['data']

# 3. 动态读取字段
print(f"图表标题: {chart.get('title', '未命名')}")
print(f"X轴字段: {chart.get('x_axis', {}).get('field', '索引')}")
print(f"数据字段: {list(data[0].keys()) if data else []}")

# 4. 根据 series 配置绘制
for series in chart.get('series', []):
    field = series.get('point_name')
    if field and field in data[0]:
        values = [d[field] for d in data]
        plt.plot(values, label=series.get('label', field))

plt.legend()
plt.savefig(f'chart_{test_case_id}.png')
```

---

## 六、常见反模式

❌ **不要预设字段名**：
```python
# 错误
action = result['actual_output']['action']
confidence = result['actual_output']['confidence_score']
```

✅ **要动态检查**：
```python
# 正确
actual = result.get('actual_output', {})
available_fields = list(actual.keys())
# 根据实际存在的字段分析
```

❌ **不要假设业务含义**：
```python
# 错误：假设 action 的含义
if action == "-1":
    meaning = "降电压"  # 可能不是电压！
```

✅ **要基于数据描述**：
```python
# 正确：根据数据说明
print(f"模型输出 action={action}，期望值为 {expected}")
# 让读者自己理解业务含义
```

---

## 总结

**核心原则**: 
1. **读取先于假设** - 先读JSON，看有什么字段
2. **动态而非静态** - 根据实际字段生成分析
3. **通用而非特定** - 不绑定特定业务场景
4. **数据说话** - 让数据自己呈现规律，而非强加解释
