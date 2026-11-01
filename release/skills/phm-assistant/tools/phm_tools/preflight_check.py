#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
preflight_check.py - PHM 前置条件综合检查入口脚本

功能：
- 整合所有检查工具
- 生成综合检查报告
- 支持交互式和命令行模式

用法：
    python preflight_check.py \
        --data data.csv \
        --device-type centrifugal_pump \
        --device-id pump_001 \
        --output-dir ./phm_output
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

# 导入各检查模块
from check_data import check_data as check_data_func
from check_device import check_device_info, check_metric_mapping
from check_metrics import check_metric_types as check_metrics_func
from check_env import check_environment


def run_preflight_check(
    data_file: Optional[str] = None,
    device_type: Optional[str] = None,
    device_id: Optional[str] = None,
    output_dir: str = "."
) -> Dict[str, Any]:
    """
    Phase 0 前置条件综合检查

    参数:
    - data_file: 数据文件路径
    - device_type: 设备类型
    - device_id: 设备 ID
    - output_dir: 输出目录

    返回:
    {
        "passed": bool,
        "checks": {
            "data": {...},
            "device": {...},
            "metrics": {...},
            "env": {...}
        },
        "summary": "...",
        "next_steps": [...]
    }
    """
    result = {
        "passed": True,
        "checks": {},
        "summary": "",
        "next_steps": []
    }

    # 1. 数据检查
    if data_file:
        print("正在检查数据文件...")
        data_check = check_data_func(data_file)
        result["checks"]["data"] = data_check
        if not data_check["passed"]:
            result["passed"] = False
    else:
        result["checks"]["data"] = {"passed": False, "issues": ["未提供数据文件"]}
        result["passed"] = False

    # 2. 设备信息检查
    columns = None
    if data_check.get("analysis", {}).get("columns"):
        columns = data_check["analysis"]["columns"]

    device_check = check_device_info(device_type, device_id, columns)
    result["checks"]["device"] = device_check

    # 3. 测点类型检查
    if data_file and device_type:
        print("正在分析测点类型...")
        metrics_check = check_metrics_func(data_file, device_type)
        result["checks"]["metrics"] = metrics_check

        # 补充测点映射检查
        if metrics_check.get("recommended_targets"):
            mapping = check_metric_mapping(
                columns, device_type,
                result["checks"]["device"].get("recommended_hierarchy")
            )
            result["checks"]["mapping"] = mapping

    # 4. 环境检查
    print("正在检查环境...")
    env_check = check_environment(output_dir)
    result["checks"]["env"] = env_check
    if not env_check["passed"]:
        result["passed"] = False

    # 生成摘要和后续步骤
    result["summary"] = generate_summary(result["checks"])
    result["next_steps"] = generate_next_steps(result["checks"])

    return result


def generate_summary(checks: Dict[str, Any]) -> str:
    """生成检查摘要"""
    passed_checks = []
    failed_checks = []

    for name, check in checks.items():
        if check.get("passed", True):
            passed_checks.append(name)
        else:
            failed_checks.append(name)

    if not failed_checks:
        return "✅ 所有检查通过"

    return f"⚠️ 通过 {len(passed_checks)} 项，失败 {len(failed_checks)} 项: {', '.join(failed_checks)}"


def generate_next_steps(checks: Dict[str, Any]) -> List[str]:
    """生成后续步骤"""
    steps = []

    # 数据检查失败
    data_check = checks.get("data", {})
    if not data_check.get("passed", True):
        issues = data_check.get("issues", [])
        if any("不存在" in str(i) for i in issues):
            steps.append("1. 提供数据文件路径")
        if any("格式" in str(i) for i in issues):
            steps.append("2. 检查文件格式是否正确")
        if any("数据量" in str(i) for i in issues):
            steps.append("3. 收集更多数据样本")
        return steps

    # 设备信息检查失败
    device_check = checks.get("device", {})
    missing = device_check.get("missing", [])
    if missing:
        if "设备类型" in missing:
            steps.append(f"1. 指定设备类型 (可选: centrifugal_pump, motor, compressor, fan)")
        if "设备 ID" in missing:
            steps.append("2. 指定设备 ID")
        if "部件列表" in missing:
            steps.append("3. 确认设备部件结构")
        return steps

    # 环境检查失败
    env_check = checks.get("env", {})
    if not env_check.get("passed", True):
        missing_deps = env_check.get("dependencies", {}).get("missing", [])
        if missing_deps:
            steps.append(f"1. 安装缺失依赖: pip install {' '.join(missing_deps)}")
        return steps

    # 全部通过
    steps.append("1. 进入 Phase 1: 数据准备")
    steps.append("2. 配置工况切分参数")
    steps.append("3. 开始模型训练")

    return steps


