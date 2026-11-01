#!/usr/bin/env python3
"""检测中文字体是否可用"""

import matplotlib
import matplotlib.pyplot as plt
import sys
import os


def check_chinese_font():
    """检测并设置中文字体"""
    fonts = ["SimHei", "Microsoft YaHei", "WenQuanYi Micro Hei", "DejaVu Sans"]

    for font in fonts:
        try:
            plt.rcParams["font.sans-serif"] = [font]
            plt.rcParams["axes.unicode_minus"] = False

            # 测试渲染
            fig, ax = plt.subplots(figsize=(4, 2))
            ax.text(0.5, 0.5, "中文测试", fontsize=14, ha="center")
            ax.axis("off")

            # 尝试保存到临时目录
            temp_path = os.path.join(os.environ.get("TEMP", "/tmp"), "font_test.png")
            plt.savefig(temp_path, dpi=100, bbox_inches="tight")
            plt.close()

            # 清理测试文件
            if os.path.exists(temp_path):
                os.remove(temp_path)

            print(f"✅ 中文字体可用: {font}")
            return font

        except Exception as e:
            plt.close()
            continue

    print("❌ 警告：未找到中文字体")
    print("   图表中的中文可能显示为方框")
    print("   建议安装: SimHei 或 Microsoft YaHei")
    print("   或者使用: pip install matplotlib-fontja")
    sys.exit(1)


if __name__ == "__main__":
    check_chinese_font()
