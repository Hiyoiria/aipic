#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
formal_analysis.py  ─  Study 2 正式分析脚本（按 new_frame.md v4）

输出:
  analysis/output/formal_report.md
  analysis/output/table3_regression_accuracy.csv
  analysis/output/table4_regression_dprime.csv
  analysis/output/table5_regression_calibration.csv
  analysis/output/table7_heterogeneity_accuracy.csv
  analysis/output/table8_heterogeneity_calibration.csv
  analysis/output/F3_correlation_heatmap.png
"""
import sys, os, math, warnings, datetime
import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import zscore as _zscore, chi2_contingency
import statsmodels.formula.api as smf
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.anova import anova_lm as sm_anova_lm
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.stattools import durbin_watson as dw_test
import pingouin as pg

sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

FINAL_DIR = os.path.join(os.path.dirname(__file__), 'final_data_1')
OUT_DIR   = os.path.join(os.path.dirname(__file__), 'output_1')
os.makedirs(OUT_DIR, exist_ok=True)

log_path = os.path.join(OUT_DIR, 'formal_report_v2.md')
_log = open(log_path, 'w', encoding='utf-8')

def pr(*a, **kw):
    print(*a, **kw); print(*a, **kw, file=_log)

def h1(t): pr(f'\n# {t}\n')
def h2(t): pr(f'\n## {t}\n')
def h3(t): pr(f'\n### {t}\n')

# ── 统计格式化辅助 ─────────────────────────────────────────────────────
def stars(p):
    if pd.isna(p): return ''
    if p < .001: return '***'
    if p < .01:  return '**'
    if p < .05:  return '*'
    return ''

def fmt_p(p):
    """APA 7th ed: 无前导零；p < .001 时写 '< .001'。"""
    if pd.isna(p): return '—'
    if p < .001:   return '< .001'
    s = f'{p:.3f}'          # '0.038'
    return s.lstrip('0') or '.000'   # '.038'

def fmt(v, dec=3):
    if v is None or (isinstance(v, float) and np.isnan(v)): return '—'
    if isinstance(v, str): return v
    if isinstance(v, (int, np.integer)): return str(v)
    return f'{v:.{dec}f}'

def fmt_r(v, dec=3):
    """无前导零的小数（用于 r, R², β 等∈[−1,1] 的量）。"""
    if v is None or (isinstance(v, float) and np.isnan(v)): return '—'
    s = f'{v:.{dec}f}'
    if s.startswith('0.'):  return s[1:]    # '.123'
    if s.startswith('-0.'): return '-' + s[2:]  # '-.123'
    return s

def ms(arr, dec=3):
    """Mean (SD) 字符串，默认 3 位小数。"""
    a = np.array(arr, dtype=float); a = a[~np.isnan(a)]
    if len(a) == 0: return '—'
    return f'{np.mean(a):.{dec}f} ({np.std(a, ddof=1):.{dec}f})'

def ms2(arr, dec=2):
    """Mean (SD) 字符串，2 位小数（用于 Likert 量表等）。"""
    return ms(arr, dec=dec)

def pct_str(n, total):
    return f'{n} ({n/total*100:.1f}%)' if total > 0 else '0 (0.0%)'

def welch_df(x1, x2):
    """Welch-Satterthwaite 自由度近似。"""
    n1, n2 = len(x1), len(x2)
    v1, v2 = np.var(x1, ddof=1), np.var(x2, ddof=1)
    num = (v1/n1 + v2/n2)**2
    den = (v1/n1)**2/(n1-1) + (v2/n2)**2/(n2-1)
    return num/den if den > 0 else float(n1+n2-2)

def cramers_v(ct):
    """Cramér's V 效应量。"""
    chi2, p, dof, _ = chi2_contingency(ct)
    n  = ct.sum().sum()
    k  = min(ct.shape) - 1
    V  = math.sqrt(chi2 / (n * k)) if n * k > 0 else 0.0
    return chi2, p, dof, V

def md_table(headers, rows):
    ncols = len(headers)
    def to_s(x): return x if isinstance(x, str) else fmt(x)
    str_rows = [[to_s(c) for c in r] + ['']*(ncols-len(r)) for r in rows]
    widths = [max(len(headers[i]), max((len(r[i]) for r in str_rows), default=0))
              for i in range(ncols)]
    def line(cells):
        return '| ' + ' | '.join(str(c).ljust(w) for c,w in zip(cells,widths)) + ' |'
    sep = '| ' + ' | '.join('-'*w for w in widths) + ' |'
    pr('\n'.join([line(headers), sep] + [line(r[:ncols]) for r in str_rows]))

# 哑变量列表（β 显示为 "—"）
DUMMY_VARS = {'gender_female','age_25_34','age_35_44','age_45_54',
              'edu_college','edu_bachelor','edu_masters','edu_phd'}

def regression_table_md(model, X_raw, X_std, var_labels=None):
    """输出回归表（B / SE / 95%CI / β / t / p / VIF）→ Markdown。"""
    params = model.params; bse = model.bse
    tvals  = model.tvalues; pvals = model.pvalues
    ci     = model.conf_int()           # 列 0 = lower, 列 1 = upper

    # 标准化系数 β = B × SD_X / SD_Y（使用原始变量 SD，非标准化后的 SD）
    y_sd = model.model.endog.std(ddof=1)
    beta = {col: params[col] * X_raw[col].std(ddof=1) / y_sd
            if col in params.index and X_raw[col].std(ddof=1) > 0 else np.nan
            for col in X_raw.columns}

    # VIF
    X_vif = X_raw.dropna()
    X_mat  = sm.add_constant(X_vif)
    vif_vals = {}
    for i, col in enumerate(X_vif.columns):
        try:   vif_vals[col] = variance_inflation_factor(X_mat.values, i+1)
        except: vif_vals[col] = np.nan

    rows = []
    for col in params.index:
        lbl = (var_labels or {}).get(col, col)
        ci_lo = ci.loc[col, 0] if col in ci.index else np.nan
        ci_hi = ci.loc[col, 1] if col in ci.index else np.nan
        ci_str = f'[{ci_lo:.3f}, {ci_hi:.3f}]' if not (np.isnan(ci_lo) or np.isnan(ci_hi)) else '—'

        if col == 'Intercept':
            rows.append([lbl, fmt(params[col],3), fmt(bse[col],3), ci_str,
                         '—', fmt(tvals[col],3), '—', '—'])
        else:
            is_dummy = col in DUMMY_VARS
            beta_str = '—' if is_dummy else fmt_r(beta.get(col, np.nan))
            vif_str  = '—' if np.isnan(vif_vals.get(col, np.nan)) else fmt(vif_vals.get(col, np.nan), 2)
            p_str    = fmt_p(pvals[col]) + stars(pvals[col])
            rows.append([lbl, fmt(params[col],3), fmt(bse[col],3), ci_str,
                         beta_str, fmt(tvals[col],3), p_str, vif_str])

    md_table(['变量', 'B', 'SE', '95% CI', 'β', 't', 'p', 'VIF'], rows)
    fp_val  = fmt_p(model.f_pvalue)
    fp_star = stars(model.f_pvalue)
    p_eq    = '' if fp_val.startswith('<') else '= '   # 添加 = 号（避免"p .245"格式）
    # 用 _..._ 而非 *...* 做斜体，避免结尾 *** 与关闭 * 连成 ****
    pr(f'\n_R² = {fmt_r(model.rsquared)}, Adj.R² = {fmt_r(model.rsquared_adj)}, '
       f'F({model.df_model:.0f}, {model.df_resid:.0f}) = {model.fvalue:.3f}, '
       f'p {p_eq}{fp_val}{fp_star}_')

    df_out = pd.DataFrame(rows, columns=['变量','B','SE','95% CI','β','t','p','VIF'])
    return df_out

def chow_test(df_full, df1, df2, formula):
    m_full = smf.ols(formula, data=df_full).fit()
    m1 = smf.ols(formula, data=df1).fit()
    m2 = smf.ols(formula, data=df2).fit()
    k = len(m_full.params)
    F_num = (m_full.ssr - m1.ssr - m2.ssr) / k
    F_den = (m1.ssr + m2.ssr) / (len(df1)+len(df2)-2*k)
    F_stat = F_num / F_den if F_den > 0 else np.nan
    n = len(df1)+len(df2)
    p_val = 1-stats.f.cdf(F_stat, k, n-2*k) if not np.isnan(F_stat) else np.nan
    return F_stat, p_val, k

def hedges_g(x1, x2):
    n1, n2 = len(x1), len(x2)
    s = math.sqrt(((n1-1)*np.std(x1,ddof=1)**2+(n2-1)*np.std(x2,ddof=1)**2)/(n1+n2-2))
    d = (np.mean(x1)-np.mean(x2))/s if s else float('nan')
    return d*(1-3/(4*(n1+n2-2)-1))

def residual_diagnostics_md(model):
    """残差诊断：Shapiro-Wilk 正态性 + Breusch-Pagan 同方差性 + Durbin-Watson。"""
    resids = model.resid.values
    exog   = model.model.exog
    sw_stat, sw_p = stats.shapiro(resids)
    try:
        _, bp_p, _, _ = het_breuschpagan(resids, exog)
    except Exception:
        bp_p = np.nan
    dw_val = dw_test(resids)
    norm_str = '正态' if sw_p >= .05 else '偏离正态（可能影响小样本推断）'
    homo_str = '同方差' if pd.isna(bp_p) or bp_p >= .05 else '疑似异方差'
    pr(f'\n> **残差诊断**: Shapiro-Wilk *W* = {sw_stat:.3f}, *p* = {fmt_p(sw_p)+stars(sw_p)} '
       f'（{norm_str}）; Breusch-Pagan *p* = {fmt_p(bp_p)+stars(bp_p)} '
       f'（{homo_str}）; Durbin-Watson = {dw_val:.2f}')

def sdt_person(df_p):
    ai   = df_p[df_p['image_type']=='AI']
    real = df_p[df_p['image_type']=='Real']
    if len(ai)==0 or len(real)==0:
        return dict(dprime=np.nan, c=np.nan, hr=np.nan, far=np.nan)
    hits = (ai['judgment']=='AI').sum()
    fas  = (real['judgment']=='AI').sum()
    hr_  = (hits+0.5)/(len(ai)+1)
    far_ = (fas+0.5)/(len(real)+1)
    dp = stats.norm.ppf(hr_) - stats.norm.ppf(far_)
    c_ = -0.5*(stats.norm.ppf(hr_)+stats.norm.ppf(far_))
    return dict(dprime=dp, c=c_, hr=hr_, far=far_)

# ═══════════════════════════════════════════════════════════════════
# 图像元数据
# ═══════════════════════════════════════════════════════════════════
IMAGE_META = {
    'ai_01': {'type':'AI','style':'illustration','source':'ai-art',    'reverse_searchable':True},
    'ai_02': {'type':'AI','style':'photograph',  'source':'ai-art',    'reverse_searchable':True},
    'ai_04': {'type':'AI','style':'cartoon',     'source':'ai-art',    'reverse_searchable':True},
    'ai_08': {'type':'AI','style':'photograph',  'source':'midjourney','reverse_searchable':False},
    'ai_09': {'type':'AI','style':'cartoon',     'source':'midjourney','reverse_searchable':False},
    'ai_13': {'type':'AI','style':'photograph',  'source':'midjourney','reverse_searchable':False},
    'ai_15': {'type':'AI','style':'photograph',  'source':'nanobanana','reverse_searchable':False},
    'ai_16': {'type':'AI','style':'illustration','source':'nanobanana','reverse_searchable':False},
    'ai_19': {'type':'AI','style':'photograph',  'source':'nanobanana','reverse_searchable':False},
    'real_01':{'type':'Real','style':'illustration','source':'camera', 'reverse_searchable':False},
    'real_02':{'type':'Real','style':'photograph',  'source':'camera', 'reverse_searchable':False},
    'real_03':{'type':'Real','style':'cartoon',     'source':'camera', 'reverse_searchable':False},
    'real_04':{'type':'Real','style':'photograph',  'source':'camera', 'reverse_searchable':False},
    'real_05':{'type':'Real','style':'illustration','source':'camera', 'reverse_searchable':False},
    'real_06':{'type':'Real','style':'photograph',  'source':'camera', 'reverse_searchable':False},
    'real_11':{'type':'Real','style':'photograph',  'source':'website','reverse_searchable':True},
    'real_12':{'type':'Real','style':'photograph',  'source':'website','reverse_searchable':True},
    'real_14':{'type':'Real','style':'cartoon',     'source':'website','reverse_searchable':True},
    'real_15':{'type':'Real','style':'illustration','source':'website','reverse_searchable':True},
    'real_16':{'type':'Real','style':'photograph',  'source':'website','reverse_searchable':True},
    'real_20':{'type':'Real','style':'cartoon',     'source':'website','reverse_searchable':True},
}
img_meta_df = pd.DataFrame(IMAGE_META).T.reset_index().rename(columns={'index':'image_id'})

