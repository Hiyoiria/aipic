#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
encode_summary.py
─────────────────────────────────────────────────────────────────
把 participant_summary_extended.csv 中的所有名义 / 定序变量编码为数值，
遵循 clean_analysis.py 的编码约定。

编码规则：
  组别              A=0  C=1
  来源              real=0  synth=1
  性别              female=1  其余（male / prefer-not-to-say）=0
  年龄段            18-24=1  25-34=2  35-44=3  45-54=4
  学历              high-school=1  some-college=2  bachelors=3  masters=4  doctorate=5
  AI工具使用经验    no=0  yes=1
  阅读了干预材料    no=0  not_sure=1  yes=2
  阅读了策略列表    no=0  yes / 策略列表=1
  注意力检测通过    False=0  True=1

不改动的列（已是数值）：
  AI熟悉度 前测自评能力 AI使用频率(1-5) 整体正确率 AI图正确率
  真实图正确率 后测表现自评 delete 干预停留时间(秒) 策略使用程度

输出：analysis/output/participant_summary_encoded.csv
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
import numpy as np

IN  = 'analysis/output/participant_summary_extended.csv'
OUT = 'analysis/output/participant_summary_encoded.csv'

df = pd.read_csv(IN)
print(f'读入：{len(df)} 行，{len(df.columns)} 列')

# ── 组别 ──────────────────────────────────────────────────────
df['组别'] = df['组别'].map({'A': 0, 'C': 1})

# ── 来源 ──────────────────────────────────────────────────────
df['来源'] = df['来源'].map({'real': 0, 'synth': 1})

# ── 性别（其他/prefer-not-to-say 归入 0=男参照组）────────────
df['性别'] = (df['性别'] == 'female').astype(float)

# ── 年龄段（定序）────────────────────────────────────────────
age_map = {'18-24': 1, '25-34': 2, '35-44': 3, '45-54': 4}
df['年龄段'] = df['年龄段'].map(age_map)

# ── 学历（定序）──────────────────────────────────────────────
edu_map = {
    'high-school':   1,
    'some-college':  2,
    'bachelors':     3,
    'masters':       4,
    'doctorate':     5,
}
df['学历'] = df['学历'].map(edu_map)

# ── AI工具使用经验 ────────────────────────────────────────────
df['AI工具使用经验'] = df['AI工具使用经验'].map({'no': 0, 'yes': 1})

# ── 阅读了干预材料 ────────────────────────────────────────────
df['阅读了干预材料'] = df['阅读了干预材料'].map({'no': 0, 'not_sure': 1, 'yes': 2})

# ── 阅读了策略列表（no=0；yes 或具体策略字符串=1）─────────────
def encode_strategy_read(v):
    if pd.isna(v):
        return np.nan
    if str(v).strip().lower() == 'no':
        return 0
    return 1   # 'yes' 或 'anatomy,texture,text' 等具体列表

df['阅读了策略列表'] = df['阅读了策略列表'].apply(encode_strategy_read)

# ── 注意力检测通过 ─────────────────────────────────────────────
df['注意力检测通过'] = df['注意力检测通过'].astype(float)

# ── Manipulation check 通过标记 ───────────────────────────────────
#   mc_passed = 1 表示通过：
#     A组：无需check → 全部为 1
#     C组：阅读了干预材料==2(yes) 且 阅读了策略列表==1(yes) → 1，否则 0
def mc_passed(row):
    if row['组别'] == 0:          # A组
        return 1
    read_mat = row['阅读了干预材料']
    read_str = row['阅读了策略列表']
    if read_mat == 2 and read_str == 1:
        return 1
    return 0

df['mc_passed'] = df.apply(mc_passed, axis=1)

# ── 学历分组（三分类，供分析用；保留 学历 原列供描述）─────────────
#   1 = 高中 + 大专（edu_ord 1-2）
#   2 = 本科（edu_ord 3）← 参照组
#   3 = 硕士 + 博士（edu_ord 4-5）
def edu_3group(v):
    if pd.isna(v): return np.nan
    if v <= 2: return 1
    if v == 3: return 2
    return 3

df['学历分组'] = df['学历'].apply(edu_3group)

# ── 保存 ──────────────────────────────────────────────────────
df.to_csv(OUT, index=False, encoding='utf-8-sig')
print(f'输出：{len(df)} 行，{len(df.columns)} 列')
print(f'列名：{df.columns.tolist()}')

# ── 编码摘要 ──────────────────────────────────────────────────
print('\n── 编码摘要 ──')
print(f'组别        0=A  1=C   分布：{dict(df["组别"].value_counts().sort_index())}')
print(f'来源        0=real  1=synth   分布：{dict(df["来源"].value_counts().sort_index())}')
print(f'性别        0=男(+其他)  1=女   分布：{dict(df["性别"].value_counts().sort_index())}')
print(f'年龄段      1=18-24 2=25-34 3=35-44 4=45-54   分布：{dict(df["年龄段"].value_counts().sort_index())}')
print(f'学历        1=高中 2=大专 3=本科 4=硕士 5=博士   分布：{dict(df["学历"].value_counts().sort_index())}')
print(f'AI工具使用  0=no  1=yes   分布：{dict(df["AI工具使用经验"].value_counts().sort_index())}')
print(f'阅读干预    0=no  1=not_sure  2=yes   分布：{dict(df["阅读了干预材料"].dropna().value_counts().sort_index())}')
print(f'阅读策略    0=no  1=yes/详细   分布：{dict(df["阅读了策略列表"].dropna().value_counts().sort_index())}')
print(f'注意力通过  0=False  1=True   分布：{dict(df["注意力检测通过"].value_counts().sort_index())}')
print(f'学历分组    1=高中/大专  2=本科  3=硕博   分布：{dict(df["学历分组"].dropna().value_counts().sort_index())}')
print(f'mc_passed   C组通过/未通过   分布：{dict(df[df["组别"]==1]["mc_passed"].value_counts().sort_index())}')

# ── 生成 mc_passed 过滤表 ──────────────────────────────────────────
OUT_MC = 'analysis/output/participant_summary_mc_passed.csv'
df_mc = df[(df['delete'].isna() | (df['delete'] != 1)) & (df['mc_passed'] == 1)].copy()
df_mc.to_csv(OUT_MC, index=False, encoding='utf-8-sig')
n_A = (df_mc['组别'] == 0).sum()
n_C = (df_mc['组别'] == 1).sum()
print(f'\nMC通过样本：{len(df_mc)} 人（A={n_A}, C={n_C}）')
print(f'已保存 → {OUT_MC}')

print(f'\n已保存 → {OUT}')
