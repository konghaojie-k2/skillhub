#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_metrics.py - 测点类型推荐工具

功能：
- 基于领域知识推荐观测量和因子量
- 相关性分析
- 生成 target-factor 映射建议

用法：
    python check_metrics.py --data data.csv --device-type centrifugal_pump
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional


# 领域知识规则
DOMAIN_RULES = {
    "centrifugal_pump": {
        "likely_targets": ["vibration", "bearing_temp", "seal_pressure", "flow_deviation"],
        "likely_factors": ["rpm", "load", "flow_rate", "inlet_pressure", "outlet_pressure"],
        "target_info": {
            "vibration": {"component": "bearing", "alarm_threshold": 10.0, "unit": "mm/s"},
            "bearing_temp": {"component": "bearing", "alarm_threshold": 80.0, "unit": "°C"},
            "seal_pressure": {"component": "seal", "alarm_threshold": 5.0, "unit": "bar"}
        }
    },
    "motor": {
        "likely_targets": ["winding_temp", "vibration", "current", "power_factor"],
        "likely_factors": ["load", "rpm", "ambient_temp", "voltage"],
        "target_info": {
            "winding_temp": {"component": "stator", "alarm_threshold": 120.0, "unit": "°C"},
            "vibration": {"component": "bearing", "alarm_threshold": 7.0, "unit": "mm/s"}
        }
    },
    "compressor": {
        "likely_targets": ["discharge_temp", "oil_temp", "vibration", "pressure_ratio"],
        "likely_factors": ["rpm", "load", "inlet_temp", "cooling_water_flow"],
        "target_info": {
            "discharge_temp": {"component": "cylinder", "alarm_threshold": 180.0, "unit": "°C"},
            "oil_temp": {"component": "lubrication", "alarm_threshold": 70.0, "unit": "°C"}
        }
    },
    "fan": {
        "likely_targets": ["vibration", "bearing_temp", "airflow"],
        "likely_factors": ["rpm", "load", "inlet_temp"],
        "target_info": {
            "vibration": {"component": "impeller", "alarm_threshold": 7.0, "unit": "mm/s"},
            "bearing_temp": {"component": "bearing", "alarm_threshold": 70.0, "unit": "°C"}
        }
    }
}


def check_metric_types(data_file: str, device_type: str) -> Dict[str, Any]:
    """
    测点类型分析

    返回:
    {
        "passed": bool,
        "recommended_targets": [...],
        "recommended_factors": [...],
        "correlation_matrix": {...},
        "target_factor_mapping": {...},
        "issues": [...],
        "recommendations": [...]
    }
    """
    import pandas as pd
    import numpy as np

    result = {
        "passed": False,
        "recommended_targets": [],
        "recommended_factors": [],
        "correlation_matrix": {},
        "target_factor_mapping": {},
        "issues": [],
        "recommendations": []
    }

    # 读取数据
    try:
        if data_file.endswith('.csv'):
            data = pd.read_csv(data_file)
        elif data_file.endswith(('.xlsx', '.xls')):
            data = pd.read_excel(data_file)
        else:
            result["issues"].append("不支持的文件格式")
            return result
    except Exception as e:
        result["issues"].append(f"读取数据失败: {str(e)}")
        return result

    columns = list(data.columns)

    # 获取领域规则
    rules = DOMAIN_RULES.get(device_type, {})
    likely_targets = rules.get("likely_targets", [])
    likely_factors = rules.get("likely_factors", [])
    target_info = rules.get("target_info", {})

    # 匹配测点
    columns_lower = {c.lower(): c for c in columns}

    # 推荐观测量
    for target in likely_targets:
        for pattern, col in columns_lower.items():
            if target in pattern:
                info = target_info.get(target, {})
                result["recommended_targets"].append({
                    "metric": col,
                    "confidence": 0.9 if target in target_info else 0.7,
                    "reason": f"{device_type} 关键健康指标",
                    "component": info.get("component"),
                    "alarm_threshold": info.get("alarm_threshold"),
                    "unit": info.get("unit")
                })

    # 推荐因子量
    for factor in likely_factors:
        for pattern, col in columns_lower.items():
            if factor in pattern:
                result["recommended_factors"].append({
                    "metric": col,
                    "type": "operating_condition",
                    "confidence": 0.8,
                    "reason": "影响观测量的工况参数"
                })

    # 相关性分析
    numeric_data = data.select_dtypes(include=[np.number])
    if len(numeric_data.columns) > 1:
        corr_matrix = numeric_data.corr()
        result["correlation_matrix"] = {
            col: {str(k): v for k, v in row.items()}
            for col, row in corr_matrix.to_dict().items()
        }

        # 基于相关性推荐 target-factor 映射
        for target_info_item in result["recommended_targets"]:
            target_col = target_info_item["metric"]
            if target_col in corr_matrix.columns:
                strong_factors = []
                for factor_info_item in result["recommended_factors"]:
                    factor_col = factor_info_item["metric"]
                    if factor_col in corr_matrix.columns:
                        corr = abs(corr_matrix.loc[target_col, factor_col])
                        if corr > 0.5:
                            strong_factors.append({
                                "factor": factor_col,
                                "correlation": float(corr)
                            })

                if strong_factors:
                    result["target_factor_mapping"][target_col] = sorted(
                        strong_factors, key=lambda x: x["correlation"], reverse=True
                    )[:5]

    # 判断是否通过
    result["passed"] = len(result["recommended_targets"]) > 0

    if not result["passed"]:
        result["recommendations"].append(
            f"未能从数据中找到与 {device_type} 相关的典型测点，请手动确认"
        )

    return result


def print_result(result: Dict[str, Any]):
    """打印检查结果"""
    print("\n" + "=" * 50)
    print("📐 测点类型分析结果")
    print("=" * 50)

    status = "✅" if result["passed"] else "⚠️"
    print(f"\n状态: {status}")

    # 观测量推荐
    if result.get("recommended_targets"):
        print("\n【推荐 1】观测量 (Target Metrics):")
        for target in result["recommended_targets"]:
            confidence = target.get("confidence", 0)
            status_icon = "✅" if confidence > 0.8 else "❌"
            print(f"  {status_icon} {target['metric']}")
            print(f"      置信度: {confidence:.0%}")
            print(f"      理由: {target['reason']}")
            if target.get("component"):
                print(f"      建议部件: {target['component']}")
            if target.get("alarm_threshold"):
                print(f"      报警阈值: {target['alarm_threshold']} {target.get('unit', '')}")

    # 因子量推荐
    if result.get("recommended_factors"):
        print("\n【推荐 2】因子量 (Factor Metrics):")
        for factor in result["recommended_factors"]:
            print(f"  ❌ {factor['metric']} → 因子量 ({factor['type']})")
            print(f"      理由: {factor['reason']}")

    # Target-Factor 映射
    if result.get("target_factor_mapping"):
        print("\n【推荐 3】Target-Factor 映射:")
        for target, factors in result["target_factor_mapping"].items():
            factor_names = [f"{f['factor']} ({f['correlation']:.2f})" for f in factors]
            print(f"  {target} ← {', '.join(factor_names)}")

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
    parser = argparse.ArgumentParser(description="测点类型推荐工具")
    parser.add_argument("--data", "-d", required=True, help="数据文件路径")
    parser.add_argument("--device-type", "-t", required=True, help="设备类型")
    parser.add_argument("--json", "-j", action="store_true", help="JSON 格式输出")

    args = parser.parse_args()

    result = check_metric_types(args.data, args.device_type)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_result(result)

    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