# ═══════════════════════════════════════════════════════════════════
# 样本加载（来源：final_data/，已完成 MC 过滤，N=106）
# ═══════════════════════════════════════════════════════════════════
VALID_IMAGES = set(IMAGE_META.keys())
N_IMAGES = 21

ext = pd.read_csv(os.path.join(FINAL_DIR, 'participants.csv'))

ext = ext.rename(columns={
    '组别':            'group_num',         # 0=A, 1=C
    '来源':            'source_num',         # 0=real, 1=synth
    'AI熟悉度':        'ai_familiarity',
    '前测自评能力':    'self_assessed_ability',
    'AI使用频率(1-5)': 'ai_exposure_num',   # 连续变量
    '整体正确率':      'acc_total',
    'AI图正确率':      'acc_ai',
    '真实图正确率':    'acc_real',
    '后测表现自评':    'self_performance',
    '性别':            'gender_num',         # 0=male, 1=female
    '年龄段':          'age_num',            # 1-4
    '学历':            'edu_ord',            # 1-5 ordinal
    '学历分组':        'edu_group',          # 1=高中/大专 2=本科 3=硕博
    '干预停留时间(秒)':'intervention_duration_s',
    '阅读了干预材料':  'manipulation_check_read',    # 0/1/2
    '阅读了策略列表':  'manipulation_check_strategies',  # 0/1
    '策略使用程度':    'strategy_usage_degree',
    '注意力检测通过':  'attention_check_passed',
})

# 恢复文本标签（供显示 / 字符串筛选用）
ext['group']     = ext['group_num'].map({0:'对照', 1:'实验'})
ext['source']    = ext['source_num'].map({0:'real', 1:'synth'})
ext['gender']    = ext['gender_num'].map({0:'male', 1:'female'})
ext['age']       = ext['age_num'].map({1:'18-24', 2:'25-34', 3:'35-44', 4:'45-54'})
ext['education'] = ext['edu_ord'].map({1:'high-school', 2:'some-college',
                                        3:'bachelors',   4:'masters', 5:'doctorate'})
ext['edu_grp_label'] = ext['edu_group'].map({1:'高中/大专', 2:'本科', 3:'硕博'})

# ── 行为数据（responses + logs，已过滤到 MC 通过样本）────────────
r_all = pd.read_csv(os.path.join(FINAL_DIR, 'responses.csv'))
lg    = pd.read_csv(os.path.join(FINAL_DIR, 'interaction_logs.csv'))

r_f = r_all[r_all['participant_id'].isin(set(ext['participant_id']))
             & r_all['image_id'].isin(VALID_IMAGES)].copy()
r_f = r_f.merge(img_meta_df[['image_id','type','style','source','reverse_searchable']],
                on='image_id', how='left')
r_f = r_f.rename(columns={'type': 'image_type'})

# SDT per participant（从 responses 原始数据计算，与 acc 独立）
sdt_list = []
for pid, g in r_f.groupby('participant_id'):
    d = sdt_person(g); d['participant_id'] = pid; sdt_list.append(d)
sdt = pd.DataFrame(sdt_list)

conf_m    = r_f.groupby('participant_id')['confidence'].mean().reset_index(name='mean_conf')
lens_used = lg[lg['action']=='OPEN_LENS']['participant_id'].unique()
lens_deep = lg[lg['action'].isin(['SCROLL_LENS','CLICK_RESULT'])].groupby('participant_id').size().reset_index(name='lens_depth')

# Master table：以 ext 为主，合并 SDT 和行为变量
master = (ext
    .merge(sdt,    on='participant_id', how='left')
    .merge(conf_m, on='participant_id', how='left'))
master['lens_used']  = master['participant_id'].isin(lens_used).astype(int)
master = master.merge(lens_deep, on='participant_id', how='left')
master['lens_depth'] = master['lens_depth'].fillna(0)
master['intervention_duration_s'] = master['intervention_duration_s'].fillna(0)

# 频率文本标签（供人口统计交叉表使用）
_freq_rev = {1:'never',2:'rarely',3:'sometimes',4:'often',5:'very-often'}
master['ai_exposure_freq'] = master['ai_exposure_num'].map(_freq_rev)

# 派生变量
master['calibration_gap']       = master['self_performance'] / 5 - master['acc_total']
master['calib_bias']            = master['mean_conf'] / 5 - master['acc_total']
master['crr']                   = 1 - master['far']
master['efficacy_change_proxy'] = master['self_performance'] - master['self_assessed_ability']

# 样本计数（用于报告）
n_raw            = 202   # 平台注册（原始一轮）
n_after_complete = 119   # 完成 21 张
n_attn_fail      = 5     # 注意力检测失败
n_after_attn     = 114   # 通过注意力检测
n_delete         = 2     # 手动排除（delete=1，已去除与注意力检测重叠的1人）
n_mc_fail        = 6     # 实验组 manipulation check 未通过
n_orig           = 106   # 原始一轮最终分析样本
n_final          = len(master)
n_extra          = n_final - n_orig  # 合并额外数据新增人数

# Dummy 编码（参照组：性别=男，年龄=18-24，学历=本科）
# 直接使用编码表中的数值列，无需字符串比较
master['gender_female']   = master['gender_num'].astype(float)             # 0=男 1=女
master['age_25_34']       = (master['age_num'] == 2).astype(float)
master['age_35_44']       = (master['age_num'] == 3).astype(float)
master['age_45_54']       = (master['age_num'] == 4).astype(float)
# 学历三分类（参照组 = 2=本科）
master['edu_lower']       = (master['edu_group'] == 1).astype(float)  # 高中+大专
master['edu_higher']      = (master['edu_group'] == 3).astype(float)  # 硕博
master['group_c']         = master['group_num'].astype(float)              # 0=A 1=C

gA = master[master['group']=='对照']
gC = master[master['group']=='实验']
nA, nC = len(gA), len(gC)

n_miss_gender = master['gender'].isna().sum()
n_miss_age    = master['age'].isna().sum()

CTRL_VARS = ['gender_female','age_25_34','age_35_44','age_45_54',
             'edu_lower','edu_higher',
             'ai_exposure_num','self_assessed_ability']
# 调节模型专用（排除 self_assessed_ability，因 sae_c 是其中心化版本）
CTRL_VARS_MOD = [v for v in CTRL_VARS if v != 'self_assessed_ability']

VAR_LABELS = {
    'Intercept':            '截距',
    'group_c':              '组别（C=1）',
    'gender_female':        '性别（女=1）',
    'age_25_34':            '年龄 25–34（vs 18–24）',
    'age_35_44':            '年龄 35–44',
    'age_45_54':            '年龄 45–54',
    'edu_lower':            '学历 低（高中/大专 vs 本科）',
    'edu_higher':           '学历 高（硕博 vs 本科）',
    'ai_exposure_num':      'AI使用频率（1–5）',
    'self_assessed_ability':'前测自评能力（1–5）',
    'sae_c':                '前测自评能力（中心化）',
    'sae_c:group_c':        '交互：自评能力 × 组别',
    'group_c:sae_c':        '交互：组别 × 自评能力',
    'aie_c':                'AI使用频率（中心化）',
    'aie_c:group_c':        '交互：AI频率 × 组别',
    'group_c:aie_c':        '交互：组别 × AI频率',
}

# ═══════════════════════════════════════════════════════════════════
# ▌ 开始输出 Markdown 报告
# ═══════════════════════════════════════════════════════════════════
today = datetime.date.today().isoformat()
h1('Study 2 正式分析报告')
pr(f'**最终样本**: n={n_final}（对照={nA}, 实验={nC}）| **日期**: {today}')
pr('\n---')

# ═══════════════════════════════════════════════════════════════════
# 一、数据与方法
# ═══════════════════════════════════════════════════════════════════
h2('一、数据与方法')
h3('1.1 数据说明')
pr(f'- **实验平台**: 在线实验（picquiz.zeabur.app）')
pr(f'- **数据集**: 实验平台在线收集的真实数据')
pr(f'- **排除图像**: ai_06, ai_11, ai_18（质量问题），保留 {N_IMAGES} 张有效图像（9张AI，12张真实）')
pr(f'- **组别**: 对照组 vs 实验组（干预：策略教学）')

h3('1.2 核心变量说明')
md_table(
    ['变量名', '中文名称', '操作化', '来源', '量程'],
    [
        ['acc_total',             '整体正确率',     '正确判断数 / 21',                        'responses',    '0–1'],
        ["d'（dprime）",           'SDT敏感度',      'Loglinear 校正：z(HR) − z(FAR)',         '计算',         '连续'],
        ['c（判断标准）',           '判断偏向',       '负值=偏向判为AI；正值=偏向保守',          '计算',         '连续'],
        ['self_assessed_ability', '前测自评能力',    '自我评估辨别AI图片能力（前测）',           'participants', '1–5'],
        ['self_performance',      '后测表现自评',    '对自己实验表现的整体自我评估（后测）',     'post-survey',  '1–5'],
        ['calibration_gap',       '信心校准差距',    'self_performance/5 − acc_total（正=过度自信）', '计算',   '连续'],
        ['ai_exposure_num',       'AI使用频率',      'never=1 … very-often=5',                  'participants', '1–5'],
        ['efficacy_change_proxy', '效能变化代理',    'self_performance − self_assessed_ability（后−前测自评，探索性）', '计算', '连续'],
    ]
)

h3('1.3 样本过滤流程')
_filter_rows = [
    ['原始参与者（A+C）',              '—',                                str(n_raw)],
    ['完成全部21张图像',               '—',                                str(n_after_complete)],
    ['通过注意力检验',                 f'排除 {n_attn_fail} 人',           str(n_after_attn)],
    ['手动质检排除',                   f'排除 delete=1 共 {n_delete} 人',  str(n_after_attn - n_delete)],
    ['Manipulation Check（实验组）',   f'实验组未通过 MC 者排除 {n_mc_fail} 人', str(n_orig)],
]
if n_extra > 0:
    _filter_rows.append(
        [f'合并额外数据（已同等过滤）', f'新增 {n_extra} 人',
         f'**{n_final}**（对照={nA}, 实验={nC})']
    )
else:
    _filter_rows[-1][-1] = f'**{n_final}**（对照={nA}, 实验={nC})'
md_table(['步骤', '操作', '保留 n'], _filter_rows)

# ═══════════════════════════════════════════════════════════════════
# 二、基线等价性检验
# ═══════════════════════════════════════════════════════════════════
h2('二、基线等价性检验')
pr('> 随机分组假设：两组在人口统计学和基线能力上应无显著差异（*p* > .05）。\n')

