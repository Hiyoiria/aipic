#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
describe_participants.py
────────────────────────────────────────────────────────────
对 participant_summary_full.csv 进行描述性统计汇总。

输出：analysis/output/participant_description.txt
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

IN_FILE  = 'analysis/output/participant_summary_full.csv'
OUT_FILE = 'analysis/output/participant_description.txt'

df = pd.read_csv(IN_FILE)

lines = []

def pr(*args):
    s = ' '.join(str(a) for a in args)
    print(s)
    lines.append(s)

def sep(title=''):
    if title:
        pr(f'\n{"─"*50}')
        pr(f'  {title}')
        pr(f'{"─"*50}')
    else:
        pr(f'{"─"*50}')

def fmt(x):
    if pd.isna(x):
        return 'NaN'
    if isinstance(x, float):
        return f'{x:.3f}'
    return str(x)

def ttest_md(a, b, label):
    """Welch t-test + Cohen d，返回格式化字符串"""
    a = a.dropna(); b = b.dropna()
    if len(a) < 2 or len(b) < 2:
        return f'{label}: 样本不足'
    t, p = stats.ttest_ind(a, b, equal_var=False)
    pool_sd = np.sqrt((a.std(ddof=1)**2 + b.std(ddof=1)**2) / 2)
    d = (a.mean() - b.mean()) / pool_sd if pool_sd > 0 else np.nan
    p_str = f'< .001' if p < .001 else f'= {p:.3f}'
    star = '***' if p < .001 else ('**' if p < .01 else ('*' if p < .05 else ''))
    return (f'{label}: A={a.mean():.3f}±{a.std(ddof=1):.3f}, '
            f'C={b.mean():.3f}±{b.std(ddof=1):.3f}, '
            f't({len(a)+len(b)-2:.0f})={t:.3f}, p {p_str}{star}, d={d:.3f}')

# ── 0. 基本信息 ───────────────────────────────────────────────────
sep('0. 数据来源')
pr(f'文件：{IN_FILE}')
pr(f'总行数（被试数）：{len(df)}')
pr(f'列名：{list(df.columns)}')

# ── 1. 样本分布 ───────────────────────────────────────────────────
sep('1. 样本分布')

pr('按组别：')
pr(df['组别'].value_counts().sort_index().to_string())

pr('\n按来源：')
pr(df['来源'].value_counts().sort_index().to_string())

pr('\n按组别 × 来源：')
ct = pd.crosstab(df['组别'], df['来源'], margins=True)
pr(ct.to_string())

# ── 2. 前测完整性 ──────────────────────────────────────────────────
sep('2. 前测完整性（presurvey_incomplete）')

inc = df['presurvey_incomplete'].value_counts().sort_index()
pr(f'完整（0）：{inc.get(0, 0)} 人')
pr(f'不完整（1）：{inc.get(1, 0)} 人')

pr('\n不完整者分布（按组别 × 来源）：')
sub = df[df['presurvey_incomplete'] == 1]
if len(sub) > 0:
    pr(pd.crosstab(sub['组别'], sub['来源'], margins=True).to_string())
    pr('\n不完整者字段一览：')
    show_cols = [c for c in ['participant_id', '组别', '来源',
                             'AI熟悉度', '前测自评能力', 'AI使用频率(1-5)'] if c in sub.columns]
    pr(sub[show_cols].to_string(index=False))
else:
    pr('无前测不完整被试。')

# ── 3. 前测 AI 相关变量描述 ────────────────────────────────────────
sep('3. 前测 AI 相关变量（仅前测完整者）')

df_ok = df[df['presurvey_incomplete'] == 0].copy()
pr(f'前测完整被试：{len(df_ok)} 人（A={len(df_ok[df_ok["组别"]=="A"])}, C={len(df_ok[df_ok["组别"]=="C"])}）')

num_cols = ['AI熟悉度', '前测自评能力', 'AI使用频率(1-5)', 'AI素养综合分']
for col in num_cols:
    if col not in df_ok.columns:
        continue
    pr(f'\n[{col}]')
    for g, gdf in df_ok.groupby('组别'):
        v = gdf[col].dropna()
        pr(f'  组{g}（n={len(v)}）: M={v.mean():.3f}, SD={v.std(ddof=1):.3f}, '
           f'Mdn={v.median():.3f}, [min={v.min():.3f}, max={v.max():.3f}]')

