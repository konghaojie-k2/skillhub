#!/usr/bin/env python3
"""
根据 test case 中的 chart 配置和时序数据渲染图表
"""

import json
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from pathlib import Path
import sys


def setup_chinese_font():
    """设置中文字体"""
    fonts = ["SimHei", "Microsoft YaHei", "WenQuanYi Micro Hei", "DejaVu Sans"]
    for font in fonts:
        try:
            plt.rcParams["font.sans-serif"] = [font]
            plt.rcParams["axes.unicode_minus"] = False
            return True
        except:
            continue
    print("警告: 未找到中文字体")
    return False


def parse_timestamp(ts_str):
    """解析时间戳字符串"""
    try:
        return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
    except:
        return ts_str


def render_chart_from_testcase(testcase_path, output_dir="."):
    """
    根据测试用例中的 chart 配置渲染图表

    Args:
        testcase_path: 测试用例JSON文件路径
        output_dir: 输出目录

    Returns:
        生成的图表文件路径
    """
    with open(testcase_path, "r", encoding="utf-8") as f:
        testcase = json.load(f)

    test_case_id = testcase["id"]
    raw_input = testcase.get("raw_input", {})

    if "chart" not in raw_input or "data" not in raw_input:
        print(f"跳过 {test_case_id}: 无图表数据")
        return None

    chart_config = raw_input["chart"]
    data = raw_input["data"]

    return render_chart(chart_config, data, test_case_id, output_dir)


