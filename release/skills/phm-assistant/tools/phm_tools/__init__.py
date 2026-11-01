#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
phm_tools - PHM 助手工具集

提供前置条件检查功能：
- check_data: 数据文件检查
- check_device: 设备信息验证
- check_metrics: 测点类型推荐
- check_env: Python 环境检查
- run_preflight_check: 综合检查入口
"""

from check_data import check_data as check_data_func
from check_device import check_device_info, check_metric_mapping
from check_metrics import check_metric_types as check_metrics_func
from check_env import check_environment
from preflight_check import run_preflight_check

__all__ = [
    "check_data_func",
    "check_device_info",
    "check_metric_mapping",
    "check_metrics_func",
    "check_environment",
    "run_preflight_check",
]
