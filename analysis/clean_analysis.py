#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
clean_analysis.py  ─ 基于手动筛选样本的四项分析
──────────────────────────────────────────────────────────────
样本：participant_summary_full.csv 中 delete != 1 的被试

分析：
  1. 组间前测基线差异（人口统计学 + AI素养相关）
  2. 准确率组间差异（整体 / AI图 / 真实图）+ Mann-Whitney
  3. 控制 AI 素养后的准确率 OLS 回归
  4. AI 素养调节效应（group × moderator 交互）简单斜率

输出：analysis/output/clean_analysis_report.txt
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd, numpy as np
from scipy import stats
from scipy.stats import zscore
import statsmodels.formula.api as smf
import warnings
warnings.filterwarnings('ignore')

SUMMARY = 'analysis/output/participant_summary_full.csv'
PART    = 'analysis/data/participants_combined.csv'
OUT     = 'analysis/output/clean_analysis_report.txt'

# ═══════════════════════════════════════════════════════════════
# 0. 数据准备
# ═══════════════════════════════════════════════════════════════
df_raw = pd.read_csv(SUMMARY)
df = df_raw[df_raw['delete'] != 1].copy()

df = df.rename(columns={
    '组别':            'group',
    '来源':            'source',
    'AI熟悉度':        'ai_fam',
    '前测自评能力':    'self_abil',
    'AI使用频率(1-5)': 'ai_exp',
    '整体正确率':      'acc_total',
    'AI图正确率':      'acc_ai',
    '真实图正确率':    'acc_real',
    '后测表现自评':    'self_perf',
})

# 合并人口统计学 + ai_tool_usage
demo = pd.read_csv(PART)[['participant_id','gender','age','education','ai_tool_usage']]
df = df.merge(demo, on='participant_id', how='left')

# 重算 AI素养综合分（三项z均值）
df['ai_tool_num'] = (df['ai_tool_usage'] == 'yes').astype(float)
_v = df.dropna(subset=['ai_fam','ai_exp','ai_tool_num'])
df['ai_comp'] = np.nan
if len(_v) > 1:
    df.loc[_v.index, 'ai_comp'] = (
        zscore(_v['ai_fam'].values)
        + zscore(_v['ai_exp'].values)
        + zscore(_v['ai_tool_num'].values)) / 3

df['group_c']  = (df['group'] == 'C').astype(float)   # A=0, C=1
df['source_c'] = (df['source'] == 'synth').astype(float)

gA = df[df['group'] == 'A']
gC = df[df['group'] == 'C']
n_A, n_C = len(gA), len(gC)

# ═══════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════
lines = []

def pr(*a):
    s = ' '.join(str(x) for x in a)
    print(s); lines.append(s)

def sep(t=''):
    if t:
        pr(f'\n{"═"*64}')
        pr(f'  {t}')
        pr(f'{"═"*64}')
    else:
        pr('─'*64)

def fp(p):
    if pd.isna(p): return 'NaN'
    return '< .001' if p < .001 else f'{p:.3f}'

def st(p, mark_sig=True):
    if pd.isna(p): return ''
    s = '***' if p<.001 else ('**' if p<.01 else ('*' if p<.05 else ''))
    return s + (' ◄' if mark_sig and p<.05 else '')

def welch_t(a, b, label):
    a, b = a.dropna(), b.dropna()
    if len(a) < 2 or len(b) < 2:
        pr(f'  {label}: 样本不足'); return
    t, p = stats.ttest_ind(a, b, equal_var=False)
    df_w = (a.var(ddof=1)/len(a) + b.var(ddof=1)/len(b))**2 / (
            (a.var(ddof=1)/len(a))**2/(len(a)-1) +
            (b.var(ddof=1)/len(b))**2/(len(b)-1))
    pool_sd = np.sqrt(((len(a)-1)*a.std(ddof=1)**2 +
                       (len(b)-1)*b.std(ddof=1)**2) / (len(a)+len(b)-2))
    d = (b.mean()-a.mean())/pool_sd if pool_sd > 0 else np.nan
    pr(f'  {label}')
    pr(f'    A: M={a.mean():.3f}, SD={a.std(ddof=1):.3f}, n={len(a)}')
    pr(f'    C: M={b.mean():.3f}, SD={b.std(ddof=1):.3f}, n={len(b)}')
    pr(f'    t({df_w:.1f})={t:.3f}, p={fp(p)}{st(p)}, Cohen d={d:.3f}')

