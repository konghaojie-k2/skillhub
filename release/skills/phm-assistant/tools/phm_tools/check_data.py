#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_data.py - 数据文件检查工具

功能：
- 检查数据文件存在性
- 验证文件格式
- 检查编码
- 统计基本信息

用法：
    python check_data.py --file data.csv
    python check_data.py --file data.xlsx --encoding utf-8
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional


def check_file_exists(file_path: str) -> Dict[str, Any]:
    """检查文件是否存在"""
    result = {
        "passed": True,
        "file_exists": False,
        "file_path": file_path,
        "file_size": 0,
        "issues": [],
        "recommendations": []
    }

    if not os.path.exists(file_path):
        result["passed"] = False
        result["file_exists"] = False
        result["issues"].append(f"文件不存在: {file_path}")
        return result

    result["file_exists"] = True
    result["file_size"] = os.path.getsize(file_path)

    return result


def check_file_format(file_path: str) -> Dict[str, Any]:
    """检查文件格式"""
    result = {
        "passed": True,
        "format": None,
        "readable": False,
        "issues": [],
        "recommendations": []
    }

    ext = Path(file_path).suffix.lower()

    supported_formats = {
        ".csv": "csv",
        ".xlsx": "excel",
        ".xls": "excel",
        ".parquet": "parquet",
        ".json": "json",
        ".pkl": "pickle",
        ".pickle": "pickle"
    }

    if ext not in supported_formats:
        result["passed"] = False
        result["issues"].append(f"不支持的文件格式: {ext}")
        result["recommendations"].append("支持格式: CSV, Excel, Parquet, JSON, Pickle")
        return result

    result["format"] = supported_formats[ext]

    # 尝试读取文件
    try:
        if ext == ".csv":
            import pandas as pd
            pd.read_csv(file_path, nrows=5)
        elif ext in [".xlsx", ".xls"]:
            import pandas as pd
            pd.read_excel(file_path, nrows=5)
        elif ext == ".parquet":
            import pandas as pd
            pd.read_parquet(file_path)
        elif ext == ".json":
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
        result["readable"] = True
    except Exception as e:
        result["passed"] = False
        result["readable"] = False
        result["issues"].append(f"文件读取失败: {str(e)}")

    return result


def check_encoding(file_path: str, encoding: str = "utf-8") -> Dict[str, Any]:
    """检查文件编码"""
    result = {
        "passed": True,
        "encoding": encoding,
        "issues": [],
        "recommendations": []
    }

    ext = Path(file_path).suffix.lower()

    # 只对文本文件检查编码
    if ext not in [".csv", ".txt", ".json"]:
        return result

    try:
        with open(file_path, 'r', encoding=encoding) as f:
            f.read(1024)
    except UnicodeDecodeError:
        result["passed"] = False
        result["issues"].append(f"编码 {encoding} 读取失败")
        result["recommendations"].append("尝试其他编码: gbk, gb2312, latin1")
    except Exception as e:
        result["issues"].append(f"编码检查失败: {str(e)}")

    return result


def analyze_data_basic(file_path: str) -> Dict[str, Any]:
    """基本数据分析"""
    result = {
        "passed": True,
        "row_count": 0,
        "column_count": 0,
        "columns": [],
        "time_range": None,
        "missing_ratio": 0,
        "issues": [],
        "recommendations": []
    }

    ext = Path(file_path).suffix.lower()

    try:
        import pandas as pd

        if ext == ".csv":
            data = pd.read_csv(file_path)
        elif ext in [".xlsx", ".xls"]:
            data = pd.read_excel(file_path)
        elif ext == ".parquet":
            data = pd.read_parquet(file_path)
        else:
            return result

        result["row_count"] = len(data)
        result["column_count"] = len(data.columns)
        result["columns"] = list(data.columns)

        # 缺失值检查
        missing_ratio = data.isnull().mean().mean()
        result["missing_ratio"] = missing_ratio

        if missing_ratio > 0.1:
            result["issues"].append(f"缺失值比例过高: {missing_ratio:.1%}")
            result["recommendations"].append("建议进行缺失值处理")

        if len(data) < 1000:
            result["issues"].append(f"数据量不足: {len(data)} 行 (建议 > 1000)")
            result["recommendations"].append("收集更多数据以获得可靠模型")

        # 时间范围检查
        if isinstance(data.index, pd.DatetimeIndex):
            result["time_range"] = {
                "start": str(data.index.min()),
                "end": str(data.index.max()),
                "days": (data.index.max() - data.index.min()).days
            }
        elif "timestamp" in data.columns:
            try:
                time_col = pd.to_datetime(data["timestamp"])
                result["time_range"] = {
                    "start": str(time_col.min()),
                    "end": str(time_col.max()),
                    "days": (time_col.max() - time_col.min()).days
                }
            except:
                pass

    except Exception as e:
        result["passed"] = False
        result["issues"].append(f"数据分析失败: {str(e)}")

    return result


