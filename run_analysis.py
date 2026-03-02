#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_analysis.py  ─  Study 2 一键运行所有分析
═══════════════════════════════════════════════════════════
数据来源：analysis/final_data/（MC 通过后，N=106，A=54，C=52）

依次执行：
  1. formal_analysis.py     → analysis/output/formal_report.md + 回归/异质性 CSV
  2. make_figures.py        → analysis/output/figures/ (F1–F7 PNG + PDF)
  3. strategy_text_analysis.py → analysis/output/strategy_*.csv + strategy_text_report.md

用法：
  python run_analysis.py
═══════════════════════════════════════════════════════════
"""
import sys, subprocess, time, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SCRIPTS = [
    ('正式统计分析',   'analysis/formal_analysis_v2.py'),
    ('图表生成',       'analysis/make_figures.py'),
    ('策略文本分析',   'analysis/strategy_text_analysis.py'),
]

def run(label, path):
    print(f'\n{"═"*60}')
    print(f'▶  {label}  ({path})')
    print('═'*60)
    t0 = time.time()
    result = subprocess.run(
        [sys.executable, path],
        capture_output=False,   # 直接输出到终端
        text=True,
        encoding='utf-8',
    )
    elapsed = time.time() - t0
    if result.returncode != 0:
        print(f'\n✗  {label} 运行失败（return code {result.returncode}）')
        sys.exit(result.returncode)
    print(f'\n✓  {label} 完成（{elapsed:.1f}s）')

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    total_t0 = time.time()
    for label, path in SCRIPTS:
        run(label, path)
    print(f'\n{"═"*60}')
    print(f'✓  全部完成（{time.time()-total_t0:.1f}s）')
    print('═'*60)
    print('输出目录：')
    print('  analysis/output/formal_report.md')
    print('  analysis/output/figures/  (F1–F7)')
    print('  analysis/output/strategy_text_report.md')