def chi2_test(col, label):
    sub = df[[col,'group']].dropna()
    ct = pd.crosstab(sub[col], sub['group'])
    chi, p, dof, _ = stats.chi2_contingency(ct)
    pr(f'  {label}: χ²({dof})={chi:.3f}, p={fp(p)}{st(p)}')
    pr(ct.to_string())

def reg_table(m, label=''):
    if label:
        pr(f'\n  [{label}]')
    hdr = f"  {'变量':<22} {'B':>8} {'SE':>7} {'t':>7} {'p':>10}  sig"
    pr(hdr); pr('  ' + '─'*58)
    for nm in m.params.index:
        if nm == 'Intercept': continue
        b, se, t, p = m.params[nm], m.bse[nm], m.tvalues[nm], m.pvalues[nm]
        pr(f"  {nm:<22} {b:>8.4f} {se:>7.4f} {t:>7.3f} {fp(p):>10}  {st(p)}")
    pr('  ' + '─'*58)
    p_eq = '=' if not fp(m.f_pvalue).startswith('<') else ''
    pr(f'  R²={m.rsquared:.3f}, adj.R²={m.rsquared_adj:.3f}, '
       f'F({m.df_model:.0f},{m.df_resid:.0f})={m.fvalue:.3f}, '
       f'p{p_eq}{fp(m.f_pvalue)}{st(m.f_pvalue, mark_sig=False)}')

def simple_slopes(df_s, dv, mod_var, mod_label):
    """group_c × mod_c 简单斜率（控制 source_c）"""
    df_s = df_s.copy().dropna(subset=[dv, mod_var])
    mod_c = mod_var + '_c'
    df_s[mod_c] = df_s[mod_var] - df_s[mod_var].mean()
    sd = df_s[mod_var].std(ddof=1)
    formula = f'{dv} ~ group_c * {mod_c} + source_c'
    m = smf.ols(formula, data=df_s).fit()

    b_g  = m.params.get('group_c', np.nan)
    b_gi = m.params.get(f'group_c:{mod_c}', np.nan)
    se_g  = m.bse.get('group_c', np.nan)
    se_gi = m.bse.get(f'group_c:{mod_c}', np.nan)
    cov   = m.cov_params().loc['group_c', f'group_c:{mod_c}'] \
            if 'group_c' in m.cov_params().index and \
               f'group_c:{mod_c}' in m.cov_params().columns else 0

    # 交互项
    b_int, se_int, t_int, p_int = (m.params.get(f'group_c:{mod_c}', np.nan),
                                    m.bse.get(f'group_c:{mod_c}', np.nan),
                                    m.tvalues.get(f'group_c:{mod_c}', np.nan),
                                    m.pvalues.get(f'group_c:{mod_c}', np.nan))
    pr(f'\n  DV={dv} | 调节变量={mod_label}')
    pr(f'  交互项 group_c×{mod_label}: B={b_int:.4f}, SE={se_int:.4f}, '
       f't={t_int:.3f}, p={fp(p_int)}{st(p_int)}')

    pr(f'  简单斜率（group C vs A 的效应 B）:')
    for lbl, val in [('-1SD', -sd), ('均值', 0.0), ('+1SD', +sd)]:
        b_s  = b_g + b_gi * val
        se_s = np.sqrt(se_g**2 + val**2*se_gi**2 + 2*val*cov)
        t_s  = b_s / se_s if se_s > 0 else np.nan
        p_s  = 2*stats.t.sf(abs(t_s), df=m.df_resid) if not np.isnan(t_s) else np.nan
        pr(f'    {lbl:>5} ({mod_label}): B={b_s:.4f}, SE={se_s:.4f}, '
           f't={t_s:.3f}, p={fp(p_s)}{st(p_s)}')
    return m

