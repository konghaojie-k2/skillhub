---
name: auto-iteration-loop
description: "工况切分项目的自动迭代优化循环系统。让agent在内部循环中自动识别优化方向、执行优化、自我反思评估、决定继续或停止。TRIGGER when: (1) 用户说开始自动优化、启动迭代循环、跑几轮优化; (2) 用户问有没有其他优化方向、还有什么可以改进的; (3) 用户说让agent自己跑; (4) 用户指定轮次数如跑5轮迭代。"
---

# 自动迭代优化循环

## 概述

工况切分项目的自动迭代优化系统。Agent在内部循环执行完整的优化工作流：识别方向→执行优化→反思评估→版本管理→终止检查，无需用户反复确认。

## 循环参数

从用户命令解析或使用默认值：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| max_rounds | 5 | 最大迭代轮次 |
| patience | 2 | 连续无改进容忍轮次 |
| target_score | 0.85 | 性能达标阈值 |
| min_improvement | 0.01 | 最小有效改进阈值 |

## 工作流

```
FOR round IN 1..max_rounds:

  PHASE 1: 状态检查
    → 读取 memory/iteration-state.json（或初始化）
    → 检查终止条件

  PHASE 2: 识别优化方向
    → 分析当前评估指标瓶颈
    → 参考 references/optimization-patterns.md
    → 生成候选并选择优先级最高的方向

  PHASE 3: 执行优化
    → 创建实验分支: git checkout -b experiment/<方向名称>
    → 实施具体优化方案
    → 运行测试验证: uv pytest
    → 调用 evaluator 获取新评分

  PHASE 4: 反思评估
    → 对比前后性能变化
    → 判断改进是否有效 (improvement >= min_improvement)
    → 有效: 合并分支、更新版本记录
    → 无效: 丢弃分支、增加patience_counter

  PHASE 5: 终止检查
    → 满足终止条件则输出总结并BREAK
    → 否则继续下一轮

END FOR
```

## 终止条件

满足任一则停止循环：

1. **性能达标**: current_score >= target_score
2. **连续无改进**: patience_counter >= patience
3. **穷尽方向**: 无可用优化候选
4. **达到上限**: round >= max_rounds

## 版本管理流程

严格遵循项目版本迭代工作流：

**优化前**:
```bash
git checkout master
git checkout -b experiment/<优化方向名称>
```

**优化成功**:
```bash
git checkout master
git merge experiment/<优化方向名称>
git tag -a vX -m "版本描述"
git branch -d experiment/<优化方向名称>
```

**优化失败**:
```bash
git checkout master
git branch -D experiment/<优化方向名称>
```

详见 `references/version-control-workflow.md`。

## 状态文件

### memory/iteration-state.json

```json
{
  "round_num": 3,
  "current_score": 0.78,
  "patience_counter": 0,
  "completed_optimizations": ["贝叶斯优化"],
  "current_phase": "反思评估",
  "last_improvement": 0.05,
  "optimization_history": [...]
}
```

每个Phase结束后立即保存状态。

## 输出格式

### 每轮开始
```
╔══════════════════════════════════════════════════════════╗
║ 轮次 3/5                                                  ║
╠══════════════════════════════════════════════════════════╣
║ 当前评分: 0.72                                            ║
║ 本轮目标: 多尺度时序特征提取                               ║
╚══════════════════════════════════════════════════════════╝
```

### 每轮结束
```
╔══════════════════════════════════════════════════════════╗
║ 反思结果                                                  ║
╠══════════════════════════════════════════════════════════╣
║ ✓ 有效改进: +0.05                                         ║
║ 新评分: 0.77                                              ║
║ 分支已合并: experiment/多尺度 → master                    ║
╚══════════════════════════════════════════════════════════╝
```

### 最终总结
生成 `memory/iteration-summary.md` 包含：总轮次、最终评分、完成优化列表、终止原因。

## 优化方向生成

Agent动态分析瓶颈并生成候选：

1. 运行 evaluator 获取当前指标
2. 诊断瓶颈（哪个指标偏低）
3. 参考 `references/optimization-patterns.md` 中的瓶颈诊断映射
4. 生成候选列表，按预期收益×可行性排序
5. 选择Top1作为本轮目标

## References

- `references/optimization-patterns.md` - 优化方向模板和瓶颈诊断映射
- `references/version-control-workflow.md` - 详细版本管理流程