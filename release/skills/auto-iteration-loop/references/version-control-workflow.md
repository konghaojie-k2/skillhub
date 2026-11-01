# 版本管理流程参考

工况切分项目遵循严格的版本迭代工作流，自动优化循环必须遵守。

## 分支命名规范

```
experiment/优化方向名称

示例:
experiment/bayesian-optimization
experiment/multi-scale-features
experiment/adaptive-weights
```

## 完整工作流

### 优化前（创建分支）

```bash
# 1. 确保在 master 分支
git checkout master

# 2. 创建实验分支
git checkout -b experiment/<优化方向名称>

# 3. 开始开发...
```

### 优化成功（合并分支）

```bash
# 1. 回到 master
git checkout master

# 2. 合并实验分支
git merge experiment/<优化方向名称>

# 3. 创建版本标签
git tag -a vX -m "<版本描述>"

# 4. 删除实验分支
git branch -d experiment/<优化方向名称>

# 5. 更新记录文件
# - docs/algorithm_changelog.md
# - memory/code-journal.md
```

### 优化失败（丢弃分支）

```bash
# 1. 回到 master
git checkout master

# 2. 强制删除实验分支（未合并）
git branch -D experiment/<优化方向名称>

# 3. 不更新版本记录
```

## 状态文件更新

每次有效改进后，必须更新：

| 文件 | 内容 |
|------|------|
| `memory/iteration-state.json` | 更新评分、完成列表、历史记录 |
| `memory/optimization-candidates.md` | 标记已完成方向、更新优先级 |
| `docs/algorithm_changelog.md` | 记录技术细节变化 |
| `memory/code-journal.md` | 记录代码活动 |

## 版本号规则

```
v1 - 基础框架
v2 - 第一个有效优化
v3 - 第二个有效优化
...

版本描述格式:
"vX: 优化方向名称 (+Y分)"
```