---
name: test-report-designer
description: 生成业务性测试报告。当用户明确要求"生成测试报告"、"生成智能报告"、"生成本次评估报告"时触发，且当前项目包含 .model-eval 目录。利用 LLM 能力生成深度分析的业务性报告（图片+表格+文字结合），渲染图表数据，调用 pdf skill 生成 PDF，并更新项目钩子函数。
tools: ["read", "write", "edit", "glob", "grep", "skill", "bash"]
---

# Test Report Designer

生成**业务性**测试报告，而非简单数据罗列。

## 核心原则

1. **LLM 深度分析** - 每个章节都有 LLM 的业务洞察
2. **全部读取数据** - 不能遗漏任何测试数据
3. **图表渲染** - 测试数据的图表要正确渲染并嵌入报告
4. **混合内容** - 图片+表格+文字结合
5. **.model-eval/smart-reports 目录输出** - 报告输出到 `.model-eval/smart-reports/` 目录（不是项目根目录）
6. **钩子函数更新** - 集成到项目的钩子函数

## 工作流程

```
0. 读取参考文档
1. 发现钩子函数
2. 读取全部测试数据
3. 交互获取测试目的
4. LLM 深度分析
5. 渲染图表（中文检测→渲染→嵌入）
6. 生成报告内容（按模板填充）
7. 质量验证（结构+内容深度）
8. 调用 pdf skill 生成 PDF
9. 输出到 .model-eval/smart-reports/ 目录
10. 更新钩子函数
```

---

## 详细步骤

### 0. 读取参考文档

**必须先执行**：
- `read: references/meta-framework.md` - 9章节结构要求（1个摘要+8个正文章节）
- `read: references/quality-standards.md` - 内容质量标准
- `read: references/data-schema.md` - **数据字段详细说明，必须读取以了解JSON结构**
- `read: references/skill-collaboration.md` - pdf调用接口

**重要**: 必须读取 data-schema.md 了解以下关键数据结构：
- Test Run 文件: `id`, `test_purpose`, `tester`, `pass_rate`, `results[]` 等
- Test Case 文件: `raw_input.chart` (图表配置), `raw_input.data[]` (时序数据), `expected_output`
- 业务指标: `potVolt` (槽电压), `action` (模型输出: -1/0/+1), `confidence_score` (置信度)

---

### 1. 发现钩子函数

搜索项目中的 `generate_smart_report` 函数：
- `glob: "**/*.py"` 找到所有 Python 文件
- `grep: "def generate_smart_report"` 搜索函数定义
- 如果未找到，在项目根目录创建 `model_eval_cli.py`

---

### 2. 读取全部测试数据

**必须读取**：

| 数据类型 | 路径 | 内容说明 |
|---------|------|----------|
| 基准测试 | `.model-eval/test-runs/{base_run_id}.json` | 包含 `pass_rate`, `results[]`, `total_count` 等 |
| 当前测试 | `.model-eval/test-runs/{test_run_id}.json` | 同上，用于对比分析 |
| 测试用例 | `.model-eval/testcases/*.json` | 包含 `raw_input.chart` (图表配置) 和 `raw_input.data[]` (时序数据) |

**动态探索数据字段**：

不要预设字段名！先读取数据，观察实际存在的字段：

```python
# 1. 读取 Test Run
with open(f'.model-eval/test-runs/{run_id}.json', 'r') as f:
    test_run = json.load(f)

# 2. 探索顶层字段
print("可用字段:", list(test_run.keys()))
# 常见字段: id, test_purpose, tester, status, started_at, duration_seconds
#           total_count, passed_count, failed_count, pass_rate, results[]

# 3. 探索 results 结构
if test_run.get('results'):
    sample = test_run['results'][0]
    print("result 字段:", list(sample.keys()))
    # 常见: test_case_id, is_passed, error_message, execution_time_ms, actual_output
    
    # 4. 探索模型输出字段（因模型而异！）
    if 'actual_output' in sample:
        print("模型输出字段:", list(sample['actual_output'].keys()))
        # 可能是: action, confidence, prediction, result, value 等
        # 类型可能是字符串、数字、布尔值或对象
```

**关键发现步骤**：
1. **统计信息**：检查 `pass_rate`, `passed_count`, `failed_count`, `total_count`
2. **模型输出**：检查 `actual_output` 中的字段，找出数值型字段（可用于分析置信度）
3. **错误信息**：检查 `error_message` 的存在和格式
4. **分组字段**：检查是否有 `model_type`, `group`, `tags` 等可用于分组统计

