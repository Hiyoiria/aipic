#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_figures.py  ─  Study 2 图表生成（F1–F7）
参考 fig.md 规格说明。

最高要求：
  - 图内无标题
  - 非专有词用中文
  - 基本只用黑白灰（对照组浅灰，实验组深灰/黑）

输出目录：analysis/output/figures/
格式：300 dpi PNG + 矢量 PDF
"""
import sys, io, os, warnings
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import norm, pearsonr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import statsmodels.formula.api as smf

# ── 中文字体 ─────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family':        ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'sans-serif'],
    'axes.unicode_minus': False,
    'font.size':          10,
    'axes.linewidth':     0.8,
    'xtick.major.width':  0.8,
    'ytick.major.width':  0.8,
})

# ── 颜色（黑白灰）────────────────────────────────────────────────
COL_A  = '#AAAAAA'   # 对照组：浅灰
COL_C  = '#333333'   # 实验组：深灰
EDGE   = '#000000'
ALPHA  = 0.35        # 散点透明度
LW     = 1.6         # 线宽

# ── 路径 ─────────────────────────────────────────────────────────
FINAL_DIR = 'analysis/final_data'
ENC       = os.path.join(FINAL_DIR, 'participants.csv')
RESP      = os.path.join(FINAL_DIR, 'responses.csv')
OUT_DIR   = 'analysis/output/figures'
os.makedirs(OUT_DIR, exist_ok=True)

def savefig(name):
    for fmt, dpi in [('png', 300), ('pdf', None)]:
        path = os.path.join(OUT_DIR, f'{name}.{fmt}')
        plt.savefig(path, dpi=dpi, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
    print(f'  → {name}.png / .pdf')
    plt.close()

# ── 数据加载（final_data/ 已完成 MC 过滤）───────────────────────
enc = pd.read_csv(ENC)
enc['group'] = enc['组别'].map({0: '对照', 1: '实验'})

VALID = {'ai_01','ai_02','ai_04','ai_08','ai_09','ai_13','ai_15','ai_16','ai_19',
         'real_01','real_02','real_03','real_04','real_05','real_06',
         'real_11','real_12','real_14','real_15','real_16','real_20'}
AI_IDS = {x for x in VALID if x.startswith('ai_')}

resp = pd.read_csv(RESP)
resp = resp[resp['participant_id'].isin(set(enc['participant_id'])) &
            resp['image_id'].isin(VALID)].copy()
resp = resp.merge(enc[['participant_id','group']], on='participant_id', how='left')
resp['img_type'] = resp['image_id'].apply(lambda x: 'AI' if x in AI_IDS else 'Real')

# SDT per participant
sdt_rows = []
for pid, g in resp.groupby('participant_id'):
    ai_g  = g[g['img_type']=='AI']
    re_g  = g[g['img_type']=='Real']
    n_ai, n_re = len(ai_g), len(re_g)
    if n_ai == 0 or n_re == 0: continue
    hr_ll  = (ai_g['is_correct'].sum()       + 0.5) / (n_ai + 1)
    far_ll = ((re_g['is_correct']==0).sum()  + 0.5) / (n_re + 1)
    hr_raw  = ai_g['is_correct'].mean()
    far_raw = 1 - re_g['is_correct'].mean()
    dp  = norm.ppf(hr_ll)  - norm.ppf(far_ll)
    c_v = -0.5 * (norm.ppf(hr_ll) + norm.ppf(far_ll))
    sdt_rows.append({'participant_id': pid,
                     'dprime': dp, 'c': c_v,
                     'hr': hr_raw, 'far': far_raw})
sdt_df = pd.DataFrame(sdt_rows)

master = enc.merge(sdt_df, on='participant_id', how='left')
master = master.rename(columns={
    '整体正确率':  'acc_total',
    'AI图正确率':  'acc_ai',
    '真实图正确率': 'acc_real',
    '前测自评能力': 'self_abil',
    'AI熟悉度':   'ai_fam',
    'AI使用频率(1-5)': 'ai_exp',
    '后测表现自评': 'self_perf',
})
master['calib_gap'] = master['self_perf'] / 5 - master['acc_total']

gA = master[master['group']=='对照']
gC = master[master['group']=='实验']
nA, nC = len(gA), len(gC)

print(f'样本：A={nA}, C={nC}  图像：{len(VALID)} 张')

# ════════════════════════════════════════════════════════════════
# F1  干预主效应对比图（两子图：a 0–1指标 / b SDT指标）
# ════════════════════════════════════════════════════════════════
print('F1...')

# 从数据计算
def ms_se(series):
    a = series.dropna().values.astype(float)
    return a.mean(), a.std(ddof=1) / np.sqrt(len(a))

F1a_vars = [
    ('acc_total', '辨别准确率'),
    ('hr',        '命中率 HR'),
    ('far',       '虚报率 FAR'),
]
F1b_vars = [
    ('dprime', "敏感度 d'"),
    ('c',      '判断标准 c'),
]

fig, axes = plt.subplots(1, 2, figsize=(9, 4.5),
                         gridspec_kw={'width_ratios': [3, 2]})

for ax, var_list, ylabel in zip(
        axes,
        [F1a_vars, F1b_vars],
        ['正确率 / 比率', "d'  /  c 值"]):

    labels = [lbl for _, lbl in var_list]
    x = np.arange(len(labels))
    bw = 0.32

    for i, (col, lbl) in enumerate(var_list):
        mA, seA = ms_se(gA[col])
        mC, seC = ms_se(gC[col])
        ax.bar(x[i]-bw/2, mA, bw, color=COL_A, edgecolor=EDGE, linewidth=0.7,
               label='对照组' if i==0 else '')
        ax.bar(x[i]+bw/2, mC, bw, color=COL_C, edgecolor=EDGE, linewidth=0.7,
               label='实验组' if i==0 else '')
        ax.errorbar(x[i]-bw/2, mA, yerr=seA, fmt='none', color=EDGE, linewidth=0.8, capsize=3)
        ax.errorbar(x[i]+bw/2, mC, yerr=seC, fmt='none', color=EDGE, linewidth=0.8, capsize=3)

    # 显著性标注
    sig_map = {'辨别准确率': '*', "命中率 HR": '*', "敏感度 d'": '*'}
    for i, (col, lbl) in enumerate(var_list):
        if lbl in sig_map:
            mA, seA = ms_se(gA[col])
            mC, seC = ms_se(gC[col])
            top = max(mA+seA, mC+seC) + 0.04
            ax.plot([x[i]-bw/2, x[i]+bw/2], [top, top], color=EDGE, lw=0.8)
            ax.text(x[i], top+0.01, sig_map[lbl], ha='center', va='bottom', fontsize=11)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.axhline(0, color=EDGE, lw=0.5, ls='-')
    ax.spines[['top','right']].set_visible(False)
    ax.grid(axis='y', lw=0.4, color='#DDDDDD')

axes[0].legend(loc='upper right', fontsize=8, framealpha=0.5)
axes[0].set_ylim(0, None)
plt.tight_layout(pad=1.5)
savefig('F1_main_effect')

# ════════════════════════════════════════════════════════════════
# F2  交互效应折线图（AI图 vs 真实图，A vs C）
# ════════════════════════════════════════════════════════════════
print('F2...')

# 数据
F2 = {
    'AI图像':   {'对照': (0.580, 0.207/np.sqrt(54)), '实验': (0.663, 0.218/np.sqrt(58))},
    '真实图像': {'对照': (0.603, 0.201/np.sqrt(54)), '实验': (0.655, 0.200/np.sqrt(58))},
}
xticks = list(F2.keys())
x_pos  = [0, 1]

fig, ax = plt.subplots(figsize=(5.5, 4))

for grp, col, ls, mk, lbl in [
        ('对照', COL_A, '--', 'o', '对照组'),
        ('实验', COL_C, '-',  's', '实验组')]:
    means = [F2[k][grp][0] for k in xticks]
    ses   = [F2[k][grp][1] for k in xticks]
    ax.plot(x_pos, means, color=col, ls=ls, lw=LW, marker=mk,
            markersize=7, label=lbl)
    ax.errorbar(x_pos, means, yerr=ses, fmt='none', color=col, lw=0.8, capsize=4)

# 标注差异
annots = [
    (0, 0.663+0.218/np.sqrt(58)+0.025, 'Δ=+8.3%\np=.042*'),
    (1, 0.655+0.200/np.sqrt(58)+0.025, 'Δ=+5.2%\np=.175 n.s.'),
]
for xi, y, txt in annots:
    ax.text(xi, y, txt, ha='center', va='bottom', fontsize=7.5, color='#555555')

ax.set_xticks(x_pos)
ax.set_xticklabels(xticks, fontsize=10)
ax.set_ylabel('正确率', fontsize=10)
ax.set_ylim(0.45, 0.80)
ax.spines[['top','right']].set_visible(False)
ax.grid(axis='y', lw=0.4, color='#DDDDDD')
ax.legend(loc='upper right', fontsize=9, framealpha=0.4)
plt.tight_layout()
savefig('F2_interaction')

# ════════════════════════════════════════════════════════════════
# F3  调节效应图（前测自评 × 组别 → 准确率）
# ════════════════════════════════════════════════════════════════
print('F3...')

mod_df = master[['acc_total','self_abil','group']].dropna().copy()
mod_df['group_c'] = (mod_df['group']=='实验').astype(float)
mod_df['sae_c']   = mod_df['self_abil'] - mod_df['self_abil'].mean()

m_mod = smf.ols('acc_total ~ group_c * sae_c', data=mod_df).fit()

x_grid = np.linspace(1, 5, 100)
x_c    = x_grid - mod_df['self_abil'].mean()
pred_A = m_mod.params['Intercept'] + m_mod.params['sae_c'] * x_c
pred_C = (m_mod.params['Intercept'] + m_mod.params['group_c']
          + (m_mod.params['sae_c'] + m_mod.params['group_c:sae_c']) * x_c)

# CI bands via prediction variance (简化：用 ±1 SE of residuals)
res_se = np.sqrt(m_mod.mse_resid)
ci_hw  = 1.96 * res_se / np.sqrt(len(mod_df))

fig, ax = plt.subplots(figsize=(6, 4.5))

# 散点（jitter）
rng = np.random.default_rng(42)
for grp, col, mk in [('对照', COL_A, 'o'), ('实验', COL_C, 's')]:
    sub = mod_df[mod_df['group']==grp]
    jx  = sub['self_abil'].values + rng.uniform(-0.08, 0.08, len(sub))
    ax.scatter(jx, sub['acc_total'].values, color=col, marker=mk,
               alpha=ALPHA, s=30, edgecolors='none', label=f'{grp}组')

# 回归线 + CI阴影
for pred, col, ls in [(pred_A, COL_A, '--'), (pred_C, COL_C, '-')]:
    ax.plot(x_grid, pred, color=col, lw=LW, ls=ls)
    ax.fill_between(x_grid, pred-ci_hw, pred+ci_hw, color=col, alpha=0.12)

# 简单斜率标注
ax.text(1.7, 0.88, '低自评:\nB=+0.092, p=.015*', fontsize=7.5, color='#444444',
        ha='center', va='bottom')
ax.text(3.9, 0.55, '高自评:\nB=+0.016, p=.680', fontsize=7.5, color='#888888',
        ha='center', va='bottom')

ax.set_xlabel('前测自评辨别能力（1–5）', fontsize=10)
ax.set_ylabel('辨别准确率', fontsize=10)
ax.set_xlim(0.5, 5.5)
ax.set_ylim(0.05, 1.05)
ax.spines[['top','right']].set_visible(False)
ax.grid(lw=0.3, color='#EEEEEE')
ax.legend(loc='lower right', fontsize=8.5, framealpha=0.4)
plt.tight_layout()
savefig('F3_moderation')

# ════════════════════════════════════════════════════════════════
# F4  异质性森林图
# ════════════════════════════════════════════════════════════════
print('F4...')

# 使用 fig.md 中的数据（加入学历三分类行，替换旧两分）
forest_groups = [
    # (label,   B,     SE,    p,      group_band)
    ('全样本',         0.065, 0.029, .027,  0),
    # 性别
    ('性别：男',       0.108, 0.040, .009,  1),
    ('性别：女',       0.044, 0.041, .289,  1),
    # 年龄
    ('年龄：≤34',      0.059, 0.033, .075,  2),
    ('年龄：≥35',      0.084, 0.064, .201,  2),
    # 学历（三分类）
    ('学历：低',       0.020, 0.052, .700,  3),
    ('学历：中（本科）', 0.084, 0.043, .050,  3),
    ('学历：高',       0.075, 0.038, .050,  3),
    # AI频率
    ('AI频率：低',     0.018, 0.036, .622,  4),
    ('AI频率：高',     0.112, 0.041, .008,  4),
    # 前测自评
    ('前测自评：低(1-2)', 0.084, 0.049, .097, 5),
    ('前测自评：高(3-5)', 0.040, 0.034, .246, 5),
]

labels   = [r[0] for r in forest_groups]
Bs       = np.array([r[1] for r in forest_groups])
SEs      = np.array([r[2] for r in forest_groups])
ps       = np.array([r[3] for r in forest_groups])
bands    = [r[4] for r in forest_groups]

ci_lo = Bs - 1.96*SEs
ci_hi = Bs + 1.96*SEs
sig   = ps < .05

n_rows = len(labels)
y_pos  = np.arange(n_rows, 0, -1, dtype=float)

# 略微拉开全样本与子群之间的间距
y_pos[1:] -= 0.4

fig, ax = plt.subplots(figsize=(8.5, 0.45*n_rows + 2.5))

# 背景条纹（每个维度组交替）
band_colors = {0: None, 1: '#F5F5F5', 2: None, 3: '#F5F5F5', 4: None, 5: '#F5F5F5'}
prev_band = None
band_y = []
for i, (bd, yp) in enumerate(zip(bands, y_pos)):
    if bd != prev_band:
        if band_y and band_colors.get(bands[i-1]):
            ax.axhspan(min(band_y)-0.5, max(band_y)+0.5,
                       color=band_colors[bands[i-1]], zorder=0, alpha=0.6)
        band_y = [yp]
        prev_band = bd
    else:
        band_y.append(yp)
if band_y and band_colors.get(bands[-1]):
    ax.axhspan(min(band_y)-0.5, max(band_y)+0.5,
               color=band_colors[bands[-1]], zorder=0, alpha=0.6)

# 参考线
ax.axvline(0,     color='#888888', ls='--', lw=0.8, zorder=1)
ax.axvline(0.065, color='#BBBBBB', ls=':',  lw=0.8, zorder=1)

# CI 线 + 点
for i, (y, B, lo, hi, p_v, lbl) in enumerate(zip(y_pos, Bs, ci_lo, ci_hi, ps, labels)):
    span_zero = lo <= 0 <= hi
    ci_col = '#AAAAAA' if span_zero else EDGE
    mk_col = '#FFFFFF' if (not sig[i] and i > 0) else (EDGE if i > 0 else '#000000')
    mk_ec  = EDGE
    mk_s   = 90 if i == 0 else 55
    mk_sh  = 'D' if i == 0 else ('o' if sig[i] else 'o')

    ax.plot([lo, hi], [y, y], color=ci_col, lw=1.2, zorder=2)
    ax.plot([lo, lo], [y-0.06, y+0.06], color=ci_col, lw=1.0, zorder=2)
    ax.plot([hi, hi], [y-0.06, y+0.06], color=ci_col, lw=1.0, zorder=2)
    ax.scatter(B, y, s=mk_s, color=mk_col, edgecolors=mk_ec,
               linewidths=0.9, marker=mk_sh, zorder=3)

    # 全样本行加粗标签
    fw = 'bold' if i == 0 else 'normal'
    ax.text(-0.36, y, lbl, ha='right', va='center', fontsize=8.5, fontweight=fw)

    # 右侧数值
    star = '***' if p_v<.001 else ('**' if p_v<.01 else ('*' if p_v<.05 else ''))
    ax.text(0.27, y,
            f'{B:+.3f} [{lo:+.3f}, {hi:+.3f}]{star}',
            ha='left', va='center', fontsize=7.5, family='monospace')

ax.set_yticks([])
ax.set_xlabel('组别效应 B（实验组 − 对照组）', fontsize=9)
ax.set_xlim(-0.37, 0.45)
ax.set_ylim(min(y_pos)-0.8, max(y_pos)+0.8)
ax.spines[['top','right','left']].set_visible(False)

# 图例
from matplotlib.lines import Line2D
legend_el = [
    Line2D([0],[0], marker='D', color='w', markerfacecolor=EDGE, markersize=7,
           markeredgecolor=EDGE, label='全样本总效应'),
    Line2D([0],[0], marker='o', color='w', markerfacecolor=EDGE, markersize=6,
           markeredgecolor=EDGE, label='显著子群（实心）'),
    Line2D([0],[0], marker='o', color='w', markerfacecolor='white', markersize=6,
           markeredgecolor=EDGE, label='不显著子群（空心）'),
]
ax.legend(handles=legend_el, loc='lower right', fontsize=7.5, framealpha=0.5)
plt.tight_layout()
savefig('F4_forest')

# ════════════════════════════════════════════════════════════════
# F5  逐图哑铃图（dumbbell chart，按 Δ 降序）
# ════════════════════════════════════════════════════════════════
print('F5...')

# 从 responses 按图计算
per_img = []
for img_id in VALID:
    sub = resp[resp['image_id']==img_id]
    aA  = sub[sub['group']=='对照']['is_correct'].mean()
    aC  = sub[sub['group']=='实验']['is_correct'].mean()
    per_img.append({'img': img_id, 'aA': aA, 'aC': aC,
                    'diff': aC - aA,
                    'type': 'AI' if img_id in AI_IDS else 'Real'})
img_df = pd.DataFrame(per_img).sort_values('diff', ascending=False).reset_index(drop=True)

fig, ax = plt.subplots(figsize=(7, 8.5))

for i, row in img_df.iterrows():
    y    = len(img_df) - i - 1
    aA, aC, diff = row['aA'], row['aC'], row['diff']
    col_seg = COL_C if diff >= 0 else COL_A

    ax.plot([aA, aC], [y, y], color=col_seg, lw=1.4, zorder=2)
    ax.scatter(aA, y, color=COL_A, edgecolors=EDGE, s=40, lw=0.6, zorder=3)
    ax.scatter(aC, y, color=COL_C, edgecolors=EDGE, s=40, lw=0.6, marker='s', zorder=3)

    # 标签
    prefix = '■' if row['type']=='AI' else '●'
    ax.text(-0.025, y, f"{prefix} {row['img']}", ha='right', va='center', fontsize=8)

    # 差异值标注（|Δ|>0.10）
    if abs(diff) >= 0.10:
        ax.text(max(aA, aC)+0.018, y, f'{diff:+.3f}',
                va='center', ha='left', fontsize=7, color='#444444')

ax.axvline(0.5, color='#AAAAAA', ls='--', lw=0.8)
ax.set_xlim(-0.05, 1.12)
ax.set_ylim(-0.8, len(img_df)-0.2)
ax.set_xlabel('正确率', fontsize=10)
ax.set_yticks([])
ax.spines[['top','right','left']].set_visible(False)
ax.text(0.5, -0.6, '随机猜测基准（50%）', ha='center', fontsize=7, color='#888888')

legend_el = [
    Line2D([0],[0], marker='o', color='w', markerfacecolor=COL_A, markeredgecolor=EDGE,
           markersize=7, label='对照组'),
    Line2D([0],[0], marker='s', color='w', markerfacecolor=COL_C, markeredgecolor=EDGE,
           markersize=7, label='实验组'),
    Line2D([0],[0], color='w', lw=0, marker='$■$', markersize=8,
           markerfacecolor='#333333', label='AI 图像'),
    Line2D([0],[0], color='w', lw=0, marker='$●$', markersize=8,
           markerfacecolor='#888888', label='真实图像'),
]
ax.legend(handles=legend_el, loc='lower right', fontsize=8, framealpha=0.5)
plt.tight_layout()
savefig('F5_per_image')

# ════════════════════════════════════════════════════════════════
# F6  校准曲线（信心等级 × 实际正确率）
# ════════════════════════════════════════════════════════════════
print('F6...')

if 'confidence' in resp.columns:
    resp['conf_int'] = resp['confidence'].round().astype(int).clip(0, 5)
    calib_rows = []
    for conf_lv in range(6):
        for grp in ['对照','实验']:
            sub = resp[(resp['conf_int']==conf_lv) & (resp['group']==grp)]
            if len(sub) > 0:
                calib_rows.append({'conf': conf_lv, 'group': grp,
                                   'acc': sub['is_correct'].mean(), 'n': len(sub)})
    calib_df = pd.DataFrame(calib_rows)

    fig, ax = plt.subplots(figsize=(6, 4.5))

    # 完美校准线
    xp = np.array([0,1,2,3,4,5])
    ax.plot(xp, xp/5, color='#AAAAAA', ls='--', lw=1, label='完美校准线', zorder=1)
    ax.axhline(0.5, color='#CCCCCC', ls=':', lw=0.8, zorder=1)

    for grp, col, ls, mk, lbl in [('对照', COL_A, '--', 'o', '对照组'),
                                    ('实验', COL_C, '-',  's', '实验组')]:
        sub = calib_df[calib_df['group']==grp].sort_values('conf')
        xs, ys, ns = sub['conf'].values, sub['acc'].values, sub['n'].values
        ax.plot(xs, ys, color=col, ls=ls, lw=LW, marker=mk, markersize=7, label=lbl, zorder=3)
        # 标注 n
        for x_, y_, n_ in zip(xs, ys, ns):
            mk_style = '' if n_ >= 30 else 'o'
            ax.text(x_+0.08, y_+0.015, f'n={n_}', fontsize=6.5, color='#777777')

    ax.set_xlabel('信心等级（0–5）', fontsize=10)
    ax.set_ylabel('实际正确率', fontsize=10)
    ax.set_xticks(range(6))
    ax.set_ylim(0, 1.05)
    ax.spines[['top','right']].set_visible(False)
    ax.legend(loc='upper left', fontsize=8.5, framealpha=0.4)
    ax.grid(lw=0.3, color='#EEEEEE')
    plt.tight_layout()
    savefig('F6_calibration')
else:
    print('  confidence 列不存在，跳过 F6')

# ════════════════════════════════════════════════════════════════
# F7  相关矩阵热力图（下三角，黑白灰）
# ════════════════════════════════════════════════════════════════
print('F7...')

corr_vars = ['acc_total','dprime','self_abil','ai_fam','ai_exp','calib_gap']
corr_lbls = ['辨别准确率', "敏感度d'", '前测自评能力', 'AI熟悉度', 'AI使用频率', '信心校准差距']

cdf = master[corr_vars].dropna(how='all')
n_v = len(corr_vars)

# 计算 r 矩阵和 p 矩阵
r_mat = np.eye(n_v)
p_mat = np.ones((n_v, n_v))
for i in range(n_v):
    for j in range(i+1, n_v):
        pair = cdf[[corr_vars[i], corr_vars[j]]].dropna()
        if len(pair) > 3:
            r_v, p_v = pearsonr(pair.iloc[:,0], pair.iloc[:,1])
        else:
            r_v, p_v = np.nan, 1.0
        r_mat[i,j] = r_mat[j,i] = r_v
        p_mat[i,j] = p_mat[j,i] = p_v

# 黑白灰热力图：用灰度发散色阶
fig, ax = plt.subplots(figsize=(6.5, 5.5))

mask = np.triu(np.ones_like(r_mat, dtype=bool), k=1)
r_plot = np.where(mask, np.nan, r_mat)

# 自定义灰度发散（负→白，0→中灰，正→黑）不用彩色
from matplotlib.colors import LinearSegmentedColormap
bw_div = LinearSegmentedColormap.from_list(
    'bw_div', ['#FFFFFF', '#BBBBBB', '#333333'], N=256)

im = ax.imshow(r_plot, cmap=bw_div, vmin=-1, vmax=1, aspect='auto')
plt.colorbar(im, ax=ax, shrink=0.8, label='Pearson r')

ax.set_xticks(range(n_v))
ax.set_yticks(range(n_v))
ax.set_xticklabels(corr_lbls, rotation=30, ha='right', fontsize=9)
ax.set_yticklabels(corr_lbls, fontsize=9)

for i in range(n_v):
    for j in range(n_v):
        if mask[i,j] or i == j:
            continue
        r_v = r_mat[i,j]
        p_v = p_mat[i,j]
        star = '***' if p_v<.001 else ('**' if p_v<.01 else ('*' if p_v<.05 else ''))
        txt = f'{r_v:.2f}{star}'
        fc = 'white' if abs(r_v) > 0.45 else 'black'
        ax.text(j, i, txt, ha='center', va='center',
                fontsize=8, color=fc, fontweight='normal')

ax.set_xticks(np.arange(n_v)-0.5, minor=True)
ax.set_yticks(np.arange(n_v)-0.5, minor=True)
ax.grid(which='minor', color='white', linewidth=1.5)
ax.tick_params(which='minor', bottom=False, left=False)
plt.tight_layout()
savefig('F7_correlation_heatmap')

# ════════════════════════════════════════════════════════════════
print(f'\n✓ 所有图表已保存至 {OUT_DIR}/')
