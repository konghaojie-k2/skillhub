#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHM 残差可视化工具

生成四图诊断：
1. 预测值 vs 实际值散点图
2. 残差分布直方图
3. 残差 vs 预测值（检测异方差）
4. 时序对比图

Usage:
    from visualize_residuals import plot_residuals
    plot_residuals(y_true, y_pred, target_name="Pressure")
"""

import os
import numpy as np


def plot_residuals(y_true, y_pred, target_name="target", output_dir="results", show=False):
    """
    生成残差诊断四图

    Args:
        y_true: 实际值数组
        y_pred: 预测值数组
        target_name: 目标量名称（用于标题）
        output_dir: 输出目录
        show: 是否显示图片（默认保存到文件）

    Returns:
        str: 保存的文件路径
    """
    import matplotlib.pyplot as plt
    import matplotlib
    if not show:
        matplotlib.use('Agg')  # 非交互式后端

    os.makedirs(output_dir, exist_ok=True)

    y_true = np.asarray(y_true).flatten()
    y_pred = np.asarray(y_pred).flatten()
    residuals = y_true - y_pred

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle(f'{target_name}: Prediction vs Actual', fontsize=14)

    # 1. 散点图：预测 vs 实际
    ax1 = axes[0, 0]
    ax1.scatter(y_true, y_pred, alpha=0.3, s=10)
    min_val = min(y_true.min(), y_pred.min())
    max_val = max(y_true.max(), y_pred.max())
    ax1.plot([min_val, max_val], [min_val, max_val], 'r--', label='Perfect Prediction')
    ax1.set_xlabel('Actual')
    ax1.set_ylabel('Predicted')
    ax1.set_title('Predicted vs Actual')
    ax1.legend()

    # 2. 残差分布
    ax2 = axes[0, 1]
    ax2.hist(residuals, bins=50, edgecolor='black', alpha=0.7)
    ax2.axvline(x=0, color='r', linestyle='--')
    ax2.set_xlabel('Residual (Actual - Predicted)')
    ax2.set_ylabel('Frequency')
    ax2.set_title(f'Residual Distribution (mean={residuals.mean():.4f}, std={residuals.std():.4f})')

    # 3. 残差 vs 预测值（检测异方差）
    ax3 = axes[1, 0]
    ax3.scatter(y_pred, residuals, alpha=0.3, s=10)
    ax3.axhline(y=0, color='r', linestyle='--')
    ax3.set_xlabel('Predicted')
    ax3.set_ylabel('Residual')
    ax3.set_title('Residual vs Predicted (check heteroscedasticity)')

    # 计算异方差相关系数
    residual_squared = residuals ** 2
    if np.std(residual_squared) > 0 and np.std(y_pred) > 0:
        hetero_corr = abs(np.corrcoef(y_pred, residual_squared)[0, 1])
        if not np.isnan(hetero_corr):
            ax3.text(0.05, 0.95, f'Heteroscedasticity corr: {hetero_corr:.3f}',
                    transform=ax3.transAxes, fontsize=10, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))

    # 4. 时序对比（前500个点）
    ax4 = axes[1, 1]
    n_show = min(500, len(y_true))
    ax4.plot(range(n_show), y_true[:n_show], 'b-', label='Actual', alpha=0.7)
    ax4.plot(range(n_show), y_pred[:n_show], 'r--', label='Predicted', alpha=0.7)
    ax4.set_xlabel('Sample Index')
    ax4.set_ylabel(target_name)
    ax4.set_title(f'Time Series Comparison (first {n_show} samples)')
    ax4.legend()

    plt.tight_layout()

    filename = f"{output_dir}/{target_name.replace('/', '_')}_residuals.png"
    plt.savefig(filename, dpi=150)

    if show:
        plt.show()
    else:
        plt.close()

    return filename


if __name__ == "__main__":
    # 示例：生成测试数据并可视化
    np.random.seed(42)
    n = 1000

    # 好的预测
    y_true = np.linspace(0, 100, n) + np.random.normal(0, 5, n)
    y_pred_good = y_true + np.random.normal(0, 5, n)
    path = plot_residuals(y_true, y_pred_good, "good_prediction")
    print(f"Saved: {path}")

    # 有异方差的预测
    noise = np.random.normal(0, 1, n) * (y_true / 50)
    y_pred_hetero = y_true + noise
    path = plot_residuals(y_true, y_pred_hetero, "heteroscedastic_prediction")
    print(f"Saved: {path}")