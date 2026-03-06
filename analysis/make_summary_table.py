#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_summary_table.py
生成被试汇总表（含 participant_id，供手动筛选后追溯数据）
输出：analysis/output/participant_summary_full.csv
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd, numpy as np, warnings
from scipy.stats import zscore
warnings.filterwarnings('ignore')

DATA_DIR = 'analysis/data'
AI_IDS   = {'ai_01','ai_02','ai_04','ai_08','ai_09','ai_13','ai_15','ai_16','ai_19'}
REAL_IDS = {'real_01','real_02','real_03','real_04','real_05','real_06',
            'real_11','real_12','real_14','real_15','real_16','real_20'}
VALID = AI_IDS | REAL_IDS

# ── 加载 ──────────────────────────────────────────────────────────
p_real  = pd.read_csv(f'{DATA_DIR}/participants.csv')
p_synth = pd.read_csv(f'{DATA_DIR}/participants_synth.csv')
p_comb  = pd.read_csv(f'{DATA_DIR}/participants_combined.csv')
r_comb  = pd.read_csv(f'{DATA_DIR}/responses_combined.csv')
ps_comb = pd.read_csv(f'{DATA_DIR}/post-survey_combined.csv')

# 来源标记
real_ids  = set(p_real['participant_id'])
synth_ids = set(p_synth['participant_id'])
p_comb['source'] = p_comb['participant_id'].apply(
    lambda x: 'real' if x in real_ids else 'synth')

# ── 过滤：A/C 组，完成 21 张有效图像 ─────────────────────────────
p_comb = p_comb[p_comb['group'].isin(['A', 'C'])].copy()
r = r_comb[r_comb['image_id'].isin(VALID)].copy()
cnt = r.groupby('participant_id').size().reset_index(name='n')
full_ids = set(cnt[cnt['n'] >= 21]['participant_id']) & set(p_comb['participant_id'])

# ── 过滤：通过注意力检测（排除 == False，保留 True 和 NaN）────────
ps = ps_comb[ps_comb['participant_id'].isin(full_ids)].copy()
p_tmp = p_comb[p_comb['participant_id'].isin(full_ids)].merge(
    ps[['participant_id', 'attention_check_passed']], on='participant_id', how='left')
p_final = p_tmp[p_tmp['attention_check_passed'] != False].copy()
final_ids = set(p_final['participant_id'])

# ── 前测数据完整性标记 ────────────────────────────────────────────
# 0 值表示未填写前测问卷（非缺失，而是默认值）
p_final = p_final.copy()
p_final['presurvey_incomplete'] = (
    (p_final['ai_familiarity'] == 0) |
    (p_final['self_assessed_ability'] == 0) |
    (p_final['ai_exposure_freq'].isna())
).astype(int)

n_incomplete = p_final['presurvey_incomplete'].sum()
if n_incomplete > 0:
    print(f'警告：{n_incomplete} 人前测数据不完整（ai_familiarity=0 或问卷未填写），已标记 presurvey_incomplete=1')

# ── 计算准确率 ────────────────────────────────────────────────────
r_f = r[r['participant_id'].isin(final_ids)].copy()
r_f['image_type'] = r_f['image_id'].apply(lambda x: 'AI' if x in AI_IDS else 'Real')
acc_total = r_f.groupby('participant_id')['is_correct'].mean().reset_index(name='整体正确率')
acc_ai    = r_f[r_f['image_type'] == 'AI'].groupby('participant_id')['is_correct'].mean().reset_index(name='AI图正确率')
acc_real  = r_f[r_f['image_type'] == 'Real'].groupby('participant_id')['is_correct'].mean().reset_index(name='真实图正确率')

# ── 后测自评 ──────────────────────────────────────────────────────
ps_sel = ps_comb[ps_comb['participant_id'].isin(final_ids)][
    ['participant_id', 'self_performance']].copy()

# ── ai_exposure_freq → 数值（1–5）────────────────────────────────
_freq_map = {'never':1,'rarely':2,'sometimes':3,'often':4,'very-often':5}
p_final['ai_exposure_num'] = p_final['ai_exposure_freq'].map(_freq_map)

# ── AI 素养综合分（仅前测完整者有效）────────────────────────────
# 公式：(z_ai_familiarity + z_ai_exposure_num + z_ai_tool_num) / 3
p_final['ai_literacy_composite'] = np.nan
_v = p_final[p_final['presurvey_incomplete'] == 0].dropna(
    subset=['ai_familiarity', 'ai_exposure_num', 'ai_tool_usage'])
if len(_v) > 1:
    z_fam  = zscore(_v['ai_familiarity'].astype(float).values)
    z_freq = zscore(_v['ai_exposure_num'].astype(float).values)
    z_tool = zscore((_v['ai_tool_usage'] == 'yes').astype(float).values)
    p_final.loc[_v.index, 'ai_literacy_composite'] = (z_fam + z_freq + z_tool) / 3

# ── 组装 & 重命名 ─────────────────────────────────────────────────
base = p_final[['participant_id', 'group', 'source',
                'ai_familiarity', 'self_assessed_ability',
                'ai_exposure_num', 'ai_literacy_composite',
                'presurvey_incomplete']].rename(columns={
    'group':                 '组别',
    'source':                '来源',
    'ai_familiarity':        'AI熟悉度',
    'self_assessed_ability': '前测自评能力',
    'ai_exposure_num':       'AI使用频率(1-5)',
    'ai_literacy_composite': 'AI素养综合分',
})

master = (base
          .merge(acc_total, on='participant_id', how='left')
          .merge(acc_ai,    on='participant_id', how='left')
          .merge(acc_real,  on='participant_id', how='left')
          .merge(ps_sel.rename(columns={'self_performance': '后测表现自评'}),
                 on='participant_id', how='left')
          .sort_values(['来源', '组别']).reset_index(drop=True))

for col in ['AI素养综合分', '整体正确率', 'AI图正确率', '真实图正确率']:
    master[col] = master[col].round(3)

# participant_id 保留在第一列
cols = ['participant_id'] + [c for c in master.columns if c != 'participant_id']
master = master[cols]

out = 'analysis/output/participant_summary_full.csv'
master.to_csv(out, index=False, encoding='utf-8-sig')

print(f'总计：{len(master)} 人')
print(master.groupby(['来源', '组别']).size().reset_index(name='n').to_string(index=False))
print(f'\n前测不完整人数：{master["presurvey_incomplete"].sum()}')
print(f'已保存 -> {out}')
