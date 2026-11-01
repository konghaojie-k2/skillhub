#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_device.py - 设备信息验证工具

功能：
- 验证设备类型
- 验证设备 ID
- 推荐部件列表
- 验证测点-部件映射

用法：
    python check_device.py --device-type centrifugal_pump --device-id pump_001
    python check_device.py --data data.csv --device-type motor
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional


# 设备类型领域知识库
DEVICE_KNOWLEDGE = {
    "centrifugal_pump": {
        "name": "离心泵",
        "typical_components": [
            {"id": "bearing", "name": "轴承", "weight": 0.5, "critical": True,
             "likely_metrics": ["vibration_x", "vibration_y", "bearing_temp"]},
            {"id": "seal", "name": "密封", "weight": 0.3, "critical": False,
             "likely_metrics": ["seal_pressure", "leakage_rate"]},
            {"id": "motor", "name": "电机", "weight": 0.2, "critical": False,
             "likely_metrics": ["motor_current", "motor_temp", "rpm"]},
        ]
    },
    "motor": {
        "name": "电机",
        "typical_components": [
            {"id": "stator", "name": "定子", "weight": 0.4, "critical": True,
             "likely_metrics": ["winding_temp", "voltage", "current"]},
            {"id": "rotor", "name": "转子", "weight": 0.3, "critical": True,
             "likely_metrics": ["vibration", "rpm"]},
            {"id": "bearing", "name": "轴承", "weight": 0.3, "critical": False,
             "likely_metrics": ["bearing_temp", "vibration"]},
        ]
    },
    "compressor": {
        "name": "压缩机",
        "typical_components": [
            {"id": "cylinder", "name": "气缸", "weight": 0.4, "critical": True,
             "likely_metrics": ["discharge_temp", "pressure"]},
            {"id": "lubrication", "name": "润滑系统", "weight": 0.3, "critical": True,
             "likely_metrics": ["oil_temp", "oil_pressure"]},
            {"id": "motor", "name": "电机", "weight": 0.3, "critical": False,
             "likely_metrics": ["motor_current", "rpm"]},
        ]
    },
    "fan": {
        "name": "风机",
        "typical_components": [
            {"id": "impeller", "name": "叶轮", "weight": 0.4, "critical": True,
             "likely_metrics": ["vibration", "flow_rate"]},
            {"id": "bearing", "name": "轴承", "weight": 0.3, "critical": True,
             "likely_metrics": ["bearing_temp", "vibration"]},
            {"id": "motor", "name": "电机", "weight": 0.3, "critical": False,
             "likely_metrics": ["motor_current", "rpm"]},
        ]
    }
}


def infer_device_type(columns: List[str]) -> List[Dict[str, Any]]:
    """基于测点名称推断设备类型"""
    import pandas as pd

    results = []

    # 定义设备类型特征
    features = {
        "centrifugal_pump": ["pump", "seal", "bearing", "flow"],
        "motor": ["motor", "winding", "stator", "rotor"],
        "compressor": ["compressor", "discharge", "cylinder", "oil_"],
        "fan": ["fan", "impeller", "airflow"]
    }

    columns_lower = [c.lower() for c in columns]

    for device_type, keywords in features.items():
        score = 0
        matched = []
        for kw in keywords:
            for col in columns_lower:
                if kw in col:
                    score += 1
                    matched.append(kw)

        if score > 0:
            results.append({
                "device_type": device_type,
                "score": score,
                "matched_keywords": matched,
                "confidence": min(score / len(keywords), 1.0)
            })

    return sorted(results, key=lambda x: x["score"], reverse=True)


