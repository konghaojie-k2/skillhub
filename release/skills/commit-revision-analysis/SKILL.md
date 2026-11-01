---
name: commit-revision-analysis
description: Analyze git commit history for a specified time period and generate revision reports. Use this skill when users need to analyze code changes, generate revision summaries, understand project evolution, or create change reports. Analyzes commits from both business logic and code optimization perspectives, identifying key improvements and generating structured markdown reports.
---

# Commit Revision Analysis

## Overview

This skill enables comprehensive analysis of git commit history over a specified time period, generating structured revision reports that categorize changes into business logic improvements and code-level optimizations. The analysis produces markdown reports that summarize key changes, their impact, and statistical information.

## When to Use

Use this skill when:
- Analyzing code changes over a specific time period (e.g., past 2 months)
- Generating revision summaries for project documentation
- Understanding project evolution and key improvements
- Creating change reports for stakeholders
- Reviewing commit history to identify patterns and trends

## Workflow

### Step 1: Determine Analysis Parameters

Identify:
- **Time period**: How far back to analyze (e.g., "2 months", "30 days", "since last release")
- **Branch**: Which branch to analyze (default: current branch)
- **Output location**: Where to save the revision report (default: `src/REVISION.md`)

### Step 2: Collect Commit History

Use git commands to gather commit information:

```bash
# Get commit list with metadata
git log --since="<time_period>" --pretty=format:"%h|%an|%ad|%s" --date=short --all

# Get detailed file changes for specific commits
git show --stat --name-status <commit_hash>
```

### Step 3: Analyze Commits

Categorize each commit and its changes:

**Business Logic Analysis:**
- New features or functionality
- Business rule changes
- Data model updates
- Process improvements
- Configuration changes affecting business logic

**Code Optimization Analysis:**
- Refactoring and code structure improvements
- Dependency management updates
- Performance optimizations
- Code organization and maintainability
- Development tooling improvements
- Configuration and build system changes

### Step 4: Generate Report Structure

Create a markdown report with the following sections:

1. **Header**: Analysis time range, branch, analysis date
2. **Business Logic Improvements**: Categorized by feature/domain
3. **Code-Level Optimizations**: Categorized by type
4. **Key Changes Summary**: Business and technical value
5. **Statistics**: Commit count, file changes, contributors

### Step 5: Write Report

Generate the report file at the specified location (default: `src/REVISION.md`).

## Report Format

The revision report should follow this structure:

```markdown
# 代码改动分析报告

**分析时间范围**: <time_range>
**当前分支**: <branch_name>
**分析日期**: <analysis_date>

## 一、业务逻辑改进

### 1. <Category Name>
- **<Feature/Change Title>** (<commit_hash>)
  - Description of business impact
  - Key changes and their significance

## 二、代码层面优化

### 1. <Category Name>
- **<Optimization Title>** (<commit_hash>)
  - Description of technical improvement
  - Code-level changes and benefits

## 三、关键改动总结

### 业务价值
1. Summary of business value

### 技术价值
1. Summary of technical value

## 四、统计信息

- **总提交数**: <count>
- **新增文件**: <count>
- **修改文件**: <count>
- **删除文件**: <count>
- **主要贡献者**: <contributors>
- **主要模块**: <modules>
```

## Analysis Guidelines

### Identifying Business Logic Changes

Look for:
- New data models or schemas
- Business rule implementations
- Feature additions
- Process workflows
- Configuration affecting business behavior
- Domain-specific logic

### Identifying Code Optimizations

Look for:
- Refactoring (renaming, restructuring)
- Dependency updates
- Build system changes
- Code organization improvements
- Performance optimizations
- Development tooling
- Configuration management

### Categorization Tips

- Group related commits by feature or module
- Focus on significant changes, not minor fixes
- Highlight changes that affect multiple files or modules
- Note breaking changes or major architectural shifts
- Identify patterns across multiple commits

## Example Usage

**User Request**: "分析当前分支过去2个月的commit改动，生成REVISION.md"

**Process**:
1. Determine time period: "2 months ago"
2. Get current branch: `git branch --show-current`
3. Collect commits: `git log --since="2 months ago" --all`
4. Analyze each commit's changes
5. Categorize into business logic and code optimizations
6. Generate report at `src/REVISION.md`

## Scripts

The skill includes a Python script (`scripts/analyze_commits.py`) that can automate the analysis process. The script:
- Collects git commit history
- Analyzes file changes
- Categorizes commits
- Generates markdown reports

See `scripts/analyze_commits.py` for implementation details.

## Notes

- Always use the current branch unless specified otherwise
- Include all commits in the time period, even if they're on different branches
- Focus on meaningful changes; skip trivial commits (typos, formatting)
- Group related changes together for better readability
- Provide context for why changes were made when possible
- Use commit hashes for traceability

