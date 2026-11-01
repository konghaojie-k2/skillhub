#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_env.py - Python 环境检查工具

功能：
- 检查 Python 版本
- 检查依赖库
- 检查输出目录权限

用法：
    python check_env.py
    python check_env.py --output-dir ./phm_output
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List


# 必需依赖
REQUIRED_DEPS = {
    "pandas": {"package": "pandas", "min_version": "2.0", "purpose": "数据处理"},
    "numpy": {"package": "numpy", "min_version": "1.24", "purpose": "数值计算"},
    "sklearn": {"package": "scikit-learn", "min_version": "1.3", "purpose": "机器学习"},
    "xgboost": {"package": "xgboost", "min_version": "2.0", "purpose": "梯度提升"},
    "yaml": {"package": "pyyaml", "min_version": "6.0", "purpose": "配置文件"},
}

# 可选依赖
OPTIONAL_DEPS = {
    "scipy": {"package": "scipy", "min_version": "1.10", "purpose": "科学计算"},
    "statsmodels": {"package": "statsmodels", "min_version": "0.14", "purpose": "统计分析"},
    "matplotlib": {"package": "matplotlib", "min_version": "3.7", "purpose": "可视化"},
    "joblib": {"package": "joblib", "min_version": "1.3", "purpose": "模型保存"},
}


def check_python_version() -> Dict[str, Any]:
    """检查 Python 版本"""
    result = {
        "passed": True,
        "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "issues": [],
        "recommendations": []
    }

    if sys.version_info < (3, 9):
        result["passed"] = False
        result["issues"].append(f"Python 版本过低: {result['version']} (需要 3.9+)")

    return result


def check_dependencies() -> Dict[str, Any]:
    """检查依赖库"""
    result = {
        "passed": True,
        "required": {},
        "optional": {},
        "missing": [],
        "issues": [],
        "recommendations": []
    }

    # 检查必需依赖
    for name, info in REQUIRED_DEPS.items():
        try:
            mod = __import__(info["package"])
            version = getattr(mod, "__version__", "unknown")
            result["required"][name] = {
                "installed": True,
                "version": version,
                "status": "✅"
            }
        except ImportError:
            result["required"][name] = {
                "installed": False,
                "version": None,
                "status": "❌"
            }
            result["missing"].append(info["package"])
            result["passed"] = False

    # 检查可选依赖
    for name, info in OPTIONAL_DEPS.items():
        try:
            mod = __import__(info["package"])
            version = getattr(mod, "__version__", "unknown")
            result["optional"][name] = {
                "installed": True,
                "version": version,
                "status": "✅"
            }
        except ImportError:
            result["optional"][name] = {
                "installed": False,
                "version": None,
                "status": "⚠️"
            }

    if result["missing"]:
        result["recommendations"].append(
            f"安装缺失依赖: pip install {' '.join(result['missing'])}"
        )

    return result


def check_output_dir(output_dir: str) -> Dict[str, Any]:
    """检查输出目录权限"""
    result = {
        "passed": True,
        "path": output_dir,
        "exists": False,
        "writable": False,
        "issues": [],
        "recommendations": []
    }

    path = Path(output_dir)

    # 检查目录是否存在
    if path.exists():
        result["exists"] = True
        result["writable"] = os.access(path, os.W_OK)
    else:
        # 尝试创建
        try:
            path.mkdir(parents=True, exist_ok=True)
            result["exists"] = True
            result["writable"] = True
        except Exception as e:
            result["issues"].append(f"无法创建目录: {str(e)}")
            result["passed"] = False
            return result

    if not result["writable"]:
        result["passed"] = False
        result["issues"].append(f"目录无写入权限: {output_dir}")

    return result


def check_environment(output_dir: str = ".") -> Dict[str, Any]:
    """
    综合环境检查

    返回:
    {
        "passed": bool,
        "python": {...},
        "dependencies": {...},
        "output_dir": {...},
        "summary": "..."
    }
    """
    result = {
        "passed": True,
        "python": {},
        "dependencies": {},
        "output_dir": {},
        "summary": ""
    }

    # 1. Python 版本
    python_check = check_python_version()
    result["python"] = python_check
    if not python_check["passed"]:
        result["passed"] = False

    # 2. 依赖检查
    deps_check = check_dependencies()
    result["dependencies"] = deps_check
    if not deps_check["passed"]:
        result["passed"] = False

    # 3. 输出目录
    output_check = check_output_dir(output_dir)
    result["output_dir"] = output_check
    if not output_check["passed"]:
        result["passed"] = False

    # 生成摘要
    issues = []
    if python_check.get("issues"):
        issues.extend(python_check["issues"])
    if deps_check.get("issues"):
        issues.extend(deps_check.get("issues", []))
    if output_check.get("issues"):
        issues.extend(output_check["issues"])

    if issues:
        result["summary"] = "; ".join(issues)
    else:
        result["summary"] = "环境检查通过"

    return result


def print_result(result: Dict[str, Any]):
    """打印检查结果"""
    print("\n" + "=" * 50)
    print("🐍 Python 环境检查结果")
    print("=" * 50)

    status = "✅" if result["passed"] else "❌"
    print(f"\n状态: {status}")

    # Python 版本
    if result.get("python"):
        py = result["python"]
        py_status = "✅" if py["passed"] else "❌"
        print(f"\n【Python 版本】{py_status}")
        print(f"  版本: {py['version']}")

    # 依赖检查
    if result.get("dependencies"):
        deps = result["dependencies"]
        print(f"\n【依赖检查】")

        print("  必需依赖:")
        for name, info in deps.get("required", {}).items():
            pkg_info = REQUIRED_DEPS.get(name, {})
            print(f"    {info['status']} {name} ({pkg_info.get('purpose', '')})")
            if info.get("version"):
                print(f"        版本: {info['version']}")

        print("  可选依赖:")
        for name, info in deps.get("optional", {}).items():
            pkg_info = OPTIONAL_DEPS.get(name, {})
            print(f"    {info['status']} {name} ({pkg_info.get('purpose', '')})")

    # 输出目录
    if result.get("output_dir"):
        out = result["output_dir"]
        out_status = "✅" if out["passed"] else "❌"
        print(f"\n【输出目录】{out_status}")
        print(f"  路径: {out['path']}")
        print(f"  存在: {out['exists']}")
        print(f"  可写: {out['writable']}")

    if result.get("recommendations"):
        print("\n建议:")
        for rec in result["recommendations"]:
            print(f"  💡 {rec}")

    print(f"\n{'='*50}")
    print(f"总结: {result['summary']}")
    print("=" * 50 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Python 环境检查工具")
    parser.add_argument("--output-dir", "-o", default=".", help="输出目录")
    parser.add_argument("--json", "-j", action="store_true", help="JSON 格式输出")

    args = parser.parse_args()

    result = check_environment(args.output_dir)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_result(result)

    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