pr('\nAI使用频率分布（前测完整者，1=never … 5=very-often）：')
freq_col = 'AI使用频率(1-5)' if 'AI使用频率(1-5)' in df_ok.columns else 'AI使用频率'
if freq_col in df_ok.columns:
    freq_ct = pd.crosstab(df_ok[freq_col], df_ok['组别'])
    pr(freq_ct.to_string())

# ── 4. 组间前测差异 t 检验 ────────────────────────────────────────
sep('4. 组间前测差异（Welch t-test，仅前测完整者）')

a_ok = df_ok[df_ok['组别'] == 'A']
c_ok = df_ok[df_ok['组别'] == 'C']

for col in ['AI熟悉度', '前测自评能力', 'AI使用频率(1-5)', 'AI素养综合分']:
    if col in df_ok.columns:
        pr(ttest_md(a_ok[col], c_ok[col], col))

# ── 5. 准确率描述 ──────────────────────────────────────────────────
sep('5. 准确率描述统计（所有被试，按组别）')

acc_cols = ['整体正确率', 'AI图正确率', '真实图正确率']
for col in acc_cols:
    if col not in df.columns:
        continue
    pr(f'\n[{col}]')
    for g, gdf in df.groupby('组别'):
        v = gdf[col].dropna()
        pr(f'  组{g}（n={len(v)}）: M={v.mean():.3f}, SD={v.std(ddof=1):.3f}, '
           f'Mdn={v.median():.3f}, [min={v.min():.3f}, max={v.max():.3f}]')

pr('\n准确率组间差异（Welch t-test，全部被试）：')
a_df = df[df['组别'] == 'A']
c_df = df[df['组别'] == 'C']
for col in acc_cols:
    if col in df.columns:
        pr(ttest_md(a_df[col], c_df[col], col))

# ── 6. 后测自评 ────────────────────────────────────────────────────
sep('6. 后测表现自评（self_performance）')

if '后测表现自评' in df.columns:
    for g, gdf in df.groupby('组别'):
        v = gdf['后测表现自评'].dropna()
        pr(f'  组{g}（n={len(v)}）: M={v.mean():.3f}, SD={v.std(ddof=1):.3f}, '
           f'Mdn={v.median():.3f}')
    pr(ttest_md(a_df['后测表现自评'], c_df['后测表现自评'], '后测表现自评'))

# ── 7. 相关矩阵（数值列）──────────────────────────────────────────
sep('7. 关键变量相关矩阵（Pearson r, * p<.05, ** p<.01, *** p<.001）')

corr_vars = [c for c in ['AI熟悉度','前测自评能力','AI使用频率(1-5)','AI素养综合分',
                          '整体正确率','AI图正确率','真实图正确率','后测表现自评']
             if c in df_ok.columns]

n_v = len(corr_vars)
header = f"{'':18s}" + ''.join(f'{v[:6]:>9s}' for v in corr_vars)
pr(header)
for i, vi in enumerate(corr_vars):
    row_str = f'{vi[:18]:18s}'
    for j, vj in enumerate(corr_vars):
        if j < i:
            row_str += f'{"":>9s}'
        elif j == i:
            row_str += f'{"1.000":>9s}'
        else:
            pair = df_ok[[vi, vj]].dropna()
            if len(pair) < 3:
                row_str += f'{"N/A":>9s}'
            else:
                r_val, p_val = stats.pearsonr(pair[vi], pair[vj])
                star = '***' if p_val<.001 else ('**' if p_val<.01 else ('*' if p_val<.05 else ''))
                row_str += f'{r_val:>6.3f}{star:>3s}'
    pr(row_str)

# ── 8. 快速概览（一行汇总）────────────────────────────────────────
sep('8. 快速概览')
pr(f'总样本 N={len(df)}（A={len(df[df["组别"]=="A"])}, C={len(df[df["组别"]=="C"])}）')
pr(f'来源：real={len(df[df["来源"]=="real"])}, synth={len(df[df["来源"]=="synth"])}')
pr(f'前测完整：{len(df_ok)} / {len(df)}（{len(df_ok)/len(df)*100:.1f}%）')
for col in ['整体正确率','AI图正确率','真实图正确率']:
    if col in df.columns:
        pr(f'{col}：A组 M={a_df[col].mean():.3f}, C组 M={c_df[col].mean():.3f}, '
           f'差值={c_df[col].mean()-a_df[col].mean():+.3f}')

pr('\n=== 汇总完毕 ===')

# ── 保存 ──────────────────────────────────────────────────────────
with open(OUT_FILE, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print(f'\n已保存 -> {OUT_FILE}')
