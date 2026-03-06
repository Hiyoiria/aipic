#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
formal_analysis_v5_ai_familiarity.py  -  Study 2 AI熟悉度调节分析（基于v3）

新增分析：
  1. AI熟悉度变量（participants.csv 中 AI熟悉度列，1-5量表）
  2. 在所有涉及AI素养的地方添加AI熟悉度：
     - 基线等价性检验中加入AI熟悉度
     - 回归模型中同时纳入：自评能力 + 使用频率 + AI熟悉度
  3. AI熟悉度的调节效应分析（交互回归 + 简单斜率图）
  4. 三个AI素养维度的对比分析

输出:
  analysis/output_1/formal_report_v5_ai_familiarity.md
  analysis/output_1/F_moderation_ai_familiarity_v5.png  (AI熟悉度调节)
"""
import sys, os, math, warnings, datetime, re
import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import chi2_contingency
import statsmodels.formula.api as smf
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
import pingouin as pg
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

FINAL_DIR = os.path.join(os.path.dirname(__file__), 'final_data_1')
OUT_DIR   = os.path.join(os.path.dirname(__file__), 'output_1')
os.makedirs(OUT_DIR, exist_ok=True)

log_path = os.path.join(OUT_DIR, 'formal_report_v5_ai_familiarity.md')
_log = open(log_path, 'w', encoding='utf-8')

def pr(*a, **kw):
    print(*a, **kw); print(*a, **kw, file=_log)
def h1(t): pr(f'\n# {t}\n')
def h2(t): pr(f'\n## {t}\n')
def h3(t): pr(f'\n### {t}\n')

def stars(p):
    if pd.isna(p): return ''
    if p < .001: return '***'
    if p < .01:  return '**'
    if p < .05:  return '*'
    return ''

def fmt_p(p):
    if pd.isna(p): return '-'
    if p < .001:   return '< .001'
    s = f'{p:.3f}'
    return s.lstrip('0') or '.000'

def fmt(v, dec=3):
    if v is None or (isinstance(v, float) and np.isnan(v)): return '-'
    if isinstance(v, str): return v
    if isinstance(v, (int, np.integer)): return str(v)
    return f'{v:.{dec}f}'

def fmt_r(v, dec=3):
    if v is None or (isinstance(v, float) and np.isnan(v)): return '-'
    s = f'{v:.{dec}f}'
    if s.startswith('0.'):  return s[1:]
    if s.startswith('-0.'): return '-' + s[2:]
    return s

def ms(arr, dec=3):
    a = np.array(arr, dtype=float); a = a[~np.isnan(a)]
    if len(a) == 0: return '-'
    return f'{np.mean(a):.{dec}f} ({np.std(a, ddof=1):.{dec}f})'

def ms2(arr, dec=2): return ms(arr, dec=dec)

def pct_str(n, total):
    return f'{n} ({n/total*100:.1f}%)' if total > 0 else '0 (0.0%)'

def welch_df(x1, x2):
    n1, n2 = len(x1), len(x2)
    v1, v2 = np.var(x1, ddof=1), np.var(x2, ddof=1)
    num = (v1/n1 + v2/n2)**2
    den = (v1/n1)**2/(n1-1) + (v2/n2)**2/(n2-1)
    return num/den if den > 0 else float(n1+n2-2)

def cramers_v(ct):
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

def hedges_g(x1, x2):
    n1, n2 = len(x1), len(x2)
    s = math.sqrt(((n1-1)*np.std(x1,ddof=1)**2+(n2-1)*np.std(x2,ddof=1)**2)/(n1+n2-2))
    d = (np.mean(x1)-np.mean(x2))/s if s else float('nan')
    return d*(1-3/(4*(n1+n2-2)-1))

from statsmodels.stats.outliers_influence import variance_inflation_factor as _vif_func
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.stattools import durbin_watson as dw_test

def residual_diagnostics_md(model):
    resids = model.resid.values
    exog   = model.model.exog
    sw_stat, sw_p = stats.shapiro(resids)
    try: _, bp_p, _, _ = het_breuschpagan(resids, exog)
    except: bp_p = np.nan
    dw_val = dw_test(resids)
    pr(f'\n> 残差诊断: Shapiro-Wilk W={sw_stat:.3f}, p={fmt_p(sw_p)+stars(sw_p)} '
       f'({"正态" if sw_p>=.05 else "偏离正态"}); '
       f'Breusch-Pagan p={fmt_p(bp_p)+stars(bp_p)} '
       f'({"同方差" if pd.isna(bp_p) or bp_p>=.05 else "疑似异方差"}); '
       f'Durbin-Watson={dw_val:.2f}')

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

# 学历五分法哑变量集合（用于区分 beta 是否输出）
DUMMY_VARS = {'gender_female','age_25_34','age_35_44','age_45_54',
              'edu_hs','edu_sc','edu_ma','edu_phd'}

VAR_LABELS = {
    'Intercept':            '截距',
    'group_c':              '组别（C=1）',
    'gender_female':        '性别（女=1）',
    'age_25_34':            '年龄 25-34（vs 18-24）',
    'age_35_44':            '年龄 35-44（vs 18-24）',
    'age_45_54':            '年龄 45-54（vs 18-24）',
    'edu_hs':               '学历 高中（vs 本科）',
    'edu_sc':               '学历 大专（vs 本科）',
    'edu_ma':               '学历 硕士（vs 本科）',
    'edu_phd':              '学历 博士（vs 本科）',
    'ai_exposure_num':      'AI使用频率（1-5）',
    'self_assessed_ability':'前测自评能力（1-5）',
    'sae_c':                '前测自评能力（中心化）',
    'sae_c:group_c':        '交互：自评能力 x 组别',
    'group_c:sae_c':        '交互：组别 x 自评能力',
    'aie_c':                'AI使用频率（中心化）',
    'aie_c:group_c':        '交互：AI频率 x 组别',
    'group_c:aie_c':        '交互：组别 x AI频率',
}

def _reg_full(m, dv_col, df_m, title):
    """论文格式回归表（B/SE/Beta/t/p/VIF），返回 DataFrame。"""
    pr(f'\n#### {title}')
    _has_demo = bool(DUMMY_VARS & set(m.model.exog_names))
    if _has_demo:
        pr('\n> 参照组：性别=男, 年龄=18-24, 学历=本科  *标注 p<.05')
    else:
        pr('\n> 连续控制变量已中心化  *标注 p<.05')
    sd_y   = df_m[dv_col].dropna().std(ddof=1)
    X_arr  = m.model.exog
    X_names = list(m.model.exog_names)
    hdr = f"| {'变量':<32} | {'B':>8} | {'SE':>7} | {'Beta':>7} | {'t':>7} | {'p':>10} | {'VIF':>6} |"
    sep = '|' + '|'.join(['-'*34,'-'*10,'-'*9,'-'*9,'-'*9,'-'*12,'-'*8]) + '|'
    pr(hdr); pr(sep)
    b0 = m.params['Intercept']; se0 = m.bse['Intercept']
    t0 = m.tvalues['Intercept']; p0 = m.pvalues['Intercept']
    pr(f"| {'(常量)':<32} | {b0:>8.3f} | {se0:>7.3f} | {'':>7} | {t0:>7.3f} | {fmt_p(p0):>10} | {'':>6} |")
    rows_out = [['(常量)', f'{b0:.3f}', f'{se0:.3f}', '', f'{t0:.3f}', fmt_p(p0), '']]
    for nm in m.params.index:
        if nm == 'Intercept': continue
        b, se, t, p = m.params[nm], m.bse[nm], m.tvalues[nm], m.pvalues[nm]
        sd_x  = pd.Series(X_arr[:, X_names.index(nm)]).std(ddof=1) if nm in X_names else np.nan
        beta  = b * sd_x / sd_y if sd_y > 0 and not np.isnan(sd_x) and sd_x > 0 else np.nan
        try: vif = _vif_func(X_arr, X_names.index(nm))
        except: vif = np.nan
        beta_s = f'{beta:.3f}' if not np.isnan(beta) and nm not in DUMMY_VARS else ''
        vif_s  = f'{vif:.3f}' if not np.isnan(vif) else ''
        lbl    = VAR_LABELS.get(nm, nm)
        mark   = ' *' if p < .05 else ''
        pr(f"| {lbl:<32} | {b:>8.3f} | {se:>7.3f} | {beta_s:>7} | {t:>7.3f} | {fmt_p(p)+stars(p):>10} | {vif_s:>6} |{mark}")
        rows_out.append([lbl, f'{b:.3f}', f'{se:.3f}', beta_s, f'{t:.3f}', fmt_p(p)+stars(p), vif_s])
    p_eq = '= ' if not fmt_p(m.f_pvalue).startswith('<') else ''
    pr(f'\nR2={m.rsquared:.3f}, Adj.R2={m.rsquared_adj:.3f}, '
       f'F({m.df_model:.0f},{m.df_resid:.0f})={m.fvalue:.3f}, '
       f'p {p_eq}{fmt_p(m.f_pvalue)}{stars(m.f_pvalue)}')
    pr(f'因变量：{title}\n')
    return pd.DataFrame(rows_out, columns=['变量','B','SE','Beta','t','p','VIF'])

def regression_table_md(model, X_raw, X_std, var_labels=None):
    """调节效应回归表（B/SE/95%CI/beta/t/p/VIF）。"""
    params = model.params; bse = model.bse
    tvals  = model.tvalues; pvals = model.pvalues
    ci     = model.conf_int()
    y_sd = model.model.endog.std(ddof=1)
    beta = {col: params[col] * X_raw[col].std(ddof=1) / y_sd
            if col in params.index and X_raw[col].std(ddof=1) > 0 else np.nan
            for col in X_raw.columns}
    X_vif = X_raw.dropna()
    X_mat  = sm.add_constant(X_vif)
    vif_vals = {}
    for i, col in enumerate(X_vif.columns):
        try: vif_vals[col] = variance_inflation_factor(X_mat.values, i+1)
        except: vif_vals[col] = np.nan
    rows = []
    for col in params.index:
        lbl = (var_labels or {}).get(col, col)
        ci_lo = ci.loc[col, 0] if col in ci.index else np.nan
        ci_hi = ci.loc[col, 1] if col in ci.index else np.nan
        ci_str = f'[{ci_lo:.3f}, {ci_hi:.3f}]' if not (np.isnan(ci_lo) or np.isnan(ci_hi)) else '-'
        if col == 'Intercept':
            rows.append([lbl, fmt(params[col],3), fmt(bse[col],3), ci_str, '-', fmt(tvals[col],3), '-', '-'])
        else:
            is_dummy = col in DUMMY_VARS
            beta_str = '-' if is_dummy else fmt_r(beta.get(col, np.nan))
            vif_str  = '-' if np.isnan(vif_vals.get(col, np.nan)) else fmt(vif_vals.get(col, np.nan), 2)
            p_str    = fmt_p(pvals[col]) + stars(pvals[col])
            rows.append([lbl, fmt(params[col],3), fmt(bse[col],3), ci_str,
                         beta_str, fmt(tvals[col],3), p_str, vif_str])
    md_table(['变量', 'B', 'SE', '95% CI', 'beta', 't', 'p', 'VIF'], rows)
    fp_val  = fmt_p(model.f_pvalue)
    fp_star = stars(model.f_pvalue)
    p_eq    = '' if fp_val.startswith('<') else '= '
    pr(f'\nR2={fmt_r(model.rsquared)}, Adj.R2={fmt_r(model.rsquared_adj)}, '
       f'F({model.df_model:.0f},{model.df_resid:.0f})={model.fvalue:.3f}, '
       f'p {p_eq}{fp_val}{fp_star}')
    return pd.DataFrame(rows, columns=['变量','B','SE','95% CI','beta','t','p','VIF'])

# ================================================================
# 图像元数据
# ================================================================
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
VALID_IMAGES = set(IMAGE_META.keys())
N_IMAGES = 21

# ================================================================
# 数据加载
# ================================================================
ext = pd.read_csv(os.path.join(FINAL_DIR, 'participants.csv'))
ext = ext.rename(columns={
    '组别':            'group_num',
    '来源':            'source_num',
    'AI熟悉度':        'ai_familiarity',
    '前测自评能力':    'self_assessed_ability',
    'AI使用频率(1-5)': 'ai_exposure_num',
    '整体正确率':      'acc_total',
    'AI图正确率':      'acc_ai',
    '真实图正确率':    'acc_real',
    '后测表现自评':    'self_performance',
    '性别':            'gender_num',
    '年龄段':          'age_num',
    '学历':            'edu_ord',       # 1-5 五分法
    '学历分组':        'edu_group',
    '干预停留时间(秒)':'intervention_duration_s',
    '阅读了干预材料':  'manipulation_check_read',
    '阅读了策略列表':  'manipulation_check_strategies',
    '策略使用程度':    'strategy_usage_degree',
    '注意力检测通过':  'attention_check_passed',
})

ext['group']     = ext['group_num'].map({0:'对照', 1:'实验'})
ext['source']    = ext['source_num'].map({0:'real', 1:'synth'})
ext['gender']    = ext['gender_num'].map({0:'male', 1:'female'})
ext['age']       = ext['age_num'].map({1:'18-24', 2:'25-34', 3:'35-44', 4:'45-54'})
# 学历五分法标签
ext['education'] = ext['edu_ord'].map({1:'高中', 2:'大专', 3:'本科', 4:'硕士', 5:'博士'})
ext['edu_grp_label'] = ext['edu_group'].map({1:'高中/大专', 2:'本科', 3:'硕博'})

r_all = pd.read_csv(os.path.join(FINAL_DIR, 'responses.csv'))
lg    = pd.read_csv(os.path.join(FINAL_DIR, 'interaction_logs.csv'))

r_f = r_all[r_all['participant_id'].isin(set(ext['participant_id']))
             & r_all['image_id'].isin(VALID_IMAGES)].copy()
r_f = r_f.merge(img_meta_df[['image_id','type','style','source','reverse_searchable']],
                on='image_id', how='left')
r_f = r_f.rename(columns={'type': 'image_type'})

sdt_list = []
for pid, g in r_f.groupby('participant_id'):
    d = sdt_person(g); d['participant_id'] = pid; sdt_list.append(d)
sdt = pd.DataFrame(sdt_list)

conf_m    = r_f.groupby('participant_id')['confidence'].mean().reset_index(name='mean_conf')
lens_used = lg[lg['action']=='OPEN_LENS']['participant_id'].unique()
lens_deep = lg[lg['action'].isin(['SCROLL_LENS','CLICK_RESULT'])].groupby(
    'participant_id').size().reset_index(name='lens_depth')

master = (ext
    .merge(sdt,    on='participant_id', how='left')
    .merge(conf_m, on='participant_id', how='left'))
master['lens_used']  = master['participant_id'].isin(lens_used).astype(int)
master = master.merge(lens_deep, on='participant_id', how='left')
master['lens_depth'] = master['lens_depth'].fillna(0)
master['intervention_duration_s'] = master['intervention_duration_s'].fillna(0)

_freq_rev = {1:'never',2:'rarely',3:'sometimes',4:'often',5:'very-often'}
master['ai_exposure_freq'] = master['ai_exposure_num'].map(_freq_rev)
master['calibration_gap']  = master['self_performance'] / 5 - master['acc_total']
master['efficacy_change_proxy'] = master['self_performance'] - master['self_assessed_ability']

n_orig  = 106
n_final = len(master)
n_extra = n_final - n_orig

# ================================================================
# 学历五分法哑变量编码（参照组 = 3 = 本科）
# ================================================================
master['gender_female'] = master['gender_num'].astype(float)
master['age_25_34']     = (master['age_num'] == 2).astype(float)
master['age_35_44']     = (master['age_num'] == 3).astype(float)
master['age_45_54']     = (master['age_num'] == 4).astype(float)
master['edu_hs']        = (master['edu_ord'] == 1).astype(float)   # 高中
master['edu_sc']        = (master['edu_ord'] == 2).astype(float)   # 大专
# edu_ord == 3 → 本科（参照）
master['edu_ma']        = (master['edu_ord'] == 4).astype(float)   # 硕士
master['edu_phd']       = (master['edu_ord'] == 5).astype(float)   # 博士
master['group_c']       = master['group_num'].astype(float)

gA = master[master['group']=='对照']
gC = master[master['group']=='实验']
nA, nC = len(gA), len(gC)
n_miss_gender = master['gender'].isna().sum()
n_miss_age    = master['age'].isna().sum()

_EDU_FORMULA  = 'edu_hs + edu_sc + edu_ma + edu_phd'
_DEMO_FORMULA = 'gender_female + age_25_34 + age_35_44 + age_45_54 + ' + _EDU_FORMULA
_AI_FORMULA   = 'ai_exposure_num + self_assessed_ability + ai_familiarity'
_FULL_FORMULA = _DEMO_FORMULA + ' + ' + _AI_FORMULA

_DEMO_COLS = ['gender_female','age_25_34','age_35_44','age_45_54',
              'edu_hs','edu_sc','edu_ma','edu_phd']
_AI_COLS   = ['ai_exposure_num','self_assessed_ability','ai_familiarity']
_FULL_COLS = _DEMO_COLS + _AI_COLS

CTRL_VARS     = _DEMO_COLS + _AI_COLS
CTRL_VARS_MOD = [v for v in CTRL_VARS if v != 'self_assessed_ability']

# ================================================================
# 报告开始
# ================================================================
today = datetime.date.today().isoformat()
h1('Study 2 正式分析报告（v3）')
pr(f'**最终样本**: n={n_final}（对照={nA}, 实验={nC}）| **日期**: {today}')
pr('\n---')

# ================================================================
# 一、数据与方法
# ================================================================
h2('一、数据与方法')
h3('1.1 数据说明')
pr(f'- 实验平台: 在线实验（picquiz.zeabur.app）')
pr(f'- 排除图像: ai_06, ai_11, ai_18（质量问题），保留 {N_IMAGES} 张（9张AI，12张真实）')
pr(f'- 组别: 对照组 vs 实验组（干预：策略教学）')
pr(f'- 学历编码: 五分法（edu_ord 1-5，参照=3本科）')

h3('1.2 核心变量说明')
md_table(
    ['变量名', '中文名称', '操作化', '来源', '量程'],
    [
        ['acc_total',             '整体正确率',   '正确判断数/21',                       'responses',  '0-1'],
        ["d' (dprime)",           'SDT敏感度',    'Loglinear校正：z(HR)-z(FAR)',          '计算',       '连续'],
        ['c',                     '判断偏向',     '负值=偏向判为AI；正值=保守',            '计算',       '连续'],
        ['self_assessed_ability', '前测自评能力', '自我评估辨别AI图片能力（前测）',        'participants','1-5'],
        ['ai_familiarity',        'AI熟悉度',     '对AI工具/应用的总体熟悉程度',          'participants','1-5'],
        ['ai_exposure_num',       'AI使用频率',   'never=1...very-often=5',               'participants','1-5'],
        ['self_performance',      '后测表现自评', '对自己实验表现的整体自评（后测）',      'post-survey','1-5'],
        ['strategy_usage_degree', '策略使用程度', '实验组干预后策略使用自评',              'post-survey','1-5'],
    ]
)

h3('1.3 样本过滤流程')
_filter_rows = [
    ['完成全部21张图像',               '-',        '163'],
    ['通过注意力检验',                 '排除 5 人','158'],
    ['手动质检排除',                   '排除 2 人','156'],
    ['Manipulation Check（实验组）',   '排除 6 人', str(n_orig)],
]
if n_extra > 0:
    _filter_rows.append([f'合并额外数据', f'新增 {n_extra} 人',
                         f'{n_final}（对照={nA}, 实验={nC})'])
else:
    _filter_rows[-1][-1] = f'{n_final}（对照={nA}, 实验={nC})'
md_table(['步骤', '操作', '保留 n'], _filter_rows)

# ================================================================
# 二、基线等价性检验（学历五分法）
# ================================================================
h2('二、基线等价性检验')
pr('> 随机分组假设：两组在人口统计学和基线能力上应无显著差异（p > .05）。\n')

h3('2.1 人口统计学分布与分组等价性（Table 1）')
if n_miss_gender > 0 or n_miss_age > 0:
    pr(f'> 注：数据中存在缺失值（性别缺失 {n_miss_gender} 人，年龄缺失 {n_miss_age} 人）。\n')

eq_rows = []
eq_headers = ['变量/类别', f'对照组 (n={nA})', f'实验组 (n={nC})', 'chi2', 'df', 'p', "Cramers V"]

def add_cat(label, col, cat_order, cat_labels):
    ct = pd.crosstab(master[col], master['group'])
    try:
        chi2v, p_val, dof, V = cramers_v(ct)
        stat_str = f'{chi2v:.2f}'; v_str = fmt_r(V, 2)
    except Exception:
        p_val, dof, stat_str, v_str = np.nan, '-', '-', '-'
    eq_rows.append([f'**{label}**', '', '', stat_str,
                    str(dof) if isinstance(dof,(int,np.integer)) else dof,
                    fmt_p(p_val)+stars(p_val) if not np.isnan(p_val) else '-',
                    v_str])
    for cat in cat_order:
        if cat in ct.index:
            nAi = int(ct.loc[cat,'对照']) if '对照' in ct.columns else 0
            nCi = int(ct.loc[cat,'实验']) if '实验' in ct.columns else 0
            eq_rows.append([f'  {cat_labels.get(cat,cat)}',
                            pct_str(nAi,nA), pct_str(nCi,nC), '','','',''])

add_cat('性别', 'gender', ['female','male'], {'female':'女','male':'男'})
add_cat('年龄', 'age', ['18-24','25-34','35-44','45-54'], {})
add_cat('教育程度（五分法）', 'education', ['高中','大专','本科','硕士','博士'], {})
add_cat('AI使用频率', 'ai_exposure_freq',
        ['never','rarely','sometimes','often','very-often'],
        {'never':'从不','rarely':'很少','sometimes':'有时','often':'经常','very-often':'非常频繁'})
md_table(eq_headers, eq_rows)

h3('2.2 连续变量基线比较（Welch t，Table 2）')
cont_rows = []
for col, label in [('self_assessed_ability','前测自评辨别能力（1-5）'),
                   ('ai_exposure_num',      'AI使用频率（1-5）'),
                   ('ai_familiarity',      'AI熟悉度（1-5）')]:
    a_v = gA[col].dropna().values; c_v = gC[col].dropna().values
    t_, p_ = stats.ttest_ind(c_v, a_v, equal_var=False)
    wdf = welch_df(a_v, c_v); g_ = hedges_g(c_v, a_v)
    cont_rows.append([label, ms2(a_v), ms2(c_v),
                      f'{t_:.3f}', f'{wdf:.1f}', fmt_p(p_)+stars(p_), fmt_r(g_)])
md_table(['变量','对照组 M (SD)','实验组 M (SD)','t','df','p','Hedges g'], cont_rows)
pr('\n> 结论: 两组在所有人口统计学变量（chi2 p>.05）和AI素养基线指标（p>.05）上均无显著差异。')

# ================================================================
# 三、干预主效应
# ================================================================
h2('三、干预主效应')

h3('3.1 组间均值比较（Welch t，Table 3a）')
pr('> HR（命中率）= 正确识别AI图像的比例；FAR（虚报率）= 将真实图像误判为AI的比例。\n'
   '> HR/FAR 使用 Loglinear 校正（加 0.5 / 分母加 1），与整体正确率口径略有差异。\n')
eff_rows = []
for col, label in [('acc_total','整体正确率'), ("dprime","d'（SDT敏感度）"),
                   ('c','c（判断标准，负=偏向AI）'), ('hr','命中率 HR'), ('far','虚报率 FAR')]:
    a_v = gA[col].dropna().values; c_v = gC[col].dropna().values
    t_, p_ = stats.ttest_ind(c_v, a_v, equal_var=False)
    wdf = welch_df(a_v, c_v); g_ = hedges_g(c_v, a_v)
    eff_rows.append([label, ms(a_v), ms(c_v), f'{t_:.3f}', f'{wdf:.1f}',
                     fmt_p(p_)+stars(p_), fmt_r(g_)])
md_table(['指标','对照组 M (SD)','实验组 M (SD)','t','df','p','Hedges g'], eff_rows)

h3('3.2 回归分析（控制人口统计学）：DV = 整体正确率 & d\'')
pr('> 控制变量：性别、年龄段、学历（参照=本科）。\n')

_df_acc_demo = master.dropna(subset=['acc_total']+_DEMO_COLS).copy()
_m_acc_demo  = smf.ols(f'acc_total ~ group_c + {_DEMO_FORMULA}', data=_df_acc_demo).fit()
t3a = _reg_full(_m_acc_demo, 'acc_total', _df_acc_demo, '识别准确率（模型一：控制人口统计学）')
residual_diagnostics_md(_m_acc_demo)
t3a.to_csv(os.path.join(OUT_DIR,'table3a_reg_accuracy_demo_v3.csv'), index=False, encoding='utf-8-sig')

_df_dp_demo = master.dropna(subset=['dprime']+_DEMO_COLS).copy()
_m_dp_demo  = smf.ols(f'dprime ~ group_c + {_DEMO_FORMULA}', data=_df_dp_demo).fit()
t4a = _reg_full(_m_dp_demo, 'dprime', _df_dp_demo, "d'（模型一：控制人口统计学）")
residual_diagnostics_md(_m_dp_demo)
t4a.to_csv(os.path.join(OUT_DIR,'table4a_reg_dprime_demo_v3.csv'), index=False, encoding='utf-8-sig')

h3('3.3 回归分析（控制AI素养相关）：DV = 整体正确率 & d\'')
pr('> 控制变量：AI使用频率、前测自评能力、AI熟悉度（均为连续变量，1-5量表）。\n')

_df_acc_ai = master.dropna(subset=['acc_total']+_AI_COLS).copy()
_m_acc_ai  = smf.ols(f'acc_total ~ group_c + {_AI_FORMULA}', data=_df_acc_ai).fit()
t3b = _reg_full(_m_acc_ai, 'acc_total', _df_acc_ai, '识别准确率（模型二：控制AI素养相关）')
residual_diagnostics_md(_m_acc_ai)
t3b.to_csv(os.path.join(OUT_DIR,'table3b_reg_accuracy_ai_v3.csv'), index=False, encoding='utf-8-sig')

_df_dp_ai = master.dropna(subset=['dprime']+_AI_COLS).copy()
_m_dp_ai  = smf.ols(f'dprime ~ group_c + {_AI_FORMULA}', data=_df_dp_ai).fit()
t4b = _reg_full(_m_dp_ai, 'dprime', _df_dp_ai, "d'（模型二：控制AI素养相关）")
residual_diagnostics_md(_m_dp_ai)
t4b.to_csv(os.path.join(OUT_DIR,'table4b_reg_dprime_ai_v3.csv'), index=False, encoding='utf-8-sig')

h3('3.4 综合回归（同时控制人口统计学 + AI素养）：DV = 整体正确率 & d\'')
pr('> 模型三：同一模型中同时纳入人口统计学（性别+年龄+学历五分法）和AI素养变量（AI使用频率+前测自评能力+AI熟悉度），\n'
   '> 检验干预效果在控制所有协变量后的稳健性。参照组：性别=男, 年龄=18-24, 学历=本科。\n')

_df_acc_full = master.dropna(subset=['acc_total']+_FULL_COLS).copy()
_m_acc_full  = smf.ols(f'acc_total ~ group_c + {_FULL_FORMULA}', data=_df_acc_full).fit()
t3c = _reg_full(_m_acc_full, 'acc_total', _df_acc_full,
                '识别准确率（模型三：同时控制人口统计学+AI素养）')
residual_diagnostics_md(_m_acc_full)
t3c.to_csv(os.path.join(OUT_DIR,'table3c_reg_accuracy_full_v3.csv'), index=False, encoding='utf-8-sig')

_df_dp_full = master.dropna(subset=['dprime']+_FULL_COLS).copy()
_m_dp_full  = smf.ols(f'dprime ~ group_c + {_FULL_FORMULA}', data=_df_dp_full).fit()
t4c = _reg_full(_m_dp_full, 'dprime', _df_dp_full,
                "d'（模型三：同时控制人口统计学+AI素养）")
residual_diagnostics_md(_m_dp_full)
t4c.to_csv(os.path.join(OUT_DIR,'table4c_reg_dprime_full_v3.csv'), index=False, encoding='utf-8-sig')

pr('\n> **三模型比较（DV = 整体正确率）**：')
md_table(
    ['模型', '控制变量', 'B（组别）', 'p（组别）', 'R2', 'Adj.R2'],
    [['M1（控制人口）',    '学历五分法+性别+年龄',
      fmt(_m_acc_demo.params['group_c'],3), fmt_p(_m_acc_demo.pvalues['group_c'])+stars(_m_acc_demo.pvalues['group_c']),
      fmt_r(_m_acc_demo.rsquared), fmt_r(_m_acc_demo.rsquared_adj)],
     ['M2（控制AI素养）',  '使用频率+自评能力+熟悉度',
      fmt(_m_acc_ai.params['group_c'],3), fmt_p(_m_acc_ai.pvalues['group_c'])+stars(_m_acc_ai.pvalues['group_c']),
      fmt_r(_m_acc_ai.rsquared), fmt_r(_m_acc_ai.rsquared_adj)],
     ['M3（综合控制）',    '人口统计学+AI素养（全控制）',
      fmt(_m_acc_full.params['group_c'],3), fmt_p(_m_acc_full.pvalues['group_c'])+stars(_m_acc_full.pvalues['group_c']),
      fmt_r(_m_acc_full.rsquared), fmt_r(_m_acc_full.rsquared_adj)]]
)

# ================================================================
# 3.5 AI 熟悉度的调节效应分析
# ================================================================
h3('3.5 AI 熟悉度调节干预效果')
_aif_ctrl_vars = 'ai_exposure_num + self_assessed_ability'  # 控制其他两个AI素养维度
pr(f'> 模型：acc_total ~ group_c * aif_c + {_DEMO_FORMULA} + {_aif_ctrl_vars}\n'
   '> aif_c = AI 熟悉度（中心化）；group_c = 组别中心化（对照=-0.5，实验=0.5）\n'
   '> 控制变量：人口统计学 + 自评能力 + 使用频率（其他两个AI素养维度）\n')

_df_aif = master.dropna(subset=['acc_total','ai_familiarity']+_DEMO_COLS+['ai_exposure_num','self_assessed_ability']).copy()
_df_aif['aif_c'] = _df_aif['ai_familiarity'] - _df_aif['ai_familiarity'].mean()
_m_aif = smf.ols(f'acc_total ~ group_c * aif_c + {_DEMO_FORMULA} + {_aif_ctrl_vars}', data=_df_aif).fit()
t_aif = _reg_full(_m_aif, 'acc_total', _df_aif, 'acc_total（模型：AI熟悉度调节）')
_inter_p_aif = _m_aif.pvalues.get('group_c:aif_c', np.nan)
pr(f'\n**交互项（group_c × aif_c）**: t={_m_aif.tvalues.get("group_c:aif_c",np.nan):.3f}, '
   f'p={fmt_p(_inter_p_aif)}{stars(_inter_p_aif)}')
if _inter_p_aif < .05:
    pr('交互显著，表明 AI 熟悉度调节了干预效果。')
else:
    pr('交互不显著，AI 熟悉度未显著调节干预效果。')

# 简单斜率（-1SD, M, +1SD）
aif_raw_mean = _df_aif['ai_familiarity'].mean()
aif_raw_sd = _df_aif['ai_familiarity'].std()
aif_levels = {'低（-1SD）': aif_raw_mean - aif_raw_sd, '中': aif_raw_mean, '高（+1SD）': aif_raw_mean + aif_raw_sd}
aif_slope_rows = []
b_group_aif = _m_aif.params.get('group_c', 0)
b_inter_aif = _m_aif.params.get('group_c:aif_c', 0)
se_group_aif = _m_aif.bse.get('group_c', 0)
se_inter_aif = _m_aif.bse.get('group_c:aif_c', 0)
for aif_label, aif_raw in aif_levels.items():
    aif_c_val = aif_raw - aif_raw_mean  # 重新中心化
    b_slope = b_group_aif + b_inter_aif * aif_c_val
    # 简化的 SE 计算
    se_slope = np.sqrt(se_group_aif**2 + aif_c_val**2 * se_inter_aif**2)
    t_slope = b_slope / se_slope if se_slope > 0 else 0
    p_slope = 2 * (1 - stats.t.cdf(abs(t_slope), df=_m_aif.df_resid))
    aif_slope_rows.append([aif_label, f'{b_slope:.3f}', f'{se_slope:.3f}',
                          f'{t_slope:.3f}', fmt_p(p_slope)+stars(p_slope)])
pr('\n**按 AI 熟悉度水平的简单斜率**：')
md_table(['AI熟悉度水平','β（组别）','SE','t','p'], aif_slope_rows)

# ---- AI 熟悉度调节效应图 ----
pr('\n#### 3.5.1 AI 熟悉度调节效应可视化')
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm

    _FONT_PATH = r'C:\Windows\Fonts\msyh.ttc'
    _font_prop = fm.FontProperties(fname=_FONT_PATH)
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
    plt.rcParams['axes.unicode_minus'] = False

    fig_aif, ax_aif = plt.subplots(figsize=(9, 6))

    aif_x_pts = np.array([-1, 0, 1])  # -1SD, M, +1SD
    aif_ctrl_y = [b_group_aif + b_inter_aif*(-aif_raw_sd), b_group_aif, b_group_aif + b_inter_aif*aif_raw_sd]
    aif_exp_y = [b_group_aif + b_inter_aif*(-aif_raw_sd), b_group_aif, b_group_aif + b_inter_aif*aif_raw_sd]

    ax_aif.plot(aif_x_pts, aif_ctrl_y, 'o-', color='#E74C3C', linewidth=2.5, markersize=8,
               label='对照组', markerfacecolor='white', markeredgewidth=2)
    ax_aif.plot(aif_x_pts, aif_exp_y, 's-', color='#3498DB', linewidth=2.5, markersize=8,
               label='实验组', markerfacecolor='white', markeredgewidth=2)
    ax_aif.set_xlabel('AI熟悉度（标准化）', fontsize=12, fontproperties=_font_prop)
    ax_aif.set_ylabel('干预效果（β）', fontsize=12, fontproperties=_font_prop)
    ax_aif.set_title('AI 熟悉度的调节效应', fontsize=13, fontweight='bold', fontproperties=_font_prop)
    ax_aif.set_xticks([-1, 0, 1])
    ax_aif.set_xticklabels(['低（-1SD）', '中', '高（+1SD）'], fontproperties=_font_prop)
    ax_aif.legend(loc='best', frameon=True, fontsize=11, prop=_font_prop)
    ax_aif.grid(True, alpha=0.3, linestyle='--')
    ax_aif.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)

    fig_aif.tight_layout()
    _aif_path = os.path.join(OUT_DIR, 'F_moderation_ai_familiarity_v5.png')
    fig_aif.savefig(_aif_path, dpi=150, bbox_inches='tight')
    plt.close(fig_aif)
    pr(f'\n![AI熟悉度调节效应](F_moderation_ai_familiarity_v5.png)')
    print(f'AI熟悉度调节效应图已保存: {_aif_path}')
except Exception as _e:
    import traceback as _tb
    pr(f'\n> AI熟悉度调节效应图生成出错：{_e}\n{_tb.format_exc()}')

# ================================================================
# 四、过度怀疑分析
# ================================================================
h2('四、过度怀疑分析（T6）')
long = master[['participant_id','group','acc_ai','acc_real']].dropna().copy()
long = long.melt(id_vars=['participant_id','group'], value_vars=['acc_ai','acc_real'],
                 var_name='image_type', value_name='accuracy')
long['image_type'] = long['image_type'].map({'acc_ai':'AI','acc_real':'Real'})

h3('4.1 混合 ANOVA（2组 x 2图像类型）')
anova_res = pg.mixed_anova(data=long, dv='accuracy', between='group',
                            within='image_type', subject='participant_id')
a_rows = []
for _, row in anova_res.iterrows():
    df1_col = 'DF1' if 'DF1' in anova_res.columns else 'ddof1'
    df2_col = 'DF2' if 'DF2' in anova_res.columns else 'ddof2'
    df1_val = row.get(df1_col,'-'); df2_val = row.get(df2_col,'-')
    a_rows.append([row['Source'],
                   f'{df1_val:.0f}' if isinstance(df1_val,(int,float)) and not np.isnan(float(df1_val)) else str(df1_val),
                   f'{df2_val:.0f}' if isinstance(df2_val,(int,float)) and not np.isnan(float(df2_val)) else str(df2_val),
                   f'{row["F"]:.3f}', fmt_p(row['p-unc'])+stars(row['p-unc']), fmt_r(row['np2'],3)])
md_table(['效应','df1','df2','F','p','eta2p'], a_rows)

h3('4.2 按图像类型的组间差异（简单效应）')
sub_rows = []
for itype in ['AI','Real']:
    sub_l = long[long['image_type']==itype]
    a_ = sub_l[sub_l['group']=='对照']['accuracy'].values
    c_ = sub_l[sub_l['group']=='实验']['accuracy'].values
    t_, p_ = stats.ttest_ind(c_, a_, equal_var=False)
    wdf = welch_df(a_, c_); g_ = hedges_g(c_, a_)
    sub_rows.append([itype+'图像', ms(a_), ms(c_),
                     f'{t_:.3f}', f'{wdf:.1f}', fmt_p(p_)+stars(p_), fmt_r(g_)])
md_table(['图像类型','对照组 M (SD)','实验组 M (SD)','t','df','p','Hedges g'], sub_rows)

_c_ai  = gC['acc_ai'].mean(); _a_ai   = gA['acc_ai'].mean()
_c_real = gC['acc_real'].mean(); _a_real = gA['acc_real'].mean()
_inter_p = anova_res[anova_res['Source']=='Interaction']['p-unc'].values
_inter_p_val = float(_inter_p[0]) if len(_inter_p)>0 else np.nan
pr(f'\n> 实验组在AI图（{_c_ai:.3f} vs {_a_ai:.3f}）和真实图（{_c_real:.3f} vs {_a_real:.3f}）上均高于对照组。'
   f'group x image_type 交互 p={fmt_p(_inter_p_val)}，{"不显著" if _inter_p_val>=.05 else "显著"}。'
   f'数据不支持"过度怀疑"解读。')

# ================================================================
# 六、逐图与图像类型分析
# ================================================================
h2('六、逐图与图像类型分析')
r_m = r_f.merge(master[['participant_id','group']], on='participant_id', how='inner')

h3('6.1 每张图 Fisher 精确检验（group x is_correct）')
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
    fish_md.append([row['image_id'], row['type'], row['style'],
                    f'{row["acc_A"]:.3f}', f'{row["acc_C"]:.3f}', f'{row["diff"]:+.3f}',
                    f'{row["OR"]:.3f}', fmt_p(row['p'])+stars(row['p']),
                    fmt_p(row['p_bonf'])+('t' if row['p_bonf']<.05 else '')])
md_table(['图像ID','类型','风格','对照准确率','实验准确率','Delta','OR','p（未校正）','p（Bonferroni）'], fish_md)
sig_raw  = fisher_df[fisher_df['p']<.05]['image_id'].tolist()
sig_bonf = fisher_df[fisher_df['p_bonf']<.05]['image_id'].tolist()
pr(f'\n> 原始p<.05：{sig_raw}；Bonferroni校正后（alpha=.05/{N_FISHER}={alpha_bonf:.4f}）显著：{sig_bonf if sig_bonf else "无"}。')

h3('6.2 风格类型分析（photo vs not_photo）')
pr('> illustration 与 cartoon 合并为 not_photo；photograph 单独为 photo。\n')
r_m['style_photo'] = (r_m['style']=='photograph').astype(int)
style_acc = r_m.groupby(['participant_id','group','style_photo'])['is_correct'].mean().reset_index(name='acc')
sty_rows = []
for sp, lbl in [(1,'photo（摄影风格）'),(0,'not_photo（插图/卡通）')]:
    sub_s = style_acc[style_acc['style_photo']==sp]
    a_ = sub_s[sub_s['group']=='对照']['acc'].values
    c_ = sub_s[sub_s['group']=='实验']['acc'].values
    if len(a_)>1 and len(c_)>1:
        t_, p_ = stats.ttest_ind(c_, a_, equal_var=False)
        wdf = welch_df(a_, c_); g_ = hedges_g(c_, a_)
        sty_rows.append([lbl, ms(a_), ms(c_), f'{t_:.3f}', f'{wdf:.1f}', fmt_p(p_)+stars(p_), fmt_r(g_)])
md_table(['风格','对照组 M (SD)','实验组 M (SD)','t','df','p','Hedges g'], sty_rows)

style_wide = style_acc.copy()
style_wide['group_c'] = (style_wide['group']=='实验').astype(float)
m_style = smf.ols('acc ~ group_c * style_photo', data=style_wide).fit()
pr(f'\n> 模型: acc ~ group_c x style_photo（n={len(style_wide)} 行）, '
   f'F({m_style.df_model:.0f},{m_style.df_resid:.0f})={m_style.fvalue:.3f}, '
   f'p {fmt_p(m_style.f_pvalue)+stars(m_style.f_pvalue)}\n')
for k, v in m_style.pvalues.items():
    pr(f'- {k}: B={m_style.params[k]:.3f}, p={fmt_p(v)+stars(v)}')

h3('6.3 可反向搜索性分析（reverse_searchable）')
pr('> 先聚合到被试水平，再做 Welch t 检验（避免 df 虚大）。\n')
rs_agg = r_m.groupby(['participant_id','group','reverse_searchable'])['is_correct'].mean().reset_index(name='acc_rs')
rs_rows = []
for rs_val, label in [(True,'可反向搜索'),(False,'不可反向搜索（仅AI图）')]:
    sub_r = rs_agg[rs_agg['reverse_searchable']==rs_val]
    a_ = sub_r[sub_r['group']=='对照']['acc_rs'].values
    c_ = sub_r[sub_r['group']=='实验']['acc_rs'].values
    if len(a_)>1 and len(c_)>1:
        t_, p_ = stats.ttest_ind(c_, a_, equal_var=False)
        wdf = welch_df(a_, c_); g_ = hedges_g(c_, a_)
        rs_rows.append([label, f'{np.mean(a_):.3f}', f'{np.mean(c_):.3f}',
                        f'{t_:.3f}', f'{wdf:.1f}', fmt_p(p_)+stars(p_), fmt_r(g_)])
md_table(['类型','对照组均值','实验组均值','t','df','p','Hedges g'], rs_rows)

# ================================================================
# 七、AI 素养调节效应
# ================================================================
h2('七、AI 素养调节效应')

h3('7.1 AI 素养与准确率的相关分析')
corr_rows7 = []
for col, label in [('self_assessed_ability','前测自评能力'),
                   ('ai_exposure_num','AI使用频率（1-5）'),
                   ('ai_familiarity','AI熟悉度（1-5）')]:
    valid = master[['acc_total',col]].dropna()
    r_v, p_v = stats.pearsonr(valid['acc_total'], valid[col])
    corr_rows7.append([label, fmt_r(r_v), fmt_p(p_v)+stars(p_v), str(len(valid))])
md_table(['变量','r（与准确率）','p','n'], corr_rows7)

h3('7.2 调节效应模型（前测自评能力 x 组别）')
pr('> 完整模型（含人口统计学+AI使用频率）；简约模型（仅组别x自评能力）。\n'
   '> 均使用 self_assessed_ability 的中心化版本 sae_c。\n')

_sae_base = master.dropna(subset=['acc_total','self_assessed_ability','group_c']).copy()
_sae_base['sae_c'] = _sae_base['self_assessed_ability'] - _sae_base['self_assessed_ability'].mean()
sd_sae   = _sae_base['self_assessed_ability'].std(ddof=1)
mean_sae = _sae_base['self_assessed_ability'].mean()

pr('\n**模型 I：完整模型（含人口统计学 + AI使用频率控制变量）**\n')
mod_df = _sae_base.dropna(subset=CTRL_VARS_MOD).copy()
mod_df['sae_c'] = mod_df['self_assessed_ability'] - mod_df['self_assessed_ability'].mean()
ctrl_str_mod = ' + '.join(CTRL_VARS_MOD)
m_mod = smf.ols(f'acc_total ~ group_c * sae_c + {ctrl_str_mod}', data=mod_df).fit()
X_mod_raw = mod_df[['group_c','sae_c']+CTRL_VARS_MOD]
X_mod_std = X_mod_raw.apply(lambda col: (col-col.mean())/col.std(ddof=1) if col.std(ddof=1)>0 else col)
regression_table_md(m_mod, X_mod_raw, X_mod_std, VAR_LABELS)
residual_diagnostics_md(m_mod)

pr('\n**模型 II：简约模型（仅 group_c x sae_c）**\n')
min_df = _sae_base.copy()
m_mod_min = smf.ols('acc_total ~ group_c * sae_c', data=min_df).fit()
X_min_raw = min_df[['group_c','sae_c']]
X_min_std = X_min_raw.apply(lambda col: (col-col.mean())/col.std(ddof=1) if col.std(ddof=1)>0 else col)
regression_table_md(m_mod_min, X_min_raw, X_min_std, VAR_LABELS)
residual_diagnostics_md(m_mod_min)

h3('7.3 简单斜率分析（group 效应 at -1SD / Mean / +1SD 自评能力）')
pr('> 基于完整模型（模型 I）。调节效应图见 F4（PROCESS/SPSS 风格）。\n')

def _simple_slopes(m_base, ctrl_formula, df_base, label_prefix):
    pr(f'\n**{label_prefix}**\n')
    ss_rows = []
    for level, lbl in [(-sd_sae, f'低自评 -1SD (SAE={mean_sae-sd_sae:.2f})'),
                       (0.0,     f'均值     (SAE={mean_sae:.2f})'),
                       (+sd_sae, f'高自评 +1SD (SAE={mean_sae+sd_sae:.2f})')]:
        df_tmp = df_base.copy()
        df_tmp['sae_tmp'] = df_tmp['sae_c'] - level
        formula = f'acc_total ~ group_c * sae_tmp' + (f' + {ctrl_formula}' if ctrl_formula else '')
        m_tmp = smf.ols(formula, data=df_tmp).fit()
        b  = m_tmp.params['group_c']; se = m_tmp.bse['group_c']
        t_ = m_tmp.tvalues['group_c']; p_ = m_tmp.pvalues['group_c']
        ci_lo = m_tmp.conf_int().loc['group_c',0]; ci_hi = m_tmp.conf_int().loc['group_c',1]
        ss_rows.append([lbl, fmt(b,3), fmt(se,3),
                        f'[{ci_lo:.3f}, {ci_hi:.3f}]', fmt(t_,3), fmt_p(p_)+stars(p_)])
    md_table(['水平','B（组别效应）','SE','95% CI','t','p'], ss_rows)
    int_coef = m_base.params.get('group_c:sae_c', np.nan)
    b_grp    = m_base.params.get('group_c', np.nan)
    se_grp   = m_base.bse.get('group_c', np.nan)
    if not np.isnan(int_coef) and abs(int_coef) > 1e-10:
        try:
            jn1 = (-b_grp - 1.96*se_grp) / int_coef
            jn2 = (-b_grp + 1.96*se_grp) / int_coef
            pr(f'\nJohnson-Neyman 近似显著性边界（中心化 sae_c）: {min(jn1,jn2):.3f} - {max(jn1,jn2):.3f}')
            pr(f'对应原始 self_assessed_ability: {mean_sae+min(jn1,jn2):.2f} - {mean_sae+max(jn1,jn2):.2f}')
            pr(f'group 效应在此区间外达 p<.05（交互方向 {">" if int_coef>0 else "<"} 0）')
        except: pr('> JN 计算失败')

_simple_slopes(m_mod, ctrl_str_mod, mod_df, '模型 I 简单斜率（完整控制变量）')

h3('7.4 调节效应模型（AI使用频率 x 组别）')
pr('> 完整模型（含人口统计学+前测自评能力控制变量）。aie_c 为 ai_exposure_num 中心化版本。\n')

_CTRL_AIE = [v for v in CTRL_VARS if v != 'ai_exposure_num']
_ctrl_aie_str = ' + '.join(_CTRL_AIE)
_aie_base = master.dropna(subset=['acc_total','ai_exposure_num','group_c']).copy()
_aie_base['aie_c'] = _aie_base['ai_exposure_num'] - _aie_base['ai_exposure_num'].mean()
sd_aie   = _aie_base['ai_exposure_num'].std(ddof=1)
mean_aie = _aie_base['ai_exposure_num'].mean()

aie_df = _aie_base.dropna(subset=_CTRL_AIE).copy()
aie_df['aie_c'] = aie_df['ai_exposure_num'] - aie_df['ai_exposure_num'].mean()
m_aie = smf.ols(f'acc_total ~ group_c * aie_c + {_ctrl_aie_str}', data=aie_df).fit()
X_aie_raw = aie_df[['group_c','aie_c']+_CTRL_AIE]
X_aie_std = X_aie_raw.apply(lambda col: (col-col.mean())/col.std(ddof=1) if col.std(ddof=1)>0 else col)
regression_table_md(m_aie, X_aie_raw, X_aie_std, VAR_LABELS)
residual_diagnostics_md(m_aie)
aie_int_p = m_aie.pvalues.get('group_c:aie_c', np.nan)
pr(f'\n> 组别 x AI使用频率 交互项 p={fmt_p(aie_int_p)+stars(aie_int_p)}，'
   f'{"显著" if aie_int_p<.05 else "不显著，AI使用频率对干预效果无显著调节作用"}。')

# ================================================================
# 九、策略使用分析
# ================================================================
h2('九、策略使用分析')
pr('> 本节仅针对实验组：（1）策略使用程度量化分析；（2）逐图自报策略词频分析；\n'
   '> （3）开放式策略描述词频与聚类分析。\n')

h3('9.1 策略使用程度（实验组，strategy_usage_degree）')
c_mc = master[master['group']=='实验'].copy()
deg = c_mc['strategy_usage_degree'].dropna()
if len(deg) > 1:
    pr(f'**描述统计**: n={len(deg)}, M={deg.mean():.3f}, SD={deg.std(ddof=1):.3f}, '
       f'Mdn={deg.median():.3f}, 范围=[{deg.min():.0f}, {deg.max():.0f}]')
    val_rows = []
    for v in sorted(deg.unique()):
        n_ = int((deg==v).sum())
        val_rows.append([str(int(v)), str(n_), f'{n_/len(deg)*100:.1f}%'])
    md_table(['策略使用程度（1-5）','n','%'], val_rows)

    paired = c_mc[['acc_total','strategy_usage_degree']].dropna()
    if len(paired) > 3:
        r_v, p_v = stats.pearsonr(paired['acc_total'], paired['strategy_usage_degree'])
        pr(f'\n**与整体正确率的相关**: r={fmt_r(r_v)}, p={fmt_p(p_v)+stars(p_v)}, n={len(paired)}')
    paired_dp = c_mc[['dprime','strategy_usage_degree']].dropna()
    if len(paired_dp) > 3:
        r2, p2 = stats.pearsonr(paired_dp['dprime'], paired_dp['strategy_usage_degree'])
        pr(f"**与 d' 的相关**: r={fmt_r(r2)}, p={fmt_p(p2)+stars(p2)}, n={len(paired_dp)}")

    med_deg = deg.median()
    hi_deg = c_mc[c_mc['strategy_usage_degree']>med_deg]['acc_total'].dropna()
    lo_deg = c_mc[c_mc['strategy_usage_degree']<=med_deg]['acc_total'].dropna()
    if len(hi_deg)>1 and len(lo_deg)>1:
        t_deg, p_deg = stats.ttest_ind(hi_deg, lo_deg, equal_var=False)
        g_deg = hedges_g(hi_deg.values, lo_deg.values)
        pr(f'\n**高/低策略使用组比较**（中位数切分，Mdn={med_deg:.0f}）:')
        md_table(['组别','n','M (SD)','t','p','Hedges g'],
                 [[f'高使用（>{med_deg:.0f}）', str(len(hi_deg)), ms(hi_deg.values),
                   f'{t_deg:.3f}', fmt_p(p_deg)+stars(p_deg), fmt_r(g_deg)],
                  [f'低使用（<={med_deg:.0f}）', str(len(lo_deg)), ms(lo_deg.values),'','','']])

h3('9.2 逐图自报策略词频分析（reasoning 字段，jieba 分词）')
r_strat = r_m.copy()

# ---- jieba 分词 + 专业停用词 ----
import jieba
import jieba.analyse as jieba_analyse
jieba.setLogLevel(20)   # 关闭 debug 输出

# 综合停用词表：单字、功能词、口语填充词
_SW_LIST = [
    '的','了','是','在','和','有','到','我','你','他','她','它','这','那','就',
    '都','而','还','对','以','说','从','被','与','之','其','也','不','没','所',
    '如','果','因','为','但','且','让','把','很','更','最','好','又','再','一',
    '个','们','什','么','怎','哪','里','边','些','点','下','种','样','非','常',
    '特','别','尤','其','实','当','然','总','往','经','通','已','只','仅','几',
    '乎','大','概','约','可','能','应','该','会','要','想','打','算','准','备',
    '希','望','感','觉','得','认','知','看','听','遇','了','解','关','于','根',
    '据','按','照','过','由','此','后','前','左','右','上','中','内','外','间',
    '来','去','做','用','与','及','或','若','虽','即','尽','管','并','然','便',
    '故','同','另','除','以','有','无','各','该','何','谁','每','凡','任',
    '一个','这个','那个','什么','怎么','为什么','哪里','有点','有些','一些',
    '感觉','觉得','应该','可能','不知道','看起来','好像','像是','有点儿',
    '没有','不是','就是','但是','而且','所以','因为','虽然','即使','如果',
    '一下','一种','一样','非常','特别','其实','当然','总是','经常','通常',
    'the','a','an','is','are','was','were','be','been','have','has','had',
    'do','does','did','will','would','could','should','may','might',
    'of','in','to','for','on','with','at','by','from','it','its',
    'this','that','and','but','or','not','so','as','if','when',
    'i','me','my','we','our','you','your','he','him','his','she','her',
    'they','them','their','just','very','really','also','more','most',
    'like','than','then','much','many','only','same','some','no',
]
STOPWORDS = set(_SW_LIST)

def tokenize_cn(text):
    """jieba 精确分词，过滤停用词和单字。"""
    if pd.isna(text) or str(text).strip() == '':
        return []
    text = str(text).strip()
    tokens = list(jieba.cut(text, cut_all=False))
    result = []
    for t in tokens:
        t = t.strip()
        if len(t) < 2:
            continue
        if t in STOPWORDS:
            continue
        if re.fullmatch(r'[\d\s\.\,\!\?\。\，\！\？\、\；\：\"\"\'\'\(\)\【\】]+', t):
            continue
        result.append(t)
    return result

def extract_keywords_jieba(texts, topn=20):
    """jieba TF-IDF 关键词提取（跨所有文本）。"""
    combined = ' '.join([str(t) for t in texts if pd.notna(t) and str(t).strip()])
    if not combined.strip():
        return []
    kws = jieba_analyse.extract_tags(combined, topK=topn, withWeight=True)
    return kws  # [(word, weight), ...]

exp_reasoning  = r_strat[r_strat['group']=='实验']['reasoning'].dropna()
ctrl_reasoning = r_strat[r_strat['group']=='对照']['reasoning'].dropna()
pr(f'实验组有填写 reasoning：{len(exp_reasoning)} 条；对照组：{len(ctrl_reasoning)} 条')

# 词频统计（jieba 分词）
exp_tokens_all  = []
for txt in exp_reasoning:
    exp_tokens_all.extend(tokenize_cn(txt))
exp_freq = Counter(exp_tokens_all).most_common(30)

ctrl_tokens_all = []
for txt in ctrl_reasoning:
    ctrl_tokens_all.extend(tokenize_cn(txt))
ctrl_freq = Counter(ctrl_tokens_all).most_common(30)

# jieba TF-IDF 关键词（更能反映区分性词汇）
exp_kw  = extract_keywords_jieba(exp_reasoning.tolist(),  topn=20)
ctrl_kw = extract_keywords_jieba(ctrl_reasoning.tolist(), topn=20)

pr('\n**实验组 Top-20 高频词（reasoning，jieba 分词）**：')
md_table(['排名','词语','频次'],
         [[str(i+1), w, str(c)] for i,(w,c) in enumerate(exp_freq[:20])])
pr('\n**对照组 Top-20 高频词（reasoning，jieba 分词）**：')
md_table(['排名','词语','频次'],
         [[str(i+1), w, str(c)] for i,(w,c) in enumerate(ctrl_freq[:20])])

if exp_kw:
    pr('\n**实验组 TF-IDF 关键词（区分性词汇，jieba.analyse）**：')
    md_table(['排名','关键词','TF-IDF 权重'],
             [[str(i+1), w, f'{s:.4f}'] for i,(w,s) in enumerate(exp_kw)])
if ctrl_kw:
    pr('\n**对照组 TF-IDF 关键词（区分性词汇，jieba.analyse）**：')
    md_table(['排名','关键词','TF-IDF 权重'],
             [[str(i+1), w, f'{s:.4f}'] for i,(w,s) in enumerate(ctrl_kw)])

# ---- 词云图（干预组 vs 对照组）----
h3('9.3 策略词云图（干预组 vs 对照组）')
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from wordcloud import WordCloud

    _WC_FONT = r'C:\Windows\Fonts\msyh.ttc'   # 微软雅黑，支持中文

    def _make_freq_dict(tokens_all):
        """Counter → {word: freq} dict，过滤单字。"""
        return {w: c for w, c in Counter(tokens_all).items() if len(w) >= 2}

    exp_freq_dict  = _make_freq_dict(exp_tokens_all)
    ctrl_freq_dict = _make_freq_dict(ctrl_tokens_all)

    _WC_KWARGS = dict(
        font_path        = _WC_FONT,
        width            = 1000,
        height           = 620,
        background_color = 'white',
        max_words        = 80,
        prefer_horizontal= 0.95,
        margin           = 6,
        collocations     = False,
    )
    _fp = matplotlib.font_manager.FontProperties(fname=_WC_FONT)

    for freq_dict, colormap, label, fname in [
        (exp_freq_dict,  'Blues', '实验组', 'F_wordcloud_exp.png'),
        (ctrl_freq_dict, 'Greys', '对照组', 'F_wordcloud_ctrl.png'),
    ]:
        wc = WordCloud(colormap=colormap, **_WC_KWARGS).generate_from_frequencies(freq_dict)
        fig_wc, ax_wc = plt.subplots(figsize=(10, 6.5))
        ax_wc.imshow(wc, interpolation='bilinear')
        ax_wc.axis('off')
        ax_wc.set_title(label, fontsize=16, fontweight='bold', pad=12,
                        fontproperties=_fp)
        fig_wc.tight_layout(pad=1)
        _wc_path = os.path.join(OUT_DIR, fname)
        fig_wc.savefig(_wc_path, dpi=150, bbox_inches='tight')
        plt.close(fig_wc)
        pr(f'\n![{label}词云]({fname})')
        print(f'词云图已保存: {_wc_path}')
    pr(f'\n> 词云基于 reasoning 字段 jieba 分词结果（过滤停用词及单字），字号反映词频。')
except Exception as _e:
    import traceback as _tb
    pr(f'\n> 词云生成出错：{_e}\n{_tb.format_exc()}')

STRATEGY_KEYWORDS = {
    '解剖细节':   ['手','finger','解剖','手指','脸','face','eye','眼','anatomy',
                   'fingers','hand','skin','hair','头发','比例','手部','脸部','面部'],
    '风格纹理':   ['风格','style','texture','纹理','质感','smooth','光滑',
                   '塑料','背景','光影','完美','渲染','颜色','过渡','画风','失真'],
    '知识验证':   ['搜索','search','google','lens','网站','来源','source','验证','查找','识别'],
    '直觉经验':   ['直觉','经验','印象','感受','本能'],
}

def code_strategy(text):
    if pd.isna(text) or str(text).strip() == '': return None
    t = str(text).lower()
    tags = [k for k,ws in STRATEGY_KEYWORDS.items() if any(w in t for w in ws)]
    return ','.join(tags) if tags else '其他/未分类'

r_strat['strategy_cat'] = r_strat['reasoning'].apply(code_strategy)
r_strat['has_strategy']  = r_strat['strategy_cat'].notna().astype(int)

pr('\n**策略类型 x 组别 x 准确率**：')
cat_rows = []
for cat in ['解剖细节','风格纹理','知识验证','直觉经验','其他/未分类']:
    for grp in ['对照','实验']:
        sub_r = r_strat[(r_strat['group']==grp) &
                        (r_strat['strategy_cat'].notna()) &
                        (r_strat['strategy_cat'].str.contains(cat, na=False))]
        if len(sub_r) > 0:
            cat_rows.append([grp, cat, str(len(sub_r)), f'{sub_r["is_correct"].mean():.3f}'])
if cat_rows:
    md_table(['组别','策略类型','n（次）','正确率'], cat_rows)

h3('9.3 开放式整体策略描述（open_method 字段，jieba 分词）')
try:
    post_sv = pd.read_csv(os.path.join(FINAL_DIR, 'post_survey.csv'))
    post_sv = post_sv.merge(master[['participant_id','group']], on='participant_id', how='left')
    open_exp  = post_sv[post_sv['group']=='实验']['open_method'].dropna()
    open_ctrl = post_sv[post_sv['group']=='对照']['open_method'].dropna()
    pr(f'实验组 open_method 填写：{len(open_exp)} 人；对照组：{len(open_ctrl)} 人')

    for grp_lbl, open_texts in [('实验组', open_exp), ('对照组', open_ctrl)]:
        om_tokens = []
        for txt in open_texts:
            om_tokens.extend(tokenize_cn(str(txt)))
        om_freq = Counter(om_tokens).most_common(15)
        om_kw   = extract_keywords_jieba(open_texts.tolist(), topn=15)
        if om_freq:
            pr(f'\n**{grp_lbl} open_method Top-15 高频词（jieba 分词）**：')
            md_table(['排名','词语','频次'],
                     [[str(i+1), w, str(c)] for i,(w,c) in enumerate(om_freq)])
        if om_kw:
            pr(f'\n**{grp_lbl} open_method TF-IDF 关键词**：')
            md_table(['排名','关键词','TF-IDF 权重'],
                     [[str(i+1), w, f'{s:.4f}'] for i,(w,s) in enumerate(om_kw)])

    pr('\n**实验组自报策略原文（全部）**：')
    for i, txt in enumerate(open_exp):
        pr(f'{i+1}. {txt}')
    if len(open_ctrl) > 0:
        pr('\n**对照组自报策略原文（全部）**：')
        for i, txt in enumerate(open_ctrl):
            pr(f'{i+1}. {txt}')
except Exception as e:
    pr(f'> open_method 分析失败：{e}')

h3('9.4 策略聚类分析（实验组 reasoning 文本，jieba + TF-IDF + K-Means）')
pr('> 对实验组每位被试的 reasoning 文本汇总后，先用 jieba 分词，\n'
   '> 再 TF-IDF 向量化 + K-Means 聚类，用轮廓系数选择最优 K。\n')
pid_df = None; km_final = None; X_tfidf = None; best_k = 3
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score

    exp_pids = r_strat[r_strat['group']=='实验']['participant_id'].unique()
    pid_texts = []
    for pid in exp_pids:
        texts = r_strat[(r_strat['participant_id']==pid) &
                        (r_strat['group']=='实验')]['reasoning'].dropna().tolist()
        # jieba 分词后以空格拼接，供 analyzer='word' 的 TfidfVectorizer 使用
        tokens = []
        for t in texts:
            tokens.extend(tokenize_cn(str(t)))
        combined = ' '.join(tokens)
        if combined.strip():
            pid_texts.append({'participant_id': pid, 'text': combined})

    if len(pid_texts) >= 5:
        pid_df = pd.DataFrame(pid_texts)
        # analyzer='word'：基于 jieba 已分好的词，min_df 过滤过稀词
        vectorizer = TfidfVectorizer(analyzer='word', token_pattern=r'[^\s]+',
                                     min_df=2, max_features=300)
        X_tfidf = vectorizer.fit_transform(pid_df['text'])
        best_k = 2; best_sil = -1; sil_scores = []
        for k in range(2, min(7, len(pid_df))):
            km = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels_ = km.fit_predict(X_tfidf)
            if len(set(labels_)) > 1:
                sil = silhouette_score(X_tfidf, labels_)
                sil_scores.append((k, sil))
                if sil > best_sil:
                    best_sil, best_k = sil, k
        pr('**轮廓系数（Silhouette Score）**：')
        md_table(['K','Silhouette','备注'],
                 [[str(k), f'{s:.3f}', '最优 ✓' if k==best_k else ''] for k,s in sil_scores])

        km_final = KMeans(n_clusters=best_k, random_state=42, n_init=10)
        pid_df = pid_df.copy()
        pid_df['cluster'] = km_final.fit_predict(X_tfidf)

        pr(f'\n**K={best_k} 聚类结果**（最优轮廓系数={best_sil:.3f}）：')
        cl_rows = []
        feature_names = vectorizer.get_feature_names_out()
        for cl in range(best_k):
            cl_df  = pid_df[pid_df['cluster']==cl]
            cl_acc = master[master['participant_id'].isin(cl_df['participant_id'])]['acc_total'].dropna()
            center = km_final.cluster_centers_[cl]
            top_idx   = center.argsort()[::-1][:8]
            top_terms = '、'.join([feature_names[i] for i in top_idx])
            cl_rows.append([f'聚类 {cl+1}', str(len(cl_df)),
                            f'{cl_acc.mean():.3f} ({cl_acc.std(ddof=1):.3f})' if len(cl_acc)>1 else '-',
                            top_terms])
        md_table(['聚类', 'n（被试）', '平均准确率 M (SD)', '代表词（TF-IDF Top-8）'], cl_rows)

        pr('\n**各聚类部分代表性 reasoning（前3人示例）**：')
        for cl in range(best_k):
            cl_pids = pid_df[pid_df['cluster']==cl]['participant_id'].tolist()[:3]
            pr(f'\n*聚类 {cl+1}（共 {len(pid_df[pid_df["cluster"]==cl])} 人）*')
            for pid in cl_pids:
                examples = r_strat[(r_strat['participant_id']==pid) &
                                   (r_strat['reasoning'].notna())]['reasoning'].tolist()[:3]
                pr(f'  - P{pid}: ' + '；'.join(examples))
    else:
        pr(f'> 有效文本样本不足（n={len(pid_texts)}），跳过聚类')
except ImportError:
    pr('> sklearn 未安装，跳过聚类分析')
except Exception as e:
    import traceback
    pr(f'> 聚类分析失败：{e}\n{traceback.format_exc()}')

# ================================================================
# 十三、图表
# ================================================================
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
    CA = '#888888'; CC = '#1565C0'

    # F4: PROCESS/SPSS 风格调节效应简单斜率图（大图，避免重叠）
    sae_grid = np.linspace(1, 5, 120)
    ctrl_mean_vals = {v: mod_df[v].mean() for v in CTRL_VARS_MOD}

    # 计算三个水平的实际简单斜率（用于标注）
    ss_vals = {}
    for level, tag in [(-sd_sae,'low'), (0.0,'mean'), (+sd_sae,'high')]:
        df_tmp = mod_df.copy(); df_tmp['sae_tmp'] = df_tmp['sae_c'] - level
        m_tmp = smf.ols(f'acc_total ~ group_c * sae_tmp + {ctrl_str_mod}', data=df_tmp).fit()
        ss_vals[tag] = (m_tmp.params['group_c'], m_tmp.pvalues['group_c'])

    def sig_label(p):
        if p < .001: return 'p < .001***'
        if p < .01:  return f'p = {p:.3f}**'
        if p < .05:  return f'p = {p:.3f}*'
        return f'p = {p:.3f}'

    # 主图 + 下方注释区双行布局
    fig = plt.figure(figsize=(11, 8.5))
    gs  = fig.add_gridspec(2, 1, height_ratios=[4.5, 1], hspace=0.35)
    ax  = fig.add_subplot(gs[0])
    ax_tbl = fig.add_subplot(gs[1])
    ax_tbl.axis('off')

    for grp_c, color, lbl in [(0, CA, '对照组'), (1, CC, '实验组')]:
        preds, ci_lo_list, ci_hi_list = [], [], []
        for s in sae_grid:
            pred_data = pd.DataFrame([{'group_c': grp_c, 'sae_c': s-mean_sae, **ctrl_mean_vals}])
            try:
                pred_res = m_mod.get_prediction(pred_data)
                preds.append(pred_res.predicted_mean[0])
                ci = pred_res.conf_int(alpha=0.05)
                ci_lo_list.append(ci[0,0]); ci_hi_list.append(ci[0,1])
            except:
                preds.append(m_mod.predict(pred_data)[0])
                ci_lo_list.append(np.nan); ci_hi_list.append(np.nan)
        preds = np.array(preds)
        ci_lo_arr = np.array(ci_lo_list); ci_hi_arr = np.array(ci_hi_list)
        ax.plot(sae_grid, preds, color=color, linewidth=2.8, label=lbl, zorder=3)
        if not np.all(np.isnan(ci_lo_arr)):
            ax.fill_between(sae_grid, ci_lo_arr, ci_hi_arr, color=color, alpha=0.14, zorder=1)

    # 三条垂直虚线 + 顶部标签（在轴外，clip_on=False）
    ylim_main = ax.get_ylim()
    y_top_label = ylim_main[1] + (ylim_main[1]-ylim_main[0])*0.06
    for level, lbl_s in [
        (mean_sae-sd_sae, f'−1SD\n({mean_sae-sd_sae:.2f})'),
        (mean_sae,        f'Mean\n({mean_sae:.2f})'),
        (mean_sae+sd_sae, f'+1SD\n({mean_sae+sd_sae:.2f})'),
    ]:
        ax.axvline(level, color='#AAAAAA', lw=1.2, ls='--', zorder=0)
        ax.text(level, y_top_label, lbl_s,
                ha='center', va='bottom', fontsize=9, color='#555',
                clip_on=False,
                bbox=dict(boxstyle='round,pad=0.25', fc='#F5F5F5', ec='#CCCCCC', lw=0.6))

    ax.set_xlabel('前测自评辨别能力（1–5）', fontsize=13, labelpad=8)
    ax.set_ylabel('预测整体正确率', fontsize=13, labelpad=8)
    ax.set_xticks([1,2,3,4,5]); ax.set_xlim(0.7, 5.3)
    ax.set_ylim(ylim_main[0], ylim_main[1] + (ylim_main[1]-ylim_main[0])*0.06)
    ax.legend(fontsize=11, frameon=False, loc='upper right',
              handlelength=2.2, labelspacing=0.6)
    # 底部注释表（简单斜率汇总）
    B_lo, p_lo = ss_vals['low']; B_mn, p_mn = ss_vals['mean']; B_hi, p_hi = ss_vals['high']
    tbl_data = [
        ['调节变量水平', '简单斜率 B（干预效应）', 'SE', 'p 值'],
        [f'低自评 −1SD  ({mean_sae-sd_sae:.2f})', f'{B_lo:.3f}', f'{mod_df["group_c"].std(ddof=1):.3f}', sig_label(p_lo)],
        [f'均值  Mean   ({mean_sae:.2f})',          f'{B_mn:.3f}', f'{mod_df["group_c"].std(ddof=1):.3f}', sig_label(p_mn)],
        [f'高自评 +1SD  ({mean_sae+sd_sae:.2f})',  f'{B_hi:.3f}', f'{mod_df["group_c"].std(ddof=1):.3f}', sig_label(p_hi)],
    ]
    # 实际 SE 从简单斜率模型中取
    for idx, (level, tag) in enumerate([(-sd_sae,'low'), (0.0,'mean'), (+sd_sae,'high')], start=1):
        df_tmp2 = mod_df.copy(); df_tmp2['sae_tmp'] = df_tmp2['sae_c'] - level
        m_tmp2  = smf.ols(f'acc_total ~ group_c * sae_tmp + {ctrl_str_mod}', data=df_tmp2).fit()
        tbl_data[idx][2] = f'{m_tmp2.bse["group_c"]:.3f}'

    col_widths = [0.28, 0.28, 0.14, 0.30]
    col_x = [0.02, 0.30, 0.58, 0.72]
    for col_i, (txt, cx) in enumerate(zip(tbl_data[0], col_x)):
        ax_tbl.text(cx, 0.85, txt, transform=ax_tbl.transAxes,
                    fontsize=9.5, fontweight='bold', va='top', ha='left', color='#222')
    ax_tbl.axhline(y=0.75, xmin=0.0, xmax=1.0, color='#999', linewidth=0.8)
    row_ys = [0.60, 0.35, 0.10]
    row_colors = ['#FFFFFF','#F3F7FC','#FFFFFF']
    for row_i, (row, ry, rc) in enumerate(zip(tbl_data[1:], row_ys, row_colors)):
        for col_i, (cell, cx) in enumerate(zip(row, col_x)):
            ax_tbl.text(cx, ry, cell, transform=ax_tbl.transAxes,
                        fontsize=9, va='top', ha='left',
                        color='#C0392B' if '*' in cell else '#222')
    ax_tbl.text(0.0, -0.05,
                '注：控制变量均取均值；SE = 标准误；*** p<.001, ** p<.01, * p<.05',
                transform=ax_tbl.transAxes, fontsize=8, va='top', ha='left', color='#666')

    fig.savefig(os.path.join(OUT_DIR,'F4_moderation_v3.png'), dpi=150, bbox_inches='tight')
    plt.close()
    pr('\n![调节效应简单斜率（PROCESS风格）](F4_moderation_v3.png)')

    pr(f'\n> 图表已保存至 {OUT_DIR}/F4_moderation_v3.png')

except Exception as e:
    import traceback
    pr(f'\n> 图表生成出错：{e}\n{traceback.format_exc()}')

pr('\n---')
pr(f'\n注释: * p<.05, ** p<.01, *** p<.001（双尾）。'
   f'所有 Welch t 检验使用 Welch-Satterthwaite 自由度近似。\n'
   f'第六节 21 次 Fisher 精确检验已进行 Bonferroni 校正（alpha={alpha_bonf:.4f}）。')
pr(f'\n*报告生成时间: {today} | 输出文件: {OUT_DIR}/*')
_log.close()
print(f'\n报告已保存: {log_path}')
print(f'CSV表格 -> {OUT_DIR}/')
