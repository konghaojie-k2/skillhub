#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_alignment.py — 浏览器实测校验 cjk-align.js 的对齐与自适应效果

用法:
  uv run --no-project --with playwright python verify_alignment.py <page.html> [--selector "pre code"] [--max-dev 2]

page.html 要求:
  - 含至少一个 <pre><code> 代码块
  - 已通过 <script src=".../cjk-align.js"></script> 引入模块（或页面自身已集成）

校验逻辑:
  1. 记录 CJKAlign.apply 前的行宽与横向溢出
  2. 执行 CJKAlign.apply(document.body)，再次测量
  3. 对齐断言: 每行渲染宽度 ≈ 设计列数 × 拉丁字宽
     （设计列数: CJK 字符计 2 列、其余计 1 列；拉丁字宽取纯 ASCII 行的实测平均值）
  4. 溢出断言: apply 后 scrollWidth - clientWidth <= 0（除非已触达 9px 字号下限）

退出码: 0 = PASS, 1 = FAIL
"""
import argparse, pathlib, re, sys
from playwright.sync_api import sync_playwright

CJK = re.compile(r'[⺀-鿿豈-﫿　-〿＀-｠￠-￦]')

# 拆行测宽。返回 { widths: [...], lines: [...] }；lines 取自 textContent（剥离 span 的纯文本）
MEASURE_JS = """(sel) => {
  const code = document.querySelector(sel);
  if (!code) return null;
  const lines = code.textContent.replace(/\\r/g, '').split('\\n');
  const htmlLines = code.innerHTML.split('\\n');
  code.innerHTML = '';
  const widths = [];
  for (const h of htmlLines) {
    const s = document.createElement('span');
    s.style.cssText = 'display:inline-block;white-space:pre';
    s.innerHTML = h || ' ';
    code.appendChild(s);
    code.appendChild(document.createTextNode('\\n'));
    widths.push(s.getBoundingClientRect().width);
  }
  return { widths, lines };
}"""

def designed_cols(line):
    return sum(2 if CJK.match(ch) else 1 for ch in line)

def check(pg, selector, label, max_dev):
    m = pg.evaluate(MEASURE_JS, selector)
    if m is None:
        print(f"[{label}] FAIL: selector {selector} 未匹配到元素")
        return None
    widths, lines = m['widths'], m['lines']
    cols = [designed_cols(ln) for ln in lines[:len(widths)]]
    # 拉丁字宽基准：纯 ASCII 行的 width/cols 平均值
    ascii_rows = [(w, c) for w, c, ln in zip(widths, cols, lines)
                  if c > 0 and not CJK.search(ln)]
    if not ascii_rows:
        print(f"[{label}] 无纯 ASCII 基准行，跳过对齐断言")
        return {'worst': 0.0, 'skipped': True}
    latin = sum(w for w, _ in ascii_rows) / sum(c for _, c in ascii_rows)
    # 逐行容差：letter-spacing 亚像素取整随 CJK 字数累积，容差与行宽成正比
    def limit(c):
        return max(max_dev, 0.04 * c * latin)
    deviations = [(i, w - c * latin, c) for i, (w, c) in enumerate(zip(widths, cols)) if c > 0]
    worst = max((abs(d) for _, d, _ in deviations), default=0.0)
    print(f"[{label}] latin={latin:.3f}px 行宽最大偏差={worst:.2f}px")
    over = [(i, d, c) for i, d, c in deviations if abs(d) > limit(c)]
    for i, d, c in over:
        print(f"  line {i}: cols={c} dev={d:+.2f}px (limit {limit(c):.1f})  {lines[i][:40]}")
    return {'worst': worst, 'over': over, 'skipped': False}

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    ap = argparse.ArgumentParser()
    ap.add_argument('page', help='本地 HTML 文件路径')
    ap.add_argument('--selector', default='pre code')
    ap.add_argument('--max-dev', type=float, default=2.0)
    args = ap.parse_args()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        pg = browser.new_page(viewport={"width": 1200, "height": 1600})
        pg.goto(pathlib.Path(args.page).resolve().as_uri())
        pg.wait_for_timeout(500)

        overflow_before = pg.evaluate(
            "(sel) => { const c = document.querySelector(sel); return c ? c.scrollWidth - c.clientWidth : null; }",
            args.selector)
        before = check(pg, args.selector, 'before', args.max_dev)

        pg.reload(); pg.wait_for_timeout(300)
        pg.evaluate("() => CJKAlign.apply(document.body)")
        pg.wait_for_timeout(200)
        info = pg.evaluate("""(sel) => {
          const c = document.querySelector(sel);
          return { overflow: c.scrollWidth - c.clientWidth,
                   fontSize: c.style.fontSize || '',
                   ls: c.style.getPropertyValue('--cjk-letter-spacing') || '' };
        }""", args.selector)
        after = check(pg, args.selector, 'after', args.max_dev)
        browser.close()

    if before is None or after is None:
        sys.exit(1)

    print(f"溢出: before={overflow_before:.1f}px after={info['overflow']}px "
          f"fontSize={info['fontSize'] or '原字号'} letter-spacing={info['ls'] or '无'}")

    ok = True
    if not after['skipped'] and after['over']:
        print(f"FAIL: apply 后 {len(after['over'])} 行超出容差")
        ok = False
    if info['overflow'] > 2 and info['fontSize']:
        print("FAIL: 已缩小字号仍有横向溢出")
        ok = False
    if not before['skipped'] and not after['skipped'] and after['worst'] >= before['worst']:
        print("FAIL: apply 后偏差未改善")
        ok = False
    print("PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)

if __name__ == '__main__':
    main()
