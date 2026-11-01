#!/usr/bin/env python3
"""检查内容质量是否达标"""

import json
import sys

REASONING_WORDS = [
    "因为",
    "所以",
    "表明",
    "说明",
    "导致",
    "反映",
    "意味着",
    "可见",
    "由此",
]
MIN_CONTENT_LENGTH = 200


def check_quality(filepath):
    """检查内容质量"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            report = json.load(f)
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        sys.exit(1)

    sections = report.get("sections", [])
    issues = []
    warnings = []

    for section in sections:
        sid = section.get("id", "unknown")
        title = section.get("title", "Unknown")
        content = section.get("content", "")

        # 检查长度
        if len(content) < MIN_CONTENT_LENGTH:
            issues.append(
                f"{title}: 内容过短（{len(content)}字符），需要≥{MIN_CONTENT_LENGTH}字符"
            )

        # 检查推理词汇
        has_reasoning = any(w in content for w in REASONING_WORDS)
        if not has_reasoning:
            issues.append(f"{title}: 缺少推理分析（建议包含：因为、所以、表明等词汇）")

        # 检查是否是数据罗列（简单启发式）
        numbers = len([c for c in content if c.isdigit()])
        if numbers / max(len(content), 1) > 0.3:
            warnings.append(f"{title}: 数字占比过高，可能存在数据罗列")

    # 输出结果
    if issues:
        print("❌ 内容质量未达标：")
        for i in issues:
            print(f"   - {i}")
        print(f"\n参考: references/quality-standards.md")
        sys.exit(1)

    if warnings:
        print("⚠️  内容警告（建议优化）：")
        for w in warnings:
            print(f"   - {w}")

    print("✅ 内容质量验证通过")
    print(f"   共检查 {len(sections)} 个章节")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python check_content_quality.py report_content.json")
        sys.exit(1)

    check_quality(sys.argv[1])