def print_result(result: Dict[str, Any]):
    """打印检查结果"""
    print("\n" + "=" * 60)
    print("🔍 PHM 前置条件检查报告")
    print("=" * 60)

    status = "✅" if result["passed"] else "⚠️"
    print(f"\n总体状态: {status}")

    # 数据检查
    data_check = result["checks"].get("data", {})
    if data_check.get("passed"):
        print("\n【数据检查】✅")
        analysis = data_check.get("analysis", {})
        print(f"  文件: {data_check.get('file_path')}")
        print(f"  数据量: {analysis.get('row_count', 0)} 行")
        print(f"  测点: {analysis.get('column_count', 0)} 列")
        print(f"  缺失值: {analysis.get('missing_ratio', 0):.1%}")
    else:
        print("\n【数据检查】❌")
        for issue in data_check.get("issues", []):
            print(f"  - {issue}")

    # 设备信息检查
    device_check = result["checks"].get("device", {})
    if device_check.get("passed"):
        print("\n【设备信息】✅")
        print(f"  设备类型: {device_check.get('device_type', 'N/A')}")
        print(f"  设备 ID: {device_check.get('device_id', 'N/A')}")

        hierarchy = device_check.get("recommended_hierarchy", {})
        if hierarchy:
            print("  推荐部件:")
            for comp in hierarchy.get("typical_components", [])[:3]:
                critical = "🔴" if comp.get("critical") else "🟢"
                print(f"    {critical} {comp['name']}")
    else:
        print("\n【设备信息】⚠️")
        for missing in device_check.get("missing", []):
            print(f"  ⚠️ 缺失: {missing}")

    # 测点类型检查
    metrics_check = result["checks"].get("metrics", {})
    if metrics_check.get("passed"):
        print("\n【测点类型】✅")
        targets = metrics_check.get("recommended_targets", [])
        if targets:
            print(f"  观测量: {', '.join([t['metric'] for t in targets[:3]])}")

        factors = metrics_check.get("recommended_factors", [])
        if factors:
            print(f"  因子量: {', '.join([f['metric'] for f in factors[:3]])}")

    # 环境检查
    env_check = result["checks"].get("env", {})
    if env_check.get("passed"):
        print("\n【环境检查】✅")
        py = env_check.get("python", {})
        print(f"  Python: {py.get('version', 'N/A')}")

        deps = env_check.get("dependencies", {})
        required = deps.get("required", {})
        installed = sum(1 for d in required.values() if d.get("installed"))
        print(f"  依赖: {installed}/{len(required)} 已安装")
    else:
        print("\n【环境检查】❌")
        deps = env_check.get("dependencies", {})
        missing = deps.get("missing", [])
        if missing:
            print(f"  缺失依赖: {', '.join(missing)}")

    # 后续步骤
    print("\n【后续步骤】")
    for step in result.get("next_steps", []):
        print(f"  {step}")

    print("\n" + "=" * 60)
    print(f"摘要: {result['summary']}")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="PHM 前置条件综合检查",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python preflight_check.py --data data.csv --device-type centrifugal_pump
    python preflight_check.py -d data.xlsx -t motor -i motor_001 -o ./output
        """
    )

    parser.add_argument("--data", "-d", help="数据文件路径 (CSV/Excel)")
    parser.add_argument("--device-type", "-t", help="设备类型 (centrifugal_pump/motor/compressor/fan)")
    parser.add_argument("--device-id", "-i", help="设备 ID")
    parser.add_argument("--output-dir", "-o", default=".", help="输出目录")
    parser.add_argument("--json", "-j", action="store_true", help="JSON 格式输出")

    args = parser.parse_args()

    # 执行检查
    result = run_preflight_check(
        data_file=args.data,
        device_type=args.device_type,
        device_id=args.device_id,
        output_dir=args.output_dir
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_result(result)

    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
