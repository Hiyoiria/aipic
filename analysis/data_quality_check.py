#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data_quality_check.py  ─ 通用数据质量检查脚本
──────────────────────────────────────────────
功能：
  1. 找出所有完成 21 道题（有效图像白名单）的被试
  2. manipulation_fail = 1  ← 未通过注意力检测
  3. presurvey_incomplete = 1  ← 前测问卷未填写（ai_familiarity=0 等）
  4. 输出完整的质检表（含 participant_id，供人工核查）

输出：analysis/output/data_quality_report.csv
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd, numpy as np, warnings
warnings.filterwarnings('ignore')

DATA_DIR = 'analysis/data'

# ── 有效图像白名单（修改此处即可适配新版实验）────────────────────
VALID_IMAGES = {
    'ai_01','ai_02','ai_04','ai_08','ai_09','ai_13','ai_15','ai_16','ai_19',
    'real_01','real_02','real_03','real_04','real_05','real_06',
    'real_11','real_12','real_14','real_15','real_16','real_20',
}
MIN_IMAGES = 21   # 至少完成几张

# ── 加载数据 ──────────────────────────────────────────────────────
print('正在加载数据...')
p  = pd.read_csv(f'{DATA_DIR}/participants_combined.csv')
r  = pd.read_csv(f'{DATA_DIR}/responses_combined.csv')
ps = pd.read_csv(f'{DATA_DIR}/post-survey_combined.csv')

n_raw = len(p)
print(f'原始被试总数：{n_raw}')

# ── Step 1：只保留 A/C 组 ─────────────────────────────────────────
p = p[p['group'].isin(['A', 'C'])].copy()
print(f'A/C 组被试：{len(p)}')

# ── Step 2：白名单过滤回答，统计每人完成张数 ──────────────────────
r_valid = r[r['image_id'].isin(VALID_IMAGES)].copy()
img_cnt = r_valid.groupby('participant_id').size().reset_index(name='n_completed')

# ── Step 3：合并，标记完成情况 ────────────────────────────────────
df = p.merge(img_cnt, on='participant_id', how='left')
df['n_completed'] = df['n_completed'].fillna(0).astype(int)
df['completed_21'] = (df['n_completed'] >= MIN_IMAGES).astype(int)

# ── Step 4：合并注意力检测结果 ────────────────────────────────────
ps_sel = ps[['participant_id', 'attention_check_passed',
             'manipulation_check_read', 'self_performance']].copy()
df = df.merge(ps_sel, on='participant_id', how='left')

# manipulation_fail：明确 == False 才标 1；未参加后测（NaN）标 0
df['manipulation_fail'] = (df['attention_check_passed'] == False).astype(int)

# ── Step 5：前测数据完整性 ────────────────────────────────────────
# 注册后未填写问卷者：ai_familiarity = 0，各字段为 NaN
df['presurvey_incomplete'] = (
    (df['ai_familiarity'] == 0) |
    (df['self_assessed_ability'] == 0) |
    (df['ai_exposure_freq'].isna())
).astype(int)

# ── Step 6：计算准确率（仅完成21张者）────────────────────────────
finished_ids = set(df[df['completed_21'] == 1]['participant_id'])
r_f = r_valid[r_valid['participant_id'].isin(finished_ids)].copy()

AI_IDS = {'ai_01','ai_02','ai_04','ai_08','ai_09','ai_13','ai_15','ai_16','ai_19'}
r_f['image_type'] = r_f['image_id'].apply(lambda x: 'AI' if x in AI_IDS else 'Real')

acc_total = r_f.groupby('participant_id')['is_correct'].mean().reset_index(name='acc_total')
acc_ai    = r_f[r_f['image_type'] == 'AI'].groupby('participant_id')['is_correct'].mean().reset_index(name='acc_ai')
acc_real  = r_f[r_f['image_type'] == 'Real'].groupby('participant_id')['is_correct'].mean().reset_index(name='acc_real')

df = (df.merge(acc_total, on='participant_id', how='left')
        .merge(acc_ai,    on='participant_id', how='left')
        .merge(acc_real,  on='participant_id', how='left'))

# ── 输出列选择与排序 ──────────────────────────────────────────────
output_cols = [
    'participant_id', 'group',
    'completed_21', 'n_completed',
    'manipulation_fail', 'attention_check_passed',
    'presurvey_incomplete',
    'ai_familiarity', 'self_assessed_ability', 'ai_exposure_freq', 'ai_tool_usage',
    'gender', 'age', 'education',
    'acc_total', 'acc_ai', 'acc_real',
    'self_performance',
    'manipulation_check_read',
    'intervention_duration_s',
    'completed',
]
output_cols = [c for c in output_cols if c in df.columns]
out_df = df[output_cols].sort_values(
    ['completed_21', 'manipulation_fail', 'presurvey_incomplete'],
    ascending=[False, True, True]
).reset_index(drop=True)

for col in ['acc_total', 'acc_ai', 'acc_real']:
    if col in out_df.columns:
        out_df[col] = out_df[col].round(3)

# ── 打印汇总 ──────────────────────────────────────────────────────
print()
print('=== 质检摘要 ===')
c21  = df[df['completed_21'] == 1]
print(f'完成 {MIN_IMAGES} 张：{len(c21)} 人')
print(f'  ├─ 通过注意力检测：{(c21["manipulation_fail"] == 0).sum()} 人')
print(f'  └─ 未通过（manipulation_fail=1）：{(c21["manipulation_fail"] == 1).sum()} 人')
print(f'前测不完整（presurvey_incomplete=1）：{df["presurvey_incomplete"].sum()} 人（含未完成者）')
print(f'  其中完成21张但前测不完整：{c21["presurvey_incomplete"].sum()} 人')
print()
print('按组分布（完成21张）：')
print(c21.groupby(['group', 'manipulation_fail']).size().reset_index(name='n').to_string(index=False))

out_path = 'analysis/output/data_quality_report.csv'
out_df.to_csv(out_path, index=False, encoding='utf-8-sig')
print(f'\n已保存 -> {out_path}  （{len(out_df)} 行）')
