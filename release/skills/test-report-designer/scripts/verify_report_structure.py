#!/usr/bin/env python3
"""验证报告结构是否符合要求"""

import json
import sys

REQUIRED_SECTIONS = [
    "summary",
    "overview",
    "environment",
    "results",
    "comparison",
    "deep_analysis",
    "cases",
    "recommendations",
    "appendix",
]


def validate_structure(filepath):
    """验证报告结构"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            report = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析错误: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"❌ 文件不存在: {filepath}")
        sys.exit(1)

    sections = report.get("sections", [])
    actual_ids = [s.get("id") for s in sections]

    errors = []

    # 检查数量
    if len(actual_ids) != 9:
        errors.append(f"章节数量错误：期望9，实际{len(actual_ids)}")

    # 检查顺序
    if actual_ids != REQUIRED_SECTIONS:
        errors.append(f"章节顺序错误")
        errors.append(f"   期望: {REQUIRED_SECTIONS}")
        errors.append(f"   实际: {actual_ids}")

    # 检查第一个章节
    if actual_ids and actual_ids[0] != "summary":
        errors.append("第一章必须是 summary（📊 测试结论摘要）")

    # 检查必需字段
    for i, section in enumerate(sections):
        section_num = i + 1
        if "id" not in section:
            errors.append(f"第{section_num}章缺少 id 字段")
        if "title" not in section:
            errors.append(f"第{section_num}章缺少 title 字段")
        if "content" not in section:
            errors.append(f"第{section_num}章缺少 content 字段")

    if errors:
        print("❌ 结构验证失败：")
        for e in errors:
            print(f"   - {e}")
        print("\n请修正后重新生成报告")
        sys.exit(1)
    else:
        print("✅ 报告结构验证通过")
        print(f"   共 {len(sections)} 个章节，顺序正确")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python verify_report_structure.py report_content.json")
        sys.exit(1)

    validate_structure(sys.argv[1])