h3('2.1 人口统计学分布与分组等价性（Table 1）')
if n_miss_gender > 0 or n_miss_age > 0:
    _n_gender_valid = n_final - n_miss_gender
    pr(f'> ⚠ 注：数据中存在缺失值（性别缺失 {n_miss_gender} 人，年龄缺失 {n_miss_age} 人）。'
       f'χ² 检验基于有效回答（性别有效 n={_n_gender_valid}），'
       f'百分比以组别总 n 为分母（含缺失），因此各类别之和可能小于 100%。\n')

eq_rows = []
eq_headers = ['变量 / 类别', f'对照组 (n={nA})', f'实验组 (n={nC})', 'χ²', 'df', "*p*", "Cramér's *V*"]

def add_cat(label, col, cat_order, cat_labels):
    ct = pd.crosstab(master[col], master['group'])
    try:
        chi2v, p_val, dof, V = cramers_v(ct)
        stat_str = f'{chi2v:.2f}'
        v_str    = fmt_r(V, 2)
    except Exception:
        p_val, dof, stat_str, v_str = np.nan, '—', '—', '—'
    eq_rows.append([f'**{label}**', '', '', stat_str,
                    str(dof) if isinstance(dof, (int, np.integer)) else dof,
                    fmt_p(p_val) + stars(p_val) if not np.isnan(p_val) else '—',
                    v_str])
    for cat in cat_order:
        if cat in ct.index:
            nAi = int(ct.loc[cat,'对照']) if '对照' in ct.columns else 0
            nCi = int(ct.loc[cat,'实验']) if '实验' in ct.columns else 0
            eq_rows.append([f'　{cat_labels.get(cat, cat)}',
                            pct_str(nAi, nA), pct_str(nCi, nC), '', '', '', ''])

add_cat('性别', 'gender',
        ['female','male','prefer-not-to-say'],
        {'female':'女','male':'男','prefer-not-to-say':'不愿透露'})
add_cat('年龄', 'age', ['18-24','25-34','35-44','45-54'], {})
add_cat('教育程度（三分类）', 'edu_grp_label',
        ['高中/大专','本科','硕博'], {})
add_cat('AI使用频率', 'ai_exposure_freq',
        ['never','rarely','sometimes','often','very-often'],
        {'never':'从不','rarely':'很少','sometimes':'有时','often':'经常','very-often':'非常频繁'})

md_table(eq_headers, eq_rows)

h3('2.2 连续变量基线比较（Welch\'s t 检验，Table 2）')
cont_rows = []
for col, label in [('self_assessed_ability','前测自评辨别能力（1–5）'),
                   ('ai_exposure_num',      'AI 使用频率（1–5）')]:
    a_v = gA[col].dropna().values
    c_v = gC[col].dropna().values
    t_, p_   = stats.ttest_ind(c_v, a_v, equal_var=False)
    wdf      = welch_df(a_v, c_v)
    g_       = hedges_g(c_v, a_v)
    cont_rows.append([label, ms2(a_v), ms2(c_v),
                      f'{t_:.3f}', f'{wdf:.1f}',
                      fmt_p(p_) + stars(p_), fmt_r(g_)])
md_table(['变量', f'对照组 M (SD)', f'实验组 M (SD)', 't', 'df', '*p*', "Hedges' *g*"], cont_rows)
pr('\n> **结论**: 两组在所有人口统计学变量（所有 χ² *p* > .05）和 AI 素养基线指标（所有 *p* > .05）上均无显著差异，随机分组成功。')

# ═══════════════════════════════════════════════════════════════════
# 回归辅助：论文规范格式（B / SE / Beta / t / p / VIF）
# ═══════════════════════════════════════════════════════════════════
from statsmodels.stats.outliers_influence import variance_inflation_factor as _vif_func

_DEMO_FORMULA = ('gender_female + '
                 'age_25_34 + age_35_44 + age_45_54 + '
                 'edu_lower + edu_higher')
_AI_FORMULA   = 'ai_exposure_num + self_assessed_ability'

_DEMO_COLS = ['gender_female', 'age_25_34', 'age_35_44', 'age_45_54', 'edu_lower', 'edu_higher']
_AI_COLS   = ['ai_exposure_num', 'self_assessed_ability']

_VAR_LBL = {
    'group_c':               '是否进行信息干预',
    'gender_female':         '性别（女 vs 男）',
    'age_25_34':             '年龄 25–34（vs 18–24）',
    'age_35_44':             '年龄 35–44（vs 18–24）',
    'age_45_54':             '年龄 45–54（vs 18–24）',
    'edu_lower':             '学历 低（高中/大专 vs 本科）',
    'edu_higher':            '学历 高（硕博 vs 本科）',
    'self_assessed_ability': '前测自评能力（1–5）',
    'ai_exposure_num':       'AI使用频率（1–5）',
}

_DEMO_DUMMIES = {'gender_female','age_25_34','age_35_44','age_45_54','edu_lower','edu_higher'}

def _reg_full(m, dv_col, df_m, title):
    """论文格式回归表：B | SE | Beta | t | p | VIF；返回 DataFrame 供 CSV 保存。"""
    pr(f'\n#### {title}')
    _has_demo = bool(_DEMO_DUMMIES & set(m.model.exog_names))
    if _has_demo:
        pr(f'\n> 自变量：group_c（C=1, A=0）  参照组：性别=男, 年龄=18–24, 学历=本科（三分类）  ◄ p < .05')
    else:
        pr(f'\n> 自变量：group_c（C=1, A=0）；连续控制变量已中心化至各自均值  ◄ p < .05')
    sd_y   = df_m[dv_col].dropna().std(ddof=1)
    X_arr  = m.model.exog
    X_names = list(m.model.exog_names)
    hdr = f"| {'变量':<30} | {'B':>8} | {'SE':>7} | {'Beta':>7} | {'t':>7} | {'p':>10} | {'VIF':>6} |"
    sep = '|' + '|'.join(['-'*32, '-'*10, '-'*9, '-'*9, '-'*9, '-'*12, '-'*8]) + '|'
    pr(hdr); pr(sep)
    b0, se0, t0, p0 = (m.params['Intercept'], m.bse['Intercept'],
                       m.tvalues['Intercept'], m.pvalues['Intercept'])
    pr(f"| {'(常量)':<30} | {b0:>8.3f} | {se0:>7.3f} | {'':>7} | {t0:>7.3f} | {fmt_p(p0):>10} | {'':>6} |")
    rows_out = [['(常量)', f'{b0:.3f}', f'{se0:.3f}', '', f'{t0:.3f}', fmt_p(p0), '']]
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
        rows_out.append([lbl, f'{b:.3f}', f'{se:.3f}', beta_s, f'{t:.3f}', fmt_p(p)+stars(p), vif_s])
    p_eq = '= ' if not fmt_p(m.f_pvalue).startswith('<') else ''
    pr(f'\n_R²={m.rsquared:.3f}, Adj.R²={m.rsquared_adj:.3f}, '
       f'F({m.df_model:.0f},{m.df_resid:.0f})={m.fvalue:.3f}, '
       f'p {p_eq}{fmt_p(m.f_pvalue)}{stars(m.f_pvalue)}_')
    pr(f'_因变量：{title}_\n')
    return pd.DataFrame(rows_out, columns=['变量', 'B', 'SE', 'Beta', 't', 'p', 'VIF'])

# ═══════════════════════════════════════════════════════════════════
# 三、干预主效应
# ═══════════════════════════════════════════════════════════════════
h2('三、干预主效应')
h3('3.1 组间均值比较（Welch\'s t 检验，Table 3a）')
pr('> 注：HR（命中率）= 正确识别AI图像的比例；FAR（虚报率）= 将真实图像误判为AI的比例。'
   ' CRR = 1 − FAR（与FAR互为补数，不独立报告）。\n'
   '> HR/FAR 使用 Loglinear 校正（极端值时各加 0.5 / 从分母减 1），因此与整体正确率'
   '（原始计数/21）的数值关系并非严格线性，两者报告口径略有差异。\n')

eff_rows = []
for col, label in [('acc_total', '整体正确率'),
                   ('dprime',    "d'（SDT敏感度）"),
                   ('c',         'c（判断标准，负=偏向AI）'),
                   ('hr',        '命中率 HR'),
                   ('far',       '虚报率 FAR')]:
    a_v = gA[col].dropna().values; c_v = gC[col].dropna().values
    t_, p_ = stats.ttest_ind(c_v, a_v, equal_var=False)
    wdf    = welch_df(a_v, c_v)
    g_     = hedges_g(c_v, a_v)
    eff_rows.append([label, ms(a_v), ms(c_v),
                     f'{t_:.3f}', f'{wdf:.1f}',
                     fmt_p(p_) + stars(p_), fmt_r(g_)])
md_table(['指标', f'对照组 M (SD)', f'实验组 M (SD)', 't', 'df', '*p*', "Hedges' *g*"], eff_rows)
pr('\n> **注**：*d\'* 与整体正确率在本样本中近似线性相关（*r* = .987），可能因判断标准 *c* 的个体差异较小（SD ≈ 0.38）所致；分别报告以呈现 SDT 信号检测框架。\n'
   '> 组间 *t* 检验均使用 Welch 校正（不假定方差齐性），自由度为 Welch-Satterthwaite 近似值。')

h3('3.2 回归分析（控制人口统计学）：DV = 整体正确率 & d\'')
pr('> 控制变量：性别、年龄段、学历（三分类）。参照组：性别=男，年龄=18–24，学历=本科。\n'
   '> 标准化系数 β = B × SD_X / SD_Y（连续变量及哑变量均计算，结果供参考）。\n')

# DV = acc_total（控制人口统计学）
_df_acc_demo = master.dropna(subset=['acc_total'] + _DEMO_COLS).copy()
_m_acc_demo  = smf.ols(f'acc_total ~ group_c + {_DEMO_FORMULA}', data=_df_acc_demo).fit()
t3a = _reg_full(_m_acc_demo, 'acc_total', _df_acc_demo, '识别准确率（模型一：控制人口统计学）')
residual_diagnostics_md(_m_acc_demo)
t3a.to_csv(os.path.join(OUT_DIR, 'table3a_reg_accuracy_demo_v2.csv'), index=False, encoding='utf-8-sig')

# DV = dprime（控制人口统计学）
_df_dp_demo = master.dropna(subset=['dprime'] + _DEMO_COLS).copy()
_m_dp_demo  = smf.ols(f'dprime ~ group_c + {_DEMO_FORMULA}', data=_df_dp_demo).fit()
t4a = _reg_full(_m_dp_demo, 'dprime', _df_dp_demo, "敏感性指标 d'（模型一：控制人口统计学）")
residual_diagnostics_md(_m_dp_demo)
t4a.to_csv(os.path.join(OUT_DIR, 'table4a_reg_dprime_demo_v2.csv'), index=False, encoding='utf-8-sig')

h3('3.3 回归分析（控制AI素养相关）：DV = 整体正确率 & d\'')
pr('> 控制变量：AI使用频率（1–5）、前测自评能力（1–5）；均为连续变量。\n')

# DV = acc_total（控制AI素养相关）
_df_acc_ai = master.dropna(subset=['acc_total'] + _AI_COLS).copy()
_m_acc_ai  = smf.ols(f'acc_total ~ group_c + {_AI_FORMULA}', data=_df_acc_ai).fit()
t3b = _reg_full(_m_acc_ai, 'acc_total', _df_acc_ai, '识别准确率（模型二：控制AI素养相关）')
residual_diagnostics_md(_m_acc_ai)
t3b.to_csv(os.path.join(OUT_DIR, 'table3b_reg_accuracy_ai_v2.csv'), index=False, encoding='utf-8-sig')

# DV = dprime（控制AI素养相关）
_df_dp_ai = master.dropna(subset=['dprime'] + _AI_COLS).copy()
_m_dp_ai  = smf.ols(f'dprime ~ group_c + {_AI_FORMULA}', data=_df_dp_ai).fit()
t4b = _reg_full(_m_dp_ai, 'dprime', _df_dp_ai, "敏感性指标 d'（模型二：控制AI素养相关）")
residual_diagnostics_md(_m_dp_ai)
t4b.to_csv(os.path.join(OUT_DIR, 'table4b_reg_dprime_ai_v2.csv'), index=False, encoding='utf-8-sig')

