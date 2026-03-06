#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""追加 formal_analysis_v3.py 第三段（七、调节效应 + SPSS/Process式斜率图）"""
import os

TARGET = os.path.join(os.path.dirname(__file__), 'formal_analysis_v3.py')

SEG = '''

# ═══════════════════════════════════════════════════════════════════
# 七、AI 素养调节效应
# ═══════════════════════════════════════════════════════════════════
h2(\'七、AI 素养调节效应\')

h3(\'7.1 AI 素养与准确率的相关分析\')
corr_rows_sec7 = []
for col, label in [(\'self_assessed_ability\',\'前测自评能力\'),(\'ai_exposure_num\',\'AI使用频率（1–5）\')]:
    valid = master[[\'acc_total\',col]].dropna()
    r_v, p_v = stats.pearsonr(valid[\'acc_total\'], valid[col])
    corr_rows_sec7.append([label, fmt_r(r_v), fmt_p(p_v)+stars(p_v), str(len(valid))])
md_table([\'变量\',\'r（与准确率）\',\'*p*\',\'n\'], corr_rows_sec7)

h3(\'7.2 调节效应模型（前测自评能力 × 组别）\')
pr(\'> 完整模型含人口统计学（学历五分类）+AI使用频率控制变量；均使用 self_assessed_ability 的中心化版本 sae_c。\\n\')

_sae_base = master.dropna(subset=[\'acc_total\',\'self_assessed_ability\',\'group_c\']).copy()
_sae_base[\'sae_c\'] = _sae_base[\'self_assessed_ability\'] - _sae_base[\'self_assessed_ability\'].mean()
sd_sae   = _sae_base[\'self_assessed_ability\'].std(ddof=1)
mean_sae = _sae_base[\'self_assessed_ability\'].mean()

pr(\'\\n**模型 I：完整模型（含学历五分类 + AI使用频率控制）**\\n\')
ctrl_str_mod = \' + \'.join(CTRL_VARS_MOD)
mod_df = _sae_base.dropna(subset=CTRL_VARS_MOD).copy()
mod_df[\'sae_c\'] = mod_df[\'self_assessed_ability\'] - mod_df[\'self_assessed_ability\'].mean()
m_mod = smf.ols(f\'acc_total ~ group_c * sae_c + {ctrl_str_mod}\', data=mod_df).fit()
_reg_full(m_mod, \'acc_total\', mod_df, \'完整调节模型（自评能力 × 组别）\',
          \'学历参照=本科；sae_c 已中心化  ◄ p < .05\')
residual_diagnostics_md(m_mod)

pr(\'\\n**模型 II：简约模型（仅 group_c × sae_c）**\\n\')
min_df = _sae_base.copy()
m_mod_min = smf.ols(\'acc_total ~ group_c * sae_c\', data=min_df).fit()
_reg_full(m_mod_min, \'acc_total\', min_df, \'简约调节模型（自评能力 × 组别）\')
residual_diagnostics_md(m_mod_min)

h3(\'7.3 简单斜率分析（group 效应 at −1SD / Mean / +1SD 自评能力）\')
pr(\'> 两个版本分别对应完整模型（模型 I）和简约模型（模型 II）。\\n\')

def _simple_slopes(m_base, ctrl_formula, df_base, label_prefix):
    pr(f\'\\n**{label_prefix}**\\n\')
    ss_rows = []
    for level, lbl in [(-sd_sae, f\'低自评 −1SD (SAE≈{mean_sae-sd_sae:.2f})\'),
                       (0.0,     f\'均值     (SAE≈{mean_sae:.2f})\'),
                       (+sd_sae, f\'高自评 +1SD (SAE≈{mean_sae+sd_sae:.2f})\')]:
        df_tmp = df_base.copy()
        df_tmp[\'sae_tmp\'] = df_tmp[\'sae_c\'] - level
        formula = \'acc_total ~ group_c * sae_tmp\' + (f\' + {ctrl_formula}\' if ctrl_formula else \'\')
        m_tmp = smf.ols(formula, data=df_tmp).fit()
        b = m_tmp.params[\'group_c\']; se = m_tmp.bse[\'group_c\']
        t_ = m_tmp.tvalues[\'group_c\']; p_ = m_tmp.pvalues[\'group_c\']
        ci_lo = m_tmp.conf_int().loc[\'group_c\',0]; ci_hi = m_tmp.conf_int().loc[\'group_c\',1]
        ss_rows.append([lbl, fmt(b,3), fmt(se,3), f\'[{ci_lo:.3f}, {ci_hi:.3f}]\',
                        fmt(t_,3), fmt_p(p_)+stars(p_)])
    md_table([\'水平\',\'B（组别效应）\',\'SE\',\'95% CI\',\'t\',\'*p*\'], ss_rows)
    int_coef = m_base.params.get(\'group_c:sae_c\', float(\'nan\'))
    b_grp    = m_base.params.get(\'group_c\', float(\'nan\'))
    se_grp   = m_base.bse.get(\'group_c\', float(\'nan\'))
    import numpy as _np
    if not _np.isnan(int_coef) and abs(int_coef) > 1e-10:
        try:
            jn1 = (-b_grp - 1.96*se_grp) / int_coef
            jn2 = (-b_grp + 1.96*se_grp) / int_coef
            pr(f\'\\nJohnson-Neyman 近似显著性边界（中心化 sae_c）: {min(jn1,jn2):.3f} 到 {max(jn1,jn2):.3f}\')
            pr(f\'→ 对应原始 self_assessed_ability: {mean_sae+min(jn1,jn2):.2f} 到 {mean_sae+max(jn1,jn2):.2f}\')
            pr(f\'→ group 效应在此区间**外**达 *p* < .05（交互方向 {">" if int_coef>0 else "<"} 0）\')
        except Exception:
            pr(\'> JN 计算失败\')

_simple_slopes(m_mod,     ctrl_str_mod, mod_df,  \'模型 I 简单斜率（完整控制变量）\')
_simple_slopes(m_mod_min, \'\',           min_df,  \'模型 II 简单斜率（简约模型）\')

h3(\'7.4 调节效应模型（AI使用频率 × 组别）\')
pr(\'> 完整模型含学历五分类 + 前测自评能力控制变量；均使用 ai_exposure_num 的中心化版本 aie_c。\\n\')

ctrl_aie_str = \' + \'.join(CTRL_VARS_AIE)
_aie_base = master.dropna(subset=[\'acc_total\',\'ai_exposure_num\',\'group_c\']).copy()
_aie_base[\'aie_c\'] = _aie_base[\'ai_exposure_num\'] - _aie_base[\'ai_exposure_num\'].mean()
sd_aie   = _aie_base[\'ai_exposure_num\'].std(ddof=1)
mean_aie = _aie_base[\'ai_exposure_num\'].mean()

pr(\'\\n**模型 I：完整模型（含学历五分类 + 前测自评能力）**\\n\')
aie_df = _aie_base.dropna(subset=CTRL_VARS_AIE).copy()
aie_df[\'aie_c\'] = aie_df[\'ai_exposure_num\'] - aie_df[\'ai_exposure_num\'].mean()
m_aie = smf.ols(f\'acc_total ~ group_c * aie_c + {ctrl_aie_str}\', data=aie_df).fit()
_reg_full(m_aie, \'acc_total\', aie_df, \'完整调节模型（AI频率 × 组别）\')
residual_diagnostics_md(m_aie)

pr(\'\\n**模型 II：简约模型（仅 group_c × aie_c）**\\n\')
aie_min_df = _aie_base.copy()
m_aie_min = smf.ols(\'acc_total ~ group_c * aie_c\', data=aie_min_df).fit()
_reg_full(m_aie_min, \'acc_total\', aie_min_df, \'简约调节模型（AI频率 × 组别）\')
residual_diagnostics_md(m_aie_min)

h3(\'7.5 简单斜率分析（group 效应 at −1SD / Mean / +1SD AI使用频率）\')
def _simple_slopes_aie(m_base, ctrl_formula, df_base, label_prefix):
    pr(f\'\\n**{label_prefix}**\\n\')
    aie_ss_rows = []
    for level, lbl in [(-sd_aie, f\'低频率 −1SD (AIE≈{mean_aie-sd_aie:.2f})\'),
                       (0.0,     f\'均值     (AIE≈{mean_aie:.2f})\'),
                       (+sd_aie, f\'高频率 +1SD (AIE≈{mean_aie+sd_aie:.2f})\')]:
        df_tmp = df_base.copy()
        df_tmp[\'aie_tmp\'] = df_tmp[\'aie_c\'] - level
        formula = \'acc_total ~ group_c * aie_tmp\' + (f\' + {ctrl_formula}\' if ctrl_formula else \'\')
        m_tmp = smf.ols(formula, data=df_tmp).fit()
        b = m_tmp.params[\'group_c\']; se = m_tmp.bse[\'group_c\']
        t_ = m_tmp.tvalues[\'group_c\']; p_ = m_tmp.pvalues[\'group_c\']
        ci_lo = m_tmp.conf_int().loc[\'group_c\',0]; ci_hi = m_tmp.conf_int().loc[\'group_c\',1]
        aie_ss_rows.append([lbl, fmt(b,3), fmt(se,3), f\'[{ci_lo:.3f}, {ci_hi:.3f}]\',
                            fmt(t_,3), fmt_p(p_)+stars(p_)])
    md_table([\'水平\',\'B（组别效应）\',\'SE\',\'95% CI\',\'t\',\'*p*\'], aie_ss_rows)

_simple_slopes_aie(m_aie,     ctrl_aie_str, aie_df,     \'模型 I 简单斜率（完整控制变量）\')
_simple_slopes_aie(m_aie_min, \'\',           aie_min_df, \'模型 II 简单斜率（简约模型）\')
'''

with open(TARGET, 'a', encoding='utf-8') as f:
    f.write(SEG)
print('seg3 OK')