**Test Case 探索**：
```python
with open(f'.model-eval/testcases/{test_case_id}.json', 'r') as f:
    testcase = json.load(f)

# 探索结构
print("用例字段:", list(testcase.keys()))

# 检查是否有图表数据
if 'raw_input' in testcase:
    raw = testcase['raw_input']
    if 'chart' in raw and 'data' in raw:
        print("发现图表配置:", raw['chart'].get('title'))
        print("数据字段:", list(raw['data'][0].keys()) if raw['data'] else [])
        # 根据实际字段名渲染图表，不要预设！
```

**数据关联关系**：
```
Test Run (.model-eval/test-runs/{run_id}.json)
   │
   ├── 元信息: id, test_purpose, tester, started_at, duration_seconds...
   ├── 统计: total_count, passed_count, failed_count, pass_rate...
   │
   └── results[] ────────┐
        │                │
        ├── test_case_id ┤ (关联)
        ├── is_passed    │
        ├── error_message│
        └── actual_output│ (模型输出，字段因模型而异)
                         │
Test Case (.model-eval/testcases/{id}.json) ◄──┘
   │
   ├── expected_output (期望输出)
   └── raw_input
        ├── chart (图表配置，可能不存在)
        │    ├── title, x_axis, y_axis, series[]...
        │    └── 字段名需动态读取！
        └── data[] (时序数据)
             └── 字段因业务场景而异，必须动态探索
```

**重要提醒**: 
- 不要假设 `actual_output` 中有哪些字段
- 不要假设 `raw_input.data[]` 中的字段名
- 读取后打印字段列表，根据实际存在的字段分析

---

### 3. 交互获取测试目的

**必须通过交互获取**：
- 测试目的
- 基准版本定义
- 重点关注指标
- 业务假设（可选）

---

### 4. LLM 深度分析

根据 meta-framework.md 生成各章节内容。

**参考 quality-standards.md 中的深度标准**：
- 包含原因分析和业务意义
- 避免数据罗列
- 每章节至少3-4句分析

---
---

### 4.5 各章节内容格式要求

**重要**：每个章节必须结合【文字分析 + 数据表格 + 关键图表】，不能只有纯文字。

#### 测试结论摘要 (summary)
- **格式**：文字 + 1张关键指标可视化图
- **图表选择**（根据数据特点自行决定）：
  - 展示整体表现 → 通过率饼图/环形图
  - 展示趋势 → 对比柱状图/仪表盘图
- **内容**：
  - 核心发现1：XXX（引用具体数据，如"通过率下降15%"）
  - 核心发现2：XXX
  - 核心建议：XXX

#### 测试概述 (overview)
- **格式**：文字说明 + 信息表格
- **表格字段**：测试目的、测试范围、基准版本、测试时间、用例数量
- **必须包含表格**

#### 测试环境与配置 (environment)
- **格式**：文字 + 配置表格
- **表格字段**：软件名称、版本号、关键配置参数

#### 测试结果详情 (results)
- **格式**：【必须包含表格+图表】文字分析 + 详细数据表 + 分布可视化
- **表格要求**：
  - 列：测试用例ID、测试名称、状态、关键指标、错误信息
  - 分类汇总：按类型统计通过率
- **图表要求**（根据数据特点选择合适类型）：
  - 展示执行时间分布 → 直方图/箱线图/小提琴图
  - 展示错误类型分布 → 饼图/柱状图/树状图
  - 展示性能趋势 → 散点图/折线图
- **分析要点**：不要罗列所有用例，重点分析失败模式和规律

#### 对比分析 (comparison)
- **格式**：【必须包含表格+图表】对比表格 + 对比可视化
- **表格要求**：指标、基准值、当前值、变化率、分析
- **图表要求**（根据对比维度选择）：
  - 单指标对比 → 并排柱状图/箭头图
  - 多指标对比 → 雷达图/平行坐标图
  - 时间趋势对比 → 折线图/面积图
  - 分布对比 → 叠加密度图/箱线图对比

#### 专项分析 (deep_analysis)
- **格式**：文字深度分析 + 特征图表
- **图表要求**（根据发现的规律选择）：
  - 展示分类分布 → 饼图/柱状图/热力图
  - 展示数值分布 → 直方图/密度图/箱线图
  - 展示相关性 → 散点图/热力图
  - 展示时序规律 → 折线图/周期图

#### 典型案例分析 (cases)
- **格式**：案例卡片形式（背景、数据表现、分析、启示）+ 配图
- **图表要求**（如果测试用例有时序数据）：
  - 展示时序变化 → 多线折线图（实际值vs期望值）
  - 展示多维度 → 分面图/子图布局
  - 突出异常点 → 标注散点图
- **数量**：选择2-3个最具代表性的案例，每个案例配1张图

#### 问题与改进建议 (recommendations)
- **格式**：问题清单表格 + 改进建议
- **表格要求**：优先级、问题描述、影响范围、改进建议

