#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
OUT_DIR  = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(OUT_DIR, exist_ok=True)

# ── Load data ──────────────────────────────────────────────────────────────
p  = pd.read_csv(os.path.join(DATA_DIR, 'participants.csv'))
r  = pd.read_csv(os.path.join(DATA_DIR, 'responses.csv'))
ps = pd.read_csv(os.path.join(DATA_DIR, 'post-survey.csv'))

print(f"participants: {len(p)}, responses: {len(r)}, post-surveys: {len(ps)}")

# ── Filter: completed all 24 images ───────────────────────────────────────
resp_count = r.groupby('participant_id').size().reset_index(name='n_responses')
full24_ids = resp_count[resp_count['n_responses'] == 24]['participant_id']
print(f"Completed 24 images: {len(full24_ids)} participants")

r24 = r[r['participant_id'].isin(full24_ids)].copy()

# ── Accuracy ───────────────────────────────────────────────────────────────
# Correct: response matches truth
# image_id starts with 'ai_' → label=AI; starts with 'real_' → label=Real
# response field: what user chose (check column names first)
print("\nResponse columns:", r24.columns.tolist())
print(r24.head(2).to_string())

# Determine correct answer column
# Typical: response column is 'response' or 'answer'; truth derived from image_id
if 'image_id' in r24.columns:
    r24['true_label'] = r24['image_id'].apply(
        lambda x: 'ai' if str(x).startswith('ai_') else 'real'
    )

# Use is_correct column (already computed by server)
if 'is_correct' in r24.columns:
    r24['correct'] = r24['is_correct'].astype(bool).astype(int)
    acc = r24.groupby('participant_id')['correct'].mean().reset_index()
    acc.columns = ['participant_id', 'accuracy']
    print(f"\nUsing 'is_correct' column for accuracy")
else:
    # Fallback: derive from judgment vs correct_answer
    resp_col = 'judgment' if 'judgment' in r24.columns else None
    truth_col = 'correct_answer' if 'correct_answer' in r24.columns else None
    if resp_col and truth_col:
        r24['correct'] = (r24[resp_col] == r24[truth_col]).astype(int)
        acc = r24.groupby('participant_id')['correct'].mean().reset_index()
        acc.columns = ['participant_id', 'accuracy']
    else:
        print("WARNING: Could not compute accuracy")
        acc = pd.DataFrame({'participant_id': full24_ids, 'accuracy': float('nan')})

# ── Merge participant info ─────────────────────────────────────────────────
print("\nParticipant columns:", p.columns.tolist())

summary = full24_ids.to_frame().merge(acc, on='participant_id', how='left')
summary = summary.merge(p, on='participant_id', how='left')

# ── Merge post-survey ──────────────────────────────────────────────────────
print("\nPost-survey columns:", ps.columns.tolist())
ps_id_col = 'participant_id' if 'participant_id' in ps.columns else ps.columns[0]
summary = summary.merge(ps, left_on='participant_id', right_on=ps_id_col, how='left')

# ── Output ─────────────────────────────────────────────────────────────────
out_path = os.path.join(OUT_DIR, 'participant_summary.csv')
summary.to_csv(out_path, index=False, encoding='utf-8-sig')
print(f"\nSaved to: {out_path}")
print(f"Total rows: {len(summary)}")
print("\n--- Summary preview ---")
# Show key columns
key_cols = ['participant_id']
for c in ['group', 'condition', 'accuracy', 'pre_score', 'post_score',
          'preScore', 'postScore', 'pre_survey', 'post_survey',
          'created_at', 'createdAt']:
    if c in summary.columns:
        key_cols.append(c)
print(summary[key_cols].to_string(index=False))

# Per-group accuracy
if 'group' in summary.columns:
    print("\n--- Accuracy by group ---")
    print(summary.groupby('group')['accuracy'].describe().to_string())
elif 'condition' in summary.columns:
    print("\n--- Accuracy by condition ---")
    print(summary.groupby('condition')['accuracy'].describe().to_string())
