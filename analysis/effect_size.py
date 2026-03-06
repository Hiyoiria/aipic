#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
预实验效应量计算
- 主要指标: 正确率 (accuracy)
- 比较: Group A (对照) vs Group C (策略干预)
- 效应量: Cohen's d, η²（独立样本t检验/Mann-Whitney U）
- 同时报告置信区间建议样本量
"""
import sys
import os
import math
import pandas as pd
import numpy as np
from scipy import stats

sys.stdout.reconfigure(encoding='utf-8')

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
OUT_DIR  = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(OUT_DIR, exist_ok=True)

N_IMAGES = 24  # 完成标准

# ── 读取 & 筛选 ─────────────────────────────────────────────────────────────
r = pd.read_csv(os.path.join(DATA_DIR, 'responses.csv'))
p = pd.read_csv(os.path.join(DATA_DIR, 'participants.csv'))

cnt = r.groupby('participant_id').size().reset_index(name='n')
full_ids = cnt[cnt['n'] >= N_IMAGES]['participant_id']
r_full = r[r['participant_id'].isin(full_ids)].copy()

# 逐人正确率
acc = (r_full.groupby('participant_id')['is_correct']
       .mean().reset_index(name='accuracy'))

# 合并组别
df = acc.merge(p[['participant_id', 'group']], on='participant_id', how='left')

group_A = df[df['group'] == 'A']['accuracy'].values
group_C = df[df['group'] == 'C']['accuracy'].values

n_A, n_C = len(group_A), len(group_C)

print('=' * 60)
print('预实验效应量报告')
print('=' * 60)
print(f'\n完成 {N_IMAGES} 张图的参与者: {len(df)} 人  (A={n_A}, C={n_C})')

# ── 描述统计 ─────────────────────────────────────────────────────────────────
print('\n── 描述统计 ──────────────────────────────────────────────')
for label, arr in [('A (对照)', group_A), ('C (干预)', group_C)]:
    print(f'  Group {label}:  n={len(arr)}  '
          f'M={arr.mean():.4f}  SD={arr.std(ddof=1):.4f}  '
          f'[{arr.min():.3f}, {arr.max():.3f}]')

diff_means = group_C.mean() - group_A.mean()
print(f'\n  均值差 (C - A): {diff_means:+.4f}  ({diff_means*100:+.1f}%)')

# ── Cohen's d（独立样本，pooled SD）────────────────────────────────────────
def cohens_d(x1, x2):
    """x1=实验组, x2=对照组；pooled SD"""
    n1, n2 = len(x1), len(x2)
    s1, s2 = x1.std(ddof=1), x2.std(ddof=1)
    pooled_sd = math.sqrt(((n1 - 1) * s1**2 + (n2 - 1) * s2**2) / (n1 + n2 - 2))
    if pooled_sd == 0:
        return float('nan')
    return (x1.mean() - x2.mean()) / pooled_sd

d = cohens_d(group_C, group_A)

# Hedges' g 校正（小样本偏差修正）
def hedges_g(d, n1, n2):
    df_ = n1 + n2 - 2
    correction = 1 - (3 / (4 * df_ - 1))
    return d * correction

g = hedges_g(d, n_C, n_A)

print('\n── Cohen\'s d & Hedges\' g ─────────────────────────────────')
print(f'  Cohen\'s d  = {d:.4f}')
print(f'  Hedges\' g  = {g:.4f}  (小样本偏差修正)')

magnitude = ('可忽略 (<0.2)' if abs(d) < 0.2
             else '小 (0.2–0.5)' if abs(d) < 0.5
             else '中 (0.5–0.8)' if abs(d) < 0.8
             else '大 (≥0.8)')
print(f'  效应量级别: {magnitude}')

# ── 独立样本 t 检验 ──────────────────────────────────────────────────────────
t_stat, p_val = stats.ttest_ind(group_C, group_A, equal_var=False)  # Welch's t

print('\n── Welch\'s t 检验 ────────────────────────────────────────')
print(f'  t = {t_stat:.4f},  p = {p_val:.4f}  (双尾)')
print(f'  注：n 极小，p 值仅供参考，效应量更具信息量')

# η²（eta squared）= t² / (t² + df)
df_welch = (((group_C.var(ddof=1)/n_C + group_A.var(ddof=1)/n_A)**2) /
            ((group_C.var(ddof=1)/n_C)**2/(n_C-1) +
             (group_A.var(ddof=1)/n_A)**2/(n_A-1)))
eta2 = t_stat**2 / (t_stat**2 + df_welch)
print(f'  η²  = {eta2:.4f}  ({eta2*100:.1f}% 方差解释量)')

# ── Mann-Whitney U（非参数，适合小样本）────────────────────────────────────
u_stat, p_mw = stats.mannwhitneyu(group_C, group_A, alternative='two-sided')
# rank-biserial correlation r = 1 - 2U/(n1*n2)
r_rb = 1 - 2 * u_stat / (n_C * n_A)

print('\n── Mann-Whitney U（非参数）───────────────────────────────')
print(f'  U = {u_stat:.1f},  p = {p_mw:.4f}  (双尾)')
print(f'  rank-biserial r = {r_rb:.4f}  (效果方向: {"C > A" if r_rb > 0 else "A > C"})')

# ── 样本量估算（正式实验参考）──────────────────────────────────────────────
print('\n── 正式实验样本量估算（基于预实验 d）────────────────────')

def power_n(d, alpha=0.05, power=0.80):
    """Cohen (1988) 独立样本 t 检验，双尾，等样本量"""
    from scipy.stats import norm, t as tdist
    if math.isnan(d) or d == 0:
        return float('inf')
    # 迭代近似
    z_alpha = norm.ppf(1 - alpha / 2)
    z_beta  = norm.ppf(power)
    n = ((z_alpha + z_beta) / d) ** 2 * 2  # 初始估计
    for _ in range(20):  # 精炼
        df_ = 2 * n - 2
        t_alpha = tdist.ppf(1 - alpha / 2, df_)
        t_beta  = tdist.ppf(power, df_)
        n = ((t_alpha + t_beta) / d) ** 2 * 2
    return math.ceil(n)

for alpha, power, label in [(0.05, 0.80, 'α=.05, power=.80'),
                              (0.05, 0.90, 'α=.05, power=.90'),
                              (0.01, 0.80, 'α=.01, power=.80')]:
    n_each = power_n(abs(d), alpha=alpha, power=power)
    print(f'  {label}:  每组 n ≈ {n_each}，共 {n_each*2}')

print('\n  注：以上基于预实验 d 估算，样本量较少时 d 不稳定。')
print('  建议在 d 基础上增加 20–30% 缓冲，并以 Hedges\' g 为准。')

# ── 汇总输出 ─────────────────────────────────────────────────────────────────
results = {
    'n_A': n_A, 'n_C': n_C,
    'mean_A': group_A.mean(), 'sd_A': group_A.std(ddof=1),
    'mean_C': group_C.mean(), 'sd_C': group_C.std(ddof=1),
    'mean_diff_C_minus_A': diff_means,
    'cohens_d': d, 'hedges_g': g,
    't_stat': t_stat, 'p_ttest': p_val,
    'eta_squared': eta2,
    'U_stat': u_stat, 'p_mannwhitney': p_mw,
    'rank_biserial_r': r_rb,
    'n_per_group_power80': power_n(abs(d), 0.05, 0.80),
    'n_per_group_power90': power_n(abs(d), 0.05, 0.90),
}

out = pd.DataFrame([results])
out_path = os.path.join(OUT_DIR, 'effect_size.csv')
out.to_csv(out_path, index=False, encoding='utf-8-sig')
print(f'\n结果已保存: {out_path}')
print('=' * 60)
