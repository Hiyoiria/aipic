#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
计算每张图片的正确率（基于完成全部图片的参与者）
输出：analysis/output/image_accuracy.csv
"""
import sys
import os
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
OUT_DIR  = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(OUT_DIR, exist_ok=True)

N_IMAGES = 24  # 视为"完成"所需的最少图片数

# ── 读取数据 ────────────────────────────────────────────────────────────────
r = pd.read_csv(os.path.join(DATA_DIR, 'responses.csv'))

# ── 筛选完成全部图片的参与者 ────────────────────────────────────────────────
cnt = r.groupby('participant_id').size().reset_index(name='n')
full_ids = cnt[cnt['n'] >= N_IMAGES]['participant_id']
r_full = r[r['participant_id'].isin(full_ids)].copy()

n_participants = len(full_ids)
print(f"完成 {N_IMAGES} 张图的参与者: {n_participants} 人")

# ── 添加类别标签 ────────────────────────────────────────────────────────────
r_full['category'] = r_full['image_id'].apply(
    lambda x: 'AI' if str(x).startswith('ai_') else 'Real'
)

# ── 逐图统计 ────────────────────────────────────────────────────────────────
img_stats = (
    r_full.groupby(['image_id', 'category'])
    .agg(
        n_responses=('is_correct', 'count'),
        n_correct=('is_correct', 'sum'),
        accuracy=('is_correct', 'mean'),
    )
    .reset_index()
)
img_stats['accuracy_pct'] = (img_stats['accuracy'] * 100).round(1)
img_stats = img_stats.sort_values(['category', 'accuracy'], ascending=[True, False])

# ── 标记难度区间 ────────────────────────────────────────────────────────────
def difficulty(acc):
    if acc >= 0.85:
        return 'too_easy'
    elif acc <= 0.30:
        return 'too_hard'
    else:
        return 'moderate'

img_stats['difficulty'] = img_stats['accuracy'].apply(difficulty)

# ── 打印结果 ────────────────────────────────────────────────────────────────
print(f"\n{'image_id':<12} {'category':<8} {'n':>4} {'correct':>8} {'accuracy%':>10} {'difficulty'}")
print('-' * 58)
for _, row in img_stats.iterrows():
    print(f"{row['image_id']:<12} {row['category']:<8} {row['n_responses']:>4} "
          f"{int(row['n_correct']):>8} {row['accuracy_pct']:>9}% {row['difficulty']}")

# ── 汇总 ────────────────────────────────────────────────────────────────────
print('\n── 难度分布 ──')
print(img_stats['difficulty'].value_counts().to_string())

print('\n── 按类别平均正确率 ──')
print(img_stats.groupby('category')['accuracy_pct'].describe().round(1).to_string())

too_easy = img_stats[img_stats['difficulty'] == 'too_easy']['image_id'].tolist()
too_hard = img_stats[img_stats['difficulty'] == 'too_hard']['image_id'].tolist()
moderate = img_stats[img_stats['difficulty'] == 'moderate']['image_id'].tolist()

print(f'\n太简单 (≥85%): {too_easy}')
print(f'太难   (≤30%): {too_hard}')
print(f'适中   (31-84%): {moderate}')

# ── 保存 ────────────────────────────────────────────────────────────────────
out_path = os.path.join(OUT_DIR, 'image_accuracy.csv')
img_stats.to_csv(out_path, index=False, encoding='utf-8-sig')
print(f'\n已保存至: {out_path}')