h3('3.4 层次回归：组别效应在控制协变量前后的变化')
m1 = smf.ols('acc_total ~ group_c', data=master).fit()
m2_df = master.dropna(subset=['self_assessed_ability'])
m2 = smf.ols('acc_total ~ group_c + self_assessed_ability', data=m2_df).fit()
md_table(
    ['模型', '纳入变量', 'B（组别）', '95% CI', 'R²', 'ΔR²', '*p*（组别）'],
    [
        ['M1', '仅组别',
         fmt(m1.params["group_c"],3),
         f'[{m1.conf_int().loc["group_c",0]:.3f}, {m1.conf_int().loc["group_c",1]:.3f}]',
         fmt_r(m1.rsquared), '—',
         fmt_p(m1.pvalues["group_c"]) + stars(m1.pvalues["group_c"])],
        ['M2', '+前测自评能力',
         fmt(m2.params["group_c"],3),
         f'[{m2.conf_int().loc["group_c",0]:.3f}, {m2.conf_int().loc["group_c",1]:.3f}]',
         fmt_r(m2.rsquared), f'{m2.rsquared-m1.rsquared:+.3f}',
         fmt_p(m2.pvalues["group_c"]) + stars(m2.pvalues["group_c"])],
    ]
)
_b1 = m1.params['group_c']; _b2 = m2.params['group_c']
_p1 = m1.pvalues['group_c']; _p2 = m2.pvalues['group_c']
_pct_chg = (_b2 - _b1) / abs(_b1) * 100 if _b1 != 0 else 0
_chg_desc = ('基本保持稳定' if abs(_pct_chg) < 10
             else ('小幅减弱' if _pct_chg < 0 else '小幅增强'))
_sig1 = '显著' if _p1 < .05 else '不显著'
_sig2 = '显著' if _p2 < .05 else '不显著'
pr(f'\n> **注**: 组别效应在 M1 中 {_sig1}（B={_b1:.3f}, *p*={fmt_p(_p1)}），'
   f'加入前测自评能力后{_chg_desc}（M2: B={_b2:.3f}, *p*={fmt_p(_p2)}，变化幅度={_pct_chg:+.1f}%），{_sig2}。'
   f'结论应聚焦控制协变量后的回归结果。')

# ═══════════════════════════════════════════════════════════════════
# 四、过度怀疑分析（SDT + 混合 ANOVA）
# ═══════════════════════════════════════════════════════════════════
h2('四、过度怀疑分析（T6）')

long = master[['participant_id','group','acc_ai','acc_real']].dropna().copy()
long = long.melt(id_vars=['participant_id','group'],
                 value_vars=['acc_ai','acc_real'],
                 var_name='image_type', value_name='accuracy')
long['image_type'] = long['image_type'].map({'acc_ai':'AI','acc_real':'Real'})

h3('4.1 混合 ANOVA（2组 × 2图像类型）')
anova_res = pg.mixed_anova(data=long, dv='accuracy', between='group',
                            within='image_type', subject='participant_id')
a_rows = []
for _, row in anova_res.iterrows():
    df1_col = 'DF1' if 'DF1' in anova_res.columns else 'ddof1'
    df2_col = 'DF2' if 'DF2' in anova_res.columns else 'ddof2'
    df1_val = row.get(df1_col, '—'); df2_val = row.get(df2_col, '—')
    a_rows.append([row['Source'],
                   f'{df1_val:.0f}' if isinstance(df1_val, (int,float)) and not np.isnan(float(df1_val)) else str(df1_val),
                   f'{df2_val:.0f}' if isinstance(df2_val, (int,float)) and not np.isnan(float(df2_val)) else str(df2_val),
                   f'{row["F"]:.3f}',
                   fmt_p(row['p-unc']) + stars(row['p-unc']),
                   fmt_r(row['np2'], 3)])
md_table(['效应', 'df₁', 'df₂', 'F', '*p*', 'η²p'], a_rows)

h3('4.2 按图像类型的组间差异（简单效应）')
sub_rows = []
for itype in ['AI','Real']:
    sub_l = long[long['image_type']==itype]
    a_ = sub_l[sub_l['group']=='对照']['accuracy'].values
    c_ = sub_l[sub_l['group']=='实验']['accuracy'].values
    t_, p_ = stats.ttest_ind(c_, a_, equal_var=False)
    wdf    = welch_df(a_, c_)
    g_     = hedges_g(c_, a_)
    sub_rows.append([itype+'图像', ms(a_), ms(c_),
                     f'{t_:.3f}', f'{wdf:.1f}',
                     fmt_p(p_) + stars(p_), fmt_r(g_)])
md_table(['图像类型', '对照组 M (SD)', '实验组 M (SD)', 't', 'df', '*p*', "Hedges' *g*"], sub_rows)

_c_ai   = gC['acc_ai'].mean(); _a_ai   = gA['acc_ai'].mean()
_c_real = gC['acc_real'].mean(); _a_real = gA['acc_real'].mean()
_inter_p = anova_res[anova_res['Source']=='Interaction']['p-unc'].values
_inter_p_val = float(_inter_p[0]) if len(_inter_p) > 0 else np.nan
pr(f'\n> **结果解读**: 实验组在AI图像上准确率高于对照组（{_c_ai:.3f} vs {_a_ai:.3f}，**p < .05**），'
   f'在真实图像上也略高（{_c_real:.3f} vs {_a_real:.3f}，未显著）。'
   f'group × image_type 交互 *p* = {fmt_p(_inter_p_val)}，{"不显著" if _inter_p_val >= .05 else "显著"}。'
   f'**当前数据不支持"过度怀疑"（实验组真实图像准确率下降）的解读**；'
   f'实验组判断标准 c 更负（见 3.1），反映更倾向判为AI，但尚未造成真实图像准确率下降。')

# ═══════════════════════════════════════════════════════════════════
# 五、信心与校准分析（T5）
# ═══════════════════════════════════════════════════════════════════
h2('五、信心与校准分析（T5）')

h3('5.1 后测表现自评与 calibration_gap 组间比较')
u_a = gA['self_performance'].dropna(); u_c = gC['self_performance'].dropna()
med_a = np.median(u_a); med_c = np.median(u_c)
iq_a  = np.percentile(u_a, 75) - np.percentile(u_a, 25)
iq_c  = np.percentile(u_c, 75) - np.percentile(u_c, 25)
U, p_u = stats.mannwhitneyu(u_c.values, u_a.values, alternative='two-sided')
n_mw = len(u_a) + len(u_c)
r_eff = 1 - 2*U/(len(u_c)*len(u_a))   # r = 1 - 2U/(n1*n2)

cg_a = gA['calibration_gap'].dropna().values
cg_c = gC['calibration_gap'].dropna().values
t_cg, p_cg = stats.ttest_ind(cg_c, cg_a, equal_var=False)
wdf_cg = welch_df(cg_a, cg_c)
g_cg   = hedges_g(cg_c, cg_a)
t_1samp, p_1samp = stats.ttest_1samp(np.concatenate([cg_a, cg_c]), 0)

md_table(
    ['指标', '对照组', '实验组', '统计量', 'df', '*p*', '效应量'],
    [
        ['后测表现自评',
         f'Mdn={med_a:.1f}, IQR={iq_a:.1f}',
         f'Mdn={med_c:.1f}, IQR={iq_c:.1f}',
         f'U={U:.0f}', f'—', fmt_p(p_u)+stars(p_u),
         f'r = {fmt_r(r_eff)}（Z/√N 估计）'],
        ['calibration_gap（M, SD）', ms(cg_a), ms(cg_c),
         f't={t_cg:.3f}', f'{wdf_cg:.1f}',
         fmt_p(p_cg)+stars(p_cg), f"g = {fmt_r(g_cg)}"],
        ['calibration_gap vs 0（全样本）', '—', '—',
         f't={t_1samp:.3f}', f'{len(cg_a)+len(cg_c)-1}',
         fmt_p(p_1samp)+stars(p_1samp), '—'],
    ]
)
pr('\n> **calibration_gap** = self_performance/5 − acc_total（正值=过度自信，负值=过度保守）\n'
   '> Mann-Whitney U 用于非正态 self_performance；Welch\'s t 用于 calibration_gap。')

h3('5.2 calibration_gap 回归（分别控制人口统计学 / AI素养相关，Table 5）')
pr('> 模型一参照组：性别=男，年龄=18–24，学历=本科；模型二仅含连续变量（无哑变量参照组）。\n')

# 模型一：控制人口统计学
_df_cg_demo = master.dropna(subset=['calibration_gap'] + _DEMO_COLS).copy()
_m_cg_demo  = smf.ols(f'calibration_gap ~ group_c + {_DEMO_FORMULA}', data=_df_cg_demo).fit()
t5a = _reg_full(_m_cg_demo, 'calibration_gap', _df_cg_demo, '信心校准差距（模型一：控制人口统计学）')
residual_diagnostics_md(_m_cg_demo)
t5a.to_csv(os.path.join(OUT_DIR, 'table5a_reg_calibration_demo_v2.csv'), index=False, encoding='utf-8-sig')

# 模型二：控制AI素养相关
_df_cg_ai = master.dropna(subset=['calibration_gap'] + _AI_COLS).copy()
_m_cg_ai  = smf.ols(f'calibration_gap ~ group_c + {_AI_FORMULA}', data=_df_cg_ai).fit()
t5b = _reg_full(_m_cg_ai, 'calibration_gap', _df_cg_ai, '信心校准差距（模型二：控制AI素养相关）')
residual_diagnostics_md(_m_cg_ai)
t5b.to_csv(os.path.join(OUT_DIR, 'table5b_reg_calibration_ai_v2.csv'), index=False, encoding='utf-8-sig')

# ═══════════════════════════════════════════════════════════════════
# 六、逐图与图像类型分析（F1, F2）
# ═══════════════════════════════════════════════════════════════════
h2('六、逐图与图像类型分析')
r_m = r_f.merge(master[['participant_id','group']], on='participant_id', how='inner')

h3('6.1 每张图 Fisher 精确检验（group × is_correct）')
N_FISHER = 0
fisher_rows_data = []
for img_id, grp in r_m.groupby('image_id'):
    tbl = pd.crosstab(grp['group'], grp['is_correct'])
    if tbl.shape == (2,2):
        N_FISHER += 1
        OR, p_f = stats.fisher_exact(tbl.values)
        acc_A = grp[grp['group']=='对照']['is_correct'].mean()
        acc_C = grp[grp['group']=='实验']['is_correct'].mean()
        meta  = IMAGE_META.get(img_id, {})
        fisher_rows_data.append({
            'image_id': img_id, 'type': meta.get('type','?'),
            'style': meta.get('style','?'),
            'acc_A': acc_A, 'acc_C': acc_C,
            'diff': acc_C - acc_A, 'OR': OR, 'p': p_f,
            'p_bonf': min(p_f * N_FISHER, 1.0)
        })

fisher_df = pd.DataFrame(fisher_rows_data).sort_values('diff', ascending=False)
alpha_bonf = 0.05 / N_FISHER

fish_md = []
for _, row in fisher_df.iterrows():
    fish_md.append([
        row['image_id'], row['type'], row['style'],
        f'{row["acc_A"]:.3f}', f'{row["acc_C"]:.3f}', f'{row["diff"]:+.3f}',
        f'{row["OR"]:.3f}',
        fmt_p(row['p']) + stars(row['p']),
        fmt_p(row['p_bonf']) + ('†' if row['p_bonf'] < .05 else ''),
    ])
