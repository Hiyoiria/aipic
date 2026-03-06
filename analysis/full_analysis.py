#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Study2 完整分析脚本
运行: python analysis/full_analysis.py
输出: analysis/output/full_analysis_report.txt  +  各 CSV

分析维度：
  1.  实验完成情况
  2.  人口统计（含 AI 素养基线）
  3.  主要结果：正确率（总 / AI图 / Real图）
  4.  前后自信心比对（self_assessed_ability vs self_performance vs 实际正确率）
  5.  信号检测论（d', criterion c）
  6.  置信度分析 + 校准曲线 + Brier Score
  7.  学习曲线 / 图片顺序效应
  8.  反应时分析
  9.  工具使用行为（Google Lens 深度）
  10. 后测问卷 & 操纵检验
  11. AI 素养作为协变量（ANCOVA / 回归）
  12. 策略使用效果（Group C 内部分析）
  13. 干预时长与成效
  14. 每张图片正确率（含分组对比）
  15. 效应量汇总 & 样本量建议
"""
import sys, os, math, warnings
import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.formula.api as smf

sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
OUT_DIR  = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(OUT_DIR, exist_ok=True)

log_path = os.path.join(OUT_DIR, 'full_analysis_report.txt')
_log = open(log_path, 'w', encoding='utf-8')

def pr(*args, **kwargs):
    print(*args, **kwargs)
    print(*args, **kwargs, file=_log)

def section(title):
    pr('\n' + '=' * 65)
    pr(f'  {title}')
    pr('=' * 65)

def sub(title):
    pr(f'\n── {title}')

def cohens_d(x1, x2):
    n1, n2 = len(x1), len(x2)
    s = math.sqrt(((n1-1)*np.std(x1,ddof=1)**2 + (n2-1)*np.std(x2,ddof=1)**2)/(n1+n2-2))
    return (np.mean(x1) - np.mean(x2)) / s if s else float('nan')

def hedges_g(d, n1, n2):
    return d * (1 - 3 / (4*(n1+n2-2) - 1))

def welch_t(x1, x2, label=''):
    t, p = stats.ttest_ind(x1, x2, equal_var=False)
    d = cohens_d(x1, x2)
    pr(f'  {label}  t={t:.3f}, p={p:.4f}, d={d:.3f}')
    return t, p, d

def spearman(x, y, label=''):
    mask = ~(np.isnan(x) | np.isnan(y))
    rho, p = stats.spearmanr(x[mask], y[mask])
    pr(f'  {label}  rho={rho:.3f}, p={p:.4f}, n={mask.sum()}')
    return rho, p

# ═══════════════════════════════════════════════════════════════════
# 0. 读取数据
# ═══════════════════════════════════════════════════════════════════
section('0. 数据加载')
p   = pd.read_csv(os.path.join(DATA_DIR, 'participants.csv'))
r   = pd.read_csv(os.path.join(DATA_DIR, 'responses.csv'))
ps  = pd.read_csv(os.path.join(DATA_DIR, 'post-survey.csv'))
lg  = pd.read_csv(os.path.join(DATA_DIR, 'interaction-logs.csv'))
pr(f'participants={len(p)}, responses={len(r)}, post-survey={len(ps)}, logs={len(lg)}')

# 排除 B 组（测试），只保留 A / C
p = p[p['group'].isin(['A','C'])].copy()
p['group_num'] = (p['group'] == 'C').astype(int)  # A=0, C=1

# ═══════════════════════════════════════════════════════════════════
# 1. 完成情况
# ═══════════════════════════════════════════════════════════════════
section('1. 实验完成情况')
N_REQ = 24
cnt = r.groupby('participant_id').size().reset_index(name='n_resp')
full_ids = cnt[cnt['n_resp'] >= N_REQ]['participant_id']
full_ids = full_ids[full_ids.isin(p['participant_id'])]

r_full  = r[r['participant_id'].isin(full_ids)].copy()
p_full  = p[p['participant_id'].isin(full_ids)].copy()
ps_full = ps[ps['participant_id'].isin(full_ids)].copy()
lg_full = lg[lg['participant_id'].isin(full_ids)].copy()

pr(f'完成 {N_REQ} 张的参与者: {len(full_ids)} 人')
for g in ['A','C']:
    tot  = len(p[p['group']==g])
    done = len(p_full[p_full['group']==g])
    pr(f'  Group {g}: {done}/{tot} 完成 ({done/tot*100:.0f}%)')

r_full['category'] = r_full['image_id'].apply(
    lambda x: 'AI' if x.startswith('ai_') else 'Real')

# ═══════════════════════════════════════════════════════════════════
# 2. 人口统计 & AI 素养基线
# ═══════════════════════════════════════════════════════════════════
section('2. 人口统计 & AI 素养基线（完成者）')

# 分类变量
for col in ['age','gender','education','ai_tool_usage','ai_exposure_freq']:
    if col in p_full.columns:
        sub(col)
        pr(p_full[col].value_counts(dropna=False).to_string())

# AI 素养连续变量
sub('AI 素养指标 by 组别（ai_familiarity / self_assessed_ability，1-5）')
ai_lit = p_full.groupby('group')[['ai_familiarity','self_assessed_ability']].agg(['mean','std']).round(2)
pr(ai_lit.to_string())

# 组间 AI 素养差异（基线平衡检验）
sub('基线平衡检验：AI 素养 A vs C')
for col in ['ai_familiarity','self_assessed_ability']:
    welch_t(p_full[p_full['group']=='C'][col].values,
            p_full[p_full['group']=='A'][col].values, label=col)

# ═══════════════════════════════════════════════════════════════════
# 3. 主要结果：正确率
# ═══════════════════════════════════════════════════════════════════
section('3. 主要结果：正确率')

def acc_per_pid(df, col='is_correct'):
    return df.groupby('participant_id')[col].mean().reset_index(name='acc')

acc_total = acc_per_pid(r_full).rename(columns={'acc':'acc_total'})
acc_ai    = acc_per_pid(r_full[r_full['category']=='AI']).rename(columns={'acc':'acc_ai'})
acc_real  = acc_per_pid(r_full[r_full['category']=='Real']).rename(columns={'acc':'acc_real'})

acc = (acc_total
       .merge(acc_ai,   on='participant_id', how='left')
       .merge(acc_real,  on='participant_id', how='left')
       .merge(p_full[['participant_id','group','ai_familiarity',
                       'self_assessed_ability','intervention_duration_s']], on='participant_id', how='left'))

sub('均值 by 组别')
pr(acc.groupby('group')[['acc_total','acc_ai','acc_real']].agg(['mean','std']).round(3).to_string())

sub('个体明细')
pr(acc[['participant_id','group','acc_total','acc_ai','acc_real']]
   .sort_values(['group','acc_total']).to_string(index=False))

gA = acc[acc['group']=='A']['acc_total'].values
gC = acc[acc['group']=='C']['acc_total'].values

sub('Welch t 检验 & 效应量')
t3, p3, d3 = welch_t(gC, gA, label='总正确率 C vs A')
g3 = hedges_g(d3, len(gC), len(gA))
pr(f'  Hedges\' g = {g3:.3f}')
pr(f'  均值差 C-A = {gC.mean()-gA.mean():+.3f} ({(gC.mean()-gA.mean())*100:+.1f}%)')

u3, pu3 = stats.mannwhitneyu(gC, gA, alternative='two-sided')
r_rb3 = (2*u3/(len(gC)*len(gA))) - 1
pr(f'  Mann-Whitney U={u3:.1f}, p={pu3:.4f}, rank-biserial r={r_rb3:.3f}')

sub('AI 图 vs Real 图正确率（配对比较，全样本）')
all_paired = acc[['acc_ai','acc_real']].dropna()
t_pair, p_pair = stats.ttest_rel(all_paired['acc_ai'], all_paired['acc_real'])
pr(f'  全样本配对 t: AI({all_paired.acc_ai.mean():.3f}) vs Real({all_paired.acc_real.mean():.3f}), '
   f't={t_pair:.3f}, p={p_pair:.4f}')

# ═══════════════════════════════════════════════════════════════════
# 4. 前后自信心比对
# ═══════════════════════════════════════════════════════════════════
section('4. 前后自信心比对')
pr('  前测: self_assessed_ability（实验前对自身AI识别能力的评估，1-5）')
pr('  后测: self_performance（实验后自评表现，1-5）')
pr('  实际: acc_total（真实正确率）')

ps_conf = (ps_full[['participant_id','self_performance']]
           .merge(acc[['participant_id','group','acc_total']], on='participant_id', how='inner')
           .merge(p_full[['participant_id','self_assessed_ability']], on='participant_id', how='left'))

sub('描述统计 by 组别')
pr(ps_conf.groupby('group')[['self_assessed_ability','self_performance','acc_total']]
   .agg(['mean','std']).round(3).to_string())

sub('前测 vs 后测自信心变化（配对 t，全有效样本）')
paired = ps_conf[['self_assessed_ability','self_performance']].dropna()
if len(paired) >= 3:
    t_c, p_c = stats.ttest_rel(paired['self_performance'], paired['self_assessed_ability'])
    pr(f'  前({paired.self_assessed_ability.mean():.2f}) → 后({paired.self_performance.mean():.2f}), '
       f't={t_c:.3f}, p={p_c:.4f}, n={len(paired)}')
else:
    pr('  样本量不足，跳过配对 t 检验')

sub('组别内前后信心变化')
for g in ['A','C']:
    sub_df = ps_conf[ps_conf['group']==g][['self_assessed_ability','self_performance']].dropna()
    if len(sub_df) >= 2:
        diff = sub_df['self_performance'] - sub_df['self_assessed_ability']
        pr(f'  Group {g}: 前→后 均值差 = {diff.mean():+.3f} (SD={diff.std(ddof=1):.3f}, n={len(sub_df)})')

sub('元认知准确性：自评 vs 实际正确率')
spearman(ps_conf['self_assessed_ability'].values, ps_conf['acc_total'].values, label='前测自评 vs 实际')
spearman(ps_conf['self_performance'].values, ps_conf['acc_total'].values, label='后测自评 vs 实际')

sub('自信校准：自评高估 / 低估人数')
ps_conf['over_pre']  = ps_conf['self_assessed_ability']/5 - ps_conf['acc_total']
ps_conf['over_post'] = ps_conf['self_performance']/5 - ps_conf['acc_total']
for col, label in [('over_pre','前测'),('over_post','后测')]:
    v = ps_conf[col].dropna()
    n_over = (v > 0.05).sum(); n_under = (v < -0.05).sum(); n_acc = len(v)-n_over-n_under
    pr(f'  {label} 高估={n_over}, 准确={n_acc}, 低估={n_under}  (容差±5%)')

# ═══════════════════════════════════════════════════════════════════
# 5. 信号检测论（SDT）
# ═══════════════════════════════════════════════════════════════════
section('5. 信号检测论（SDT）：d\'  &  criterion c')
pr('  Signal=AI图像  Hit=正确识别AI  FA=将Real误判为AI')

def sdt(df):
    ai   = df[df['category']=='AI'];  real = df[df['category']=='Real']
    n_ai = len(ai); n_real = len(real)
    if n_ai==0 or n_real==0:
        return pd.Series({'dprime':np.nan,'criterion':np.nan,'hit_rate':np.nan,'fa_rate':np.nan})
    hits = (ai['judgment']=='AI').sum()
    fas  = (real['judgment']=='AI').sum()
    hr = (hits+0.5)/(n_ai+1); fr = (fas+0.5)/(n_real+1)
    dp = stats.norm.ppf(hr) - stats.norm.ppf(fr)
    c  = -0.5*(stats.norm.ppf(hr)+stats.norm.ppf(fr))
    return pd.Series({'dprime':dp,'criterion':c,'hit_rate':hr,'fa_rate':fr})

sdt_res = r_full.groupby('participant_id').apply(sdt).reset_index()
sdt_res = sdt_res.merge(p_full[['participant_id','group']], on='participant_id')

sub('SDT 指标 by 组别')
pr(sdt_res.groupby('group')[['dprime','criterion','hit_rate','fa_rate']]
   .agg(['mean','std']).round(3).to_string())

dA_sdt = sdt_res[sdt_res['group']=='A']['dprime'].values
dC_sdt = sdt_res[sdt_res['group']=='C']['dprime'].values
welch_t(dC_sdt, dA_sdt, label="d'")
cA = sdt_res[sdt_res['group']=='A']['criterion'].values
cC = sdt_res[sdt_res['group']=='C']['criterion'].values
welch_t(cC, cA, label='criterion c')

# ═══════════════════════════════════════════════════════════════════
# 6. 置信度分析 + 校准曲线 + Brier Score
# ═══════════════════════════════════════════════════════════════════
section('6. 置信度分析 + 校准曲线 + Brier Score')

r_g = r_full.merge(p_full[['participant_id','group']], on='participant_id')

sub('置信度 by 组别')
pr(r_g.groupby('group')['confidence'].describe().round(2).to_string())

sub('置信度 by 正确/错误')
pr(r_full.groupby('is_correct')['confidence'].agg(['mean','std','count']).round(3).to_string())
welch_t(r_full[r_full['is_correct']]['confidence'].values,
        r_full[~r_full['is_correct']]['confidence'].values, label='正确 vs 错误置信度')

sub('校准曲线：各置信度等级下的实际正确率')
calib = r_full.groupby('confidence')['is_correct'].agg(['mean','count']).reset_index()
calib.columns = ['confidence','accuracy','n']
calib['expected_acc'] = calib['confidence'] / 5   # 若 1-5 → 0.2-1.0 为理想校准
pr(calib.to_string(index=False))

sub('Brier Score（越低越好，= MSE of confidence/5 vs is_correct）')
r_full['conf_norm'] = r_full['confidence'] / 5
bs_all = ((r_full['conf_norm'] - r_full['is_correct'].astype(float))**2).mean()
pr(f'  全样本 Brier Score = {bs_all:.4f}')
for g in ['A','C']:
    sub_df = r_g[r_g['group']==g]
    bs = ((sub_df['confidence']/5 - sub_df['is_correct'].astype(float))**2).mean()
    pr(f'  Group {g}: {bs:.4f}')

sub('参与者级别：置信度 vs 正确率 相关')
conf_acc = r_full.groupby('participant_id').agg(
    mean_conf=('confidence','mean'), acc=('is_correct','mean')).reset_index()
spearman(conf_acc['mean_conf'].values, conf_acc['acc'].values, label='置信度 vs 正确率（参与者级）')

# ═══════════════════════════════════════════════════════════════════
# 7. 学习曲线 / 图片顺序效应
# ═══════════════════════════════════════════════════════════════════
section('7. 学习曲线 / 图片顺序效应')
pr('  image_order: 1-12=前半段, 13-24=后半段')

r_full['half'] = r_full['image_order'].apply(lambda x: 'first' if x<=12 else 'second')
r_g2 = r_full.merge(p_full[['participant_id','group']], on='participant_id')

sub('前 vs 后半段正确率（全样本配对）')
half_pid = r_full.groupby(['participant_id','half'])['is_correct'].mean().unstack('half').dropna()
t_h, p_h = stats.ttest_rel(half_pid['second'], half_pid['first'])
pr(f'  前半({half_pid["first"].mean():.3f}) → 后半({half_pid["second"].mean():.3f}), '
   f't={t_h:.3f}, p={p_h:.4f}, n={len(half_pid)}')

sub('前 vs 后半段 by 组别')
for g in ['A','C']:
    sub_df = r_g2[r_g2['group']==g].groupby(['participant_id','half'])['is_correct'].mean().unstack('half').dropna()
    if len(sub_df) >= 2:
        t, pv = stats.ttest_rel(sub_df['second'], sub_df['first'])
        pr(f'  Group {g}: 前({sub_df["first"].mean():.3f})→后({sub_df["second"].mean():.3f}), '
           f't={t:.3f}, p={pv:.4f}, n={len(sub_df)}')

sub('按图片顺序的逐步正确率（移动平均，步长4）')
order_acc = r_full.groupby('image_order')['is_correct'].mean().reset_index()
order_acc['roll4'] = order_acc['is_correct'].rolling(4, min_periods=1).mean()
pr(order_acc[['image_order','is_correct','roll4']].to_string(index=False))

sub('线性趋势：image_order 预测 is_correct（全样本 OLS）')
r_full['correct_int'] = r_full['is_correct'].astype(int)
model_trend = smf.ols('correct_int ~ image_order', data=r_full).fit()
pr(f'  β(image_order)={model_trend.params["image_order"]:.4f}, '
   f'p={model_trend.pvalues["image_order"]:.4f}, R²={model_trend.rsquared:.4f}')


sub('前 vs 后半段置信度变化')
half_conf = r_full.groupby(['participant_id','half'])['confidence'].mean().unstack('half').dropna()
t_conf, p_conf = stats.ttest_rel(half_conf['second'], half_conf['first'])
pr(f'  前({half_conf["first"].mean():.2f})→后({half_conf["second"].mean():.2f}), '
   f't={t_conf:.3f}, p={p_conf:.4f}')

# ═══════════════════════════════════════════════════════════════════
# 8. 反应时分析
# ═══════════════════════════════════════════════════════════════════
section('8. 反应时分析')
r_full['rt_s'] = r_full['response_time_ms'] / 1000
r_g2 = r_full.merge(p_full[['participant_id','group']], on='participant_id')

sub('反应时 by 组别（秒）')
pr(r_g2.groupby('group')['rt_s'].describe().round(2).to_string())
welch_t(r_g2[r_g2['group']=='C']['rt_s'].values,
        r_g2[r_g2['group']=='A']['rt_s'].values, label='RT C vs A')

sub('反应时 by 图片类型')
pr(r_full.groupby('category')['rt_s'].agg(['mean','median','std']).round(2).to_string())

sub('反应时 by 正确/错误')
pr(r_full.groupby('is_correct')['rt_s'].agg(['mean','median','std']).round(2).to_string())

sub('反应时 by 顺序（前/后半段）')
pr(r_full.groupby('half')['rt_s'].agg(['mean','median']).round(2).to_string())

sub('参与者级：RT vs 正确率')
rt_acc = r_full.groupby('participant_id').agg(med_rt=('rt_s','median'), acc=('is_correct','mean')).reset_index()
spearman(rt_acc['med_rt'].values, rt_acc['acc'].values, label='中位RT vs 正确率')

# ═══════════════════════════════════════════════════════════════════
# 9. 工具使用行为（Google Lens）
# ═══════════════════════════════════════════════════════════════════
section('9. 工具使用行为（Google Lens）')

lg_full = lg_full.merge(p_full[['participant_id','group']], on='participant_id', how='left')

sub('各 action 总频次')
pr(lg_full['action'].value_counts().to_string())

sub('使用 Lens 人数 by 组别')
lens_users = set(lg_full[lg_full['action']=='OPEN_LENS']['participant_id'])
for g in ['A','C']:
    g_ids = set(p_full[p_full['group']==g]['participant_id'])
    used = len(g_ids & lens_users)
    pr(f'  Group {g}: {used}/{len(g_ids)} ({used/len(g_ids)*100:.0f}%)')

sub('Lens 使用次数 & 深度 by 组别')
lens_depth = (lg_full[lg_full['action'].isin(['OPEN_LENS','SCROLL_LENS','CLICK_RESULT'])]
              .groupby(['participant_id','group','action']).size().unstack('action', fill_value=0).reset_index())
lens_depth = p_full[['participant_id','group']].merge(lens_depth, on=['participant_id','group'], how='left').fillna(0)
for col in ['OPEN_LENS','SCROLL_LENS','CLICK_RESULT']:
    if col in lens_depth.columns:
        pr(f'\n  {col}:')
        pr(lens_depth.groupby('group')[col].describe().round(2).to_string())

sub('使用 Lens 的图片 vs 正确率')
lens_img = lg_full[lg_full['action']=='OPEN_LENS'][['participant_id','image_id']].drop_duplicates()
r_full['used_lens'] = r_full.set_index(['participant_id','image_id']).index.isin(
    lens_img.set_index(['participant_id','image_id']).index)
pr(r_full.groupby('used_lens')['is_correct'].agg(['mean','count']).round(3).to_string())
welch_t(r_full[r_full['used_lens']]['is_correct'].values.astype(float),
        r_full[~r_full['used_lens']]['is_correct'].values.astype(float), label='Lens使用 vs 未使用')

# ═══════════════════════════════════════════════════════════════════
# 10. 后测问卷 & 操纵检验
# ═══════════════════════════════════════════════════════════════════
section('10. 后测问卷 & 操纵检验')
ps_m = ps_full.merge(acc[['participant_id','group','acc_total']], on='participant_id', how='left')

sub('manipulation_check_read（阅读干预材料）')
pr(ps_m.groupby(['group','manipulation_check_read']).size().rename('n').to_string())

sub('manipulation_check_strategies（是否使用纹理策略）')
pr(ps_m['manipulation_check_strategies'].value_counts(dropna=False).to_string())

sub('strategy_usage_degree（策略使用程度，仅 C 组）')
pr(ps_m.groupby('group')['strategy_usage_degree'].describe().round(2).to_string())

sub('attention_check_passed')
pr(ps_m['attention_check_passed'].value_counts().to_string())

sub('open_method（自述策略）')
for _, row in ps_m[['participant_id','group','open_method']].dropna().iterrows():
    pr(f'  [{row.group}] {str(row.open_method)[:90]}')

# ═══════════════════════════════════════════════════════════════════
# 11. AI 素养作为协变量（ANCOVA / 多元回归）
# ═══════════════════════════════════════════════════════════════════
section('11. AI 素养作为协变量（ANCOVA / 多元回归）')
pr('  DV: acc_total  IV: group（A=0, C=1）  Covariates: ai_familiarity, self_assessed_ability')

reg_df = acc.copy()
reg_df['group_c'] = (reg_df['group'] == 'C').astype(int)

sub('相关矩阵：AI 素养 × 正确率')
corr_cols = ['acc_total','acc_ai','acc_real','ai_familiarity','self_assessed_ability']
corr_df = reg_df[corr_cols].dropna()
pr(corr_df.corr(method='spearman').round(3).to_string())

sub('Model 1: 仅组别（基准）')
m1 = smf.ols('acc_total ~ group_c', data=reg_df).fit()
pr(m1.summary2().tables[1].to_string())
pr(f'  R²={m1.rsquared:.4f}, F={m1.fvalue:.3f}, p={m1.f_pvalue:.4f}')

sub('Model 2: 组别 + ai_familiarity（控制 AI 素养）')
m2 = smf.ols('acc_total ~ group_c + ai_familiarity', data=reg_df.dropna(subset=['ai_familiarity'])).fit()
pr(m2.summary2().tables[1].to_string())
pr(f'  R²={m2.rsquared:.4f}, ΔR²={m2.rsquared-m1.rsquared:+.4f}')

sub('Model 3: 组别 + ai_familiarity + self_assessed_ability（完整控制）')
m3_df = reg_df.dropna(subset=['ai_familiarity','self_assessed_ability'])
m3 = smf.ols('acc_total ~ group_c + ai_familiarity + self_assessed_ability', data=m3_df).fit()
pr(m3.summary2().tables[1].to_string())
pr(f'  R²={m3.rsquared:.4f}, Adj R²={m3.rsquared_adj:.4f}')

sub('AI 素养单独预测正确率（不含组别）')
for col in ['ai_familiarity','self_assessed_ability']:
    sub_df = reg_df[['acc_total',col]].dropna()
    m = smf.ols(f'acc_total ~ {col}', data=sub_df).fit()
    pr(f'  {col}: β={m.params[col]:.4f}, p={m.pvalues[col]:.4f}, R²={m.rsquared:.4f}')

# ═══════════════════════════════════════════════════════════════════
# 12. 策略使用效果（Group C 内部分析）
# ═══════════════════════════════════════════════════════════════════
section('12. 策略使用效果（Group C 内部分析）')
ps_c = ps_m[ps_m['group']=='C'].copy()

sub('strategy_usage_degree vs 正确率')
spearman(ps_c['strategy_usage_degree'].values, ps_c['acc_total'].values,
         label='策略使用程度 vs 正确率（C组）')

sub('manipulation_check_strategies（纹理策略）yes vs no/NaN')
ps_c['used_texture'] = ps_c['manipulation_check_strategies'].apply(
    lambda x: True if str(x).strip().lower()=='yes' else False)
yes_acc = ps_c[ps_c['used_texture']]['acc_total'].values
no_acc  = ps_c[~ps_c['used_texture']]['acc_total'].values
pr(f'  使用纹理策略: n={len(yes_acc)}, M={np.mean(yes_acc):.3f}')
pr(f'  未使用纹理策略: n={len(no_acc)}, M={np.mean(no_acc):.3f}')
if len(yes_acc) >= 2 and len(no_acc) >= 2:
    welch_t(yes_acc, no_acc, label='yes vs no 纹理策略')

sub('manipulation_check_read（是否读材料）yes vs no → 正确率')
for val in ['yes','no','not_sure']:
    sub_df = ps_m[ps_m['manipulation_check_read']==val]
    if len(sub_df):
        pr(f'  {val}: n={len(sub_df)}, acc={sub_df.acc_total.mean():.3f}')

# ═══════════════════════════════════════════════════════════════════
# 13. 干预时长与成效
# ═══════════════════════════════════════════════════════════════════
section('13. 干预时长与成效')

sub('intervention_duration_s by 组别（秒）')
pr(p_full.groupby('group')['intervention_duration_s'].describe().round(1).to_string())

sub('C 组：干预时长 vs 正确率')
c_df = acc[acc['group']=='C'][['participant_id','acc_total','acc_ai','acc_real','intervention_duration_s']].dropna()
spearman(c_df['intervention_duration_s'].values, c_df['acc_total'].values,
         label='干预时长 vs 总正确率')
spearman(c_df['intervention_duration_s'].values, c_df['acc_ai'].values,
         label='干预时长 vs AI图正确率')

sub('total_duration_s（完成整个实验时长）by 组别')
pr(p_full.groupby('group')['total_duration_s'].describe().round(1).to_string())

# ═══════════════════════════════════════════════════════════════════
# 14. 每张图片正确率（含分组对比）
# ═══════════════════════════════════════════════════════════════════
section('14. 每张图片正确率（n≥5 的图）')

img_stats = (r_full.groupby(['image_id','category'])
             .agg(n=('is_correct','count'), acc=('is_correct','mean'))
             .reset_index())
img_stats['acc_pct'] = (img_stats['acc']*100).round(1)
img_stats = img_stats[img_stats['n'] >= 5]

img_grp = (r_g2.groupby(['image_id','group'])['is_correct'].mean()
           .unstack('group').round(3).reset_index())
img_grp.columns.name = None
img_grp = img_grp.rename(columns={'A':'acc_A','C':'acc_C'})
img_grp['diff_C_minus_A'] = (img_grp.get('acc_C',np.nan) - img_grp.get('acc_A',np.nan)).round(3)

img_out = img_stats.merge(img_grp, on='image_id', how='left').sort_values('acc')
pr(img_out.to_string(index=False))

sub('难度分布')
img_out['difficulty'] = img_out['acc'].apply(
    lambda x: 'too_easy(≥85%)' if x>=0.85 else ('too_hard(≤30%)' if x<=0.30 else 'moderate'))
pr(img_out['difficulty'].value_counts().to_string())

# ═══════════════════════════════════════════════════════════════════
# 15. 效应量汇总 & 样本量建议
# ═══════════════════════════════════════════════════════════════════
section('15. 效应量汇总 & 正式实验样本量建议')

def power_n(d_val, alpha=0.05, power=0.80):
    if math.isnan(d_val) or d_val == 0: return float('inf')
    from scipy.stats import norm, t as tdist
    n = ((norm.ppf(1-alpha/2)+norm.ppf(power))/d_val)**2*2
    for _ in range(20):
        n = ((tdist.ppf(1-alpha/2,2*n-2)+tdist.ppf(power,2*n-2))/d_val)**2*2
    return math.ceil(n)

d_sdt = cohens_d(dC_sdt, dA_sdt)
g_sdt = hedges_g(d_sdt, len(dC_sdt), len(dA_sdt))
pr(f'  总正确率  Cohen\'s d={d3:.3f}, Hedges\'g={g3:.3f}')
pr(f'  d\' (SDT) Cohen\'s d={d_sdt:.3f}, Hedges\'g={g_sdt:.3f}')

pr('\n  样本量估算（基于总正确率 d）:')
for alpha, pw, label in [(0.05,0.80,'α=.05, power=.80'),
                          (0.05,0.90,'α=.05, power=.90'),
                          (0.01,0.80,'α=.01, power=.80')]:
    ne = power_n(abs(d3), alpha, pw)
    pr(f'    {label}:  每组 n≈{ne}, 共{ne*2}  (+20% buffer → 共{math.ceil(ne*2*1.2)})')

# ═══════════════════════════════════════════════════════════════════
# 保存
# ═══════════════════════════════════════════════════════════════════
section('保存结果文件')

master = (acc
    .merge(sdt_res[['participant_id','dprime','criterion','hit_rate','fa_rate']], on='participant_id', how='left')
    .merge(p_full[['participant_id','age','gender','education','ai_tool_usage',
                    'ai_exposure_freq','intervention_duration_s','total_duration_s']], on='participant_id', how='left')
    .merge(lens_depth[['participant_id']+[c for c in ['OPEN_LENS','SCROLL_LENS','CLICK_RESULT'] if c in lens_depth.columns]],
           on='participant_id', how='left')
    .merge(ps_full[['participant_id','manipulation_check_read','manipulation_check_strategies',
                     'strategy_usage_degree','self_performance','attention_check_passed']],
           on='participant_id', how='left')
    .merge(ps_conf[['participant_id','self_assessed_ability','over_pre','over_post']], on='participant_id', how='left')
)
master['half1_acc'] = r_full[r_full['half']=='first'].groupby('participant_id')['is_correct'].mean().reindex(master['participant_id']).values
master['half2_acc'] = r_full[r_full['half']=='second'].groupby('participant_id')['is_correct'].mean().reindex(master['participant_id']).values
master['brier_score'] = (r_full.merge(p_full[['participant_id']], on='participant_id')
    .assign(sq_err=lambda df: (df['confidence']/5 - df['is_correct'].astype(float))**2)
    .groupby('participant_id')['sq_err'].mean()
    .reindex(master['participant_id']).values)

master.to_csv(os.path.join(OUT_DIR, 'master_table.csv'), index=False, encoding='utf-8-sig')
img_out.to_csv(os.path.join(OUT_DIR, 'image_accuracy_by_group.csv'), index=False, encoding='utf-8-sig')
pr('  master_table.csv')
pr('  image_accuracy_by_group.csv')
pr(f'\n  完整报告: {log_path}')
pr('\n分析完成。')

_log.close()
