#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_final_data_1.py
─────────────────────────────────────────────────────────────────────────────
将 final_data/ 与 data/participants_combined.csv 中的新参与者合并，
生成 final_data_1/（格式与 final_data/ 完全一致）。

规则：
  1. 若 participant_id 已存在于 final_data/ → 保留 final_data 版本，忽略 combined
  2. 新参与者须满足：completed=True, group ∈ {A,C}, 恰好有 21 张有效图像回答
  3. 通过注意力检测（attention_check_passed=True）
  4. mc_passed 计算规则与原始数据一致：
       - A 组：mc_passed=1（无 MC 要求）
       - C 组：mc_passed=1 当且仅当
           manipulation_check_read='yes' AND
           manipulation_check_strategies='yes'
  5. 仅保留 mc_passed=1 的参与者（与 final_data 已过滤惯例一致）

输出（analysis/final_data_1/）：
  participants.csv      同 final_data/participants.csv 列名
  responses.csv         同 final_data/responses.csv 列名
  post_survey.csv       同 final_data/post_survey.csv 列名
  interaction_logs.csv  同 final_data/interaction_logs.csv 列名

运行：
  python analysis/build_final_data_1.py
"""
import os, sys
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
FINAL_DIR = os.path.join(BASE_DIR, 'final_data')
DATA_DIR  = os.path.join(BASE_DIR, 'data')
OUT_DIR   = os.path.join(BASE_DIR, 'final_data_1')

# ─── 有效图像集（与 formal_analysis.py 中 IMAGE_META 一致）────────────────
VALID_IMGS = {
    'ai_01','ai_02','ai_04','ai_08','ai_09','ai_13','ai_15','ai_16','ai_19',
    'real_01','real_02','real_03','real_04','real_05','real_06',
    'real_11','real_12','real_14','real_15','real_16','real_20',
}
AI_IMGS   = {x for x in VALID_IMGS if x.startswith('ai_')}
REAL_IMGS = {x for x in VALID_IMGS if x.startswith('real_')}
N_IMAGES  = len(VALID_IMGS)   # 21

# ─── 映射表 ───────────────────────────────────────────────────────────────
GROUP_MAP  = {'A': 0, 'C': 1}
AGE_MAP    = {'18-24': 1, '25-34': 2, '35-44': 3, '45-54': 4}
GENDER_MAP = {'male': 0, 'female': 1}                   # prefer-not-to-say → NaN
EDU_MAP    = {'high-school': 1, 'some-college': 2,
              'bachelors': 3, 'masters': 4, 'doctorate': 5}
EDU_GRP    = {1: 1, 2: 1, 3: 2, 4: 3, 5: 3}            # 1=高中/大专 2=本科 3=硕博
FREQ_MAP   = {'never': 1, 'rarely': 2, 'sometimes': 3, 'often': 4, 'very-often': 5}
TOOL_MAP   = {'yes': 1, 'no': 0}
# 阅读了干预材料编码：0=no, 1=not_sure, 2=yes（与 final_data 一致）
MCR_MAP    = {'yes': 2, 'no': 0, 'not_sure': 1}

# ═══════════════════════════════════════════════════════════════════════════
# 1. 加载 final_data（基准，不可覆盖）
# ═══════════════════════════════════════════════════════════════════════════
fd_p  = pd.read_csv(os.path.join(FINAL_DIR, 'participants.csv'))
fd_r  = pd.read_csv(os.path.join(FINAL_DIR, 'responses.csv'))
fd_ps = pd.read_csv(os.path.join(FINAL_DIR, 'post_survey.csv'))
fd_lg = pd.read_csv(os.path.join(FINAL_DIR, 'interaction_logs.csv'))

fd_ids = set(fd_p['participant_id'])
print(f'[1] 现有 final_data 参与者: {len(fd_p)}')

# ═══════════════════════════════════════════════════════════════════════════
# 2. 加载 combined 数据
# ═══════════════════════════════════════════════════════════════════════════
p_comb  = pd.read_csv(os.path.join(DATA_DIR, 'participants_combined.csv'))
r_comb  = pd.read_csv(os.path.join(DATA_DIR, 'responses_combined.csv'))
ps_comb = pd.read_csv(os.path.join(DATA_DIR, 'post-survey_combined.csv'))
lg_comb = pd.read_csv(os.path.join(DATA_DIR, 'interaction-logs_combined.csv'))

# ═══════════════════════════════════════════════════════════════════════════
# 3. 筛选新候选参与者
# ═══════════════════════════════════════════════════════════════════════════
# 新参与者：不在 final_data、已完成、组别 A 或 C
new_cands = p_comb[
    ~p_comb['participant_id'].isin(fd_ids) &
    (p_comb['completed'] == True) &
    (p_comb['group'].isin(['A', 'C']))
].copy()
print(f'[2] 新候选（完成、A/C 组、不在 final_data）: {len(new_cands)}')

# 必须恰好有 21 张有效图像作答
r_valid = r_comb[r_comb['image_id'].isin(VALID_IMGS)].copy()
resp_cnt = r_valid.groupby('participant_id')['image_id'].nunique()
full_pids = set(resp_cnt[resp_cnt == N_IMAGES].index)
new_cands = new_cands[new_cands['participant_id'].isin(full_pids)]
print(f'[3] 具有完整 21 张有效作答: {len(new_cands)}')

new_pids = set(new_cands['participant_id'])

# ═══════════════════════════════════════════════════════════════════════════
# 4. 计算准确率
# ═══════════════════════════════════════════════════════════════════════════
r_new = r_valid[r_valid['participant_id'].isin(new_pids)].copy()
acc_total = r_new.groupby('participant_id')['is_correct'].mean()
acc_ai    = r_new[r_new['image_id'].isin(AI_IMGS)].groupby('participant_id')['is_correct'].mean()
acc_real  = r_new[r_new['image_id'].isin(REAL_IMGS)].groupby('participant_id')['is_correct'].mean()

# ═══════════════════════════════════════════════════════════════════════════
# 5. 关联后测问卷
# ═══════════════════════════════════════════════════════════════════════════
ps_new = (ps_comb[ps_comb['participant_id'].isin(new_pids)]
          .drop_duplicates('participant_id')
          .set_index('participant_id'))

# ═══════════════════════════════════════════════════════════════════════════
# 6. 构建新参与者行（中文列名，与 final_data 完全一致）
# ═══════════════════════════════════════════════════════════════════════════
new_rows = []
for _, row in new_cands.iterrows():
    pid  = row['participant_id']
    ps   = ps_new.loc[pid] if pid in ps_new.index else pd.Series(dtype=object)

    group_num  = GROUP_MAP.get(row['group'], np.nan)
    # _synth=False → real(0)；_synth=NaN（合成数据不带标记）→ synth(1)
    source_num = 0 if pd.notna(row.get('_synth')) and row['_synth'] == False else 1

    gender_num = GENDER_MAP.get(row.get('gender'), np.nan)
    age_num    = AGE_MAP.get(row.get('age'), np.nan)
    edu_ord_v  = EDU_MAP.get(row.get('education'), np.nan)
    edu_grp_v  = EDU_GRP.get(int(edu_ord_v), np.nan) if pd.notna(edu_ord_v) else np.nan
    ai_exp_num = FREQ_MAP.get(row.get('ai_exposure_freq'), np.nan)
    ai_tool_v  = TOOL_MAP.get(row.get('ai_tool_usage'), np.nan)
    intv_dur   = float(row.get('intervention_duration_s') or 0)

    mc_read_raw  = ps.get('manipulation_check_read')  if not ps.empty else None
    mc_strat_raw = ps.get('manipulation_check_strategies') if not ps.empty else None
    attn_passed  = bool(ps.get('attention_check_passed', False)) if not ps.empty else False
    self_perf    = ps.get('self_performance')    if not ps.empty else np.nan
    strat_deg    = ps.get('strategy_usage_degree') if not ps.empty else np.nan

    mc_read_v  = MCR_MAP.get(mc_read_raw, np.nan)
    # 策略列表：'yes'→1, 'no'→0, NaN→NaN（A 组无需填写）
    if pd.isna(mc_strat_raw):
        mc_strat_v = np.nan
    elif mc_strat_raw == 'yes':
        mc_strat_v = 1.0
    else:
        mc_strat_v = 0.0  # 'no' 或其他非预期值

    # mc_passed 判断
    if not attn_passed:
        mc_passed = 0
    elif row['group'] == 'A':
        mc_passed = 1
    else:  # C 组：必须两项均为 'yes'
        mc_passed = 1 if (mc_read_raw == 'yes' and mc_strat_raw == 'yes') else 0

    new_rows.append({
        'participant_id':   pid,
        '组别':             group_num,
        '来源':             source_num,
        'AI熟悉度':         row.get('ai_familiarity', np.nan),
        '前测自评能力':     row.get('self_assessed_ability', np.nan),
        'AI使用频率(1-5)':  ai_exp_num,
        '整体正确率':       acc_total.get(pid, np.nan),
        'AI图正确率':       acc_ai.get(pid, np.nan),
        '真实图正确率':     acc_real.get(pid, np.nan),
        '后测表现自评':     self_perf,
        'delete':           np.nan,
        '性别':             gender_num,
        '年龄段':           age_num,
        '学历':             edu_ord_v,
        'AI工具使用经验':   ai_tool_v,
        '干预停留时间(秒)': intv_dur,
        '阅读了干预材料':   mc_read_v,
        '阅读了策略列表':   mc_strat_v,
        '策略使用程度':     strat_deg if pd.notna(strat_deg) else np.nan,
        '注意力检测通过':   int(attn_passed),
        'mc_passed':        mc_passed,
        '学历分组':         edu_grp_v,
    })

new_df = pd.DataFrame(new_rows)
print(f'[4] 构建新参与者行: {len(new_df)}')

# 统计过滤情况
n_attn_fail = (new_df['注意力检测通过'] == 0).sum()
n_mc_fail   = ((new_df['注意力检测通过'] == 1) & (new_df['mc_passed'] == 0)).sum()
print(f'    注意力检测失败: {n_attn_fail}')
print(f'    MC 未通过 (C 组): {n_mc_fail}')

# 仅保留 mc_passed（与 final_data 惯例一致）
new_df_passed = new_df[new_df['mc_passed'] == 1].copy()
print(f'[5] mc_passed 过滤后: {len(new_df_passed)}')

# 打印新参与者组别来源分布
real_col = '来源'
grp_col  = '组别'
real_new = (new_df_passed[real_col] == 0).sum()
synth_new = (new_df_passed[real_col] == 1).sum()
a_new = (new_df_passed[grp_col] == 0).sum()
c_new = (new_df_passed[grp_col] == 1).sum()
print(f'    新增: A组={a_new}, C组={c_new} | real={real_new}, synth={synth_new}')

# ═══════════════════════════════════════════════════════════════════════════
# 7. 合并
# ═══════════════════════════════════════════════════════════════════════════
participants_1 = pd.concat([fd_p, new_df_passed], ignore_index=True)
passed_pids_1  = set(participants_1['participant_id'])
new_passed_pids = passed_pids_1 - fd_ids

# responses（final_data 的 + 新通过参与者的有效图像作答）
r_new_pass  = r_new[r_new['participant_id'].isin(new_passed_pids)].copy()
responses_1 = pd.concat([fd_r, r_new_pass], ignore_index=True)

# post_survey（final_data 的 + 新通过参与者的）
ps_raw_new  = ps_comb[ps_comb['participant_id'].isin(new_passed_pids)].drop_duplicates('participant_id')
post_survey_1 = pd.concat([fd_ps, ps_raw_new], ignore_index=True)

# interaction_logs（final_data 的 + 新通过参与者的）
lg_new      = lg_comb[lg_comb['participant_id'].isin(new_passed_pids)].copy()
logs_1      = pd.concat([fd_lg, lg_new], ignore_index=True)

# ═══════════════════════════════════════════════════════════════════════════
# 8. 写出
# ═══════════════════════════════════════════════════════════════════════════
os.makedirs(OUT_DIR, exist_ok=True)
participants_1.to_csv(os.path.join(OUT_DIR, 'participants.csv'),
                      index=False, encoding='utf-8-sig')
responses_1.to_csv(os.path.join(OUT_DIR, 'responses.csv'),
                   index=False, encoding='utf-8-sig')
post_survey_1.to_csv(os.path.join(OUT_DIR, 'post_survey.csv'),
                     index=False, encoding='utf-8-sig')
logs_1.to_csv(os.path.join(OUT_DIR, 'interaction_logs.csv'),
              index=False, encoding='utf-8-sig')

print()
print('─── final_data_1/ 汇总 ─────────────────────────────────────────────')
print(f'  participants.csv    : {len(participants_1)} 行'
      f'  （原 {len(fd_p)}，新增 {len(new_df_passed)}）')
print(f'  responses.csv       : {len(responses_1)} 行'
      f'  （原 {len(fd_r)}，新增 {len(r_new_pass)}）')
print(f'  post_survey.csv     : {len(post_survey_1)} 行'
      f'  （原 {len(fd_ps)}，新增 {len(ps_raw_new)}）')
print(f'  interaction_logs.csv: {len(logs_1)} 行'
      f'  （原 {len(fd_lg)}，新增 {len(lg_new)}）')
print()

# 组别 × 来源 分布（新数据集）
cross = participants_1.groupby(['组别','来源']).size().reset_index(name='n')
cross['组别_lbl'] = cross['组别'].map({0:'A(对照)', 1:'C(实验)'})
cross['来源_lbl'] = cross['来源'].map({0:'real', 1:'synth'})
print('  组别 × 来源:')
for _, r2 in cross.iterrows():
    print(f'    {r2["组别_lbl"]:10s} × {r2["来源_lbl"]:6s} = {r2["n"]}')
total_r = (participants_1['来源']==0).sum()
total_s = (participants_1['来源']==1).sum()
print(f'  total: A={len(participants_1[participants_1["组别"]==0])}, '
      f'C={len(participants_1[participants_1["组别"]==1])}'
      f'  | real={total_r}, synth={total_s}'
      f'  | 合计={len(participants_1)}')
print()
print(f'✓ 文件已写入 {OUT_DIR}')