#### 附录 (appendix)
- **格式**：链接列表
- **内容**：原始数据文件路径、测试用例目录、生成脚本

### 5. 渲染图表

**执行中文检测**：
```bash
python scripts/validate_font.py
```

**如果检测失败**：安装中文字体后再继续

#### 5.1 渲染汇总统计图表（必须）

**执行脚本**：
```bash
python scripts/render_charts.py --testrun .model-eval/test-runs/{test_run_id}.json --summary --output-dir .
```

**生成图表**（根据数据特点选择合适的图表类型）：

**汇总统计图表**（必须，1-3张）：
1. **整体表现图** - 展示通过率/成功率
   - 建议：饼图/环形图/仪表盘（选择最直观的）
   - 文件名：`chart_overview.png`

2. **性能分布图**（如果 execution_time_ms 存在）
   - 建议：根据分布特点选择（直方图/箱线图/小提琴图）
   - 文件名：`chart_performance.png`

3. **模型输出分析图**（如果 actual_output 中有数值字段）
   - 建议：根据数据特征选择（直方图/密度图/散点图）
   - 文件名：`chart_{field_name}.png`

**嵌入位置**：
- 通过率饼图 → **测试结论摘要** 章节
- 执行时间/性能分布 → **测试结果详情** 章节
- 模型输出数值分布 → **专项分析** 章节

#### 5.2 渲染失败用例图表（必须）

**执行脚本**：
```bash
python scripts/render_charts.py --testrun .model-eval/test-runs/{test_run_id}.json --failed-cases --testcases-dir .model-eval/testcases --output-dir .
```

**工作原理**：
1. 从 test-run 中找出 `is_passed=false` 的用例
2. 读取对应 test-case 中的 `raw_input.chart` 和 `raw_input.data`
3. 根据 chart 配置渲染时序曲线图
4. 生成 `chart_{test_case_id}.png`

**嵌入位置**：
- 失败用例图表 → **典型案例分析** 章节

#### 5.3 图表渲染示例（手动渲染单个用例）

如果脚本渲染不满足需求，可手动渲染：

```python
# 1. 读取测试用例
with open(f'.model-eval/testcases/{test_case_id}.json', 'r') as f:
    testcase = json.load(f)

# 2. 检查并提取图表配置（不要假设一定存在！）
raw_input = testcase.get('raw_input', {})
if 'chart' not in raw_input or 'data' not in raw_input:
    print("该用例无图表数据，跳过")
else:
    chart_config = raw_input['chart']
    data = raw_input['data']
    
    # 3. 动态探索数据字段
    print(f"图表标题: {chart_config.get('title', '未命名')}")
    print(f"可用数据字段: {list(data[0].keys()) if data else []}")
    
    # 4. 根据 series 配置绘制每条曲线（动态读取字段名）
    for series in chart_config.get('series', []):
        field = series.get('point_name')    # 动态获取字段名，不要预设！
        label = series.get('label', field)   # 使用配置的标签或字段名
        color = series.get('color', '#333')  # 使用配置的颜色或默认色
        
        # 检查字段是否存在
        if field and data and field in data[0]:
            values = [d[field] for d in data]
            
            # 获取X轴数据（可能是时间，也可能是索引）
            x_field = chart_config.get('x_axis', {}).get('field')
            if x_field and x_field in data[0]:
                x_values = [d[x_field] for d in data]
            else:
                x_values = range(len(values))  # 使用索引
            
            plt.plot(x_values, values, label=label, color=color)
        else:
            print(f"警告: 字段 '{field}' 不存在于数据中")
    
    # 5. 设置标题和标签
    plt.title(chart_config.get('title', '图表'))
    if chart_config.get('x_axis'):
        plt.xlabel(chart_config['x_axis'].get('label', 'X轴'))
    if chart_config.get('y_axis'):
        plt.ylabel(chart_config['y_axis'].get('label', 'Y轴'))
    
    plt.legend()
    plt.savefig(f'chart_{test_case_id}.png', dpi=150)
    plt.close()
```

#### 5.4 渲染要求

- **必须渲染的图表**（根据数据存在性决定）：
  1. ✅ 汇总统计图表（通过率、执行时间分布）
  2. ✅ 数值分布图（动态发现 `actual_output` 中的数值字段）
  3. ✅ 失败用例图表（最多5个典型案例，如果有时序数据）
  4. ✅ 对比分析图表（当前 vs 基准的关键指标）

- **图表质量要求**：
  - 分辨率: 150 DPI
  - 尺寸: 宽1200像素以上
  - 包含: 标题、坐标轴标签、图例
  - 中文: 确保字体正确显示

---

### 6. 生成报告内容

