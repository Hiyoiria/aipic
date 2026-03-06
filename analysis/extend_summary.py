#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extend_summary.py
──────────────────────────────────────────────────────────────
在 participant_summary_full.csv 基础上追加前后测变量，
已有列（含 delete）原样保留，不重新计算。

输出：analysis/output/participant_summary_extended.csv
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
import warnings
warnings.filterwarnings('ignore')

SUMMARY = 'analysis/output/participant_summary_full.csv'
PART    = 'analysis/data/participants_combined.csv'
PS      = 'analysis/data/post-survey_combined.csv'
OUT     = 'analysis/output/participant_summary_extended.csv'

# ── 1. 读入旧表（已有列原样保留，含 delete）──────────────────────
base = pd.read_csv(SUMMARY)
print(f'旧表：{len(base)} 行，{len(base.columns)} 列')

# ── 2. 前测追加列 ────────────────────────────────────────────────
p_new_cols = ['participant_id', 'gender', 'age', 'education',
              'ai_tool_usage', 'intervention_duration_s']
p_extra = pd.read_csv(PART)[p_new_cols].rename(columns={
    'gender':                '性别',
    'age':                   '年龄段',
    'education':             '学历',
    'ai_tool_usage':         'AI工具使用经验',
    'intervention_duration_s': '干预停留时间(秒)',
})

# ── 3. 后测追加列 ────────────────────────────────────────────────
ps_new_cols = ['participant_id', 'manipulation_check_read',
               'manipulation_check_strategies', 'strategy_usage_degree',
               'attention_check_passed']
ps_extra = pd.read_csv(PS)[ps_new_cols].rename(columns={
    'manipulation_check_read':       '阅读了干预材料',
    'manipulation_check_strategies': '阅读了策略列表',
    'strategy_usage_degree':         '策略使用程度',
    'attention_check_passed':        '注意力检测通过',
})

# ── 4. 合并：旧表 → 前测 → 后测 ──────────────────────────────────
df = (base
      .merge(p_extra,  on='participant_id', how='left')
      .merge(ps_extra, on='participant_id', how='left'))

# ── 5. 列排序：原有列不动，新列按逻辑分组追加 ────────────────────
original_cols = list(base.columns)          # 包含 delete
new_demo_cols = ['性别', '年龄段', '学历', 'AI工具使用经验', '干预停留时间(秒)']
new_post_cols = ['阅读了干预材料', '阅读了策略列表', '策略使用程度', '注意力检测通过']

# 仅保留实际存在的新列
new_demo_cols = [c for c in new_demo_cols if c in df.columns]
new_post_cols = [c for c in new_post_cols if c in df.columns]

final_cols = original_cols + new_demo_cols + new_post_cols
df = df[final_cols]

# ── 6. 保存 ──────────────────────────────────────────────────────
df.to_csv(OUT, index=False, encoding='utf-8-sig')
print(f'新表：{len(df)} 行，{len(df.columns)} 列')
print(f'列名：{df.columns.tolist()}')
print(f'\n已保存 -> {OUT}')
