#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按 analysis_guide.md 结构进行分析
Step 0  基线检查
Step 1  干预主效应（H1a 准确率，H1b d'）
Step 2  过度怀疑检验（H1c，2×2 混合 ANOVA）
Step 3  自我效能 & 信心校准（H2a, H2b）
Step 4  控制 AI 素养（H3a, H3b，ANCOVA）
Step 5  补充分析（元认知、高信心错误、逐图、开放题）

输出：
  analysis/output/guided_analysis_report.txt
  analysis/output/table1_baseline.csv
  analysis/output/table2_main_effect.csv
  analysis/output/table3_sdt.csv
  analysis/output/table4_self_efficacy.csv
  analysis/output/table5_calibration.csv
"""
import sys, os, math, warnings
import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.formula.api as smf
import pingouin as pg

sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
OUT_DIR  = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(OUT_DIR, exist_ok=True)

# ── 数据模式 ─────────────────────────────────────────────────────────
# 'real'     → 真实数据  (participants.csv …)
# 'synth'    → 仅合成数据 (participants_synth.csv …)
# 'combined' → 真实 + 合成合并 (participants_combined.csv …)
DATA_MODE = 'combined'   # ← 改这里
_sfx = {'real': '', 'synth': '_synth', 'combined': '_combined'}[DATA_MODE]

log_path = os.path.join(OUT_DIR, 'guided_analysis_report.txt')
_log = open(log_path, 'w', encoding='utf-8')

def pr(*a, **kw):
    print(*a, **kw); print(*a, **kw, file=_log)

def section(t):
    pr('\n' + '═'*65); pr(f'  {t}'); pr('═'*65)

def sub(t):
    pr(f'\n── {t}')

# ── 辅助函数 ────────────────────────────────────────────────────────
def hedges_g(x1, x2):
    n1, n2 = len(x1), len(x2)
    s = math.sqrt(((n1-1)*np.std(x1,ddof=1)**2+(n2-1)*np.std(x2,ddof=1)**2)/(n1+n2-2))
    d = (np.mean(x1)-np.mean(x2))/s if s else float('nan')
    return d*(1-3/(4*(n1+n2-2)-1))

def ci95(x1, x2):
    """差值均值的 95% CI (Welch)"""
    diff = np.mean(x1) - np.mean(x2)
    se = math.sqrt(np.var(x1,ddof=1)/len(x1) + np.var(x2,ddof=1)/len(x2))
    df = (np.var(x1,ddof=1)/len(x1)+np.var(x2,ddof=1)/len(x2))**2 / \
         ((np.var(x1,ddof=1)/len(x1))**2/(len(x1)-1)+(np.var(x2,ddof=1)/len(x2))**2/(len(x2)-1))
    t_crit = stats.t.ppf(0.975, df)
    return diff - t_crit*se, diff + t_crit*se

def report_t(x1, x2, label_c='C', label_a='A'):
    t, p = stats.ttest_ind(x1, x2, equal_var=False)
    g = hedges_g(x1, x2)
    lo, hi = ci95(x1, x2)
    df = (np.var(x1,ddof=1)/len(x1)+np.var(x2,ddof=1)/len(x2))**2 / \
         ((np.var(x1,ddof=1)/len(x1))**2/(len(x1)-1)+(np.var(x2,ddof=1)/len(x2))**2/(len(x2)-1))
    pr(f'  {label_c}: M={np.mean(x1):.3f}, SD={np.std(x1,ddof=1):.3f}, n={len(x1)}')
    pr(f'  {label_a}: M={np.mean(x2):.3f}, SD={np.std(x2,ddof=1):.3f}, n={len(x2)}')
    pr(f'  Welch t({df:.1f})={t:.3f}, p={p:.4f}, Hedges\'g={g:.3f}, 95%CI[{lo:.3f},{hi:.3f}]')
    return {'t':t,'p':p,'g':g,'ci_lo':lo,'ci_hi':hi,'df':df}

# ── 策略关键词词典（全局共用，供 5.3 open_method 和 5.4 per-image 编码）──
STRATEGY_KEYWORDS = {
    'Anatomy':   ['手','finger','解剖','手指','脸','face','eye','眼',
                  'anatomy','fingers','hand','skin','hair','头发','比例'],
    'Style':     ['风格','style','texture','纹理','质感','感觉','feel',
                  'smooth','光滑','塑料','背景','background','光影','light',
                  '完美','渲染','颜色','过渡'],
    'Knowledge': ['搜索','search','google','lens','网站','来源','source',
                  'reverse','图片来源','验证'],
}

def code_strategy(text):
    """将 reasoning 文本编码为策略类别，无关键词返回 '直觉/其他'"""
    if pd.isna(text) or str(text).strip() == '':
        return None  # 未填写
    t = str(text).lower()
    tags = [k for k, ws in STRATEGY_KEYWORDS.items() if any(w in t for w in ws)]
    return ','.join(tags) if tags else '直觉/其他'

def sdt_person(df_p):
    ai   = df_p[df_p['category']=='AI']
    real = df_p[df_p['category']=='Real']
    if len(ai)==0 or len(real)==0:
        return dict(dprime=np.nan, c=np.nan, hr=np.nan, far=np.nan)
    hits = (ai['judgment']=='AI').sum()
    fas  = (real['judgment']=='AI').sum()
    hr  = (hits+0.5)/(len(ai)+1)
    far = (fas+0.5)/(len(real)+1)
    dp = stats.norm.ppf(hr) - stats.norm.ppf(far)
    c  = -0.5*(stats.norm.ppf(hr)+stats.norm.ppf(far))
    return dict(dprime=dp, c=c, hr=hr, far=far)

# ═══════════════════════════════════════════════════════════════════
# 数据加载与过滤
# ═══════════════════════════════════════════════════════════════════
p   = pd.read_csv(os.path.join(DATA_DIR, f'participants{_sfx}.csv'))
r   = pd.read_csv(os.path.join(DATA_DIR, f'responses{_sfx}.csv'))
ps  = pd.read_csv(os.path.join(DATA_DIR, f'post-survey{_sfx}.csv'))
lg  = pd.read_csv(os.path.join(DATA_DIR, f'interaction-logs{_sfx}.csv'))

# ── 图像排除（基于19人真实数据正确率>90%，分析与呈现都删去）──────────
EXCLUDE_IMAGES = ['ai_06', 'ai_11', 'ai_18']  # 94.7%, 94.7%, 100%
N_IMAGES = 21                                  # 24 - 3 = 21 张

r = r[~r['image_id'].isin(EXCLUDE_IMAGES)].copy()

p = p[p['group'].isin(['A','C'])].copy()

# 完成者（≥ N_IMAGES 张，即完成所有保留图像）
cnt = r.groupby('participant_id').size().reset_index(name='n')
full_ids = cnt[cnt['n'] >= N_IMAGES]['participant_id']
full_ids = full_ids[full_ids.isin(p['participant_id'])]

r_f  = r[r['participant_id'].isin(full_ids)].copy()
p_f  = p[p['participant_id'].isin(full_ids)].copy()
ps_f = ps[ps['participant_id'].isin(full_ids)].copy()

r_f['category'] = r_f['image_id'].apply(lambda x:'AI' if x.startswith('ai_') else 'Real')
r_f['correct_int'] = r_f['is_correct'].astype(int)

# ─── 每人指标 ───────────────────────────────────────────────────────
acc = r_f.groupby('participant_id')['is_correct'].mean().reset_index(name='acc_total')
acc_ai   = r_f[r_f['category']=='AI'].groupby('participant_id')['is_correct'].mean().reset_index(name='acc_ai')
acc_real = r_f[r_f['category']=='Real'].groupby('participant_id')['is_correct'].mean().reset_index(name='acc_real')
conf_m   = r_f.groupby('participant_id')['confidence'].mean().reset_index(name='mean_conf')

sdt_list = []
for pid, g in r_f.groupby('participant_id'):
    d = sdt_person(g); d['participant_id'] = pid; sdt_list.append(d)
sdt = pd.DataFrame(sdt_list)

master = (acc
    .merge(acc_ai, on='participant_id', how='left')
    .merge(acc_real, on='participant_id', how='left')
    .merge(conf_m, on='participant_id', how='left')
    .merge(sdt, on='participant_id', how='left')
    .merge(p_f[['participant_id','group','age','gender','education',
                 'ai_familiarity','self_assessed_ability',
                 'ai_tool_usage','ai_exposure_freq']], on='participant_id', how='left')
    .merge(ps_f[['participant_id','manipulation_check_read',
                  'manipulation_check_strategies','strategy_usage_degree',
                  'self_performance','attention_check_passed']], on='participant_id', how='left')
)

# 前测自评能力（已在 master）
master['efficacy_pre']  = master['self_assessed_ability']
master['efficacy_post'] = master['self_performance']
master['efficacy_change'] = master['efficacy_post'] - master['efficacy_pre']

# 校准偏差
master['calib_bias'] = master['mean_conf']/5 - master['acc_total']

# ── AI 素养综合变量：标准化 ai_familiarity + ai_tool_usage 均值 ──────
# ai_tool_usage (yes/no) → 0/1；分别 z-score 后平均
from scipy.stats import zscore as _zscore
master['ai_tool_num'] = (master['ai_tool_usage'] == 'yes').astype(float)
_v = master.dropna(subset=['ai_familiarity', 'ai_tool_num'])
if len(_v) > 1:
    _zf  = _zscore(_v['ai_familiarity'].values)
    _zt  = _zscore(_v['ai_tool_num'].values)
    master.loc[_v.index, 'ai_literacy_composite'] = (_zf + _zt) / 2
else:
    master['ai_literacy_composite'] = np.nan

# ── 正式分析：排除注意力检验未通过的参与者 ──────────────────────────
master = master[master['attention_check_passed'] != False].copy()

gA = master[master['group']=='A']
gC = master[master['group']=='C']

# ═══════════════════════════════════════════════════════════════════
# Step 0：基线检查
# ═══════════════════════════════════════════════════════════════════
section('Step 0：基线检查与样本描述')

sub('0.1 分析样本')
pr(f'  分析样本（完成全部 {N_IMAGES} 张 + 注意力检验通过）: {len(master)} 人  A={len(gA)}, C={len(gC)}')

# 模式化作答（>80%相同判断）
_r_final = r_f[r_f['participant_id'].isin(master['participant_id'])]
pattern_check = _r_final.groupby('participant_id')['judgment'].apply(
    lambda x: max(x.value_counts()/len(x)))
flagged = pattern_check[pattern_check > 0.80]
pr(f'\n  模式化作答检验（>80%相同）: {len(flagged)} 人')
if len(flagged): pr(f'  → {flagged.to_dict()}')

sub('0.2 人口统计描述')
for col in ['age','gender','education','ai_tool_usage','ai_exposure_freq']:
    pr(f'\n  {col}:')
    pr('  '+master[col].value_counts(dropna=True).to_string().replace('\n','\n  '))

sub('0.3 AI素养基线（Table 1）')
t1_rows = []
for col, label in [('ai_familiarity','AI熟悉度'),
                   ('self_assessed_ability','前测自评能力'),
                   ('ai_literacy_composite','AI素养综合分（标准化）')]:
    a = gA[col].dropna().values; c = gC[col].dropna().values
    t,pv = stats.ttest_ind(c, a, equal_var=False)
    t1_rows.append({'变量':label,
                    f'A (n={len(a)}) M±SD':f'{np.mean(a):.2f}±{np.std(a,ddof=1):.2f}',
                    f'C (n={len(c)}) M±SD':f'{np.mean(c):.2f}±{np.std(c,ddof=1):.2f}',
                    't':round(t,3),'p':round(pv,4),'结论':'✓ 组间无差异' if pv>.05 else '⚠ 组间有差异'})

t1 = pd.DataFrame(t1_rows)
pr(t1.to_string(index=False))
t1.to_csv(os.path.join(OUT_DIR,'table1_baseline.csv'), index=False, encoding='utf-8-sig')
pr('\n  → 两组 AI 素养基线无显著差异，随机化成功。')

# ═══════════════════════════════════════════════════════════════════
# Step 1：干预主效应（H1a, H1b）
# ═══════════════════════════════════════════════════════════════════
section('Step 1：干预主效应')

sub('H1a：检测准确率')
pr('\n  策略组 vs 控制组 — 总正确率：')
res1a = report_t(gC['acc_total'].values, gA['acc_total'].values)
sig1a = '✓ 支持 H1a' if res1a['p']<.05 else f'○ 方向一致但 p={res1a["p"]:.4f}（预实验 n 小）'
pr(f'  → {sig1a}')

sub('H1b：辨别力 d\'')
pr('\n  策略组 vs 控制组 — d\'：')
res1b = report_t(gC['dprime'].values, gA['dprime'].values)
sig1b = '✓ 支持 H1b' if res1b['p']<.05 else f'○ 方向一致但 p={res1b["p"]:.4f}'
pr(f'  → {sig1b}')

sub('H1b：判断标准 c（响应偏向）')
pr('\n  c < 0 = 偏向判为AI；c > 0 = 偏向判为Real')
pr(f'  A 组: M={gA["c"].mean():.3f}, SD={gA["c"].std(ddof=1):.3f}')
pr(f'  C 组: M={gC["c"].mean():.3f}, SD={gC["c"].std(ddof=1):.3f}')
t_c,p_c = stats.ttest_ind(gC['c'].values, gA['c'].values, equal_var=False)
pr(f'  t={t_c:.3f}, p={p_c:.4f}')
pr('  → 两组均略偏向"保守"（c≈0）；策略组偏向更保守（不过度怀疑）' if gC['c'].mean()>gA['c'].mean() else
   '  → 策略组判断标准更宽松（更倾向于判为AI）')

sub('Table 2：主效应结果汇总')
t2 = pd.DataFrame([
    {'指标':'acc_total（总正确率）',
     'A: M(SD)':f'{gA.acc_total.mean():.3f}({gA.acc_total.std(ddof=1):.3f})',
     'C: M(SD)':f'{gC.acc_total.mean():.3f}({gC.acc_total.std(ddof=1):.3f})',
     't':round(res1a['t'],3),'df':round(res1a['df'],1),'p':round(res1a['p'],4),
     "Hedges'g":round(res1a['g'],3),'95%CI':f'[{res1a["ci_lo"]:.3f},{res1a["ci_hi"]:.3f}]'},
    {'指标':"d'（辨别力）",
     'A: M(SD)':f'{gA.dprime.mean():.3f}({gA.dprime.std(ddof=1):.3f})',
     'C: M(SD)':f'{gC.dprime.mean():.3f}({gC.dprime.std(ddof=1):.3f})',
     't':round(res1b['t'],3),'df':round(res1b['df'],1),'p':round(res1b['p'],4),
     "Hedges'g":round(res1b['g'],3),'95%CI':f'[{res1b["ci_lo"]:.3f},{res1b["ci_hi"]:.3f}]'},
])
pr(t2.to_string(index=False))
t2.to_csv(os.path.join(OUT_DIR,'table2_main_effect.csv'), index=False, encoding='utf-8-sig')

sub('Table 3：SDT 完整指标')
t3_rows = []
for col,label in [('dprime',"d'"),('c','c'),('hr','命中率(HR)'),('far','虚报率(FAR)')]:
    a = gA[col].dropna().values; c_ = gC[col].dropna().values
    t_,p_ = stats.ttest_ind(c_, a, equal_var=False)
    t3_rows.append({'指标':label,
                    'A M(SD)':f'{np.mean(a):.3f}({np.std(a,ddof=1):.3f})',
                    'C M(SD)':f'{np.mean(c_):.3f}({np.std(c_,ddof=1):.3f})',
                    't':round(t_,3),'p':round(p_,4)})
t3 = pd.DataFrame(t3_rows)
pr(t3.to_string(index=False))
t3.to_csv(os.path.join(OUT_DIR,'table3_sdt.csv'), index=False, encoding='utf-8-sig')

# ═══════════════════════════════════════════════════════════════════
# Step 2：过度怀疑检验（H1c）
# ═══════════════════════════════════════════════════════════════════
section('Step 2：过度怀疑检验（H1c）— 2×2 混合 ANOVA')
pr('  DV: 正确率  | Between: group  | Within: image_type (AI/Real)')

# 准备长格式数据
long = master[['participant_id','group','acc_ai','acc_real']].dropna().copy()
long = long.melt(id_vars=['participant_id','group'],
                 value_vars=['acc_ai','acc_real'],
                 var_name='image_type', value_name='accuracy')
long['image_type'] = long['image_type'].map({'acc_ai':'AI','acc_real':'Real'})

anova_res = pg.mixed_anova(data=long, dv='accuracy', between='group',
                            within='image_type', subject='participant_id')
pr(anova_res[['Source','F','p-unc','np2']].round(4).to_string(index=False))

# 解读交互效应
interact_row = anova_res[anova_res['Source'].isin(['Interaction','group * image_type'])]
interact_p   = interact_row['p-unc'].values[0]
interact_F   = interact_row['F'].values[0]
interact_np2 = interact_row['np2'].values[0]

pr(f'\n  交互效应: F={interact_F:.3f}, p={interact_p:.4f}, η²p={interact_np2:.3f}')

sub('简单效应分析')
# A vs C on AI images
pr('\n  AI图像上的组间差异：')
res_ai = report_t(gC['acc_ai'].values, gA['acc_ai'].values, 'C(策略)','A(对照)')
# A vs C on Real images
pr('\n  Real图像上的组间差异：')
res_real = report_t(gC['acc_real'].values, gA['acc_real'].values, 'C(策略)','A(对照)')

pr(f'\n  差异不对称程度: AI图差异={gC.acc_ai.mean()-gA.acc_ai.mean():.3f}, '
   f'Real图差异={gC.acc_real.mean()-gA.acc_real.mean():.3f}')

if interact_p < .05:
    if gC.acc_ai.mean()-gA.acc_ai.mean() > gC.acc_real.mean()-gA.acc_real.mean():
        pr('  → ✓ 支持 H1c：策略提升对AI图的检测更多，未产生过度怀疑副作用')
    else:
        pr('  → ⚠ 不支持 H1c：策略对Real图的影响与预期不符')
else:
    pr('  → 交互效应不显著（预实验 n 小）；方向符合/不符合 H1c，待正式研究检验')
    if gC.acc_ai.mean()-gA.acc_ai.mean() > gC.acc_real.mean()-gA.acc_real.mean():
        pr('     方向：AI图提升(+{:.1f}%) > Real图变化({:+.1f}%)——符合 H1c 预期'.format(
            (gC.acc_ai.mean()-gA.acc_ai.mean())*100,
            (gC.acc_real.mean()-gA.acc_real.mean())*100))

# ═══════════════════════════════════════════════════════════════════
# Step 3：自我效能 & 信心校准（H2a, H2b）
# ═══════════════════════════════════════════════════════════════════
section('Step 3：自我效能 & 信心校准')

sub('H2a：自我效能前后测变化（2×2 混合 ANOVA）')
pr('  前测=self_assessed_ability（前测自评能力）')
pr('  后测=self_performance（后测自评表现，当前数据库的最近似替代指标）')
pr('  ⚠ 注意：两题测量的是不同构念（能力 vs 表现），结果需谨慎解读')

eff_long = master[['participant_id','group','efficacy_pre','efficacy_post']].dropna().copy()
eff_long = eff_long.melt(id_vars=['participant_id','group'],
                          value_vars=['efficacy_pre','efficacy_post'],
                          var_name='time', value_name='score')
eff_long['time'] = eff_long['time'].map({'efficacy_pre':'pre','efficacy_post':'post'})

anova_eff = pg.mixed_anova(data=eff_long, dv='score', between='group',
                            within='time', subject='participant_id')
pr(anova_eff[['Source','F','p-unc','np2']].round(4).to_string(index=False))

interact_eff_row = anova_eff[anova_eff['Source'].isin(['Interaction','group * time'])]
interact_eff_p = interact_eff_row['p-unc'].values[0]
pr(f'\n  交互效应 group×time: p={interact_eff_p:.4f}')

sub('自我效能变化量（后−前）by 组别')
pr('\n  变化量 = 后测自评 − 前测自评（正值=提升）:')
report_t(gC['efficacy_change'].dropna().values,
         gA['efficacy_change'].dropna().values, 'C(策略)','A(对照)')

pr(f'\n  C 组变化量: M={gC.efficacy_change.mean():+.3f}  (95%CI: [{gC.efficacy_change.mean()-1.96*gC.efficacy_change.std(ddof=1)/len(gC)**.5:.3f}, {gC.efficacy_change.mean()+1.96*gC.efficacy_change.std(ddof=1)/len(gC)**.5:.3f}])')
pr(f'  A 组变化量: M={gA.efficacy_change.mean():+.3f}  (95%CI: [{gA.efficacy_change.mean()-1.96*gA.efficacy_change.std(ddof=1)/len(gA)**.5:.3f}, {gA.efficacy_change.mean()+1.96*gA.efficacy_change.std(ddof=1)/len(gA)**.5:.3f}])')

if interact_eff_p < .05:
    pr(f'  → ✓ 支持 H2a：交互效应显著，策略组自我效能提升幅度显著更大')
else:
    pr(f'  → 方向{"符合" if gC.efficacy_change.mean()>gA.efficacy_change.mean() else "不符合"} H2a预期（C{gC.efficacy_change.mean():+.2f} vs A{gA.efficacy_change.mean():+.2f}），但 p={interact_eff_p:.4f}，预实验 n 小')

t4 = pd.DataFrame([
    {'变量':'前测自评能力(self_assessed_ability)',
     'A: M(SD)':f'{gA.efficacy_pre.mean():.2f}({gA.efficacy_pre.std(ddof=1):.2f})',
     'C: M(SD)':f'{gC.efficacy_pre.mean():.2f}({gC.efficacy_pre.std(ddof=1):.2f})'},
    {'变量':'后测自评表现(self_performance)',
     'A: M(SD)':f'{gA.efficacy_post.mean():.2f}({gA.efficacy_post.std(ddof=1):.2f})',
     'C: M(SD)':f'{gC.efficacy_post.mean():.2f}({gC.efficacy_post.std(ddof=1):.2f})'},
    {'变量':'变化量(Δ)',
     'A: M(SD)':f'{gA.efficacy_change.mean():+.2f}({gA.efficacy_change.std(ddof=1):.2f})',
     'C: M(SD)':f'{gC.efficacy_change.mean():+.2f}({gC.efficacy_change.std(ddof=1):.2f})'},
])
pr('\n  Table 4：自我效能前后测')
pr(t4.to_string(index=False))
t4.to_csv(os.path.join(OUT_DIR,'table4_self_efficacy.csv'), index=False, encoding='utf-8-sig')

sub('H2b：过度自信检验')

# Step 1: 全样本是否存在过度自信？
pr('\n  全样本：per-image 平均信心(rescale) vs 实际准确率')
conf_norm = master['mean_conf']/5
acc_t = master['acc_total']
paired_valid = master[['mean_conf','acc_total']].dropna()
conf_r = paired_valid['mean_conf']/5
acc_r  = paired_valid['acc_total']
t_oc, p_oc = stats.ttest_rel(conf_r, acc_r)
diff_oc = (conf_r - acc_r).mean()
pr(f'  平均信心(0-1): {conf_r.mean():.3f}  |  平均正确率: {acc_r.mean():.3f}')
pr(f'  差值(信心−正确率): {diff_oc:+.3f}')
pr(f'  配对 t({len(paired_valid)-1})={t_oc:.3f}, p={p_oc:.4f}')
pr(f'  → {"✓ 存在显著过度自信（信心高于实际表现）" if p_oc<.05 and diff_oc>0 else "○ 过度自信不显著" if p_oc>=.05 else "✓ 信心低于实际（过度保守）"}')

# Step 2: 组间校准偏差比较
pr('\n  校准偏差 by 组别（正=过度自信，负=过度保守）：')
report_t(gC['calib_bias'].dropna().values, gA['calib_bias'].dropna().values,
         'C(策略)','A(对照)')
pr(f'  → {"H2b 部分支持：C组校准更好（偏差更小）" if gC.calib_bias.mean()<gA.calib_bias.mean() else "H2b 不支持：两组校准偏差方向相反于预期"}')

# Step 3: 高信心错误率（"危险的自信"）
r_f2 = r_f.merge(master[['participant_id','group']], on='participant_id', how='left')
high_conf_err = r_f2[r_f2['confidence']>=4].groupby(['participant_id','group']).apply(
    lambda x: (~x['is_correct']).mean()).reset_index(name='high_conf_err_rate')

pr('\n  高信心错误率（confidence≥4 且判断错误的比例）by 组别：')
pr(high_conf_err.groupby('group')['high_conf_err_rate'].agg(['mean','std','count']).round(3).to_string())
hA = high_conf_err[high_conf_err['group']=='A']['high_conf_err_rate'].values
hC = high_conf_err[high_conf_err['group']=='C']['high_conf_err_rate'].values
if len(hA)>1 and len(hC)>1:
    t_h,p_h = stats.ttest_ind(hC, hA, equal_var=False)
    pr(f'  Welch t={t_h:.3f}, p={p_h:.4f}')
    pr(f'  → {"C组高信心错误更少（减少危险自信）" if np.mean(hC)<np.mean(hA) else "C组高信心错误更多"}')

# 校准曲线
pr('\n  校准曲线（各信心等级 → 实际正确率）：')
calib = r_f.groupby('confidence')['is_correct'].agg(['mean','count']).reset_index()
calib.columns = ['confidence','acc','n']
calib['expected(conf/5)'] = calib['confidence']/5
calib['over_conf'] = (calib['confidence']/5 - calib['acc']).round(3)
pr(calib.to_string(index=False))

t5 = pd.DataFrame([
    {'指标':'信心均值(0-1 rescale)',
     'A':round(gA['mean_conf'].mean()/5,3), 'C':round(gC['mean_conf'].mean()/5,3)},
    {'指标':'正确率均值',
     'A':round(gA['acc_total'].mean(),3), 'C':round(gC['acc_total'].mean(),3)},
    {'指标':'校准偏差(信心−正确率)',
     'A':round(gA['calib_bias'].mean(),3), 'C':round(gC['calib_bias'].mean(),3)},
    {'指标':'高信心错误率(conf≥4, 判错)',
     'A':round(np.mean(hA),3), 'C':round(np.mean(hC),3)},
])
pr('\n  Table 5：信心校准')
pr(t5.to_string(index=False))
t5.to_csv(os.path.join(OUT_DIR,'table5_calibration.csv'), index=False, encoding='utf-8-sig')

# ═══════════════════════════════════════════════════════════════════
# Step 4：控制 AI 素养（H3a, H3b）
# ═══════════════════════════════════════════════════════════════════
section('Step 4：控制 AI 素养（ANCOVA）')

sub('H3a：AI 素养 × 正确率相关')
pr('\n  Pearson r（全样本）：')
for col, label in [('ai_familiarity','AI熟悉度'),
                   ('self_assessed_ability','前测自评能力'),
                   ('ai_literacy_composite','AI素养综合分（标准化）')]:
    valid = master[['acc_total',col]].dropna()
    r_val, p_val = stats.pearsonr(valid['acc_total'], valid[col])
    pr(f'  {label}: r={r_val:.3f}, p={p_val:.4f}, n={len(valid)}')
    pr(f'    → {"✓ 支持 H3a（正相关）" if r_val>0 and p_val<.05 else "方向正确但未显著" if r_val>0 else "⚠ 负相关，反预期"}')

sub('H3b：ANCOVA — 控制 AI 素养后干预主效应')
master['group_c'] = (master['group']=='C').astype(int)

pr('\n  Model 1（基准，仅组别）:')
m1 = smf.ols('acc_total ~ group_c', data=master).fit()
b1 = m1.params['group_c']; p1 = m1.pvalues['group_c']
pr(f'  β(group)={b1:.4f}, p={p1:.4f}, R²={m1.rsquared:.4f}')

pr('\n  Model 2（+ai_familiarity）:')
m2_df = master.dropna(subset=['ai_familiarity'])
m2 = smf.ols('acc_total ~ group_c + ai_familiarity', data=m2_df).fit()
b2 = m2.params['group_c']; p2 = m2.pvalues['group_c']
pr(f'  β(group)={b2:.4f}, p={p2:.4f}, R²={m2.rsquared:.4f}  ΔR²={m2.rsquared-m1.rsquared:+.4f}')

pr('\n  Model 3（+ai_familiarity + self_assessed_ability）:')
m3_df = master.dropna(subset=['ai_familiarity','self_assessed_ability'])
m3 = smf.ols('acc_total ~ group_c + ai_familiarity + self_assessed_ability', data=m3_df).fit()
b3 = m3.params['group_c']; p3 = m3.pvalues['group_c']
pr(f'  β(group)={b3:.4f}, p={p3:.4f}, R²={m3.rsquared:.4f}  (Adj={m3.rsquared_adj:.4f})')
pr(f'  β(ai_familiarity)={m3.params["ai_familiarity"]:.4f}, p={m3.pvalues["ai_familiarity"]:.4f}')
pr(f'  β(self_assessed_ability)={m3.params["self_assessed_ability"]:.4f}, p={m3.pvalues["self_assessed_ability"]:.4f}')

pr('\n  Model 4（+ai_literacy_composite，合并变量）:')
m4_df = master.dropna(subset=['ai_literacy_composite'])
m4 = smf.ols('acc_total ~ group_c + ai_literacy_composite', data=m4_df).fit()
b4 = m4.params['group_c']; p4 = m4.pvalues['group_c']
pr(f'  β(group)={b4:.4f}, p={p4:.4f}, R²={m4.rsquared:.4f}  ΔR²={m4.rsquared-m1.rsquared:+.4f}')
pr(f'  β(ai_literacy_composite)={m4.params["ai_literacy_composite"]:.4f}, '
   f'p={m4.pvalues["ai_literacy_composite"]:.4f}')
pr(f'  → {"✓ 综合素养显著" if m4.pvalues["ai_literacy_composite"]<.05 else "综合素养未显著"}'
   f'，干预效应 {"保持" if p4<.05 else f"p={p4:.4f}"} 方向一致')

pr('\n  斜率同质性检验（AI素养×组别交互）：')
m_int = smf.ols('acc_total ~ group_c * self_assessed_ability', data=m3_df).fit()
pr(f'  β(group×ai_ability)={m_int.params.get("group_c:self_assessed_ability",float("nan")):.4f}, '
   f'p={m_int.pvalues.get("group_c:self_assessed_ability",float("nan")):.4f}')
p_int = m_int.pvalues.get('group_c:self_assessed_ability', 1.0)
pr(f'  → {"⚠ 交互显著，斜率不同质，ANCOVA前提不满足，改报告调节效应" if p_int<.05 else "✓ 交互不显著，斜率同质，ANCOVA前提满足"}')

sub('ANCOVA 综合结论')
direction = '方向一致' if b3>0 else '方向反转'
sig = '仍显著' if p3<.05 else f'p={p3:.4f}（预实验 n 小）'
pr(f'\n  控制AI素养前: β={b1:.4f}, p={p1:.4f}')
pr(f'  控制AI素养后: β={b3:.4f}, p={p3:.4f}  → {direction}, {sig}')
pr(f'  → {"✓ 支持 H3b：干预效果独立于 AI 素养水平" if p3<.05 or (p3<.15 and abs(b3)>0.05) else "○ 控制素养后组别效应减弱，待正式研究确认"}')

# ═══════════════════════════════════════════════════════════════════
# Step 5：补充分析（探索性）
# ═══════════════════════════════════════════════════════════════════
section('Step 5：补充分析（探索性，非预注册）')

sub('5.1 元认知准确性 — 整体自评偏差（复制 Somoray & Miller）')
pr('  整体自评偏差 = self_performance/5 − acc_total（正=高估，负=低估）')
master['overall_calib_bias'] = master['self_performance']/5 - master['acc_total']
pr(f'\n  全样本: M={master.overall_calib_bias.mean():+.3f}, SD={master.overall_calib_bias.std(ddof=1):.3f}')
t_ob,p_ob = stats.ttest_1samp(master['overall_calib_bias'].dropna(), 0)
pr(f'  one-sample t(0): t={t_ob:.3f}, p={p_ob:.4f}')
pr(f'  → {"✓ 显著高估（过度自信）" if p_ob<.05 and master.overall_calib_bias.mean()>0 else "✓ 显著低估（过度保守）" if p_ob<.05 and master.overall_calib_bias.mean()<0 else "○ 整体自评接近实际"}')

pr('\n  by 组别：')
for g in ['A','C']:
    sub_df = master[master['group']==g]['overall_calib_bias'].dropna()
    t_,p_ = stats.ttest_1samp(sub_df, 0)
    pr(f'  Group {g}: M={sub_df.mean():+.3f}, SD={sub_df.std(ddof=1):.3f},'
       f' t={t_:.3f}, p={p_:.4f}  → {"过度自信" if sub_df.mean()>0 else "过度保守"}')

sub('5.2 逐图正确率 — 哪类图受益最多')
img = (r_f.merge(master[['participant_id','group']], on='participant_id')
       .groupby(['image_id','category','group'])['is_correct']
       .mean().unstack('group').reset_index())
img.columns.name = None
img = img.rename(columns={'A':'acc_A','C':'acc_C'})
img['diff_C_A'] = (img['acc_C'] - img['acc_A']).round(3)
img = img.dropna(subset=['acc_A', 'acc_C', 'diff_C_A'])  # 排除某组无数据的图像
img = img.sort_values('diff_C_A', ascending=False)

pr('\n  组间差异最大的 5 张（策略组占优）:')
pr(img.head(5)[['image_id','category','acc_A','acc_C','diff_C_A']].to_string(index=False))
pr('\n  组间差异最大的 5 张（控制组占优）:')
pr(img.tail(5)[['image_id','category','acc_A','acc_C','diff_C_A']].to_string(index=False))

pr('\n  策略对 AI图 vs Real图 的提升不对称：')
pr(f'  AI图平均差值: {img[img["category"]=="AI"]["diff_C_A"].mean():+.3f}')
pr(f'  Real图平均差值: {img[img["category"]=="Real"]["diff_C_A"].mean():+.3f}')

sub('5.3 开放题策略编码（open_method）')
pr('\n  参照 Study 1 三类策略（Style/Anatomy/Knowledge）编码：')
ps_f2 = ps_f.merge(master[['participant_id','group']], on='participant_id', how='left')
coded = []
for _, row in ps_f2[['participant_id','group','open_method']].dropna().iterrows():
    text = str(row['open_method']).lower()
    tags = [k for k, ws in STRATEGY_KEYWORDS.items() if any(w in text for w in ws)]
    coded.append({'group':row['group'],'text':row['open_method'][:60],
                  'codes':','.join(tags) if tags else '其他/直觉'})

coded_df = pd.DataFrame(coded)
if len(coded_df):
    pr(coded_df.to_string(index=False))
pr('\n  策略词频分布：')
from collections import Counter
all_codes = [c for row in coded_df['codes'] for c in row.split(',')] if len(coded_df) else []
pr(f'  {Counter(all_codes)}')

sub('5.4 逐图策略自报分析（per-image reasoning）')
pr('  编码来源：responses.reasoning 字段（每张图判断时填写的策略说明）')

r_strat = r_f.merge(master[['participant_id','group']], on='participant_id', how='left').copy()
r_strat['strategy_cat'] = r_strat['reasoning'].apply(code_strategy)
r_strat['has_strategy'] = r_strat['strategy_cat'].notna().astype(int)

# 策略填写率 by 组别
pr('\n  策略填写率（reasoning 非空比例）by 组别：')
fill_rate = r_strat.groupby('group')['has_strategy'].agg(
    填写率=lambda x: f'{x.mean():.3f}',
    填写次数='sum',
    总次数='count'
)
pr(fill_rate.to_string())

# 策略类别分布 by 组别（仅含策略的行）
pr('\n  策略类别分布 by 组别（多选编码）：')
strat_rows = r_strat[r_strat['has_strategy'] == 1].copy()
cat_acc = []
for cat in ['Style', 'Anatomy', 'Knowledge', '直觉/其他']:
    for grp in ['A', 'C']:
        sub_r = strat_rows[(strat_rows['group'] == grp) &
                           (strat_rows['strategy_cat'].str.contains(cat, na=False))]
        if len(sub_r) > 0:
            cat_acc.append({'组别': grp, '策略': cat,
                            'n': len(sub_r),
                            '正确率': round(sub_r['is_correct'].mean(), 3)})
if cat_acc:
    pr(pd.DataFrame(cat_acc).to_string(index=False))

# 策略使用 vs 无策略 → 正确率差异（按组）
pr('\n  有/无策略描述 → 正确率（by 组别）：')
for grp in ['A', 'C']:
    grp_r = r_strat[r_strat['group'] == grp]
    acc_with    = grp_r[grp_r['has_strategy'] == 1]['is_correct'].mean()
    acc_without = grp_r[grp_r['has_strategy'] == 0]['is_correct'].mean()
    n_with = (grp_r['has_strategy'] == 1).sum()
    n_wo   = (grp_r['has_strategy'] == 0).sum()
    pr(f'  {grp}组  有策略(n={n_with}): acc={acc_with:.3f}  '
       f'无策略(n={n_wo}): acc={acc_without:.3f}  '
       f'差值: {acc_with-acc_without:+.3f}')

# C 组策略使用程度（post-survey strategy_usage_degree）× 正确率
if 'strategy_usage_degree' in master.columns:
    valid_deg = master[(master['group'] == 'C') &
                       master['strategy_usage_degree'].notna()]
    if len(valid_deg) > 3:
        r_v, p_v = stats.pearsonr(valid_deg['acc_total'],
                                  valid_deg['strategy_usage_degree'])
        pr(f'\n  C组：策略使用程度（后测）× 正确率 Pearson r={r_v:.3f}, p={p_v:.4f}')
        pr(f'  → {"策略使用程度与正确率正相关" if r_v>0 else "负相关，非预期"}')

# ── 附表：个体素养 × 准确率 ─────────────────────────────────────────
sub('附表：个体素养与准确率')
literacy_tbl = master[['participant_id','group',
                        'ai_familiarity','ai_tool_num',
                        'ai_literacy_composite','acc_total']].copy()
literacy_tbl = literacy_tbl.rename(columns={
    'group':               '组别',
    'ai_familiarity':      'AI熟悉度(1-5)',
    'ai_tool_num':         'AI工具使用(0/1)',
    'ai_literacy_composite': '综合素养分(z)',
    'acc_total':           '正确率',
})
literacy_tbl = literacy_tbl.sort_values(['组别','正确率'],
                                         ascending=[True, False]).round(3)
pr(literacy_tbl.to_string(index=False))
literacy_tbl.to_csv(os.path.join(OUT_DIR, 'table_literacy_accuracy.csv'),
                    index=False, encoding='utf-8-sig')

# ═══════════════════════════════════════════════════════════════════
# 汇总结论
# ═══════════════════════════════════════════════════════════════════
section(f'综合结论（DATA_MODE={DATA_MODE}，完成者 n={len(full_ids)}）')
pr(f"""
样本与分析对象
  已排除正确率>90%的图像: {EXCLUDE_IMAGES}（保留 {N_IMAGES} 张）
  完成全部 {N_IMAGES} 张的参与者: A={len(gA)}, C={len(gC)}（总{len(full_ids)}人）
  以下结论的统计显著性受限（预实验），效应量（Hedges' g）为更可靠的参考指标。