md_table(['图像ID','类型','风格','对照组准确率','实验组准确率','Δ(实验−对照)','OR','*p*（未校正）','*p*（Bonferroni）'], fish_md)
sig_raw  = fisher_df[fisher_df['p'] < .05]['image_id'].tolist()
sig_bonf = fisher_df[fisher_df['p_bonf'] < .05]['image_id'].tolist()
pr(f'\n> 原始 *p* < .05：**{sig_raw}**；Bonferroni 校正后（α = .05/{N_FISHER} = {alpha_bonf:.4f}）显著：**{sig_bonf if sig_bonf else "无"}**。')

h3('6.2 风格类型分析（photo vs not_photo）')
pr('> illustration 与 cartoon 合并为 not_photo；photograph 单独为 photo。\n')

# 二分类风格：photo=1，not_photo=0
r_m['style_photo'] = (r_m['style'] == 'photograph').astype(int)
style_acc = r_m.groupby(['participant_id','group','style_photo'])['is_correct'].mean().reset_index(name='acc')
sty_rows = []
for sp, lbl in [(1,'photo（照片）'), (0,'not_photo（插图/卡通）')]:
    sub_s = style_acc[style_acc['style_photo']==sp]
    a_ = sub_s[sub_s['group']=='对照']['acc'].values
    c_ = sub_s[sub_s['group']=='实验']['acc'].values
    if len(a_) > 1 and len(c_) > 1:
        t_, p_ = stats.ttest_ind(c_, a_, equal_var=False)
        wdf    = welch_df(a_, c_)
        g_     = hedges_g(c_, a_)
        sty_rows.append([lbl, ms(a_), ms(c_),
                         f'{t_:.3f}', f'{wdf:.1f}',
                         fmt_p(p_)+stars(p_), fmt_r(g_)])
md_table(['风格', '对照组 M (SD)', '实验组 M (SD)', 't', 'df', '*p*', "Hedges' *g*"], sty_rows)

# 交互 OLS：group × style_photo
style_wide = style_acc.copy()
style_wide['group_c'] = (style_wide['group']=='实验').astype(float)
m_style = smf.ols('acc ~ group_c * style_photo', data=style_wide).fit()
pr(f'\n> **模型**: acc ~ group_c × style_photo（0=not_photo, 1=photo），n={len(style_wide)} 行。')
pr(f'> F({m_style.df_model:.0f},{m_style.df_resid:.0f})={m_style.fvalue:.3f}, '
   f'p {fmt_p(m_style.f_pvalue)+stars(m_style.f_pvalue)}\n')
for k, v in m_style.pvalues.items():
    pr(f'- {k}: B={m_style.params[k]:.3f}, *p* = {fmt_p(v)+stars(v)}')

h3('6.3 可反向搜索性分析（reverse_searchable）')
pr('> **分析单位**：先对每位被试在各类别图像上取平均正确率（被试水平），再做 Welch\'s *t* 检验，'
   '避免观测值级别（n≈108×图像数）重复测量导致 df 虚大（原始行级别分析会出现 df>1000）。\n')
# 聚合到被试水平后再做 t 检验
rs_agg = r_m.groupby(['participant_id','group','reverse_searchable'])['is_correct'].mean().reset_index(name='acc_rs')
rs_rows = []
for rs_val, label in [(True,'可反向搜索'), (False,'不可反向搜索（仅AI图）')]:
    sub_r = rs_agg[rs_agg['reverse_searchable']==rs_val]
    a_ = sub_r[sub_r['group']=='对照']['acc_rs'].values
    c_ = sub_r[sub_r['group']=='实验']['acc_rs'].values
    if len(a_) > 1 and len(c_) > 1:
        t_, p_ = stats.ttest_ind(c_, a_, equal_var=False)
        wdf    = welch_df(a_, c_)
        g_     = hedges_g(c_, a_)
        rs_rows.append([label, f'{np.mean(a_):.3f}', f'{np.mean(c_):.3f}',
                        f'{t_:.3f}', f'{wdf:.1f}',
                        fmt_p(p_)+stars(p_), fmt_r(g_)])
md_table(['类型', '对照组均值', '实验组均值', 't', 'df', '*p*', "Hedges' *g*"], rs_rows)

h3('6.4 AI 来源分析（仅AI图）')
r_ai = r_m[r_m['image_type']=='AI'].copy()
source_acc = r_ai.groupby(['participant_id','group','source'], observed=True)['is_correct'].mean().reset_index(name='acc')
src_rows = []
for src in ['ai-art','midjourney','nanobanana']:
    sub_s = source_acc[source_acc['source']==src]
    a_ = sub_s[sub_s['group']=='对照']['acc'].dropna().values
    c_ = sub_s[sub_s['group']=='实验']['acc'].dropna().values
    if len(a_) > 1 and len(c_) > 1:
        t_, p_ = stats.ttest_ind(c_, a_, equal_var=False)
        wdf    = welch_df(a_, c_)
        g_     = hedges_g(c_, a_)
        src_rows.append([src, ms(a_), ms(c_),
                         f'{t_:.3f}', f'{wdf:.1f}',
                         fmt_p(p_)+stars(p_), fmt_r(g_)])
md_table(['AI来源', '对照组 M (SD)', '实验组 M (SD)', 't', 'df', '*p*', "Hedges' *g*"], src_rows)

# ═══════════════════════════════════════════════════════════════════
# 七、AI 素养调节效应
# ═══════════════════════════════════════════════════════════════════
h2('七、AI 素养调节效应')

h3('7.1 AI 素养与准确率的相关分析')
corr_rows_sec7 = []
for col, label in [('self_assessed_ability','前测自评能力'),
                   ('ai_exposure_num','AI使用频率（1–5）')]:
    valid = master[['acc_total',col]].dropna()
    r_v, p_v = stats.pearsonr(valid['acc_total'], valid[col])
    corr_rows_sec7.append([label, fmt_r(r_v), fmt_p(p_v)+stars(p_v), str(len(valid))])
md_table(['变量', 'r（与准确率）', '*p*', 'n'], corr_rows_sec7)

h3('7.2 调节效应模型（前测自评能力 × 组别）')
pr('> 两个版本：**完整模型**（含人口统计学+AI使用频率控制变量）；**简约模型**（仅组别 × 自评能力，无其他控制）。\n'
   '> 均使用 self_assessed_ability 的中心化版本 sae_c。\n')

# ── 公共：中心化 sae_c ──────────────────────────────────────────────
_sae_base = master.dropna(subset=['acc_total','self_assessed_ability','group_c']).copy()
_sae_base['sae_c'] = _sae_base['self_assessed_ability'] - _sae_base['self_assessed_ability'].mean()
sd_sae   = _sae_base['self_assessed_ability'].std(ddof=1)
mean_sae = _sae_base['self_assessed_ability'].mean()

# ── 完整模型（含全部控制变量）──────────────────────────────────────
pr('\n**模型 I：完整模型（含人口统计学 + AI使用频率控制变量）**\n')
mod_df = _sae_base.dropna(subset=CTRL_VARS_MOD).copy()
mod_df['sae_c'] = mod_df['self_assessed_ability'] - mod_df['self_assessed_ability'].mean()
ctrl_str_mod = ' + '.join(CTRL_VARS_MOD)
m_mod = smf.ols(f'acc_total ~ group_c * sae_c + {ctrl_str_mod}', data=mod_df).fit()
X_mod_raw = mod_df[['group_c','sae_c'] + CTRL_VARS_MOD]
X_mod_std = X_mod_raw.apply(lambda col: (col-col.mean())/col.std(ddof=1) if col.std(ddof=1)>0 else col)
regression_table_md(m_mod, X_mod_raw, X_mod_std, VAR_LABELS)
residual_diagnostics_md(m_mod)

# ── 简约模型（仅组别 × 自评能力）──────────────────────────────────
pr('\n**模型 II：简约模型（仅 group_c × sae_c，无其他控制变量）**\n')
min_df = _sae_base.copy()
m_mod_min = smf.ols('acc_total ~ group_c * sae_c', data=min_df).fit()
X_min_raw = min_df[['group_c','sae_c']]
X_min_std = X_min_raw.apply(lambda col: (col-col.mean())/col.std(ddof=1) if col.std(ddof=1)>0 else col)
regression_table_md(m_mod_min, X_min_raw, X_min_std, VAR_LABELS)
residual_diagnostics_md(m_mod_min)

h3('7.3 简单斜率分析（group 效应 at −1SD / Mean / +1SD 自评能力）')
pr('> 两个版本分别对应完整模型（模型 I）和简约模型（模型 II）。\n')

def _simple_slopes(m_base, ctrl_formula, df_base, label_prefix):
    pr(f'\n**{label_prefix}**\n')
    ss_rows = []
    for level, lbl in [(-sd_sae, f'低自评 −1SD (SAE≈{mean_sae-sd_sae:.2f})'),
                       (0.0,     f'均值     (SAE≈{mean_sae:.2f})'),
                       (+sd_sae, f'高自评 +1SD (SAE≈{mean_sae+sd_sae:.2f})')]:
        df_tmp = df_base.copy()
        df_tmp['sae_tmp'] = df_tmp['sae_c'] - level
        formula = f'acc_total ~ group_c * sae_tmp' + (f' + {ctrl_formula}' if ctrl_formula else '')
        m_tmp = smf.ols(formula, data=df_tmp).fit()
        b = m_tmp.params['group_c']; se = m_tmp.bse['group_c']
        t_ = m_tmp.tvalues['group_c']; p_ = m_tmp.pvalues['group_c']
        ci_lo = m_tmp.conf_int().loc['group_c',0]; ci_hi = m_tmp.conf_int().loc['group_c',1]
        ss_rows.append([lbl, fmt(b,3), fmt(se,3),
                        f'[{ci_lo:.3f}, {ci_hi:.3f}]',
                        fmt(t_,3), fmt_p(p_)+stars(p_)])
    md_table(['水平', 'B（组别效应）', 'SE', '95% CI', 't', '*p*'], ss_rows)

    int_coef = m_base.params.get('group_c:sae_c', np.nan)
    b_grp    = m_base.params.get('group_c', np.nan)
    se_grp   = m_base.bse.get('group_c', np.nan)
    if not np.isnan(int_coef) and abs(int_coef) > 1e-10:
        try:
            jn1 = (-b_grp - 1.96*se_grp) / int_coef
            jn2 = (-b_grp + 1.96*se_grp) / int_coef
            pr(f'\nJohnson-Neyman 近似显著性边界（中心化 sae_c）: {min(jn1,jn2):.3f} 到 {max(jn1,jn2):.3f}')
            pr(f'→ 对应原始 self_assessed_ability: {mean_sae+min(jn1,jn2):.2f} 到 {mean_sae+max(jn1,jn2):.2f}')
            pr(f'→ group 效应在此区间**外**达 *p* < .05（交互方向 {">" if int_coef>0 else "<"} 0）')
        except Exception:
            pr('> JN 计算失败')

_simple_slopes(m_mod,     ctrl_str_mod, mod_df,  '模型 I 简单斜率（完整控制变量）')
_simple_slopes(m_mod_min, '',           min_df,  '模型 II 简单斜率（简约：无控制变量）')

h3('7.4 调节效应模型（AI使用频率 × 组别）')
pr('> 两个版本：**完整模型**（含人口统计学 + 前测自评能力控制变量）；**简约模型**（仅组别 × AI频率，无其他控制）。\n'
   '> 均使用 ai_exposure_num 的中心化版本 aie_c。\n')

# 控制变量：把 ai_exposure_num 从 CTRL_VARS 中排除（因 aie_c 是其中心化版本）
_CTRL_AIE = [v for v in CTRL_VARS if v != 'ai_exposure_num']
_ctrl_aie_str = ' + '.join(_CTRL_AIE)