# ═══════════════════════════════════════════════════════════════
# 报告头
# ═══════════════════════════════════════════════════════════════
pr('═'*64)
pr('  clean_analysis_report.txt')
pr('  样本：participant_summary_full.csv，delete != 1')
pr(f'  总N={len(df)}  A组={n_A}  C组={n_C}')
n_real  = (df['source']=='real').sum()
n_synth = (df['source']=='synth').sum()
pr(f'  来源：real={n_real}, synth={n_synth}')
pr('═'*64)

# ═══════════════════════════════════════════════════════════════
# 1. 组间前测基线差异
# ═══════════════════════════════════════════════════════════════
sep('1. 组间前测基线差异')

pr('\n─ 人口统计学（χ² 检验）─')
for col, lbl in [('gender','性别'), ('age','年龄段'), ('education','学历')]:
    chi2_test(col, lbl)

pr('\n─ 来源平衡（synth/real 在两组中的分布）─')
chi2_test('source', '数据来源')

pr('\n─ AI素养相关（Welch t-test，C vs A）─')
for col, lbl in [
    ('ai_fam',    'AI熟悉度（1–5）'),
    ('self_abil', '前测自评能力（1–5）'),
    ('ai_exp',    'AI使用频率（1–5）'),
    ('ai_comp',   'AI素养综合分（z）'),
]:
    welch_t(gA[col], gC[col], lbl)

# ═══════════════════════════════════════════════════════════════
# 2. 准确率组间差异
# ═══════════════════════════════════════════════════════════════
sep('2. 准确率组间差异')

pr('\n─ Welch t-test（C vs A）─')
for col, lbl in [
    ('acc_total','整体正确率'),
    ('acc_ai',   'AI图正确率'),
    ('acc_real', '真实图正确率'),
]:
    welch_t(gA[col], gC[col], lbl)

pr('\n─ Mann-Whitney U（非参数）─')
for col, lbl in [
    ('acc_total','整体正确率'),
    ('acc_ai',   'AI图正确率'),
    ('acc_real', '真实图正确率'),
]:
    a, b = gA[col].dropna(), gC[col].dropna()
    u, p = stats.mannwhitneyu(a, b, alternative='two-sided')
    pr(f'  {lbl}: U={u:.0f}, p={fp(p)}{st(p)}')

# ═══════════════════════════════════════════════════════════════
# 3. 控制 AI 素养后的准确率 OLS 回归
# ═══════════════════════════════════════════════════════════════
sep('3. 控制 AI 素养后的准确率回归（OLS）')
pr('  控制变量：source_c, ai_fam, self_abil, ai_exp')
pr('  关注：group_c 系数（C vs A 净效应）')

base_ctrl = 'source_c + ai_fam + self_abil + ai_exp'

for dv, lbl in [
    ('acc_total','整体正确率'),
    ('acc_ai',   'AI图正确率'),
    ('acc_real', '真实图正确率'),
]:
    formula = f'{dv} ~ group_c + {base_ctrl}'
    m = smf.ols(formula, data=df.dropna(subset=[dv,'ai_fam','self_abil','ai_exp'])).fit()
    reg_table(m, lbl)

# ═══════════════════════════════════════════════════════════════
# 4. AI素养调节效应
# ═══════════════════════════════════════════════════════════════
sep('4. AI素养调节效应（group × moderator 交互）')
pr('  DV：整体正确率；控制 source_c')
pr('  ◄ = p < .05 显著')

for mod_var, mod_lbl in [
    ('self_abil', '前测自评能力'),
    ('ai_fam',    'AI熟悉度'),
    ('ai_exp',    'AI使用频率'),
    ('ai_comp',   'AI素养综合分'),
]:
    simple_slopes(df, 'acc_total', mod_var, mod_lbl)

pr('\n─ 补充：以 AI图正确率 为 DV，调节变量 = 前测自评能力 ─')
simple_slopes(df, 'acc_ai', 'self_abil', '前测自评能力')

# ═══════════════════════════════════════════════════════════════
# 5. 论文规范回归表（参考文献格式）
#    DV1 = 整体正确率（识别准确率）
#    DV2 = d'（敏感性指标）
#    控制变量：性别/年龄/学历/AI熟悉度/前测自评能力
#    自变量：group_c（是否干预）
# ═══════════════════════════════════════════════════════════════
sep('5. 论文回归表（B / SE / Beta / t / p / VIF）')

