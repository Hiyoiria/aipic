#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sensitivity_ai_literacy.py
─────────────────────────────────────────────────────────────────────
对"AI素养"操作化的敏感性分析：同一组控制变量，分三种方式处理熟悉度与频率

  模型A：只保留 AI使用频率        (ai_exposure_num)
  模型B：只保留 AI熟悉度          (ai_familiarity)
  模型C：综合分 = z(熟悉度) + z(频率) 均值（AI素养综合分）

DV：acc_total（识别准确率）、d'（SDT敏感度）、calibration_gap（信心校准）
每个 DV × 3 种操作化 = 9 个模型，全部输出 B/SE/Beta/t/p/VIF 详细表

输出：
  analysis/output/sensitivity_ai_literacy.md
  analysis/output/sensitivity_ai_literacy.csv  （汇总：每行 = 1 个模型的 group_c 行）
"""
import sys, os, warnings
import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor as _vif_func
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.stattools import durbin_watson as dw_test

sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

# ── 路径 ────────────────────────────────────────────────────────────
FINAL_DIR = os.path.join(os.path.dirname(__file__), 'final_data')
OUT_DIR   = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(OUT_DIR, exist_ok=True)

out_path = os.path.join(OUT_DIR, 'sensitivity_ai_literacy.md')
_log = open(out_path, 'w', encoding='utf-8')

def pr(*a, **kw):
    print(*a, **kw); print(*a, **kw, file=_log)

def h1(t): pr(f'\n# {t}\n')
def h2(t): pr(f'\n## {t}\n')
def h3(t): pr(f'\n### {t}\n')

# ── 格式化辅助 ──────────────────────────────────────────────────────
def stars(p):
    if pd.isna(p): return ''
    if p < .001: return '***'
    if p < .01:  return '**'
    if p < .05:  return '*'
    return ''

def fmt_p(p):
    if pd.isna(p): return '—'
    if p < .001:   return '< .001'
    s = f'{p:.3f}'
    return s.lstrip('0') or '.000'

# ── 数据加载 ────────────────────────────────────────────────────────
ext = pd.read_csv(os.path.join(FINAL_DIR, 'participants.csv'))
ext = ext.rename(columns={
    '组别':            'group_num',
    'AI熟悉度':        'ai_familiarity',
    '前测自评能力':    'self_assessed_ability',
    'AI使用频率(1-5)': 'ai_exposure_num',
    '整体正确率':      'acc_total',
    '后测表现自评':    'self_performance',
    '性别':            'gender_num',
    '年龄段':          'age_num',
    '学历分组':        'edu_group',
})
ext['group']   = ext['group_num'].map({0:'对照', 1:'实验'})
ext['group_c'] = ext['group_num'].astype(float)

r_all = pd.read_csv(os.path.join(FINAL_DIR, 'responses.csv'))
lg    = pd.read_csv(os.path.join(FINAL_DIR, 'interaction_logs.csv'))

# SDT per participant
def sdt_person(df_p):
    ai   = df_p[df_p['image_type'] == 'AI']
    real = df_p[df_p['image_type'] == 'Real']
    if len(ai) == 0 or len(real) == 0:
        return dict(dprime=np.nan, c=np.nan)
    hits = (ai['judgment'] == 'AI').sum()
    fas  = (real['judgment'] == 'AI').sum()
    hr_  = (hits + 0.5) / (len(ai) + 1)
    far_ = (fas  + 0.5) / (len(real) + 1)
    dp = stats.norm.ppf(hr_) - stats.norm.ppf(far_)
    c_ = -0.5 * (stats.norm.ppf(hr_) + stats.norm.ppf(far_))
    return dict(dprime=dp, c=c_)

IMAGE_TYPES = {
    'ai_01':'AI','ai_02':'AI','ai_04':'AI','ai_08':'AI','ai_09':'AI',
    'ai_13':'AI','ai_15':'AI','ai_16':'AI','ai_19':'AI',
    'real_01':'Real','real_02':'Real','real_03':'Real','real_04':'Real',
    'real_05':'Real','real_06':'Real','real_11':'Real','real_12':'Real',
    'real_14':'Real','real_15':'Real','real_16':'Real','real_20':'Real',
}
r_all['image_type'] = r_all['image_id'].map(IMAGE_TYPES)
r_valid = r_all[r_all['image_id'].isin(IMAGE_TYPES)].copy()

sdt_list = []
for pid, g in r_valid.groupby('participant_id'):
    d = sdt_person(g); d['participant_id'] = pid; sdt_list.append(d)
sdt = pd.DataFrame(sdt_list)

master = ext.merge(sdt, on='participant_id', how='left')
master['calibration_gap'] = master['self_performance'] / 5 - master['acc_total']

# ── AI素养综合分 ────────────────────────────────────────────────────
# z-标准化后取均值（需要两列均有值）
literacy_df = master[['ai_familiarity', 'ai_exposure_num']].copy()
master['z_familiarity'] = (literacy_df['ai_familiarity'] - literacy_df['ai_familiarity'].mean()) / \
                           literacy_df['ai_familiarity'].std(ddof=1)
master['z_exposure']    = (literacy_df['ai_exposure_num'] - literacy_df['ai_exposure_num'].mean()) / \
                           literacy_df['ai_exposure_num'].std(ddof=1)
master['ai_literacy_composite'] = (master['z_familiarity'] + master['z_exposure']) / 2

# ── 回归输出函数 ────────────────────────────────────────────────────
_VAR_LBL = {
    'group_c':               '是否进行信息干预（C=1）',
    'self_assessed_ability': '前测自评能力（1–5）',
    'ai_exposure_num':       'AI使用频率（1–5）',
    'ai_familiarity':        'AI熟悉度（1–5）',
    'ai_literacy_composite': 'AI素养综合分（z均值）',
}

def reg_full(m, dv_col, df_m, title, summary_rows):
    """输出详细回归表并将 group_c 行追加到 summary_rows。"""
    pr(f'\n#### {title}')
    pr(f'\n> 自变量：group_c（C=1, A=0）  ◄ p < .05')
    sd_y    = df_m[dv_col].dropna().std(ddof=1)
    X_arr   = m.model.exog
    X_names = list(m.model.exog_names)

    hdr = f"| {'变量':<30} | {'B':>8} | {'SE':>7} | {'Beta':>7} | {'t':>7} | {'p':>10} | {'VIF':>6} |"
    sep = '|' + '|'.join(['-'*32, '-'*10, '-'*9, '-'*9, '-'*9, '-'*12, '-'*8]) + '|'
    pr(hdr); pr(sep)

    b0, se0, t0, p0 = (m.params['Intercept'], m.bse['Intercept'],
                       m.tvalues['Intercept'], m.pvalues['Intercept'])
    pr(f"| {'(常量)':<30} | {b0:>8.3f} | {se0:>7.3f} | {'':>7} | {t0:>7.3f} | {fmt_p(p0):>10} | {'':>6} |")

    for nm in m.params.index:
        if nm == 'Intercept': continue
        b, se, t, p = m.params[nm], m.bse[nm], m.tvalues[nm], m.pvalues[nm]
        sd_x  = pd.Series(X_arr[:, X_names.index(nm)]).std(ddof=1) if nm in X_names else np.nan
        beta  = b * sd_x / sd_y if sd_y > 0 and not np.isnan(sd_x) and sd_x > 0 else np.nan
        try:   vif = _vif_func(X_arr, X_names.index(nm))
        except: vif = np.nan
        beta_s = f'{beta:.3f}' if not np.isnan(beta) else ''
        vif_s  = f'{vif:.3f}' if not np.isnan(vif)  else ''
        lbl    = _VAR_LBL.get(nm, nm)
        mark   = ' ◄' if p < .05 else ''
        pr(f"| {lbl:<30} | {b:>8.3f} | {se:>7.3f} | {beta_s:>7} | {t:>7.3f} | {fmt_p(p)+stars(p):>10} | {vif_s:>6} |{mark}")

    p_eq = '= ' if not fmt_p(m.f_pvalue).startswith('<') else ''
    pr(f'\n_R²={m.rsquared:.3f}, Adj.R²={m.rsquared_adj:.3f}, '
       f'F({m.df_model:.0f},{m.df_resid:.0f})={m.fvalue:.3f}, '
       f'p {p_eq}{fmt_p(m.f_pvalue)}{stars(m.f_pvalue)}_')

    # 残差诊断
    resids = m.resid.values; exog = m.model.exog
    sw_stat, sw_p = stats.shapiro(resids)
    try:   _, bp_p, _, _ = het_breuschpagan(resids, exog)
    except: bp_p = np.nan
    dw_val = dw_test(resids)
    pr(f'> 残差：SW *p* = {fmt_p(sw_p)+stars(sw_p)}, BP *p* = {fmt_p(bp_p)+stars(bp_p)}, DW = {dw_val:.2f}')

    # 追加汇总行
    b_g = m.params.get('group_c', np.nan)
    se_g = m.bse.get('group_c', np.nan)
    t_g  = m.tvalues.get('group_c', np.nan)
    p_g  = m.pvalues.get('group_c', np.nan)
    summary_rows.append({
        'DV':      dv_col,
        '模型':    title.split('（')[1].rstrip('）') if '（' in title else title,
        'n':       int(m.nobs),
        'B_group': f'{b_g:.3f}',
        'SE_group':f'{se_g:.3f}',
        't_group': f'{t_g:.3f}',
        'p_group': fmt_p(p_g) + stars(p_g),
        'R²':      f'{m.rsquared:.3f}',
        'Adj.R²':  f'{m.rsquared_adj:.3f}',
        'F':       f'F({m.df_model:.0f},{m.df_resid:.0f})={m.fvalue:.3f}',
    })

# ════════════════════════════════════════════════════════════════════
# 主报告
# ════════════════════════════════════════════════════════════════════
h1('AI素养操作化敏感性分析')
pr('> **目的**：检验"AI素养"不同操作化方式对组别效应估计的稳健性。\n'
   '> 三种模型均包含 `group_c` 和 `self_assessed_ability`（前测自评能力）作为基础控制变量，\n'
   '> 在此基础上分别加入不同的AI素养测量。\n')
pr('| 模型标签 | AI素养操作化 | 公式 |')
pr('|---------|------------|------|')
pr('| 模型A | 仅AI使用频率 | `group_c + ai_exposure_num + self_assessed_ability` |')
pr('| 模型B | 仅AI熟悉度  | `group_c + ai_familiarity + self_assessed_ability` |')
pr('| 模型C | 综合分（z均值） | `group_c + ai_literacy_composite + self_assessed_ability` |')
pr('\n> **综合分**：`ai_literacy_composite = (z(ai_familiarity) + z(ai_exposure_num)) / 2`\n'
   f'> 两变量原始相关：r = {stats.pearsonr(master["ai_familiarity"].dropna(), master["ai_exposure_num"].dropna())[0]:.3f}\n')

MODELS = [
    ('模型A：仅AI使用频率',   'group_c + ai_exposure_num + self_assessed_ability',
     ['ai_exposure_num', 'self_assessed_ability']),
    ('模型B：仅AI熟悉度',     'group_c + ai_familiarity + self_assessed_ability',
     ['ai_familiarity', 'self_assessed_ability']),
    ('模型C：综合分（z均值）', 'group_c + ai_literacy_composite + self_assessed_ability',
     ['ai_literacy_composite', 'self_assessed_ability']),
]

DVS = [
    ('acc_total',       '识别准确率'),
    ('dprime',          "敏感性指标 d'"),
    ('calibration_gap', '信心校准差距'),
]

summary_rows = []

for dv_col, dv_lbl in DVS:
    h2(f'DV = {dv_lbl}（{dv_col}）')
    for model_label, formula, ctrl_cols in MODELS:
        needed = [dv_col, 'group_c'] + ctrl_cols
        df_m = master.dropna(subset=needed).copy()
        m    = smf.ols(f'{dv_col} ~ {formula}', data=df_m).fit()
        reg_full(m, dv_col, df_m, f'{dv_lbl}（{model_label}）', summary_rows)

# ── 汇总表 ──────────────────────────────────────────────────────────
h2('汇总：各模型中 group_c（组别效应）估计值')
pr('> 主要关注 B 值、t 值和 p 值的跨模型稳定性。\n')
pr('| DV | 模型 | n | B | SE | t | p | R² | Adj.R² | F |')
pr('|:--|:--|:--|--:|--:|--:|:--|--:|--:|:--|')
for row in summary_rows:
    pr(f"| {row['DV']} | {row['模型']} | {row['n']} | "
       f"{row['B_group']} | {row['SE_group']} | {row['t_group']} | {row['p_group']} | "
       f"{row['R²']} | {row['Adj.R²']} | {row['F']} |")

# CSV
summary_df = pd.DataFrame(summary_rows)
summary_df.to_csv(os.path.join(OUT_DIR, 'sensitivity_ai_literacy.csv'),
                  index=False, encoding='utf-8-sig')

_log.close()
print(f'\n输出文件：')
print(f'  {OUT_DIR}/sensitivity_ai_literacy.md')
print(f'  {OUT_DIR}/sensitivity_ai_literacy.csv')