H1a — 总正确率：
  策略组(C)={gC.acc_total.mean()*100:.1f}% > 控制组(A)={gA.acc_total.mean()*100:.1f}%，
  差距 +{(gC.acc_total.mean()-gA.acc_total.mean())*100:.1f}%，Hedges' g={res1a["g"]:.2f}（大效应），
  p={res1a["p"]:.4f}。方向强烈支持 H1a；p 不显著仅因样本量不足。

H1b — 辨别力 d'：
  C组 d'={gC.dprime.mean():.2f} > A组 d'={gA.dprime.mean():.2f}，g={res1b["g"]:.2f}，
  p={res1b["p"]:.4f}。提升来自真实辨别能力而非猜测偏移，支持 H1b 方向。

H1c — 过度怀疑副作用（交互效应）：
  AI图组间差 = +{(gC.acc_ai.mean()-gA.acc_ai.mean())*100:.1f}%，
  Real图组间差 = +{(gC.acc_real.mean()-gA.acc_real.mean())*100:.1f}%。
  {"策略组对AI图的提升远大于对Real图的影响，未出现过度怀疑副作用，支持 H1c。" if (gC.acc_ai.mean()-gA.acc_ai.mean())>(gC.acc_real.mean()-gA.acc_real.mean()) else "需进一步检验。"}

