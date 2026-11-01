#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHM 健康度评估函数

评估设备健康预测基准模型的预测质量。
通过残差分析量化健康度，支持异方差、自相关、正态性等多维度诊断。

Usage:
    from evaluate_health import evaluate_health
    metrics = evaluate_health(y_true, y_pred)
"""

import numpy as np


def evaluate_health(y_true, y_pred):
    """
    通过残差统计进行健康度量化

    健康预测的5个维度：
    1. 准确：R² 高
    2. 无偏：残差均值 ≈ 0
    3. 同方差：残差方差不随预测值变化
    4. 正态：残差呈正态分布
    5. 独立：无自相关

    health_score = R²
                 - α × 异方差惩罚
                 - β × 自相关惩罚
                 - γ × 偏度/峰度惩罚

    Args:
        y_true: 实际值数组
        y_pred: 预测值数组

    Returns:
        dict: 包含 health_score 和各项指标的字典
    """
    y_true = np.asarray(y_true).flatten()
    y_pred = np.asarray(y_pred).flatten()
    residuals = y_true - y_pred
    n = len(residuals)

    # 1. 基本准确度：R²
    r2 = 1 - (residuals.var() / y_true.var()) if y_true.var() > 0 else 0
    r2_score = max(0, min(1, r2))

    # 2. 无偏性：残差均值（归一化）
    residual_mean = residuals.mean()
    residual_std = residuals.std() + 1e-10
    unbiased_penalty = min(1, abs(residual_mean) / residual_std)

    # 3. 异方差惩罚：残差平方与预测值的相关性
    # 理想情况：残差平方与预测值无关（相关系数=0）
    residual_squared = residuals ** 2
    if np.std(residual_squared) > 0 and np.std(y_pred) > 0:
        heteroscedasticity_corr = abs(np.corrcoef(y_pred, residual_squared)[0, 1])
        if np.isnan(heteroscedasticity_corr):
            heteroscedasticity_corr = 0
    else:
        heteroscedasticity_corr = 0
    heteroscedasticity_penalty = heteroscedasticity_corr

    # 4. 自相关惩罚：残差滞后1期的自相关系数
    # 理想情况：无自相关（AC1 ≈ 0）
    if n > 10:
        autocorr = np.corrcoef(residuals[:-1], residuals[1:])[0, 1]
        if np.isnan(autocorr):
            autocorr = 0
    else:
        autocorr = 0
    autocorr_penalty = abs(autocorr)

    # 5. 残差正态性惩罚：偏度和峰度
    residual_skewness = ((residuals - residual_mean) ** 3).mean() / (residual_std ** 3)
    residual_kurtosis = ((residuals - residual_mean) ** 4).mean() / (residual_std ** 4) - 3
    normality_penalty = min(1, abs(residual_skewness) / 3) * min(1, abs(residual_kurtosis) / 5)

    # 综合评分：R² - 各维度惩罚
    # 权重分配：准确度最重要，异方差和自相关次之，正态性辅助
    alpha, beta, gamma = 0.5, 0.3, 0.2
    health_score = (
        r2_score
        - alpha * heteroscedasticity_penalty
        - beta * autocorr_penalty
        - gamma * normality_penalty
    )
    health_score = max(0, health_score)  # 确保非负

    return {
        'r2': r2,
        'r2_score': r2_score,
        'rmse': np.sqrt((residuals ** 2).mean()),
        'residual_mean': residual_mean,
        'residual_std': residual_std,
        'heteroscedasticity_corr': heteroscedasticity_corr,
        'autocorr': autocorr,
        'residual_skewness': residual_skewness,
        'residual_kurtosis': residual_kurtosis,
        'health_score': health_score,
        # 各维度惩罚（便于分析）
        'heteroscedasticity_penalty': heteroscedasticity_penalty,
        'autocorr_penalty': autocorr_penalty,
        'normality_penalty': normality_penalty,
        'unbiased_penalty': unbiased_penalty,
    }


def diagnose(metrics, threshold=0.3):
    """
    根据评估结果给出诊断建议

    Args:
        metrics: evaluate_health() 返回的指标字典
        threshold: 惩罚阈值，超过此值认为有问题

    Returns:
        list: 诊断建议列表
    """
    suggestions = []

    if metrics['heteroscedasticity_penalty'] > threshold:
        suggestions.append({
            'issue': '异方差问题',
            'severity': metrics['heteroscedasticity_penalty'],
            'description': '残差方差随预测值变化，存在漏斗效应',
            'suggestions': [
                '检查数据是否存在多个工况',
                '尝试分工况建模',
                '考虑加权回归',
            ]
        })

    if metrics['autocorr_penalty'] > threshold:
        suggestions.append({
            'issue': '自相关问题',
            'severity': metrics['autocorr_penalty'],
            'description': '残差存在时序相关性',
            'suggestions': [
                '加入滞后特征',
                '考虑时序模型（ARIMA、LSTM）',
                '检查工况切换点',
            ]
        })

    if metrics['normality_penalty'] > threshold:
        suggestions.append({
            'issue': '正态性问题',
            'severity': metrics['normality_penalty'],
            'description': '残差分布偏离正态',
            'suggestions': [
                '检查是否存在异常值',
                '分析残差分布形态（双峰？厚尾？）',
                '考虑数据变换',
            ]
        })

    if metrics['r2'] < 0.7:
        suggestions.append({
            'issue': '拟合不足',
            'severity': 1 - metrics['r2'],
            'description': f"R²={metrics['r2']:.3f}，模型解释力不足",
            'suggestions': [
                '增加特征',
                '尝试更复杂的模型',
                '检查因子量选择是否正确',
            ]
        })

    return suggestions


if __name__ == "__main__":
    # 示例：生成测试数据
    np.random.seed(42)
    n = 1000
    y_true = np.linspace(0, 100, n) + np.random.normal(0, 5, n)

    # 好的预测
    y_pred_good = y_true + np.random.normal(0, 5, n)
    metrics_good = evaluate_health(y_true, y_pred_good)
    print("=== 好的预测 ===")
    print(f"health_score: {metrics_good['health_score']:.4f}")
    print(f"R2: {metrics_good['r2']:.4f}")
    print()

    # 有异方差的预测
    noise = np.random.normal(0, 1, n) * (y_true / 50)
    y_pred_hetero = y_true + noise
    metrics_hetero = evaluate_health(y_true, y_pred_hetero)
    print("=== 有异方差的预测 ===")
    print(f"health_score: {metrics_hetero['health_score']:.4f}")
    print(f"R2: {metrics_hetero['r2']:.4f}")
    print(f"异方差惩罚: {metrics_hetero['heteroscedasticity_penalty']:.4f}")
    print()

    # 诊断
    diag = diagnose(metrics_hetero)
    for d in diag:
        print(f"问题: {d['issue']} (严重度: {d['severity']:.3f})")
        print(f"  描述: {d['description']}")
        print(f"  建议: {d['suggestions']}")