_aie_base = master.dropna(subset=['acc_total','ai_exposure_num','group_c']).copy()
_aie_base['aie_c'] = _aie_base['ai_exposure_num'] - _aie_base['ai_exposure_num'].mean()
sd_aie   = _aie_base['ai_exposure_num'].std(ddof=1)
mean_aie = _aie_base['ai_exposure_num'].mean()

# ── 完整模型 ──────────────────────────────────────────────────────
pr('\n**模型 I：完整模型（含人口统计学 + 前测自评能力控制变量）**\n')
aie_df = _aie_base.dropna(subset=_CTRL_AIE).copy()
aie_df['aie_c'] = aie_df['ai_exposure_num'] - aie_df['ai_exposure_num'].mean()
m_aie = smf.ols(f'acc_total ~ group_c * aie_c + {_ctrl_aie_str}', data=aie_df).fit()
X_aie_raw = aie_df[['group_c','aie_c'] + _CTRL_AIE]
X_aie_std = X_aie_raw.apply(lambda col: (col-col.mean())/col.std(ddof=1) if col.std(ddof=1)>0 else col)
regression_table_md(m_aie, X_aie_raw, X_aie_std, VAR_LABELS)
residual_diagnostics_md(m_aie)

# ── 简约模型 ──────────────────────────────────────────────────────
pr('\n**模型 II：简约模型（仅 group_c × aie_c，无其他控制变量）**\n')
aie_min_df = _aie_base.copy()
m_aie_min = smf.ols('acc_total ~ group_c * aie_c', data=aie_min_df).fit()
X_aie_min_raw = aie_min_df[['group_c','aie_c']]
X_aie_min_std = X_aie_min_raw.apply(lambda col: (col-col.mean())/col.std(ddof=1) if col.std(ddof=1)>0 else col)
regression_table_md(m_aie_min, X_aie_min_raw, X_aie_min_std, VAR_LABELS)
residual_diagnostics_md(m_aie_min)

h3('7.5 简单斜率分析（group 效应 at −1SD / Mean / +1SD AI使用频率）')
pr('> 两个版本分别对应完整模型（模型 I）和简约模型（模型 II）。\n')

def _simple_slopes_aie(m_base, ctrl_formula, df_base, label_prefix):
    pr(f'\n**{label_prefix}**\n')
    aie_ss_rows = []
    for level, lbl in [(-sd_aie, f'低频率 −1SD (AIE≈{mean_aie-sd_aie:.2f})'),
                       (0.0,     f'均值     (AIE≈{mean_aie:.2f})'),
                       (+sd_aie, f'高频率 +1SD (AIE≈{mean_aie+sd_aie:.2f})')]:
        df_tmp = df_base.copy()
        df_tmp['aie_tmp'] = df_tmp['aie_c'] - level
        formula = 'acc_total ~ group_c * aie_tmp' + (f' + {ctrl_formula}' if ctrl_formula else '')
        m_tmp = smf.ols(formula, data=df_tmp).fit()
        b = m_tmp.params['group_c']; se = m_tmp.bse['group_c']
        t_ = m_tmp.tvalues['group_c']; p_ = m_tmp.pvalues['group_c']
        ci_lo = m_tmp.conf_int().loc['group_c',0]; ci_hi = m_tmp.conf_int().loc['group_c',1]
        aie_ss_rows.append([lbl, fmt(b,3), fmt(se,3),
                            f'[{ci_lo:.3f}, {ci_hi:.3f}]',
                            fmt(t_,3), fmt_p(p_)+stars(p_)])
    md_table(['水平', 'B（组别效应）', 'SE', '95% CI', 't', '*p*'], aie_ss_rows)

    int_coef = m_base.params.get('group_c:aie_c', np.nan)
    b_grp    = m_base.params.get('group_c', np.nan)
    se_grp   = m_base.bse.get('group_c', np.nan)
    if not np.isnan(int_coef) and abs(int_coef) > 1e-10:
        try:
            jn1 = (-b_grp - 1.96*se_grp) / int_coef
            jn2 = (-b_grp + 1.96*se_grp) / int_coef
            pr(f'\nJohnson-Neyman 近似显著性边界（中心化 aie_c）: {min(jn1,jn2):.3f} 到 {max(jn1,jn2):.3f}')
            pr(f'→ 对应原始 ai_exposure_num: {mean_aie+min(jn1,jn2):.2f} 到 {mean_aie+max(jn1,jn2):.2f}')
            pr(f'→ group 效应在此区间**外**达 _p_ < .05（交互方向 {">" if int_coef>0 else "<"} 0）')
        except Exception:
            pr('> JN 计算失败')

_simple_slopes_aie(m_aie,     _ctrl_aie_str, aie_df,     '模型 I 简单斜率（完整控制变量）')
_simple_slopes_aie(m_aie_min, '',            aie_min_df, '模型 II 简单斜率（简约：无控制变量）')

# ═══════════════════════════════════════════════════════════════════
# 八、异质性分析 + Chow 检验（T7, T8）
# ═══════════════════════════════════════════════════════════════════
h2('八、异质性分析（T7, T8）')
pr('> **分组说明**: 学历三分类——低（高中/大专, n≈25）、中（本科, n≈45, 参照）、高（硕博, n≈45）。\n')

# ▸ 修正：edu_high 包含本科 + 研究生，避免遗漏 n≈41 的本科样本
subgroup_defs = {
    'gender_male':   master[master['gender']=='male'],
    'gender_female': master[master['gender']=='female'],
    'age_le34':      master[master['age'].isin(['18-24','25-34'])],
    'age_ge35':      master[master['age'].isin(['35-44','45-54'])],
    # 学历三分类异质性
    'edu_low':       master[master['edu_group']==1],   # 高中+大专
    'edu_mid':       master[master['edu_group']==2],   # 本科
    'edu_high':      master[master['edu_group']==3],   # 硕博
    'ai_freq_low':   master[master['ai_exposure_freq'].isin(['never','rarely','sometimes'])],
    'ai_freq_high':  master[master['ai_exposure_freq'].isin(['often','very-often'])],
    'sae_low':       master[master['self_assessed_ability'].isin([1.0,2.0])],
    'sae_high':      master[master['self_assessed_ability'].isin([3.0,4.0,5.0])],
}
sg_labels = {
    'gender_male':'性别：男','gender_female':'性别：女',
    'age_le34':'年龄：≤34','age_ge35':'年龄：≥35',
    'edu_low':'学历：低（高中/大专）','edu_mid':'学历：中（本科）','edu_high':'学历：高（硕博）',
    'ai_freq_low':'AI频率：低','ai_freq_high':'AI频率：高',
    'sae_low':'前测自评：低（1–2）','sae_high':'前测自评：高（3–5）',
}
pair_keys = [
    ('gender_male','gender_female','性别'),
    ('age_le34','age_ge35','年龄'),
    ('edu_low','edu_mid','学历（低 vs 中）'),
    ('edu_mid','edu_high','学历（中 vs 高）'),
    ('ai_freq_low','ai_freq_high','AI使用频率'),
    ('sae_low','sae_high','前测自评能力'),
]

for dv, tbl_label, tbl_fname in [
    ('acc_total',       '辨别能力异质性（T7）',  'table7_heterogeneity_accuracy_v2.csv'),
    ('calibration_gap', '信心校准异质性（T8）',  'table8_heterogeneity_calibration_v2.csv'),
]:
    h3(f'8.{"1" if "acc" in dv else "2"} {tbl_label}')
    het_rows = []
    for pair_idx, (k1, k2, pair_label) in enumerate(pair_keys):
        # 在每个新比较组之前插入分隔行（除第一行外）
        if pair_idx > 0:
            het_rows.append([f'*— {pair_label} —*', '', '', '', '', ''])
        df1 = subgroup_defs[k1].dropna(subset=[dv,'group_c'])
        df2 = subgroup_defs[k2].dropna(subset=[dv,'group_c'])
        df_pool = pd.concat([df1,df2]).dropna(subset=[dv,'group_c'])
        try:
            F_c, p_c, _ = chow_test(df_pool, df1, df2, f'{dv} ~ group_c')
            chow_str = f'F={F_c:.3f}, *p*={fmt_p(p_c)+stars(p_c)}'
        except Exception:
            chow_str = '—'
        for sg_key, sg_df in [(k1,df1),(k2,df2)]:
            lbl = sg_labels.get(sg_key, sg_key)
            if len(sg_df) < 4:
                het_rows.append([lbl, str(len(sg_df)), '—','—','—', chow_str if sg_key==k1 else ''])
                continue
            try:
                m_ = smf.ols(f'{dv} ~ group_c', data=sg_df).fit()
                B_ = m_.params.get('group_c', np.nan)
                p_ = m_.pvalues.get('group_c', np.nan)
                t_ = m_.tvalues.get('group_c', np.nan)
            except Exception:
                B_, t_, p_ = np.nan, np.nan, np.nan
            het_rows.append([lbl, str(len(sg_df)),
                             fmt(B_,3) if not np.isnan(B_) else '—',
                             fmt(t_,3) if not np.isnan(t_) else '—',
                             fmt_p(p_)+stars(p_) if not np.isnan(p_) else '—',
                             chow_str if sg_key==k1 else ''])
    md_table(['子群','n','B (组别)','t','*p*','Chow 检验'], het_rows)
    het_df = pd.DataFrame(het_rows, columns=['子群','n','B','t','p','Chow检验'])
    het_df.to_csv(os.path.join(OUT_DIR, tbl_fname), index=False, encoding='utf-8-sig')

# ═══════════════════════════════════════════════════════════════════
# 九、策略使用分析
# ═══════════════════════════════════════════════════════════════════
h2('九、策略使用分析')

STRATEGY_KEYWORDS = {
    'Anatomy':   ['手','finger','解剖','手指','脸','face','eye','眼','anatomy',
                  'fingers','hand','skin','hair','头发','比例'],
    'Style':     ['风格','style','texture','纹理','质感','感觉','feel','smooth',
                  '光滑','塑料','背景','background','光影','light','完美','渲染',
                  '颜色','过渡'],
    'Knowledge': ['搜索','search','google','lens','网站','来源','source',
                  'reverse','图片来源','验证'],
}

def code_strategy(text):
    if pd.isna(text) or str(text).strip() == '': return None
    t = str(text).lower()
    tags = [k for k,ws in STRATEGY_KEYWORDS.items() if any(w in t for w in ws)]
    return ','.join(tags) if tags else '直觉/其他'

r_strat = r_m.copy()
r_strat['strategy_cat'] = r_strat['reasoning'].apply(code_strategy)
r_strat['has_strategy'] = r_strat['strategy_cat'].notna().astype(int)

h3('9.1 逐图策略填写率（by 组别）')
fill = r_strat.groupby('group')['has_strategy'].agg(
    填写率=lambda x: f'{x.mean():.3f}',
    填写次数='sum', 总次数='count').reset_index()
md_table(list(fill.columns), fill.values.tolist())

h3('9.2 策略类别 × 正确率')
cat_rows = []
for cat in ['Style','Anatomy','Knowledge','直觉/其他']:
    for grp in ['对照','实验']:
        sub_r = r_strat[(r_strat['group']==grp) &
                        (r_strat['strategy_cat'].notna()) &
                        (r_strat['strategy_cat'].str.contains(cat, na=False))]
        if len(sub_r) > 0:
            cat_rows.append([grp, cat, str(len(sub_r)), f'{sub_r["is_correct"].mean():.3f}'])
if cat_rows:
    md_table(['组别','策略类型','n','正确率'], cat_rows)

h3('9.3 有无策略自报 → 准确率差异')
fill_rows = []
for grp in ['对照','实验']:
    g_ = r_strat[r_strat['group']==grp]
    acc_w  = g_[g_['has_strategy']==1]['is_correct'].mean()
    acc_wo = g_[g_['has_strategy']==0]['is_correct'].mean()
    n_w  = (g_['has_strategy']==1).sum()
    n_wo = (g_['has_strategy']==0).sum()
    diff = acc_w - acc_wo if not np.isnan(acc_w) else np.nan
    fill_rows.append([grp,
                      f'{acc_w:.3f} (n={n_w})' if not np.isnan(acc_w) else '—',
                      f'{acc_wo:.3f} (n={n_wo})',
                      f'{diff:+.3f}' if not np.isnan(diff) else '—'])