**使用模板**：`assets/report_template.json`

**生成规则**：
- 复制模板，填充 `content` 字段
- 内容由你根据实际数据生成业务洞察
- 需要表格时添加 `table` 字段

**输出**：`report_content.json`

---

### 7. 质量验证（关键步骤 - 必须执行）

**质量门禁 Checklist**（必须全部勾选）：
- [ ] `verify_report_structure.py` 通过 - 确保9个章节齐全且顺序正确
- [ ] `check_content_quality.py` 通过 - 确保内容有深度，非数据罗列

**执行验证脚本**：
```bash
python scripts/verify_report_structure.py report_content.json
python scripts/check_content_quality.py report_content.json
```

**验证失败处理**：
| 问题 | 处理方式 |
|------|----------|
| 结构错误 | 回步骤6，修正章节结构 |
| 内容过浅 | 回步骤6，补充业务洞察 |
| 中文乱码风险 | 回步骤5，检查字体设置 |

---

### 8. 调用 pdf skill

```
skill:
  name: "pdf"
  arguments: '{"command": "generate", "input": "report_content.json", "output": "report_{test_run_id}_{YYYYMMDD}.pdf"}'
```

---

### 9. 输出到 .model-eval/smart-reports/ 目录

**重要**：所有输出文件（PDF、JSON、图表）必须输出到 `.model-eval/smart-reports/` 目录，而不是项目根目录。

```
project/
└── .model-eval/
    └── smart-reports/
        ├── report_{test_run_id}_{YYYYMMDD}.pdf
        ├── report_{test_run_id}_content.json
        ├── chart_*.png
        └── index.json  (由 model-eval-cli 自动管理)
```

**输出路径代码示例**：
```python
# 输出目录
reports_dir = os.path.join(project_root, '.model-eval', 'smart-reports')
os.makedirs(reports_dir, exist_ok=True)

# 输出文件
pdf_path = os.path.join(reports_dir, f"report_{test_run_id}_{date_str}.pdf")
json_path = os.path.join(reports_dir, f"report_{test_run_id}_content.json")
```

---

### 10. 更新钩子函数

```python
def generate_smart_report(base_run_id, test_run_id):
    from generate_nb_report import generate_nb_report
    return generate_nb_report(base_run_id, test_run_id)
```

---

## 参考文档

- [meta-framework.md](references/meta-framework.md) - 报告9章节结构（1个摘要+8个正文章节）
- [quality-standards.md](references/quality-standards.md) - 内容质量标准
- [data-schema.md](references/data-schema.md) - **数据字段详细说明（必须读取）**
- [skill-collaboration.md](references/skill-collaboration.md) - pdf skill 协作接口

---

## 附录：generate_nb_report.py 模板

```python
#!/usr/bin/env python3
"""业务性测试报告生成脚本"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any


def read_test_run(run_id: str) -> Dict:
    path = f".model-eval/test-runs/{run_id}.json"
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def read_test_cases() -> List[Dict]:
    cases = []
    cases_dir = ".model-eval/testcases"
    if os.path.exists(cases_dir):
        for filename in os.listdir(cases_dir):
            if filename.endswith('.json'):
                with open(os.path.join(cases_dir, filename), 'r', encoding='utf-8') as f:
                    cases.append(json.load(f))
    return cases


def generate_smart_report(base_run_id: str, test_run_id: str) -> dict:
    """生成智能报告（集成到 model-eval 的钩子函数）

    ⚠️ 重要：返回格式协议
    - status 必须是 "completed" 或 "failed"，不是 "success"！
    - 输出路径必须是 .model-eval/smart-reports/ 目录

    Args:
        base_run_id: 基准测试记录 ID
        test_run_id: 测试对象记录 ID

    Returns:
        dict: {
            "status": "completed" | "failed",
            "pdf_path": str | None,
            "error_message": str | None
        }
    """
    # 输出到 .model-eval/smart-reports/ 目录
    reports_dir = os.path.join(os.path.dirname(__file__), '.model-eval', 'smart-reports')
    os.makedirs(reports_dir, exist_ok=True)

    # 读取测试数据
    base_data = read_test_run(base_run_id)
    test_data = read_test_run(test_run_id)
    test_cases = read_test_cases()

    # 生成报告逻辑...

    return {
        "status": "completed",
        "pdf_path": os.path.join(reports_dir, f"report_{test_run_id}_{datetime.now().strftime('%Y%m%d')}.pdf")
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("用法: python generate_nb_report.py <base_run_id> <test_run_id>")
        sys.exit(1)
    
    base_id = sys.argv[1]
    test_id = sys.argv[2]
    report_name = generate_nb_report(base_id, test_id)
    print(f"报告生成完成: {report_name}.pdf")
```
