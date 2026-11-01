#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project Harness 规范合规检查脚本。

用法：
    uv run check-compliance.py [--scope {all|attachments|docs|adr}]

规则来源：项目根目录的 CONTRIBUTING.md
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

# 强制 UTF-8 输出，避免 Windows 控制台编码错误
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


def find_project_root() -> Path:
    """从当前目录向上查找包含 CONTRIBUTING.md 的项目根目录。"""
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / "CONTRIBUTING.md").exists():
            return parent
    print("❌ 错误：未找到 CONTRIBUTING.md，请在项目根目录运行")
    sys.exit(1)


def check_attachments(root: Path) -> List[Tuple[str, str]]:
    """检查 50-attachments/ 规范。"""
    issues = []
    attachments_dir = root / "50-attachments"

    if not attachments_dir.exists():
        return [("warning", "50-attachments/ 目录不存在")]

    # 规则 1：根目录只允许 INDEX.md
    for item in attachments_dir.iterdir():
        if item.is_file() and item.name != "INDEX.md":
            issues.append((
                "error",
                f"50-attachments/ 根目录发现非法文件：{item.name}"
            ))
        elif item.is_dir():
            # 规则 2：子目录内检查
            issues.extend(check_attachment_subdir(item))

    # 规则 3：INDEX.md 存在性
    if not (attachments_dir / "INDEX.md").exists():
        issues.append(("error", "50-attachments/INDEX.md 缺失"))

    return issues


def check_attachment_subdir(subdir: Path) -> List[Tuple[str, str]]:
    """检查单个附件子目录。"""
    issues = []

    for item in subdir.iterdir():
        if item.is_file():
            # 检查命名规范（默认：必须包含日期）
            if not re.search(r"_\d{8}", item.name) and item.suffix.lower() not in [".md"]:
                # README.md 和 INDEX.md 可豁免
                if item.name not in ["README.md", "INDEX.md"]:
                    issues.append((
                        "warning",
                        f"文件命名缺少日期后缀：{subdir.name}/{item.name}"
                    ))

    return issues


def check_index_sync(root: Path) -> List[Tuple[str, str]]:
    """检查 INDEX.md 与实际文件是否同步。"""
    issues = []
    attachments_dir = root / "50-attachments"
    index_file = attachments_dir / "INDEX.md"

    if not index_file.exists():
        return issues

    index_content = index_file.read_text(encoding="utf-8")

    # 收集所有子目录中的文件（排除 INDEX.md）
    actual_files = set()
    for subdir in attachments_dir.iterdir():
        if subdir.is_dir():
            for item in subdir.iterdir():
                if item.is_file():
                    actual_files.add(item.name)

    # 简单检查：INDEX.md 中是否提到了这些文件
    for filename in actual_files:
        if filename not in index_content:
            issues.append((
                "warning",
                f"文件未在 INDEX.md 中登记：{filename}"
            ))

    return issues


def check_adr_format(root: Path) -> List[Tuple[str, str]]:
    """检查 ADR 格式规范。"""
    issues = []
    decisions_dir = root / "00-meta" / "decisions"

    if not decisions_dir.exists():
        return [("warning", "00-meta/decisions/ 目录不存在")]

    adr_pattern = re.compile(r"ADR-\d{4}-.*\.md$")

    for item in decisions_dir.iterdir():
        if item.is_file() and item.suffix == ".md":
            # 豁免目录说明文件
            if item.name in ("README.md", "INDEX.md"):
                continue
            if not adr_pattern.match(item.name):
                issues.append((
                    "warning",
                    f"ADR 文件名不符合规范（ADR-XXXX-标题.md）：{item.name}"
                ))

    return issues


def print_report(issues: List[Tuple[str, str]], scope: str):
    """输出检查报告。"""
    errors = [i for i in issues if i[0] == "error"]
    warnings = [i for i in issues if i[0] == "warning"]

    print(f"\n{'='*60}")
    print(f"规范检查报告（范围：{scope}）")
    print(f"{'='*60}")

    if not issues:
        print("\n✅ 所有检查项通过")
        return

    if errors:
        print(f"\n❌ 错误（{len(errors)} 项）：")
        for _, msg in errors:
            print(f"   - {msg}")

    if warnings:
        print(f"\n⚠️  警告（{len(warnings)} 项）：")
        for _, msg in warnings:
            print(f"   - {msg}")

    print(f"\n{'='*60}")
    print(f"总计：{len(errors)} 个错误，{len(warnings)} 个警告")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(description="Project Harness 规范检查")
    parser.add_argument(
        "--scope",
        choices=["all", "attachments", "docs", "adr"],
        default="all",
        help="检查范围"
    )
    args = parser.parse_args()

    root = find_project_root()
    print(f"项目根目录：{root}")

    all_issues = []

    if args.scope in ("all", "attachments"):
        all_issues.extend(check_attachments(root))
        all_issues.extend(check_index_sync(root))

    if args.scope in ("all", "adr"):
        all_issues.extend(check_adr_format(root))

    print_report(all_issues, args.scope)

    # 有错误时返回非零退出码
    if any(i[0] == "error" for i in all_issues):
        sys.exit(1)


if __name__ == "__main__":
    main()
