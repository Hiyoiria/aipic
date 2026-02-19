#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 2: Study 2 数据分析脚本
前置: 先运行 fetch_data.py 下载数据

运行方式:
    python analysis/analyze.py

输出: analysis/output/ 目录下的统计报告和图表
"""

import os
import sys
import warnings
import pandas as pd
import numpy as np
from scipy import stats

sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')

# ─── Helpers ──────────────────────────────────────────────

def load(name):
    path = os.path.join(DATA_DIR, f'{name}.csv')
    if not os.path.exists(path):
        print(f"  [WARN] {path} not found, skipping.")
        return None
    df = pd.read_csv(path)
    print(f"  Loaded {name}: {len(df)} rows x {len(df.columns)} cols")
    return df


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def save_df(df, name):
    path = os.path.join(OUTPUT_DIR, f'{name}.csv')
    df.to_csv(path, index=False, encoding='utf-8-sig')
    print(f"  -> Saved {path}")


# ─── Main ─────────────────────────────────────────────────

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ── Load data ──
    section("1. Loading Data")
    participants = load('participants')
    responses = load('responses')
    post_survey = load('post-survey')
    interaction_logs = load('interaction-logs')

    if participants is None or responses is None:
        print("\nERROR: participants.csv and responses.csv are required.")
        print("Run fetch_data.py first.")
        return

    # ── Data Cleaning ──
    section("2. Data Cleaning")

    # Filter completed participants
    completed = participants[participants['completed'] == True].copy()
    print(f"  Total participants: {len(participants)}")
    print(f"  Completed: {len(completed)}")

    # Attention check filter (if post-survey available)
    if post_survey is not None and 'attention_check_passed' in post_survey.columns:
        failed_ids = post_survey[post_survey['attention_check_passed'] == False]['participant_id'].tolist()
        print(f"  Failed attention check: {len(failed_ids)}")
        valid = completed[~completed['participant_id'].isin(failed_ids)].copy()
    else:
        valid = completed.copy()
        failed_ids = []

    print(f"  Valid participants for analysis: {len(valid)}")
    valid_ids = set(valid['participant_id'].tolist())

    # Filter responses to valid participants
    resp = responses[responses['participant_id'].isin(valid_ids)].copy()
    print(f"  Valid responses: {len(resp)}")

    # ── Group Balance ──
    section("3. Group Assignment Balance")
    group_counts = valid['group'].value_counts().sort_index()
    print(f"  Group A (Control): {group_counts.get('A', 0)}")
    print(f"  Group C (Strategy): {group_counts.get('C', 0)}")

    # ── Demographics ──
    section("4. Demographics Summary")
    for col in ['age', 'gender', 'education', 'ai_tool_usage', 'ai_exposure_freq']:
        if col in valid.columns:
            print(f"\n  {col}:")
            counts = valid[col].value_counts()
            for val, cnt in counts.items():
                print(f"    {val}: {cnt} ({cnt/len(valid)*100:.1f}%)")

    for col in ['ai_familiarity', 'self_assessed_ability']:
        if col in valid.columns:
            vals = pd.to_numeric(valid[col], errors='coerce').dropna()
            if len(vals) > 0:
                print(f"\n  {col}: M={vals.mean():.2f}, SD={vals.std():.2f}, range=[{vals.min():.0f}-{vals.max():.0f}]")

    # ── Accuracy Analysis (Primary DV) ──
    section("5. Accuracy Analysis (Primary DV)")

    # Per-participant accuracy
    acc_by_participant = resp.groupby('participant_id')['is_correct'].mean().reset_index()
    acc_by_participant.columns = ['participant_id', 'accuracy']
    acc_merged = acc_by_participant.merge(valid[['participant_id', 'group']], on='participant_id')

    for g in ['A', 'C']:
        subset = acc_merged[acc_merged['group'] == g]['accuracy']
        if len(subset) > 0:
            print(f"\n  Group {g}: N={len(subset)}, M={subset.mean():.4f}, SD={subset.std():.4f}, "
                  f"95%CI=[{subset.mean()-1.96*subset.sem():.4f}, {subset.mean()+1.96*subset.sem():.4f}]")

    # Independent t-test
    a_acc = acc_merged[acc_merged['group'] == 'A']['accuracy']
    c_acc = acc_merged[acc_merged['group'] == 'C']['accuracy']
    if len(a_acc) > 1 and len(c_acc) > 1:
        t_stat, p_val = stats.ttest_ind(a_acc, c_acc)
        cohens_d = (c_acc.mean() - a_acc.mean()) / np.sqrt((a_acc.std()**2 + c_acc.std()**2) / 2)
        print(f"\n  Independent t-test: t={t_stat:.4f}, p={p_val:.4f}, Cohen's d={cohens_d:.4f}")
        if p_val < 0.05:
            print(f"  -> Significant difference (p < .05)")
        else:
            print(f"  -> No significant difference (p >= .05)")

    # Accuracy by image type (AI vs Real)
    print("\n  Accuracy by Image Type:")
    for img_type in ['AI', 'Real']:
        sub = resp[resp['correct_answer'] == img_type]
        for g in ['A', 'C']:
            g_ids = valid[valid['group'] == g]['participant_id']
            g_sub = sub[sub['participant_id'].isin(g_ids)]
            if len(g_sub) > 0:
                acc = g_sub['is_correct'].mean()
                print(f"    {img_type} images, Group {g}: {acc:.4f} ({g_sub['is_correct'].sum()}/{len(g_sub)})")

    # ── Confidence Analysis ──
    section("6. Confidence Analysis")

    conf_by_participant = resp.groupby('participant_id')['confidence'].mean().reset_index()
    conf_merged = conf_by_participant.merge(valid[['participant_id', 'group']], on='participant_id')

    for g in ['A', 'C']:
        subset = conf_merged[conf_merged['group'] == g]['confidence']
        if len(subset) > 0:
            print(f"  Group {g}: M={subset.mean():.2f}, SD={subset.std():.2f}")

    # Confidence x Correctness
    print("\n  Confidence by Correctness:")
    for correct_label, correct_val in [('Correct', True), ('Incorrect', False)]:
        sub = resp[resp['is_correct'] == correct_val]['confidence']
        if len(sub) > 0:
            print(f"    {correct_label}: M={sub.mean():.2f}, SD={sub.std():.2f}")

    # ── Response Time Analysis ──
    section("7. Response Time Analysis")

    resp['response_time_s'] = resp['response_time_ms'] / 1000
    rt_by_participant = resp.groupby('participant_id')['response_time_s'].median().reset_index()
    rt_merged = rt_by_participant.merge(valid[['participant_id', 'group']], on='participant_id')

    for g in ['A', 'C']:
        subset = rt_merged[rt_merged['group'] == g]['response_time_s']
        if len(subset) > 0:
            print(f"  Group {g}: Median={subset.median():.2f}s, M={subset.mean():.2f}s, SD={subset.std():.2f}s")

    # ── Self-Efficacy Pre vs Post ──
    section("8. Self-Efficacy: Pre vs Post Comparison")

    if post_survey is not None and 'post_self_efficacy' in post_survey.columns:
        se_merged = valid[['participant_id', 'group', 'self_assessed_ability']].merge(
            post_survey[['participant_id', 'post_self_efficacy']], on='participant_id', how='inner'
        )
        se_merged['self_assessed_ability'] = pd.to_numeric(se_merged['self_assessed_ability'], errors='coerce')
        se_merged['post_self_efficacy'] = pd.to_numeric(se_merged['post_self_efficacy'], errors='coerce')
        se_merged = se_merged.dropna(subset=['self_assessed_ability', 'post_self_efficacy'])
        se_merged['se_change'] = se_merged['post_self_efficacy'] - se_merged['self_assessed_ability']

        for g in ['A', 'C']:
            sub = se_merged[se_merged['group'] == g]
            if len(sub) > 0:
                print(f"\n  Group {g} (N={len(sub)}):")
                print(f"    Pre:  M={sub['self_assessed_ability'].mean():.2f}, SD={sub['self_assessed_ability'].std():.2f}")
                print(f"    Post: M={sub['post_self_efficacy'].mean():.2f}, SD={sub['post_self_efficacy'].std():.2f}")
                print(f"    Change: M={sub['se_change'].mean():.2f}, SD={sub['se_change'].std():.2f}")
                if len(sub) > 1:
                    t, p = stats.ttest_rel(sub['self_assessed_ability'], sub['post_self_efficacy'])
                    print(f"    Paired t-test: t={t:.4f}, p={p:.4f}")
    else:
        print("  Post-survey data not available.")

    # ── Interaction Log Analysis (Lens Usage) ──
    section("9. Google Lens Usage Analysis")

    if interaction_logs is not None and len(interaction_logs) > 0:
        logs = interaction_logs[interaction_logs['participant_id'].isin(valid_ids)].copy()
        print(f"  Total interaction logs (valid participants): {len(logs)}")

        # Lens open rate by group
        lens_opens = logs[logs['action'] == 'OPEN_LENS']
        lens_users = set(lens_opens['participant_id'].tolist())

        for g in ['A', 'C']:
            g_ids = set(valid[valid['group'] == g]['participant_id'].tolist())
            g_lens = g_ids & lens_users
            total = len(g_ids)
            used = len(g_lens)
            rate = used / total * 100 if total > 0 else 0
            print(f"\n  Group {g}: {used}/{total} ({rate:.1f}%) used Google Lens")

        # Number of lens opens per participant
        opens_per_p = lens_opens.groupby('participant_id').size().reset_index(name='lens_opens')
        opens_merged = opens_per_p.merge(valid[['participant_id', 'group']], on='participant_id')
        for g in ['A', 'C']:
            sub = opens_merged[opens_merged['group'] == g]['lens_opens']
            if len(sub) > 0:
                print(f"  Group {g} lens opens (among users): M={sub.mean():.2f}, SD={sub.std():.2f}")

        # Action breakdown
        print("\n  Action breakdown:")
        action_counts = logs['action'].value_counts()
        for action, cnt in action_counts.items():
            print(f"    {action}: {cnt}")
    else:
        print("  No interaction log data available.")

    # ── Manipulation Check ──
    section("10. Manipulation Check")

    if post_survey is not None:
        ps = post_survey[post_survey['participant_id'].isin(valid_ids)].copy()

        if 'manipulation_check_read' in ps.columns:
            print("\n  Read intervention material?")
            read_counts = ps['manipulation_check_read'].value_counts()
            for val, cnt in read_counts.items():
                print(f"    {val}: {cnt}")

        if 'strategy_usage_degree' in ps.columns:
            c_ids = set(valid[valid['group'] == 'C']['participant_id'].tolist())
            c_ps = ps[ps['participant_id'].isin(c_ids)]
            su = pd.to_numeric(c_ps['strategy_usage_degree'], errors='coerce').dropna()
            if len(su) > 0:
                print(f"\n  Strategy usage degree (Group C only):")
                print(f"    M={su.mean():.2f}, SD={su.std():.2f}, range=[{su.min():.0f}-{su.max():.0f}]")

        if 'self_performance' in ps.columns:
            print("\n  Self-rated performance by group:")
            for g in ['A', 'C']:
                g_ids = set(valid[valid['group'] == g]['participant_id'].tolist())
                g_ps = ps[ps['participant_id'].isin(g_ids)]
                sp = pd.to_numeric(g_ps['self_performance'], errors='coerce').dropna()
                if len(sp) > 0:
                    print(f"    Group {g}: M={sp.mean():.2f}, SD={sp.std():.2f}")
    else:
        print("  Post-survey data not available.")

    # ── Save Merged Analysis Dataset ──
    section("11. Exporting Merged Dataset")

    # Build per-participant summary
    summary = valid[['participant_id', 'group', 'age', 'gender', 'education',
                      'ai_tool_usage', 'ai_familiarity', 'self_assessed_ability',
                      'ai_exposure_freq', 'intervention_duration_s', 'total_duration_s']].copy()

    # Add accuracy
    summary = summary.merge(acc_by_participant, on='participant_id', how='left')

    # Add accuracy by type
    for img_type in ['AI', 'Real']:
        type_acc = resp[resp['correct_answer'] == img_type].groupby('participant_id')['is_correct'].mean().reset_index()
        type_acc.columns = ['participant_id', f'accuracy_{img_type.lower()}']
        summary = summary.merge(type_acc, on='participant_id', how='left')

    # Add mean confidence
    summary = summary.merge(conf_by_participant, on='participant_id', how='left')

    # Add median RT
    summary = summary.merge(rt_by_participant.rename(columns={'response_time_s': 'median_rt_s'}), on='participant_id', how='left')

    # Add post-survey
    if post_survey is not None:
        ps_cols = ['participant_id', 'manipulation_check_read', 'strategy_usage_degree',
                   'self_performance', 'post_self_efficacy', 'attention_check_passed']
        ps_cols = [c for c in ps_cols if c in post_survey.columns]
        summary = summary.merge(post_survey[ps_cols], on='participant_id', how='left')

    # Add lens usage count
    if interaction_logs is not None and len(interaction_logs) > 0:
        lens_count = interaction_logs[
            (interaction_logs['participant_id'].isin(valid_ids)) &
            (interaction_logs['action'] == 'OPEN_LENS')
        ].groupby('participant_id').size().reset_index(name='lens_open_count')
        summary = summary.merge(lens_count, on='participant_id', how='left')
        summary['lens_open_count'] = summary['lens_open_count'].fillna(0).astype(int)

    save_df(summary, 'participant_summary')
    save_df(resp, 'valid_responses')

    print(f"\n  Summary columns: {list(summary.columns)}")
    print(f"\n{'='*60}")
    print(f"  Analysis complete! Check {OUTPUT_DIR}/ for outputs.")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
