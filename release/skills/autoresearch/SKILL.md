---
name: autoresearch
description: AutoResearch - 基于量化评估的自动化优化框架。用于需要迭代优化的任务，如代码重构、性能优化、格式对齐等。当用户需要：(1) 基于量化指标自动优化某些内容，(2) 实现"评估-改进-回滚"循环，(3) 持续迭代直到达到目标，(4) 自动化实验流程时使用此 skill。
---

# AutoResearch

基于量化评估的自动化迭代优化框架。

## 核心概念

AutoResearch 将"评估-改进-决策"循环自动化：

1. **量化评估** - 用数字衡量当前状态
2. **自动优化** - 尝试改进，根据评估结果决策
3. **回滚机制** - 如果改进失败则自动恢复
4. **持续迭代** - 循环直到达到目标

## 快速开始

### 方法1：使用框架脚本

```python
from autoresearch import AutoResearch, quick_research

# 简单用法
results = quick_research(
    target_score=100,
    score_pattern=r'score: (\d+)',
    backup_files=['file.md']
)

# 完整用法
ar = AutoResearch(
    evaluate_cmd="python validate.py",
    score_pattern=r'score: (\d+)',
    target_score=100,
    max_iterations=50,
    backup_files=['file.md']
)
results = ar.run()
```

### 方法2：使用 experiment.py 模式

创建 `experiment.py`：

```python
#!/usr/bin/env python3
from pathlib import Path
from autoresearch import AutoResearch

def evaluate():
    """评估函数，返回当前分数"""
    # 你的评估逻辑
    return score

def experiment():
    """实验函数，执行一次优化尝试"""
    # 你的优化逻辑
    return True  # 成功或失败

ar = AutoResearch(
    evaluate_func=evaluate,
    experiment_func=experiment,
    target_score=100,
    backup_files=['target_file.md']
)

if __name__ == '__main__':
    ar.run()
```

## 配置选项

| 参数 | 类型 | 说明 |
|------|------|------|
| `evaluate_func` | Callable | 评估函数，返回当前分数 |
| `evaluate_cmd` | str | 评估命令（与 score_pattern 一起使用） |
| `score_pattern` | str | 从命令输出提取分数的正则表达式 |
| `target_score` | float | 目标分数 |
| `max_iterations` | int | 最大迭代次数 |
| `backup_files` | List[str] | 需要备份的文件列表 |
| `experiment_func` | Callable | 实验函数，执行优化尝试 |
| `score_direction` | str | "maximize" 或 "minimize" |

## 工作流

```
初始评估 → 备份 → 实验 → 再评估 → 决策 → 循环
              ↓
        改进？保留 : 回滚
```

## 使用场景

- **ASCII 框对齐** - 评估对齐质量，自动调整
- **代码重构** - 评估代码质量指标，自动重构
- **性能优化** - 评估性能指标，自动调优
- **格式规范化** - 评估格式合规性，自动修复

## 脚本

- `scripts/autoresearch.py` - 核心框架代码
