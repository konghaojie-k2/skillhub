#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安装 UTF-8 全局配置到 Python site-packages

运行此脚本后，所有 Python 脚本将自动使用 UTF-8 编码
支持自动检测虚拟环境位置（backend/.venv 或 .venv）
"""

import sys
import shutil
import os
from pathlib import Path

# 必须在最开始配置 UTF-8，否则输出会乱码
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')


def find_site_packages():
    """查找虚拟环境的 site-packages 目录"""

    # 可能的虚拟环境位置
    possible_paths = [
        Path("backend/.venv/Lib/site-packages"),
        Path(".venv/Lib/site-packages"),
        Path("venv/Lib/site-packages"),
        Path("../backend/.venv/Lib/site-packages"),
    ]

    # 检查 sys.prefix（如果是通过 uv run 等方式运行）
    sys_site_packages = Path(sys.prefix) / "Lib" / "site-packages"
    if sys_site_packages.exists():
        return sys_site_packages

    # 检查其他可能的位置
    for path in possible_paths:
        if path.exists():
            return path

    return None


def install_sitecustomize():
    """安装 sitecustomize.py 到全局 site-packages"""

    # 获取当前脚本所在目录
    current_dir = Path(__file__).parent
    source_file = current_dir / "sitecustomize.py"

    if not source_file.exists():
        print(f"错误: 找不到 {source_file}")
        return False

    # 查找 site-packages 目录
    site_packages = find_site_packages()

    if not site_packages:
        print(f"错误: 找不到 site-packages 目录")
        print(f"请确保虚拟环境已创建（.venv 或 backend/.venv）")
        return False

    # 目标文件
    target_file = site_packages / "sitecustomize.py"

    # 备份已存在的文件
    if target_file.exists():
        backup_file = target_file.with_suffix('.py.backup')
        shutil.copy2(target_file, backup_file)
        print(f"已备份现有配置: {backup_file}")

    # 复制文件
    try:
        shutil.copy2(source_file, target_file)
        print(f"✅ 成功安装 UTF-8 配置到: {target_file}")
        print(f"✅ 现在所有 Python 脚本将自动使用 UTF-8 编码")
        return True
    except Exception as e:
        print(f"❌ 安装失败: {e}")
        return False


def uninstall_sitecustomize():
    """卸载 sitecustomize.py"""

    site_packages = find_site_packages()
    if not site_packages:
        print("错误: 找不到 site-packages 目录")
        return

    target_file = site_packages / "sitecustomize.py"
    backup_file = target_file.with_suffix('.py.backup')

    if target_file.exists():
        os.remove(target_file)
        print(f"✅ 已删除: {target_file}")

    if backup_file.exists():
        # 恢复备份
        shutil.copy2(backup_file, target_file)
        os.remove(backup_file)
        print(f"✅ 已恢复备份")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--uninstall":
        print("正在卸载 UTF-8 配置...")
        uninstall_sitecustomize()
    else:
        print("正在安装 UTF-8 全局配置...")
        print("-" * 50)
        success = install_sitecustomize()
        print("-" * 50)

        if success:
            print("\n测试安装:")
            print("运行: python -c \"print('测试中文: 🎉 ✅')\"")
        else:
            print("\n安装失败，请检查错误信息")