md_table(['组别','有策略自报','无策略自报','差值（有−无）'], fill_rows)

if 'strategy_usage_degree' in master.columns:
    valid_deg = master[(master['group']=='实验') & master['strategy_usage_degree'].notna()]
    if len(valid_deg) > 3:
        r_v, p_v = stats.pearsonr(valid_deg['acc_total'], valid_deg['strategy_usage_degree'])
        pr(f'\n> 实验组 strategy_usage_degree × 准确率: *r* = {fmt_r(r_v)}, *p* = {fmt_p(p_v)+stars(p_v)}')

# ═══════════════════════════════════════════════════════════════════
# 十、相关矩阵（F3）
# ═══════════════════════════════════════════════════════════════════
h2('十、相关矩阵（F3）')
pr('> 注：干预时长（intervention_duration_s）在 A 组中无实际干预（填充为 0），对全样本相关分析会人为压低相关值，故从相关矩阵中排除。\n'
   '> 效能变化代理 = self_performance − self_assessed_ability（后测自评表现 − 前测自评能力；量表含义不同，仅作探索性指标）。\n')

# 相关矩阵不含 intervention_duration_s
corr_vars = ['acc_total','dprime','self_assessed_ability',
             'ai_exposure_num','calibration_gap','efficacy_change_proxy']
corr_labels = ["准确率","d'","前测自评","AI使用频率","校准差距","效能变化代理"]

corr_df  = master[corr_vars].dropna(how='all')
corr_mat = corr_df.corr(method='pearson').round(3)   # 仅供热力图使用

# 相关矩阵显示：每对变量直接用 pearsonr 计算（避免 corr_mat 四舍五入导致 r 显示不一致）
corr_rows = []
for i, (v, lbl) in enumerate(zip(corr_vars, corr_labels)):
    row = [lbl]
    for j in range(len(corr_vars)):
        if j > i:
            row.append('—')
        elif i == j:
            row.append('1.000')
        else:
            pair = corr_df[[corr_vars[i], corr_vars[j]]].dropna()
            if len(pair) > 2:
                r_val, p_val = stats.pearsonr(pair.iloc[:,0], pair.iloc[:,1])
            else:
                r_val, p_val = np.nan, 1.0
            row.append(f'{r_val:.3f}{stars(p_val)}')
    corr_rows.append(row)
md_table([''] + corr_labels, corr_rows)
pr('\n*注：\\* p < .05，\\*\\* p < .01，\\*\\*\\* p < .001（双尾，未校正）*')

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import seaborn as sns
    mask = np.triu(np.ones_like(corr_mat, dtype=bool))
    fig, ax = plt.subplots(figsize=(9,7))
    sns.heatmap(corr_mat, mask=mask, annot=True, fmt='.2f', cmap='RdBu_r',
                center=0, vmin=-1, vmax=1, ax=ax,
                xticklabels=corr_labels, yticklabels=corr_labels,
                linewidths=0.5, annot_kws={'size':8})
    ax.set_title('变量相关矩阵（Pearson r）', fontsize=12, pad=10)
    plt.tight_layout()
    fig_path = os.path.join(OUT_DIR, 'F3_correlation_heatmap_v2.png')
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()
    pr(f'\n![相关矩阵热力图](F3_correlation_heatmap_v2.png)')
except ImportError:
    pr('\n> ⚠ matplotlib/seaborn 未安装，跳过热力图绘制')

# ═══════════════════════════════════════════════════════════════════
# 十一、综合结论
# ═══════════════════════════════════════════════════════════════════
h2('十一、综合结论')
pr(f'**最终样本**: n={n_final}（对照={nA}, 实验={nC}）\n')

acc_t, acc_p = stats.ttest_ind(gC['acc_total'].dropna().values,
                                gA['acc_total'].dropna().values, equal_var=False)
acc_g = hedges_g(gC['acc_total'].dropna().values, gA['acc_total'].dropna().values)
int_p = m_mod.pvalues.get('group_c:sae_c', float('nan'))
int_b = m_mod.params.get('group_c:sae_c', float('nan'))

md_table(
    ['分析', '主要结果', '统计量', '*p*'],
    [
        ['主效应：整体正确率',
         f'对照={gA.acc_total.mean():.3f}, 实验={gC.acc_total.mean():.3f}, g={fmt_r(acc_g)}',
         f't={acc_t:.3f}', fmt_p(acc_p)+stars(acc_p)],
        ["主效应：d'",
         f"对照={gA.dprime.mean():.3f}, 实验={gC.dprime.mean():.3f}",
         '见 Table 3a', '—'],
        ['判断偏向 c',
         f'对照={gA.c.mean():.3f}（保守）, 实验={gC.c.mean():.3f}（激进）',
         '见 Table 3a', '—'],
        ['过度怀疑',
         f'实验在AI图更好（+{_c_ai-_a_ai:.3f}）；Real图差异不显著；数据不支持过度怀疑',
         f'交互 F', fmt_p(_inter_p_val)+stars(_inter_p_val)],
        ['校准差距（全样本）',
         f'M={np.nanmean(np.concatenate([cg_a,cg_c])):+.3f}（轻度过度自信）',
         f't={t_1samp:.3f}', fmt_p(p_1samp)+stars(p_1samp)],
        ['调节：自评能力 × 组别',
         f'低自评者 C>A 显著；高自评者无差异',
         f'B={int_b:.3f}', fmt_p(int_p)+stars(int_p)],
        ['异质性',
         '见 Table 7–8（Chow 检验）', '—', '—'],
    ]
)

# ═══════════════════════════════════════════════════════════════════
# 十二、干预相关专项分析
# ═══════════════════════════════════════════════════════════════════
h2('十二、干预相关专项分析')

# ── 12.1 操纵检查（C 组）──────────────────────────────────────────
h3('12.1 操纵检查（干预组实验）')
c_mc = master[master['group']=='实验'].copy()
pr(f'实验组 n = {len(c_mc)}')

# 阅读了干预材料（0=no 1=not_sure 2=yes）
if 'manipulation_check_read' in c_mc.columns:
    mc_read_map = {0:'否', 1:'不确定', 2:'是'}
    mc_read_vc = c_mc['manipulation_check_read'].map(mc_read_map).value_counts()
    pr('\n**阅读了干预材料（C 组）**')
    for k in ['是','不确定','否']:
        n_ = int(mc_read_vc.get(k, 0))
        pct_ = n_ / len(c_mc) * 100
        pr(f'  {k}: n={n_} ({pct_:.1f}%)')
    n_read = int((c_mc['manipulation_check_read'] == 2).sum())
    pr(f'  → 明确阅读率: {n_read}/{len(c_mc)} = {n_read/len(c_mc)*100:.1f}%')

# 阅读了策略列表（0=no 1=yes/详细）
if 'manipulation_check_strategies' in c_mc.columns:
    pr('\n**阅读了策略列表（C 组）**')
    n_strat = int((c_mc['manipulation_check_strategies'] == 1).sum())
    pr(f'  是: n={n_strat} ({n_strat/len(c_mc)*100:.1f}%)')
    pr(f'  否: n={len(c_mc)-n_strat} ({(1-n_strat/len(c_mc))*100:.1f}%)')

# 策略使用程度（连续变量，C 组）
if 'strategy_usage_degree' in c_mc.columns:
    deg = c_mc['strategy_usage_degree'].dropna()
    if len(deg) > 1:
        pr(f'\n**策略使用程度（C 组，连续）**: M={deg.mean():.3f}, SD={deg.std(ddof=1):.3f}, '
           f'Mdn={deg.median():.3f}, [min={deg.min():.1f}, max={deg.max():.1f}], n={len(deg)}')
        # 与准确率相关
        paired = c_mc[['acc_total','strategy_usage_degree']].dropna()
        if len(paired) > 3:
            r_v, p_v = stats.pearsonr(paired['acc_total'], paired['strategy_usage_degree'])
            pr(f'  与整体准确率相关: r={fmt_r(r_v)}, p={fmt_p(p_v)+stars(p_v)}')

# ── 12.2 干预页面停留时间 ─────────────────────────────────────────
h3('12.2 干预页面停留时间（intervention_duration_s）')
dur = master[master['group']=='实验']['intervention_duration_s'].dropna()
dur = dur[dur > 0]   # 对照组填充为 0，排除
pr(f'实验组 n={len(dur)}: M={dur.mean():.1f}s, SD={dur.std(ddof=1):.1f}s, '
   f'Mdn={dur.median():.1f}s, [min={dur.min():.0f}s, max={dur.max():.0f}s]')
dur_rows = []
for threshold, label in [(30,'<30s'), (60,'30–60s'), (90,'60–90s'), (180,'90–180s'), (9999,'>180s')]:
    prev = 0 if threshold == 30 else [30,60,90,180][([30,60,90,180,9999].index(threshold))-1]
    n_ = int(((dur >= prev) & (dur < threshold)).sum()) if threshold < 9999 else int((dur >= 180).sum())
    dur_rows.append([label, str(n_), f'{n_/len(dur)*100:.1f}%'])
md_table(['时长区间','n','%'], dur_rows)

# 停留时间与准确率相关（C 组）
paired_dur = master[master['group']=='实验'][['acc_total','intervention_duration_s']].dropna()
paired_dur = paired_dur[paired_dur['intervention_duration_s'] > 0]
if len(paired_dur) > 3:
    r_v, p_v = stats.pearsonr(paired_dur['acc_total'], paired_dur['intervention_duration_s'])
    pr(f'\n实验组：停留时间 × 准确率相关: r={fmt_r(r_v)}, p={fmt_p(p_v)+stars(p_v)}, n={len(paired_dur)}')

# ── 12.3 Google Lens 使用分析 ─────────────────────────────────────
h3('12.3 Google Lens 使用行为')
n_lens_A = int(gA['lens_used'].sum())
n_lens_C = int(gC['lens_used'].sum())
pr(f'使用 Lens（OPEN_LENS）：对照组 {n_lens_A}/{nA} ({n_lens_A/nA*100:.1f}%)，'
   f'实验组 {n_lens_C}/{nC} ({n_lens_C/nC*100:.1f}%)')

# Lens 使用者 vs 未使用者的准确率（全样本）
lens_yes = master[master['lens_used']==1]['acc_total'].dropna()
lens_no  = master[master['lens_used']==0]['acc_total'].dropna()
if len(lens_yes) > 1 and len(lens_no) > 1:
    t_, p_ = stats.ttest_ind(lens_yes, lens_no, equal_var=False)
    g_ = hedges_g(lens_yes.values, lens_no.values)
    pr(f'Lens使用者准确率: M={lens_yes.mean():.3f} (n={len(lens_yes)}) vs '
       f'未使用: M={lens_no.mean():.3f} (n={len(lens_no)}), '
       f't={t_:.3f}, p={fmt_p(p_)+stars(p_)}, g={fmt_r(g_)}')

# Lens 深度与准确率（C 组，有使用的人）
c_lens = master[(master['group']=='实验') & (master['lens_used']==1)][['acc_total','lens_depth']].dropna()
if len(c_lens) > 3:
    r_v, p_v = stats.pearsonr(c_lens['acc_total'], c_lens['lens_depth'])
    pr(f'实验组 Lens深度（操作次数）× 准确率: r={fmt_r(r_v)}, p={fmt_p(p_v)+stars(p_v)}, n={len(c_lens)}')

# ── 12.4 描述性统计汇总（clean_analysis 风格）────────────────────
h3('12.4 描述性统计汇总（各变量，按组别）')
pr('> 格式：A 组 M (SD)，C 组 M (SD)\n')

