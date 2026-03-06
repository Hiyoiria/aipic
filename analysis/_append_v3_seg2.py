#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""追加 formal_analysis_v3.py 第二段（四～六节）"""
import os

TARGET = os.path.join(os.path.dirname(__file__), 'formal_analysis_v3.py')

SEG = '''

# ═══════════════════════════════════════════════════════════════════
# 四、过度怀疑分析
# ═══════════════════════════════════════════════════════════════════
h2(\'四、过度怀疑分析（T6）\')

long = master[[\'participant_id\',\'group\',\'acc_ai\',\'acc_real\']].dropna().copy()
long = long.melt(id_vars=[\'participant_id\',\'group\'],
                 value_vars=[\'acc_ai\',\'acc_real\'],
                 var_name=\'image_type\', value_name=\'accuracy\')
long[\'image_type\'] = long[\'image_type\'].map({\'acc_ai\':\'AI\',\'acc_real\':\'Real\'})

h3(\'4.1 混合 ANOVA（2组 × 2图像类型）\')
anova_res = pg.mixed_anova(data=long, dv=\'accuracy\', between=\'group\',
                            within=\'image_type\', subject=\'participant_id\')
a_rows = []
for _, row in anova_res.iterrows():
    df1_col = \'DF1\' if \'DF1\' in anova_res.columns else \'ddof1\'
    df2_col = \'DF2\' if \'DF2\' in anova_res.columns else \'ddof2\'
    df1_val = row.get(df1_col, \'—\'); df2_val = row.get(df2_col, \'—\')
    a_rows.append([row[\'Source\'],
                   fmt(float(df1_val),0) if isinstance(df1_val,(int,float)) else str(df1_val),
                   fmt(float(df2_val),0) if isinstance(df2_val,(int,float)) else str(df2_val),
                   f\'{row["F"]:.3f}\', fmt_p(row[\'p-unc\'])+stars(row[\'p-unc\']),
                   fmt_r(row[\'np2\'],3)])
md_table([\'效应\',\'df₁\',\'df₂\',\'F\',\'*p*\',\'η²p\'], a_rows)

h3(\'4.2 按图像类型的组间差异（简单效应）\')
sub_rows = []
for itype in [\'AI\',\'Real\']:
    sub_l = long[long[\'image_type\']==itype]
    a_ = sub_l[sub_l[\'group\']==\'对照\'][\'accuracy\'].values
    c_ = sub_l[sub_l[\'group\']==\'实验\'][\'accuracy\'].values
    t_, p_ = stats.ttest_ind(c_, a_, equal_var=False)
    wdf    = welch_df(a_, c_); g_ = hedges_g(c_, a_)
    sub_rows.append([itype+\'图像\', ms(a_), ms(c_),
                     f\'{t_:.3f}\', f\'{wdf:.1f}\', fmt_p(p_)+stars(p_), fmt_r(g_)])
md_table([\'图像类型\',\'对照组 M (SD)\',\'实验组 M (SD)\',\'t\',\'df\',\'*p*\',"Hedges\' *g*"], sub_rows)

_inter_p_arr = anova_res[anova_res[\'Source\']==\'Interaction\'][\'p-unc\'].values
_inter_p_val = float(_inter_p_arr[0]) if len(_inter_p_arr) > 0 else float(\'nan\')

# ═══════════════════════════════════════════════════════════════════
# 五、信心与校准分析
# ═══════════════════════════════════════════════════════════════════
h2(\'五、信心与校准分析（T5）\')
h3(\'5.1 后测表现自评与 calibration_gap 组间比较\')
u_a = gA[\'self_performance\'].dropna(); u_c = gC[\'self_performance\'].dropna()
med_a = float(np.median(u_a)); med_c = float(np.median(u_c))
iq_a  = float(np.percentile(u_a, 75) - np.percentile(u_a, 25))
iq_c  = float(np.percentile(u_c, 75) - np.percentile(u_c, 25))
U, p_u = stats.mannwhitneyu(u_c.values, u_a.values, alternative=\'two-sided\')
r_eff = 1 - 2*U/(len(u_c)*len(u_a))
cg_a = gA[\'calibration_gap\'].dropna().values
cg_c = gC[\'calibration_gap\'].dropna().values
t_cg, p_cg = stats.ttest_ind(cg_c, cg_a, equal_var=False)
wdf_cg = welch_df(cg_a, cg_c); g_cg = hedges_g(cg_c, cg_a)
t_1samp, p_1samp = stats.ttest_1samp(np.concatenate([cg_a, cg_c]), 0)
md_table(
    [\'指标\',\'对照组\',\'实验组\',\'统计量\',\'df\',\'*p*\',\'效应量\'],
    [
        [\'后测表现自评\', f\'Mdn={med_a:.1f}, IQR={iq_a:.1f}\',
         f\'Mdn={med_c:.1f}, IQR={iq_c:.1f}\',
         f\'U={U:.0f}\', \'—\', fmt_p(p_u)+stars(p_u), f\'r={fmt_r(r_eff)}\'],
        [\'calibration_gap（M,SD）\', ms(cg_a), ms(cg_c),
         f\'t={t_cg:.3f}\', f\'{wdf_cg:.1f}\', fmt_p(p_cg)+stars(p_cg), f\'g={fmt_r(g_cg)}\'],
        [\'calibration_gap vs 0（全样本）\', \'—\', \'—\',
         f\'t={t_1samp:.3f}\', f\'{len(cg_a)+len(cg_c)-1}\',
         fmt_p(p_1samp)+stars(p_1samp), \'—\'],
    ]
)

# ═══════════════════════════════════════════════════════════════════
# 六、逐图与图像类型分析
# ═══════════════════════════════════════════════════════════════════
h2(\'六、逐图与图像类型分析\')
r_m = r_f.merge(master[[\'participant_id\',\'group\']], on=\'participant_id\', how=\'inner\')

h3(\'6.1 每张图 Fisher 精确检验（group × is_correct）\')
N_FISHER = 0
fisher_rows_data = []
for img_id, grp in r_m.groupby(\'image_id\'):
    tbl = pd.crosstab(grp[\'group\'], grp[\'is_correct\'])
    if tbl.shape == (2,2):
        N_FISHER += 1
        OR, p_f = stats.fisher_exact(tbl.values)
        acc_A = grp[grp[\'group\']==\'对照\'][\'is_correct\'].mean()
        acc_C = grp[grp[\'group\']==\'实验\'][\'is_correct\'].mean()
        meta  = IMAGE_META.get(img_id, {})
        fisher_rows_data.append({
            \'image_id\': img_id, \'type\': meta.get(\'type\',\'?\'),
            \'style\': meta.get(\'style\',\'?\'),
            \'acc_A\': acc_A, \'acc_C\': acc_C,
            \'diff\': acc_C - acc_A, \'OR\': OR, \'p\': p_f,
            \'p_bonf\': min(p_f * N_FISHER, 1.0)
        })

fisher_df = pd.DataFrame(fisher_rows_data).sort_values(\'diff\', ascending=False)
alpha_bonf = 0.05 / N_FISHER if N_FISHER > 0 else 0.05
fish_md = []
for _, row in fisher_df.iterrows():
    fish_md.append([
        row[\'image_id\'], row[\'type\'], row[\'style\'],
        f\'{row["acc_A"]:.3f}\', f\'{row["acc_C"]:.3f}\', f\'{row["diff"]:+.3f}\',
        f\'{row["OR"]:.3f}\', fmt_p(row[\'p\'])+stars(row[\'p\']),
        fmt_p(row[\'p_bonf\'])+(\' ★\' if row[\'p_bonf\'] < .05 else \'\'),
    ])
md_table([\'图像ID\',\'类型\',\'风格\',\'对照组准确率\',\'实验组准确率\',\'Δ(实验−对照)\',\'OR\',\'*p*（未校正）\',\'*p*（Bonferroni）\'], fish_md)
sig_raw  = fisher_df[fisher_df[\'p\'] < .05][\'image_id\'].tolist()
sig_bonf = fisher_df[fisher_df[\'p_bonf\'] < .05][\'image_id\'].tolist()
pr(f\'\\n> 原始 *p* < .05：**{sig_raw}**；Bonferroni 校正后（α={alpha_bonf:.4f}）显著：**{sig_bonf if sig_bonf else "无"}**。\')

h3(\'6.2 风格类型分析（photo vs not_photo）\')
r_m[\'style_photo\'] = (r_m[\'style\'] == \'photograph\').astype(int)
style_acc = r_m.groupby([\'participant_id\',\'group\',\'style_photo\'])[\'is_correct\'].mean().reset_index(name=\'acc\')
sty_rows = []
for sp, lbl in [(1,\'photo（摄影风格）\'), (0,\'not_photo（图绘风格）\')]:
    sub_s = style_acc[style_acc[\'style_photo\']==sp]
    a_ = sub_s[sub_s[\'group\']==\'对照\'][\'acc\'].values
    c_ = sub_s[sub_s[\'group\']==\'实验\'][\'acc\'].values
    if len(a_) > 1 and len(c_) > 1:
        t_, p_ = stats.ttest_ind(c_, a_, equal_var=False)
        wdf    = welch_df(a_, c_); g_ = hedges_g(c_, a_)
        sty_rows.append([lbl, ms(a_), ms(c_), f\'{t_:.3f}\', f\'{wdf:.1f}\', fmt_p(p_)+stars(p_), fmt_r(g_)])
md_table([\'风格\',\'对照组 M (SD)\',\'实验组 M (SD)\',\'t\',\'df\',\'*p*\',"Hedges\' *g*"], sty_rows)
style_wide = style_acc.copy()
style_wide[\'group_c\'] = (style_wide[\'group\']==\'实验\').astype(float)
m_style = smf.ols(\'acc ~ group_c * style_photo\', data=style_wide).fit()
pr(f\'\\n> **模型**: acc ~ group_c × style_photo，n={len(style_wide)}行。\')
pr(f\'> F({m_style.df_model:.0f},{m_style.df_resid:.0f})={m_style.fvalue:.3f}, p {fmt_p(m_style.f_pvalue)+stars(m_style.f_pvalue)}\\n\')
for k, v in m_style.pvalues.items():
    pr(f\'- {k}: B={m_style.params[k]:.3f}, *p*={fmt_p(v)+stars(v)}\')

h3(\'6.3 可反向搜索性分析\')
rs_agg = r_m.groupby([\'participant_id\',\'group\',\'reverse_searchable\'])[\'is_correct\'].mean().reset_index(name=\'acc_rs\')
rs_rows = []
for rs_val, label in [(True,\'可反向搜索\'), (False,\'不可反向搜索（仅AI图）\')]:
    sub_r = rs_agg[rs_agg[\'reverse_searchable\']==rs_val]
    a_ = sub_r[sub_r[\'group\']==\'对照\'][\'acc_rs\'].values
    c_ = sub_r[sub_r[\'group\']==\'实验\'][\'acc_rs\'].values
    if len(a_) > 1 and len(c_) > 1:
        t_, p_ = stats.ttest_ind(c_, a_, equal_var=False)
        wdf    = welch_df(a_, c_); g_ = hedges_g(c_, a_)
        rs_rows.append([label, f\'{np.mean(a_):.3f}\', f\'{np.mean(c_):.3f}\',
                        f\'{t_:.3f}\', f\'{wdf:.1f}\', fmt_p(p_)+stars(p_), fmt_r(g_)])
md_table([\'类型\',\'对照组均值\',\'实验组均值\',\'t\',\'df\',\'*p*\',"Hedges\' *g*"], rs_rows)
'''

with open(TARGET, 'a', encoding='utf-8') as f:
    f.write(SEG)
print('seg2 OK, lines appended.')