from statsmodels.stats.outliers_influence import variance_inflation_factor as vif_func

# ── 5a. 计算 d'（从 responses 原始数据）──────────────────────────
AI_IDS   = {'ai_01','ai_02','ai_04','ai_08','ai_09','ai_13','ai_15','ai_16','ai_19'}
REAL_IDS = {'real_01','real_02','real_03','real_04','real_05','real_06',
            'real_11','real_12','real_14','real_15','real_16','real_20'}
VALID_ALL = AI_IDS | REAL_IDS

resp = pd.read_csv('analysis/data/responses_combined.csv')
resp = resp[resp['participant_id'].isin(df['participant_id'])
            & resp['image_id'].isin(VALID_ALL)].copy()
resp['img_type'] = resp['image_id'].apply(lambda x: 'AI' if x in AI_IDS else 'Real')

def _cr(rate, n):
    """连续性校正（避免 0/1 边界）"""
    if rate == 0: return 0.5 / n
    if rate == 1: return (n - 0.5) / n
    return rate

sdt_rows = []
for pid, grp in resp.groupby('participant_id'):
    ai_r  = grp[grp['img_type'] == 'AI']
    real_r = grp[grp['img_type'] == 'Real']
    hr_raw  = ai_r['is_correct'].mean()   # AI 图中正确识别为 AI 的比例
    far_raw = 1 - real_r['is_correct'].mean()  # 真实图中误判为 AI 的比例
    hr  = _cr(hr_raw,  len(ai_r))
    far = _cr(far_raw, len(real_r))
    dprime = stats.norm.ppf(hr) - stats.norm.ppf(far)
    sdt_rows.append({'participant_id': pid, 'dprime': dprime})

sdt_df = pd.DataFrame(sdt_rows)
df = df.merge(sdt_df, on='participant_id', how='left')

pr(f'\n  d\' 描述：n={df["dprime"].notna().sum()}, '
   f'M={df["dprime"].mean():.3f}, SD={df["dprime"].std(ddof=1):.3f}')
pr(f'  整体正确率描述：M={df["acc_total"].mean():.3f}, SD={df["acc_total"].std(ddof=1):.3f}')

# ── 5b. Dummy 变量编码 ────────────────────────────────────────────
# 性别：参照组 = 男（含 prefer-not-to-say 归入参照组）
df['gender_female'] = (df['gender'] == 'female').astype(float)

# 年龄：参照组 = 18-24（最大组）
df['age_25_34'] = (df['age'] == '25-34').astype(float)
df['age_35_44'] = (df['age'] == '35-44').astype(float)
df['age_45_54'] = (df['age'] == '45-54').astype(float)

# 学历：参照组 = bachelors（最大组，44人）
df['edu_highschool'] = (df['education'] == 'high-school').astype(float)
df['edu_college']    = (df['education'] == 'some-college').astype(float)
df['edu_masters']    = (df['education'] == 'masters').astype(float)
df['edu_phd']        = (df['education'] == 'doctorate').astype(float)

# ── 5c. 回归表输出函数 ───────────────────────────────────────────
VAR_LABELS = {
    'group_c':        '是否进行信息干预',
    'gender_female':  '性别（女 vs 男/其他）',
    'age_25_34':      '年龄 25–34（vs 18–24）',
    'age_35_44':      '年龄 35–44（vs 18–24）',
    'age_45_54':      '年龄 45–54（vs 18–24）',
    'edu_highschool': '学历 高中（vs 本科）',
    'edu_college':    '学历 大专（vs 本科）',
    'edu_masters':    '学历 硕士（vs 本科）',
    'edu_phd':        '学历 博士（vs 本科）',
    'ai_fam':         'AI熟悉度（1–5）',
    'self_abil':      '前测自评能力（1–5）',
    'ai_exp':         'AI使用频率（1–5）',
}