def render_chart(chart_config, data, test_case_id, output_dir="."):
    """
    渲染单个图表

    Args:
        chart_config: 图表配置
        data: 时序数据数组
        test_case_id: 测试用例ID
        output_dir: 输出目录

    Returns:
        生成的图表文件路径
    """
    setup_chinese_font()

    title = chart_config.get("title", "图表")
    x_axis_config = chart_config.get("x_axis", {})
    y_axis_config = chart_config.get("y_axis", {})
    series_list = chart_config.get("series", [])

    # 提取x轴数据
    x_field = x_axis_config.get("field", "timestamp")
    x_label = x_axis_config.get("label", "时间")

    x_data = []
    for d in data:
        if x_field in d:
            x_data.append(parse_timestamp(d[x_field]))
        else:
            x_data.append(len(x_data))

    # 创建图形
    fig, ax1 = plt.subplots(figsize=(14, 6))

    # 收集y轴信息
    y_axes_configs = []
    if y_axis_config:
        y_axes_configs.append(
            {
                "field": y_axis_config.get("field"),
                "label": y_axis_config.get("label", "数值"),
                "min": y_axis_config.get("min"),
                "max": y_axis_config.get("max"),
                "axis": ax1,
            }
        )

    # 如果有第二个y轴配置
    y_axis2_config = chart_config.get("y_axis2")
    if y_axis2_config:
        ax2 = ax1.twinx()
        y_axes_configs.append(
            {
                "field": y_axis2_config.get("field"),
                "label": y_axis2_config.get("label", "数值2"),
                "min": y_axis2_config.get("min"),
                "max": y_axis2_config.get("max"),
                "axis": ax2,
            }
        )

    # 额外的y轴
    y_axes_extra = chart_config.get("y_axes", [])
    for i, y_extra in enumerate(y_axes_extra[:2]):  # 最多4个y轴
        if y_extra.get("visible", True):
            if i % 2 == 0:
                ax_extra = ax1.twinx()
                ax_extra.spines["right"].set_position(("outward", 60 * (i // 2 + 1)))
            else:
                ax_extra = ax1.twinx()
                ax_extra.spines["right"].set_position(("outward", 60 * (i // 2 + 1)))

            y_axes_configs.append(
                {
                    "field": y_extra.get("field"),
                    "label": y_extra.get("label"),
                    "min": y_extra.get("min"),
                    "max": y_extra.get("max"),
                    "axis": ax_extra,
                }
            )

    # 绘制每条线
    lines = []
    labels = []

    for series in series_list:
        point_name = series.get("point_name")
        label = series.get("label", point_name)
        color = series.get("color", "#333333")
        line_type = series.get("type", "line")
        line_style = series.get("line_style", "solid")
        y_axis_index = int(series.get("y_axis_index", 0))

        # 提取y轴数据
        y_data = []
        for d in data:
            if point_name in d:
                y_data.append(d[point_name])
            else:
                y_data.append(None)

        # 获取对应的y轴
        if y_axis_index < len(y_axes_configs):
            ax = y_axes_configs[y_axis_index]["axis"]
        else:
            ax = ax1

        # 绘制
        if line_type == "line":
            (line,) = ax.plot(
                x_data,
                y_data,
                label=label,
                color=color,
                linestyle=line_style,
                linewidth=1.5,
                marker="o",
                markersize=3,
            )
            lines.append(line)
            labels.append(label)

    # 设置标题和标签
    ax1.set_title(title, fontsize=14, fontweight="bold", pad=20)
    ax1.set_xlabel(x_label, fontsize=11)

    # 设置y轴标签
    for y_config in y_axes_configs:
        ax = y_config["axis"]
        ax.set_ylabel(y_config["label"], fontsize=11)
        if y_config["min"] is not None and y_config["max"] is not None:
            ax.set_ylim(y_config["min"], y_config["max"])

    # 合并图例
    if lines:
        ax1.legend(lines, labels, loc="upper right", fontsize=9)

    # 旋转x轴标签
    plt.xticks(rotation=45, ha="right")

    # 添加网格
    ax1.grid(True, alpha=0.3, linestyle="--")

    # 调整布局
    plt.tight_layout()

    # 保存
    output_path = Path(output_dir) / f"chart_{test_case_id}.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()

    print(f"✅ 图表已生成: {output_path}")
    return str(output_path)


def render_summary_charts(test_run_data, base_run_data=None, output_dir="."):
    """
    渲染汇总统计图表

    Args:
        test_run_data: 当前测试运行的数据
        base_run_data: 基准测试运行的数据(可选)
        output_dir: 输出目录

    Returns:
        生成的图表文件路径列表
    """
    setup_chinese_font()
    output_paths = []

    # 1. 通过率饼图
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # 当前运行
    labels = ["通过", "失败"]
    sizes = [test_run_data["passed_count"], test_run_data["failed_count"]]
    colors = ["#52c41a", "#ff4d4f"]
    explode = (0.05, 0)

    ax1.pie(
        sizes,
        explode=explode,
        labels=labels,
        colors=colors,
        autopct="%1.1f%%",
        shadow=True,
        startangle=90,
        textprops={"fontsize": 12},
    )
    ax1.set_title(
        f"当前测试通过率\n({test_run_data['id']})", fontsize=13, fontweight="bold"
    )

    # 如果有基准对比
    if base_run_data:
        sizes_base = [base_run_data["passed_count"], base_run_data["failed_count"]]
        ax2.pie(
            sizes_base,
            explode=explode,
            labels=labels,
            colors=colors,
            autopct="%1.1f%%",
            shadow=True,
            startangle=90,
            textprops={"fontsize": 12},
        )
        ax2.set_title(
            f"基准测试通过率\n({base_run_data['id']})", fontsize=13, fontweight="bold"
        )
    else:
        ax2.axis("off")

    plt.tight_layout()
    output_path = Path(output_dir) / "chart_summary_passrate.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    output_paths.append(str(output_path))
    print(f"✅ 汇总图表已生成: {output_path}")

    # 2. 执行时间分布图
    results = test_run_data.get("results", [])
    if results:
        execution_times = [r["execution_time_ms"] / 1000 for r in results]  # 转为秒

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.hist(execution_times, bins=20, color="#1890ff", alpha=0.7, edgecolor="black")
        ax.set_xlabel("执行时间 (秒)", fontsize=11)
        ax.set_ylabel("用例数量", fontsize=11)
        ax.set_title("测试用例执行时间分布", fontsize=13, fontweight="bold")
        ax.axvline(
            np.mean(execution_times),
            color="red",
            linestyle="--",
            label=f"平均值: {np.mean(execution_times):.2f}s",
        )
        ax.legend()
        ax.grid(True, alpha=0.3, linestyle="--")

        plt.tight_layout()
        output_path = Path(output_dir) / "chart_execution_time.png"
        plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close()
        output_paths.append(str(output_path))
        print(f"✅ 执行时间图表已生成: {output_path}")

    # 3. 置信度分布图
    if results:
        confidence_scores = [
            r["actual_output"].get("confidence_score", 0)
            for r in results
            if "actual_output" in r and "confidence_score" in r["actual_output"]
        ]

        if confidence_scores:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.hist(
                confidence_scores,
                bins=20,
                color="#722ed1",
                alpha=0.7,
                edgecolor="black",
            )
            ax.set_xlabel("置信度分数", fontsize=11)
            ax.set_ylabel("用例数量", fontsize=11)
            ax.set_title("模型置信度分布", fontsize=13, fontweight="bold")
            ax.axvline(0, color="red", linestyle="--", linewidth=2, label="零线")
            ax.legend()
            ax.grid(True, alpha=0.3, linestyle="--")

            plt.tight_layout()
            output_path = Path(output_dir) / "chart_confidence.png"
            plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
            plt.close()
            output_paths.append(str(output_path))
            print(f"✅ 置信度图表已生成: {output_path}")

    return output_paths


def render_failed_case_charts(
    test_run_data, testcases_dir, output_dir=".", max_cases=5
):
    """
    为失败的测试用例渲染图表

    Args:
        test_run_data: 测试运行数据
        testcases_dir: 测试用例目录
        output_dir: 输出目录
        max_cases: 最多渲染的失败用例数

    Returns:
        生成的图表文件路径列表
    """
    output_paths = []
    results = test_run_data.get("results", [])

    # 找出失败的用例
    failed_results = [r for r in results if not r.get("is_passed", True)]

    # 限制数量
    failed_results = failed_results[:max_cases]

    for result in failed_results:
        test_case_id = result["test_case_id"]
        testcase_path = Path(testcases_dir) / f"{test_case_id}.json"

        if testcase_path.exists():
            output_path = render_chart_from_testcase(str(testcase_path), output_dir)
            if output_path:
                output_paths.append(output_path)
        else:
            print(f"警告: 找不到测试用例文件 {testcase_path}")

    return output_paths


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="渲染测试报告图表")
    parser.add_argument("--testcase", help="单个测试用例JSON文件路径")
    parser.add_argument("--testrun", help="测试运行JSON文件路径")
    parser.add_argument(
        "--testcases-dir", default=".model-eval/testcases", help="测试用例目录"
    )
    parser.add_argument("--output-dir", default=".", help="输出目录")
    parser.add_argument("--summary", action="store_true", help="渲染汇总图表")
    parser.add_argument("--failed-cases", action="store_true", help="渲染失败用例图表")

    args = parser.parse_args()

    if args.testcase:
        render_chart_from_testcase(args.testcase, args.output_dir)
    elif args.testrun and args.summary:
        with open(args.testrun, "r", encoding="utf-8") as f:
            test_run_data = json.load(f)
        render_summary_charts(test_run_data, output_dir=args.output_dir)
    elif args.testrun and args.failed_cases:
        with open(args.testrun, "r", encoding="utf-8") as f:
            test_run_data = json.load(f)
        render_failed_case_charts(test_run_data, args.testcases_dir, args.output_dir)
    else:
        print("用法示例:")
        print("  python render_charts.py --testcase testcases/xxx.json")
        print("  python render_charts.py --testrun test-runs/xxx.json --summary")
        print("  python render_charts.py --testrun test-runs/xxx.json --failed-cases")
