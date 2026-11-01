#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git Commit Revision Analysis Script

Analyzes git commit history over a specified time period and generates
a structured revision report categorizing changes into business logic
improvements and code optimizations.

Usage:
    python analyze_commits.py --since "2 months ago" --output src/REVISION.md
"""

import subprocess
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class Commit:
    """Represents a git commit with its metadata."""
    hash: str
    author: str
    date: str
    message: str
    files_changed: List[Tuple[str, str]]  # (status, filename)


def run_git_command(cmd: List[str]) -> str:
    """Execute a git command and return stdout."""
    try:
        result = subprocess.run(
            ["git"] + cmd,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Git command failed: {e.stderr}")


def get_current_branch() -> str:
    """Get the current git branch name."""
    return run_git_command(["branch", "--show-current"]).strip() or "HEAD"


def get_commits_since(time_period: str, branch: str = None) -> List[str]:
    """Get list of commit hashes since the specified time period."""
    cmd = [
        "log",
        f"--since={time_period}",
        "--pretty=format:%h|%an|%ad|%s",
        "--date=short"
    ]
    if branch:
        cmd.append(branch)
    else:
        cmd.append("--all")
    
    output = run_git_command(cmd)
    if not output:
        return []
    
    commits = []
    for line in output.split('\n'):
        if '|' in line:
            parts = line.split('|', 3)
            if len(parts) == 4:
                commits.append({
                    'hash': parts[0],
                    'author': parts[1],
                    'date': parts[2],
                    'message': parts[3]
                })
    return commits


def get_commit_file_changes(commit_hash: str) -> List[Tuple[str, str]]:
    """Get file changes for a specific commit."""
    output = run_git_command(["show", "--stat", "--name-status", commit_hash])
    
    changes = []
    for line in output.split('\n'):
        line = line.strip()
        if not line or line.startswith('commit') or line.startswith('Author') or line.startswith('Date'):
            continue
        
        # Parse file status (A=Added, M=Modified, D=Deleted, R=Renamed)
        if re.match(r'^[AMD]\s+', line) or re.match(r'^R\d+\s+', line):
            parts = line.split('\t', 1)
            if len(parts) == 2:
                status = parts[0].split()[0]
                filename = parts[1].split('\t')[-1]
                changes.append((status, filename))
    
    return changes


def categorize_commit(commit: Dict, files: List[Tuple[str, str]]) -> Tuple[str, str]:
    """
    Categorize a commit as business logic or code optimization.
    Returns: (category, subcategory)
    """
    message = commit['message'].lower()
    file_types = [f[1].lower() for f in files]
    
    # Business logic indicators
    business_keywords = [
        'feature', '功能', '业务', '管理', '标准', '规则', '流程',
        '数据', '模型', '配置', '参数', '管控', '分析', '探索'
    ]
    
    # Code optimization indicators
    code_keywords = [
        'refactor', '重构', '优化', '性能', '依赖', '配置', '工具',
        '结构', '模块', '清理', '删除', '更新', '修复', 'bug'
    ]
    
    # Check file types
    has_notebook = any('.ipynb' in f for f in file_types)
    has_config = any('config' in f or 'pyproject' in f or '.gitignore' in f for f in file_types)
    has_src_code = any(f.startswith('src/') for f in file_types)
    has_doc = any('doc/' in f or 'README' in f for f in file_types)
    
    # Categorize
    business_score = sum(1 for kw in business_keywords if kw in message)
    code_score = sum(1 for kw in code_keywords if kw in message)
    
    if has_notebook or business_score > code_score:
        if '标准' in commit['message'] or 'spec' in message:
            return ('business', '管理标准')
        elif '特征' in commit['message'] or 'feature' in message:
            return ('business', '特征工程')
        elif '数据' in commit['message'] or 'data' in message:
            return ('business', '数据处理')
        else:
            return ('business', '功能开发')
    else:
        if has_config or 'config' in message:
            return ('code', '配置管理')
        elif '重构' in commit['message'] or 'refactor' in message:
            return ('code', '代码重构')
        elif has_doc:
            return ('code', '文档优化')
        else:
            return ('code', '代码优化')


def generate_report(
    commits: List[Dict],
    branch: str,
    time_period: str,
    output_path: Path
) -> None:
    """Generate the revision report markdown file."""
    
    # Analyze commits
    business_changes = defaultdict(list)
    code_changes = defaultdict(list)
    stats = {
        'total_commits': len(commits),
        'added_files': 0,
        'modified_files': 0,
        'deleted_files': 0,
        'contributors': set(),
        'modules': set()
    }
    
    for commit in commits:
        files = get_commit_file_changes(commit['hash'])
        category, subcategory = categorize_commit(commit, files)
        
        # Update statistics
        stats['contributors'].add(commit['author'])
        for status, filename in files:
            if status == 'A':
                stats['added_files'] += 1
            elif status == 'M':
                stats['modified_files'] += 1
            elif status == 'D':
                stats['deleted_files'] += 1
            
            # Extract module
            if '/' in filename:
                module = filename.split('/')[0]
                stats['modules'].add(module)
        
        commit_info = {
            'hash': commit['hash'],
            'message': commit['message'],
            'author': commit['author'],
            'date': commit['date'],
            'files': files
        }
        
        if category == 'business':
            business_changes[subcategory].append(commit_info)
        else:
            code_changes[subcategory].append(commit_info)
    
    # Generate markdown
    lines = [
        "# 代码改动分析报告",
        "",
        f"**分析时间范围**: {time_period}",
        f"**当前分支**: {branch}",
        f"**分析日期**: {datetime.now().strftime('%Y-%m-%d')}",
        "",
        "---",
        "",
        "## 一、业务逻辑改进",
        ""
    ]
    
    # Business changes
    for i, (subcategory, commit_list) in enumerate(business_changes.items(), 1):
        lines.append(f"### {i}. {subcategory}")
        for commit_info in commit_list:
            lines.append(f"- **{commit_info['message']}** ({commit_info['hash']})")
            lines.append(f"  - 作者: {commit_info['author']}, 日期: {commit_info['date']}")
            if commit_info['files']:
                file_summary = ", ".join([f[1] for f in commit_info['files'][:5]])
                if len(commit_info['files']) > 5:
                    file_summary += f" 等{len(commit_info['files'])}个文件"
                lines.append(f"  - 涉及文件: {file_summary}")
            lines.append("")
    
    lines.extend([
        "## 二、代码层面优化",
        ""
    ])
    
    # Code changes
    for i, (subcategory, commit_list) in enumerate(code_changes.items(), 1):
        lines.append(f"### {i}. {subcategory}")
        for commit_info in commit_list:
            lines.append(f"- **{commit_info['message']}** ({commit_info['hash']})")
            lines.append(f"  - 作者: {commit_info['author']}, 日期: {commit_info['date']}")
            if commit_info['files']:
                file_summary = ", ".join([f[1] for f in commit_info['files'][:5]])
                if len(commit_info['files']) > 5:
                    file_summary += f" 等{len(commit_info['files'])}个文件"
                lines.append(f"  - 涉及文件: {file_summary}")
            lines.append("")
    
    # Statistics
    lines.extend([
        "## 三、统计信息",
        "",
        f"- **总提交数**: {stats['total_commits']}个commit",
        f"- **新增文件**: 约{stats['added_files']}个文件",
        f"- **修改文件**: 约{stats['modified_files']}个文件",
        f"- **删除文件**: {stats['deleted_files']}个文件",
        f"- **主要贡献者**: {', '.join(sorted(stats['contributors']))}",
        f"- **主要模块**: {', '.join(sorted(stats['modules']))}",
        "",
        "---",
        "",
        "*本报告由代码改动分析工具自动生成*"
    ])
    
    # Write file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text('\n'.join(lines), encoding='utf-8')
    print(f"✅ 报告已生成: {output_path}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='分析git commit历史并生成改动报告')
    parser.add_argument(
        '--since',
        default='2 months ago',
        help='分析的时间范围 (默认: "2 months ago")'
    )
    parser.add_argument(
        '--branch',
        default=None,
        help='要分析的分支 (默认: 当前分支)'
    )
    parser.add_argument(
        '--output',
        default='src/REVISION.md',
        help='输出文件路径 (默认: src/REVISION.md)'
    )
    
    args = parser.parse_args()
    
    branch = args.branch or get_current_branch()
    commits = get_commits_since(args.since, branch)
    
    if not commits:
        print(f"⚠️  在 '{args.since}' 时间范围内未找到任何commit")
        return
    
    print(f"📊 分析 {len(commits)} 个commit...")
    output_path = Path(args.output)
    generate_report(commits, branch, args.since, output_path)


if __name__ == '__main__':
    main()

