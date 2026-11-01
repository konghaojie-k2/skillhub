#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""arc-fit.py - 圆形/弧形构图的坐标助手

SVG 用 clipPath 把画面裁进圆里时，元素必须落在圆的可见范围内，
否则会被裁掉一角。本脚本按弦长公式反算每个高度处的可见 x 区间。

公式:
    dx = sqrt(r^2 - (y - cy)^2)
    可见 x 范围 = [cx - dx, cx + dx]

用法:
    python arc-fit.py <cx> <cy> <r> <y1> <y2> ...
        查询若干 y 高度处的可见 x 范围

    python arc-fit.py --rect <cx> <cy> <r> <x> <y> <w> <h>
        检查矩形（左上角 x,y，宽 w，高 h）是否完整落在圆内，
        越界时给出可放置的 x 区间建议

示例:
    python arc-fit.py 340 240 190 372 388 400 412
    python arc-fit.py --rect 340 240 190 185 372 81 68

退出码 (仅 --rect): 0 = 完整可见, 1 = 会被裁切
"""

import math
import sys


def half_width(cy, r, y):
    """y 高度处的可见半宽 dx；该 y 超出圆范围时返回 None"""
    dy = abs(y - cy)
    if dy >= r:
        return None
    return math.sqrt(r * r - dy * dy)


def query(cx, cy, r, ys):
    print("圆心 (%g, %g)  半径 %g" % (cx, cy, r))
    print("圆纵向范围: y = %g .. %g" % (cy - r, cy + r))
    print("")
    print("%7s | %22s | %8s" % ("y", "可见 x 范围", "可见宽度"))
    print("-" * 46)
    for y in ys:
        dx = half_width(cy, r, y)
        if dx is None:
            print("%7.1f | %22s | %8s" % (y, "（圆外，不可见）", "-"))
        else:
            lo, hi = cx - dx, cx + dx
            print("%7.1f | %8.1f .. %8.1f | %8.1f" % (y, lo, hi, 2 * dx))


def check_rect(cx, cy, r, x, y, w, h):
    corners = [
        ("左上", x, y),
        ("右上", x + w, y),
        ("左下", x, y + h),
        ("右下", x + w, y + h),
    ]
    print("圆心 (%g, %g)  半径 %g" % (cx, cy, r))
    print("矩形: 左上 (%g, %g)  宽 %g  高 %g" % (x, y, w, h))
    print("")
    print("%-6s | %16s | %8s | %s" % ("角点", "坐标", "距圆心", "状态"))
    print("-" * 50)

    ok = True
    worst = 0.0
    for name, px, py in corners:
        d = math.hypot(px - cx, py - cy)
        inside = d <= r
        ok = ok and inside
        worst = max(worst, d)
        print("%-6s | (%6.1f,%6.1f) | %8.1f | %s"
              % (name, px, py, d, "在内" if inside else "越界"))
    print("-" * 50)

    if ok:
        print("结果: 完整可见（最远角 %.1f <= 半径 %g）" % (worst, r))
        return 0

    print("结果: 会被裁切（最远角 %.1f > 半径 %g，超出 %.1f）" % (worst, r, worst - r))

    # 建议：取矩形上下边中距圆心更远的一侧，反算该处允许的半宽
    bottom = max(abs(y - cy), abs(y + h - cy))
    if bottom < r:
        dx_need = math.sqrt(r * r - bottom * bottom)
        x_lo = cx - dx_need
        x_hi = cx + dx_need - w
        if x_lo <= x_hi:
            print("建议: 保持尺寸不变时，x 取值区间为 [%.1f, %.1f]" % (x_lo, x_hi))
            print("      （当前 x = %g%s）" % (
                x, "" if x_lo <= x <= x_hi else "，需移动"))
        else:
            print("建议: 该高度处圆宽 %.1f 小于矩形宽 %g，需缩小或上移" % (2 * dx_need, w))
    else:
        print("建议: 矩形纵向已超出圆范围，需上移或缩小高度")

    return 1


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2

    if argv[1] == "--rect":
        if len(argv) != 9:
            print("用法: python arc-fit.py --rect <cx> <cy> <r> <x> <y> <w> <h>")
            return 2
        nums = [float(v) for v in argv[2:9]]
        return check_rect(*nums)

    if len(argv) < 5:
        print("用法: python arc-fit.py <cx> <cy> <r> <y1> <y2> ...")
        return 2

    cx, cy, r = (float(v) for v in argv[1:4])
    ys = [float(v) for v in argv[4:]]
    query(cx, cy, r, ys)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
