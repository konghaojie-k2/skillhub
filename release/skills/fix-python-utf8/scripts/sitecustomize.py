#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python 全局 UTF-8 配置

此文件会在 Python 启动时自动导入，配置所有 Python 脚本使用 UTF-8 编码。
安装到虚拟环境的 site-packages 目录后自动生效。
"""

import sys

# 强制配置标准输出为 UTF-8（兼容 Windows）
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# 确保 default encoding 也是 utf-8
if sys.getdefaultencoding() != 'utf-8':
    import io
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace')
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