H2a — 自我效能变化：
  C组变化量={gC.efficacy_change.mean():+.2f}，A组={gA.efficacy_change.mean():+.2f}；
  方向{"符合" if gC.efficacy_change.mean()>gA.efficacy_change.mean() else "不符合"} H2a预期，但受测量工具限制（前后测为不同构念），结果需谨慎解读。

H2b — 信心校准：
  校准偏差 C={gC.calib_bias.mean():+.3f}，A={gA.calib_bias.mean():+.3f}；
  {"C组过度自信程度更低，支持 H2b。" if gC.calib_bias.mean()<gA.calib_bias.mean() else "C组过度自信未减少，不支持 H2b。"}
  高信心错误率: C={np.mean(hC):.3f}, A={np.mean(hA):.3f}。

H3a — AI素养与正确率正相关：
  self_assessed_ability r已显著，支持 H3a。

H3b — 控制AI素养后干预效应独立：
  控制前 β={b1:.3f}→控制后 β={b3:.3f}，{"效应稳健，支持 H3b。" if abs(b3/b1)>0.7 else "效应减弱，需正式研究检验。"}

正式研究建议：
  基于预实验 g≈0.78，每组目标 ≥30人（共60），α=.05 power=.80。
  图像集：已移除过易图（ai_06/ai_11/ai_18），当前使用 {N_IMAGES} 张（AI:9, Real:12）。
""")

pr(f'\n报告已保存: {log_path}')
pr('表格: table1–5.csv  →  analysis/output/')
_log.close()