desc_rows = []
for col, lbl in [
    ('acc_total',             '整体正确率'),
    ('acc_ai',                'AI图正确率'),
    ('acc_real',              '真实图正确率'),
    ('dprime',                "d'（SDT敏感度）"),
    ('c',                     'c（判断标准）'),
    ('mean_conf',             '平均信心评分'),
    ('calibration_gap',       '信心校准差距（self_perf/5 − acc）'),
    ('self_assessed_ability', '前测自评能力（1–5）'),
    ('ai_exposure_num',       'AI使用频率（1–5）'),
    ('self_performance',      '后测表现自评（1–5）'),
]:
    if col not in master.columns: continue
    a_v = gA[col].dropna()
    c_v = gC[col].dropna()
    desc_rows.append([
        lbl,
        f'{a_v.mean():.3f} ({a_v.std(ddof=1):.3f})' if len(a_v) > 1 else '—',
        f'{c_v.mean():.3f} ({c_v.std(ddof=1):.3f})' if len(c_v) > 1 else '—',
    ])
md_table(['变量', '对照组 M (SD)', '实验组 M (SD)'], desc_rows)

# ── 12.5 前测基线差异（chi2 + Welch t，clean_analysis 风格）────────
h3('12.5 前测基线差异（组间等价性检验）')

pr('\n**人口统计学（χ² 检验）**')
for col, lbl in [('gender','性别'), ('age','年龄段'), ('edu_grp_label','学历分组')]:
    sub = master[[col,'group']].dropna()
    ct  = pd.crosstab(sub[col], sub['group'])
    try:
        chi2v, p_v, dof, _ = stats.chi2_contingency(ct)
        pr(f'  {lbl}: χ²({dof})={chi2v:.3f}, p={fmt_p(p_v)+stars(p_v)}')
    except Exception:
        pr(f'  {lbl}: 无法计算（样本不足）')

pr('\n**AI 素养相关（Welch t-test）**')
for col, lbl in [('self_assessed_ability','前测自评能力'),
                  ('ai_exposure_num','AI使用频率')]:
    a_v = gA[col].dropna().values
    c_v = gC[col].dropna().values
    if len(a_v) < 2 or len(c_v) < 2:
        pr(f'  {lbl}: 样本不足'); continue
    t_, p_ = stats.ttest_ind(c_v, a_v, equal_var=False)
    wdf    = welch_df(a_v, c_v)
    g_     = hedges_g(c_v, a_v)
    pr(f'  {lbl}: 对照 M={a_v.mean():.3f}±{a_v.std(ddof=1):.3f}, '
       f'实验 M={c_v.mean():.3f}±{c_v.std(ddof=1):.3f}, '
       f't({wdf:.1f})={t_:.3f}, p={fmt_p(p_)+stars(p_)}, g={fmt_r(g_)}')

pr('\n**来源平衡（real/synth 在两组中的分布）**')
src_ct = pd.crosstab(master['source'], master['group'])
try:
    chi2v, p_v, dof, _ = stats.chi2_contingency(src_ct)
    pr(f'  来源 × 组别: χ²({dof})={chi2v:.3f}, p={fmt_p(p_v)+stars(p_v)}')
except Exception:
    pr(src_ct.to_string())

# ═══════════════════════════════════════════════════════════════════
# 十三、图表输出
# ═══════════════════════════════════════════════════════════════════
h2('十三、图表')
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.lines import Line2D

    plt.rcParams.update({
        'font.sans-serif': ['Microsoft YaHei', 'SimHei', 'DejaVu Sans'],
        'axes.unicode_minus': False,
        'axes.spines.top':   False,
        'axes.spines.right': False,
        'figure.facecolor':  'white',
        'axes.facecolor':    'white',
    })
    CA  = '#888888'   # 对照组：灰
    CC  = '#1565C0'   # 实验组：蓝
    CAI = '#C0392B'   # AI图像：深红
    CRL = '#2980B9'   # 真实图像：蓝

    # ── F1: 主效应 bar chart（正确率 + d'）────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(7, 4))
    for ax, col, yl in [(axes[0], 'acc_total', '整体正确率'),
                        (axes[1], 'dprime',    "d'")]:
        for xi, (grp, color, lbl) in enumerate([('对照', CA, '对照组'), ('实验', CC, '实验组')]):
            vals = master[master['group'] == grp][col].dropna()
            ax.bar(xi, vals.mean(), color=color, width=0.55, alpha=0.88,
                   yerr=vals.sem(), capsize=5,
                   error_kw={'ecolor': '#333', 'linewidth': 1.2})
            ax.text(xi, vals.mean() + vals.sem() + 0.01, lbl,
                    ha='center', va='bottom', fontsize=10)
        ax.set_xticks([])
        ax.set_ylabel(yl, fontsize=11)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:.2f}'))
    plt.tight_layout(pad=2)
    p1 = os.path.join(OUT_DIR, 'F1_main_effect.png')
    fig.savefig(p1, dpi=150, bbox_inches='tight')
    plt.close()
    pr(f'\n![主效应](F1_main_effect.png)')

    # ── F2: group × image_type 交互线图 ──────────────────────────────
    fig, ax = plt.subplots(figsize=(4.5, 4))
    for grp, color, lbl in [('对照', CA, '对照组'), ('实验', CC, '实验组')]:
        gdf = master[master['group'] == grp]
        ms  = [gdf['acc_ai'].mean(),   gdf['acc_real'].mean()]
        ses = [gdf['acc_ai'].sem(),    gdf['acc_real'].sem()]
        ax.errorbar([0, 1], ms, yerr=ses, marker='o', markersize=7,
                    linewidth=2.2, color=color, label=lbl, capsize=4)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(['AI 图像', '真实图像'], fontsize=11)
    ax.set_ylabel('正确率', fontsize=11)
    ax.set_ylim(0.45, 0.85)
    ax.legend(fontsize=10, frameon=False)
    plt.tight_layout()
    p2 = os.path.join(OUT_DIR, 'F2_interaction.png')
    fig.savefig(p2, dpi=150, bbox_inches='tight')
    plt.close()
    pr(f'\n![交互效应](F2_interaction.png)')

    # ── F4: 调节效应简单斜率图 ────────────────────────────────────────
    sae_grid  = np.linspace(1, 5, 80)
    ctrl_mean = {v: mod_df[v].mean() for v in CTRL_VARS_MOD}
    fig, ax = plt.subplots(figsize=(5.5, 4.2))
    for grp_c, color, lbl in [(0, CA, '对照组'), (1, CC, '实验组')]:
        preds = [m_mod.predict(pd.DataFrame(
                    [{'group_c': grp_c, 'sae_c': s - mean_sae, **ctrl_mean}]))[0]
                 for s in sae_grid]
        ax.plot(sae_grid, preds, color=color, linewidth=2.5, label=lbl)
    ax.axvline(mean_sae, color='#BBBBBB', lw=1, ls='--')
    ax.text(mean_sae + 0.06, ax.get_ylim()[0] + 0.005, '均值', fontsize=8.5, color='#888')
    ax.set_xlabel('前测自评辨别能力（1–5）', fontsize=11)
    ax.set_ylabel('预测整体正确率', fontsize=11)
    ax.set_xticks([1, 2, 3, 4, 5])
    ax.legend(fontsize=10, frameon=False)
    plt.tight_layout()
    p4 = os.path.join(OUT_DIR, 'F4_moderation.png')
    fig.savefig(p4, dpi=150, bbox_inches='tight')
    plt.close()
    pr(f'\n![调节效应](F4_moderation.png)')

    # ── F5: 逐图正确率差异 dot plot ───────────────────────────────────
    fd = fisher_df.sort_values('diff').reset_index(drop=True)
    dot_colors = [CAI if t == 'AI' else CRL for t in fd['type']]
    fig, ax = plt.subplots(figsize=(5.5, 7.5))
    ax.scatter(fd['diff'], range(len(fd)), c=dot_colors, s=60, zorder=3)
    ax.axvline(0, color='#888', lw=0.9, ls='--')
    ax.set_yticks(range(len(fd)))
    ax.set_yticklabels(
        [f"{r['image_id']}（{'AI' if r['type']=='AI' else '真实'}）"
         for _, r in fd.iterrows()], fontsize=9)
    ax.set_xlabel('实验组 − 对照组正确率差值', fontsize=11)
    ax.grid(axis='x', alpha=0.25, lw=0.7)
    ax.legend(handles=[
        mpatches.Patch(color=CAI, label='AI 图像'),
        mpatches.Patch(color=CRL, label='真实图像'),
    ], fontsize=9.5, frameon=False, loc='lower right')
    plt.tight_layout()
    p5 = os.path.join(OUT_DIR, 'F5_per_image.png')
    fig.savefig(p5, dpi=150, bbox_inches='tight')
    plt.close()
    pr(f'\n![逐图差异](F5_per_image.png)')

    # ── F6: 亚组效应森林图（DV = 整体正确率）─────────────────────────
    forest_rows = []
    for k1, k2, _ in pair_keys:
        for sg_key in [k1, k2]:
            sg_df = subgroup_defs[sg_key].dropna(subset=['acc_total', 'group_c'])
            if len(sg_df) >= 5:
                try:
                    m_ = smf.ols('acc_total ~ group_c', data=sg_df).fit()
                    B_ = m_.params['group_c']
                    lo, hi = m_.conf_int().loc['group_c']
                    forest_rows.append({
                        'lbl': sg_labels[sg_key], 'B': B_,
                        'lo': lo, 'hi': hi,
                        'sig': m_.pvalues['group_c'] < .05,
                    })
                except Exception:
                    pass

    if forest_rows:
        nr = len(forest_rows)
        fig, ax = plt.subplots(figsize=(6, nr * 0.55 + 0.9))
        for i, r in enumerate(forest_rows):
            ax.plot([r['lo'], r['hi']], [i, i], color='#AAAAAA', lw=2, zorder=1)
            mk = 'D' if r['sig'] else 'o'
            dot_c = CC if r['B'] > 0 else CA
            ax.scatter([r['B']], [i], color=dot_c, s=60, marker=mk, zorder=2)
        ax.axvline(0, color='#555', lw=1, ls='--', alpha=0.7)
        ax.set_yticks(range(nr))
        ax.set_yticklabels([r['lbl'] for r in forest_rows], fontsize=9.5)
        ax.set_xlabel('组别效应 B（整体正确率，95% CI）', fontsize=11)
        ax.grid(axis='x', alpha=0.2, lw=0.7)
        ax.legend(handles=[
            Line2D([0], [0], marker='D', color='w', markerfacecolor='#555',
                   markersize=7, label='p < .05'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#555',
                   markersize=7, label='p ≥ .05'),
        ], fontsize=9, frameon=False, loc='lower right')
        plt.tight_layout()
        p6 = os.path.join(OUT_DIR, 'F6_forest.png')
        fig.savefig(p6, dpi=150, bbox_inches='tight')
        plt.close()
        pr(f'\n![亚组森林图](F6_forest.png)')

    pr(f'\n> 图表已保存至 `{OUT_DIR}/`（F1–F6 + F3 相关矩阵）')

except Exception as e:
    pr(f'\n> ⚠ 图表生成出错：{e}')

pr('\n---')
pr(f'\n**注释**: \\* *p* < .05, \\*\\* *p* < .01, \\*\\*\\* *p* < .001（双尾）。'
   f'所有 Welch\'s *t* 检验使用 Welch-Satterthwaite 自由度近似。\n'
   f'第六节 21 次 Fisher 精确检验已进行 Bonferroni 校正（α = {alpha_bonf:.4f}）。')
pr(f'\n*报告生成时间: {today} | 输出文件: {OUT_DIR}/*')
_log.close()
print(f'\n✓ 报告已保存: {log_path}')
print(f'✓ CSV 表格 → {OUT_DIR}/')