def check_data(file_path: str, encoding: str = "utf-8") -> Dict[str, Any]:
    """
    综合数据检查

    返回:
    {
        "passed": bool,
        "file_check": {...},
        "format_check": {...},
        "encoding_check": {...},
        "analysis": {...},
        "summary": "..."
    }
    """
    result = {
        "passed": True,
        "file_path": file_path,
        "file_check": {},
        "format_check": {},
        "encoding_check": {},
        "analysis": {},
        "summary": ""
    }

    # 1. 文件存在性检查
    file_check = check_file_exists(file_path)
    result["file_check"] = file_check
    if not file_check["passed"]:
        result["passed"] = False
        result["summary"] = "文件不存在"
        return result

    # 2. 格式检查
    format_check = check_file_format(file_path)
    result["format_check"] = format_check
    if not format_check["passed"]:
        result["passed"] = False
        result["summary"] = f"格式检查失败: {format_check['issues']}"
        return result

    # 3. 编码检查
    encoding_check = check_encoding(file_path, encoding)
    result["encoding_check"] = encoding_check

    # 4. 数据分析
    analysis = analyze_data_basic(file_path)
    result["analysis"] = analysis

    # 生成摘要
    issues = []
    if not file_check["passed"]:
        issues.extend(file_check["issues"])
    if not format_check["passed"]:
        issues.extend(format_check["issues"])
    if not analysis["passed"]:
        issues.extend(analysis["issues"])

    if issues:
        result["summary"] = "; ".join(issues)
    else:
        result["summary"] = "数据检查通过"

    return result


def print_result(result: Dict[str, Any]):
    """打印检查结果"""
    print("\n" + "=" * 50)
    print("📊 数据可用性检查结果")
    print("=" * 50)

    print(f"\n文件路径: {result['file_path']}")

    if result["file_check"]:
        fc = result["file_check"]
        status = "✅" if fc["file_exists"] else "❌"
        print(f"\n【文件存在】{status}")
        print(f"  文件大小: {fc['file_size']} bytes")

    if result["format_check"]:
        fc = result["format_check"]
        status = "✅" if fc["readable"] else "❌"
        print(f"\n【格式检查】{status}")
        print(f"  格式: {fc.get('format', 'unknown')}")

    if result["analysis"]:
        an = result["analysis"]
        print(f"\n【数据分析】")
        print(f"  数据量: {an['row_count']} 行")
        print(f"  测点数: {an['column_count']} 列")
        print(f"  缺失值: {an['missing_ratio']:.1%}")

        if an["time_range"]:
            tr = an["time_range"]
            print(f"  时间范围: {tr['days']} 天 ({tr['start']} ~ {tr['end']})")

    if result["analysis"].get("issues"):
        print("\n【问题】")
        for issue in result["analysis"]["issues"]:
            print(f"  ⚠️ {issue}")

    if result["analysis"].get("recommendations"):
        print("\n【建议】")
        for rec in result["analysis"]["recommendations"]:
            print(f"  💡 {rec}")

    print(f"\n{'='*50}")
    print(f"总结: {result['summary']}")
    print("=" * 50 + "\n")


def main():
    parser = argparse.ArgumentParser(description="数据文件检查工具")
    parser.add_argument("--file", "-f", required=True, help="数据文件路径")
    parser.add_argument("--encoding", "-e", default="utf-8", help="文件编码")
    parser.add_argument("--json", "-j", action="store_true", help="JSON 格式输出")

    args = parser.parse_args()

    result = check_data(args.file, args.encoding)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_result(result)

    # 返回状态码
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