def check_device_info(device_type: Optional[str], device_id: Optional[str],
                     columns: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    检查设备信息

    返回:
    {
        "passed": bool,
        "device_type": str,
        "device_id": str,
        "inferred_type": [...],
        "recommended_hierarchy": {...},
        "missing": [...],
        "issues": [...],
        "recommendations": [...]
    }
    """
    result = {
        "passed": False,
        "device_type": device_type,
        "device_id": device_id,
        "inferred_type": [],
        "recommended_hierarchy": {},
        "missing": [],
        "issues": [],
        "recommendations": []
    }

    # 检查设备类型
    if not device_type:
        result["missing"].append("设备类型")

        # 尝试从列名推断
        if columns:
            inferred = infer_device_type(columns)
            result["inferred_type"] = inferred

            if inferred:
                result["recommendations"].append(
                    f"根据测点名称，推测设备类型可能是: {inferred[0]['device_type']}"
                )
    elif device_type in DEVICE_KNOWLEDGE:
        result["device_type"] = device_type

        # 推荐部件列表
        knowledge = DEVICE_KNOWLEDGE[device_type]
        result["recommended_hierarchy"] = {
            "device_type": device_type,
            "device_name": knowledge["name"],
            "components": knowledge["typical_components"]
        }
    else:
        result["issues"].append(f"未知设备类型: {device_type}")
        result["recommendations"].append(f"支持的设备类型: {list(DEVICE_KNOWLEDGE.keys())}")

    # 检查设备 ID
    if not device_id:
        result["missing"].append("设备 ID")
    else:
        result["device_id"] = device_id

    # 判断是否通过
    result["passed"] = len(result["missing"]) == 0 and len(result["issues"]) == 0

    return result


def check_metric_mapping(columns: List[str], device_type: str,
                       hierarchy: Optional[Dict] = None) -> Dict[str, Any]:
    """检查测点-部件映射"""
    result = {
        "passed": True,
        "mapped_metrics": [],
        "unmapped_metrics": [],
        "recommendations": []
    }

    # 如果没有提供 hierarchy，使用推荐的
    if not hierarchy and device_type in DEVICE_KNOWLEDGE:
        hierarchy = DEVICE_KNOWLEDGE[device_type]

    if not hierarchy:
        return result

    # 获取所有已知的测点
    known_metrics = set()
    for comp in hierarchy.get("typical_components", []):
        for metric in comp.get("likely_metrics", []):
            known_metrics.add(metric.lower())

    # 匹配测点
    columns_lower = {c: c.lower() for c in columns}

    for col, col_lower in columns_lower.items():
        matched = False
        for known in known_metrics:
            if known in col_lower or col_lower in known:
                result["mapped_metrics"].append({
                    "metric": col,
                    "matched": known
                })
                matched = True
                break

        if not matched:
            result["unmapped_metrics"].append(col)

    if result["unmapped_metrics"]:
        result["recommendations"].append(
            f"以下测点未映射到部件: {', '.join(result['unmapped_metrics'][:5])}"
        )

    return result


def print_result(result: Dict[str, Any]):
    """打印检查结果"""
    print("\n" + "=" * 50)
    print("🔧 设备信息检查结果")
    print("=" * 50)

    status = "✅" if result["passed"] else "⚠️"
    print(f"\n状态: {status}")

    if result.get("device_type"):
        print(f"\n设备类型: {result['device_type']}")

        # 显示推荐的部件列表
        if result.get("recommended_hierarchy"):
            rh = result["recommended_hierarchy"]
            print(f"  设备名称: {rh.get('device_name', 'N/A')}")
            print("\n推荐部件结构:")

            for comp in rh.get("typical_components", []):
                critical = "🔴" if comp.get("critical") else "🟢"
                print(f"  {critical} {comp['name']} (权重: {comp['weight']})")
                print(f"      可能的测点: {', '.join(comp.get('likely_metrics', []))}")

    if result.get("device_id"):
        print(f"\n设备 ID: {result['device_id']}")

    if result.get("inferred_type"):
        print("\n根据测点推断的设备类型:")
        for inferred in result["inferred_type"][:3]:
            print(f"  - {inferred['device_type']} (置信度: {inferred['confidence']:.0%})")

    if result.get("missing"):
        print("\n缺失信息:")
        for m in result["missing"]:
            print(f"  ⚠️ {m}")

    if result.get("issues"):
        print("\n问题:")
        for issue in result["issues"]:
            print(f"  ❌ {issue}")

    if result.get("recommendations"):
        print("\n建议:")
        for rec in result["recommendations"]:
            print(f"  💡 {rec}")

    print("=" * 50 + "\n")


def main():
    parser = argparse.ArgumentParser(description="设备信息验证工具")
    parser.add_argument("--device-type", "-t", help="设备类型")
    parser.add_argument("--device-id", "-i", help="设备 ID")
    parser.add_argument("--data", "-d", help="数据文件路径 (用于推断设备类型)")
    parser.add_argument("--json", "-j", action="store_true", help="JSON 格式输出")

    args = parser.parse_args()

    columns = None

    # 如果提供了数据文件，读取列名
    if args.data:
        try:
            import pandas as pd
            if args.data.endswith('.csv'):
                df = pd.read_csv(args.data, nrows=0)
            elif args.data.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(args.data, nrows=0)
            columns = list(df.columns)
        except Exception as e:
            print(f"警告: 无法读取数据文件: {e}")

    result = check_device_info(args.device_type, args.device_id, columns)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_result(result)

    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