def reg_table_full(m, dv_col, df_m, label=''):
    if label:
        pr(f'\n  ── {label} ──')
    sd_y = df_m[dv_col].dropna().std(ddof=1)
    X_arr = m.model.exog
    X_names = list(m.model.exog_names)

    hdr = f"  {'变量':<28} {'B':>8} {'SE':>7} {'Beta':>7} {'t':>7} {'p':>10} {'VIF':>6}"
    pr(hdr); pr('  ' + '─'*72)

    # 常量行
    b0, se0, t0, p0 = (m.params['Intercept'], m.bse['Intercept'],
                       m.tvalues['Intercept'], m.pvalues['Intercept'])
    pr(f"  {'(常量)':<28} {b0:>8.3f} {se0:>7.3f} {'':>7} {t0:>7.3f} {fp(p0):>10}")

    # 预测变量行
    for nm in m.params.index:
        if nm == 'Intercept': continue
        b, se, t, p = m.params[nm], m.bse[nm], m.tvalues[nm], m.pvalues[nm]
        # Beta（标准化）
        if nm in X_names:
            sd_x = pd.Series(X_arr[:, X_names.index(nm)]).std(ddof=1)
            beta = b * sd_x / sd_y if sd_y > 0 and sd_x > 0 else np.nan
        else:
            beta = np.nan
        # VIF
        try:
            vif = vif_func(X_arr, X_names.index(nm))
        except Exception:
            vif = np.nan
        beta_s = f'{beta:.3f}' if not np.isnan(beta) else ''
        vif_s  = f'{vif:.3f}' if not np.isnan(vif) else ''
        lbl    = VAR_LABELS.get(nm, nm)
        mark   = '  ◄' if p < .05 else ''
        pr(f"  {lbl:<28} {b:>8.3f} {se:>7.3f} {beta_s:>7} {t:>7.3f} {fp(p):>10} {vif_s:>6}{mark}")

    pr('  ' + '─'*72)
    p_eq = '=' if not fp(m.f_pvalue).startswith('<') else ''
    pr(f"  R²={m.rsquared:.3f}  Adj.R²={m.rsquared_adj:.3f}  "
       f"F({m.df_model:.0f},{m.df_resid:.0f})={m.fvalue:.3f}  "
       f"p{p_eq}{fp(m.f_pvalue)}{st(m.f_pvalue, mark_sig=False)}")
    pr(f"  因变量：{label}")

# ── 5d. 运行回归 ──────────────────────────────────────────────────
# 模型一：控制人口统计学（不含AI素养相关）
CTRL_DEMO = ('gender_female + '
             'age_25_34 + age_35_44 + age_45_54 + '
             'edu_highschool + edu_college + edu_masters + edu_phd')

# 模型二：控制AI素养相关（不含人口统计学）
CTRL_AI   = 'ai_fam + self_abil + ai_exp'

DEMO_COLS = ['gender_female',
             'age_25_34','age_35_44','age_45_54',
             'edu_highschool','edu_college','edu_masters','edu_phd']
AI_COLS   = ['ai_fam','self_abil','ai_exp']

pr('\n  自变量：是否进行信息干预（group_c, C=1 A=0）')
pr('  参照组：性别=男（含其他）, 年龄=18-24, 学历=本科')
pr('  ◄ = p < .05 显著')

for dv_col, dv_lbl in [('acc_total', '识别准确率'), ('dprime', "敏感性指标 d'")]:
    sep(f'5. {dv_lbl}')

    # 模型一：人口统计学
    pr('\n  【模型一】控制变量 = 性别 / 年龄 / 学历')
    df_m1 = df.dropna(subset=[dv_col] + DEMO_COLS)
    m1 = smf.ols(f'{dv_col} ~ group_c + {CTRL_DEMO}', data=df_m1).fit()
    reg_table_full(m1, dv_col, df_m1, dv_lbl)

    # 模型二：AI素养相关
    pr('\n  【模型二】控制变量 = AI熟悉度 / 前测自评能力 / AI使用频率')
    df_m2 = df.dropna(subset=[dv_col] + AI_COLS)
    m2 = smf.ols(f'{dv_col} ~ group_c + {CTRL_AI}', data=df_m2).fit()
    reg_table_full(m2, dv_col, df_m2, dv_lbl)

# ═══════════════════════════════════════════════════════════════
# 保存
# ═══════════════════════════════════════════════════════════════
pr('\n' + '═'*64)
pr('  分析完毕')
pr('═'*64)

with open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print(f'\n已保存 -> {OUT}')
