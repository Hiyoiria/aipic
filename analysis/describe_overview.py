#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
describe_overview.py
────────────────────────────────────────────────────────────────────
纯描述性统计 + 数据结构概览，输出 Markdown 供 preview 使用。
样本：participant_summary_mc_passed.csv
  （delete!=1 且 C组 mc_passed=1，即两项 manipulation check 均通过）
  A=54，C=52，N=106

输出：analysis/output/data_overview.md
"""
import sys, io, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# ── 路径 ──────────────────────────────────────────────────────────
ENC  = 'C:\\Users\\t-yimengwu\\Desktop\\study2\\analysis\\final_data_1\\participants.csv'   # MC 通过后样本
OUT  = 'C:\\Users\\t-yimengwu\\Desktop\\study2\\analysis\\output\\data_overview.md'

# ── 读入（mc_passed.csv 已只含 delete!=1 且 mc_passed=1 的行）─────
df = pd.read_csv(ENC).copy()

df['group']   = df['组别'].map({0:'对照组', 1:'实验组'})
df['gender']  = df['性别'].map({0:'男', 1:'女'})
df['age']     = df['年龄段'].map({1:'18–24', 2:'25–34', 3:'35–44', 4:'45–54'})
df['edu5']    = df['学历'].map({1:'高中', 2:'大专', 3:'本科', 4:'硕士', 5:'博士'})
df['edu3']    = df['学历分组'].map({1:'高中/大专', 2:'本科', 3:'硕博'})
df['aitool']  = df['AI工具使用经验'].map({0:'无', 1:'有'})
df['aifreq']  = df['AI使用频率(1-5)'].map({1:'从不',2:'很少',3:'有时',4:'经常',5:'非常频繁'})

gA = df[df['组别']==0]
gC = df[df['组别']==1]
nA, nC, N = len(gA), len(gC), len(df)

# ── 输出缓冲 ─────────────────────────────────────────────────────
lines = []

def w(*a):
    s = ' '.join(str(x) for x in a)
    print(s)
    lines.append(s)

def h1(t): w(f'\n# {t}\n')
def h2(t): w(f'\n## {t}\n')
def h3(t): w(f'\n### {t}\n')

def pct(n, total):
    return f'{n} ({n/total*100:.1f}%)' if total > 0 else '—'

def ms(arr):
    a = np.array(arr, dtype=float)
    a = a[~np.isnan(a)]
    if len(a) == 0: return '—'
    return f'{a.mean():.2f} ({a.std(ddof=1):.2f})'

def md5(arr):
    """Mdn [min, max]"""
    a = np.array(arr, dtype=float)
    a = a[~np.isnan(a)]
    if len(a) == 0: return '—'
    return f'Mdn={np.median(a):.2f}, [{a.min():.2f}–{a.max():.2f}]'

def cat_table(col, order, label_map=None, title=''):
    """按类别输出 A / C / Total 三列频数表"""
    if title: h3(title)
    rows = [['类别', f'对照组 (n={nA})', f'实验组 (n={nC})', f'总计 (n={N})']]
    rows.append(['---', '---', '---', '---'])
    for cat in order:
        lbl = label_map.get(cat, cat) if label_map else cat
        nai = int((df.loc[df['组别']==0, col] == cat).sum())
        nci = int((df.loc[df['组别']==1, col] == cat).sum())
        nti = int((df[col] == cat).sum())
        rows.append([lbl, pct(nai, nA), pct(nci, nC), pct(nti, N)])
    for r in rows:
        w('| ' + ' | '.join(str(c) for c in r) + ' |')

def cont_table(var_list, title=''):
    """连续变量 M (SD) 表，三列；跳过不存在或重复的列"""
    if title: h3(title)
    rows = [['变量', f'对照组 (n={nA})', f'实验组 (n={nC})', f'总计 (n={N})'],
            ['---', '---', '---', '---']]
    seen = set()
    for col, lbl in var_list:
        if not lbl or col in seen: continue
        seen.add(col)
        if col not in df.columns: continue
        a_ = df.loc[df['组别']==0, col]
        c_ = df.loc[df['组别']==1, col]
        rows.append([lbl, ms(a_), ms(c_), ms(df[col])])
    for r in rows:
        w('| ' + ' | '.join(str(c) for c in r) + ' |')

def cont_detail(var_list, title=''):
    """连续变量详细描述（M / SD / Mdn / min / max / n）；跳过重复列"""
    if title: h3(title)
    rows = [['变量', 'M', 'SD', 'Mdn', 'Min', 'Max', 'n'],
            ['---']*7]
    seen = set()
    for col, lbl in var_list:
        if not lbl or col in seen: continue
        seen.add(col)
        if col not in df.columns: continue
        a = df[col].dropna().values.astype(float)
        if len(a) == 0:
            rows.append([lbl, '—', '—', '—', '—', '—', '0'])
        else:
            rows.append([lbl,
                         f'{a.mean():.3f}',
                         f'{a.std(ddof=1):.3f}',
                         f'{np.median(a):.3f}',
                         f'{a.min():.3f}',
                         f'{a.max():.3f}',
                         str(int(len(a)))])
    for r in rows:
        w('| ' + ' | '.join(str(c) for c in r) + ' |')

# ══════════════════════════════════════════════════════════════════
today = datetime.date.today().isoformat()
h1('Study 2 — 数据概览与描述性统计')
w(f'> 生成时间：{today}　|　最终分析样本：**n = {N}**（A 组 {nA}，C 组 {nC}）\n')
w('---')

# ══════════════════════════════════════════════════════════════════
h2('一、数据结构')

h3('1.1 样本过滤流程')
w('| 步骤 | 操作 | 保留 n |')
w('|---|---|---|')
w('| 原始参与者 | 平台注册 A / C 组 | 202 |')
w('| 完成全部 21 张图像 | — | 119 |')
w('| 通过注意力检测 | 排除 5 人 | 114 |')
w('| 手动质检排除 | delete = 1，共 3 人 | 112 |')
w(f'| **Manipulation Check（C 组）** | C 组中未读干预材料或未读策略列表，排除 6 人 | **{N}** |')

h3('1.2 核心数据文件（final_data/）')
# 动态读取 final_data 行数
import os as _os
def _nrows(path):
    try:
        return len(pd.read_csv(path))
    except Exception:
        return '?'
n_resp = _nrows('analysis/final_data/responses.csv')
n_logs = _nrows('analysis/final_data/interaction_logs.csv')
n_post = _nrows('analysis/final_data/post_survey.csv')
w('| 文件 | 内容 | 行数（MC 过滤后）|')
w('|---|---|---|')
w(f'| `participants.csv` | 每位被试的汇总数据（含编码 + mc_passed） | {N} |')
w(f'| `responses.csv` | 逐题作答记录（is_correct, confidence, judgment…） | {n_resp} |')
w(f'| `interaction_logs.csv` | 行为日志（OPEN_LENS, SCROLL_LENS…） | {n_logs} |')
w(f'| `post_survey.csv` | 后测问卷（manipulation check, strategy_usage…） | {n_post} |')

h3('1.3 核心变量说明')
w('| 变量 | 操作化 | 量程 | 来源 |')
w('|---|---|---|---|')
w('| `acc_total` | 正确判断数 / 21 | 0–1 | responses |')
w('| `acc_ai` | AI 图正确率 | 0–1 | responses |')
w('| `acc_real` | 真实图正确率 | 0–1 | responses |')
w("| `d'`（dprime） | SDT 敏感度，z(HR) − z(FAR)，Loglinear 校正 | 连续 | 计算 |")
w('| `c`（criterion） | 判断标准偏向，负=偏判为AI | 连续 | 计算 |')
w('| `self_assessed_ability` | 前测自评辨别能力 | 1–5 | participants |')
w('| `self_performance` | 后测对自身表现的整体评估 | 1–5 | post-survey |')
w('| `calibration_gap` | self_performance/5 − acc_total（正 = 过度自信） | 连续 | 计算 |')
w('| `ai_familiarity` | AI 工具熟悉程度 | 1–5 | participants |')
w('| `ai_exposure_num` | AI 使用频率（never=1…very-often=5） | 1–5 | participants |')
w('| `intervention_duration_s` | 干预页面停留时长（秒，A 组填 0） | 秒 | participants |')

# ══════════════════════════════════════════════════════════════════
h2('二、样本人口统计学')

h3('2.1 组别 × 来源分布')
w('| | A 组 | C 组 | 合计 |')
w('|---|---|---|---|')
for src_code, src_lbl in [(0,'real（真实招募）'), (1,'synth（合成招募）')]:
    nai = int(((df['组别']==0) & (df['来源']==src_code)).sum())
    nci = int(((df['组别']==1) & (df['来源']==src_code)).sum())
    nti = int((df['来源']==src_code).sum())
    w(f'| {src_lbl} | {pct(nai,nA)} | {pct(nci,nC)} | {pct(nti,N)} |')
w(f'| **合计** | **{nA}** | **{nC}** | **{N}** |')

cat_table('gender', ['男','女'],
          title='2.2 性别分布')

cat_table('age', ['18–24','25–34','35–44','45–54'],
          title='2.3 年龄分布')

cat_table('edu5', ['高中','大专','本科','硕士','博士'],
          title='2.4 学历分布（五级）')

cat_table('edu3', ['高中/大专','本科','硕博'],
          title='2.5 学历分组（三级，供分析用）')
w('> 参照组 = 本科（n 最大且居中）\n')

cat_table('aitool', ['有','无'],
          title='2.6 AI 工具使用经验')

cat_table('aifreq', ['从不','很少','有时','经常','非常频繁'],
          title='2.7 AI 使用频率分布')

# ══════════════════════════════════════════════════════════════════
h2('三、前测变量描述统计')

cont_table([
    ('AI熟悉度',        'AI 熟悉度（1–5）'),
    ('前测自评能力',    '前测自评能力（1–5）'),
    ('AI使用频率(1-5)', 'AI 使用频率（1–5）'),
], title='3.1 按组别 M (SD)')
w('> 格式：M (SD)\n')

# 全样本详细
h3('3.2 全样本详细描述')
pre_vars = [
    ('AI熟悉度',        'AI 熟悉度（1–5）'),
    ('前测自评能力',    '前测自评能力（1–5）'),
    ('AI使用频率(1-5)', 'AI 使用频率（1–5）'),
]
cont_detail(pre_vars)

# ══════════════════════════════════════════════════════════════════
h2('四、实验结果变量描述统计')

# 先从 formal_analysis 的输出 CSV 试着读 dprime 和 c
# 如果没有则只展示 acc 等
try:
    from scipy.stats import norm
    resp = pd.read_csv('analysis/data/responses_combined.csv')
    # 过滤到样本
    valid_pids = set(df['participant_id'])
    VALID = {'ai_01','ai_02','ai_04','ai_08','ai_09','ai_13','ai_15','ai_16','ai_19',
             'real_01','real_02','real_03','real_04','real_05','real_06',
             'real_11','real_12','real_14','real_15','real_16','real_20'}
    r = resp[resp['participant_id'].isin(valid_pids) & resp['image_id'].isin(VALID)].copy()
    AI_IDS = {x for x in VALID if x.startswith('ai_')}

    sdt_rows = []
    for pid, g in r.groupby('participant_id'):
        ai_g    = g[g['image_id'].isin(AI_IDS)]
        real_g  = g[~g['image_id'].isin(AI_IDS)]
        n_ai    = len(ai_g); n_real = len(real_g)
        if n_ai == 0 or n_real == 0: continue
        hr  = (ai_g['is_correct'].sum()   + 0.5) / (n_ai   + 1)
        far = ((real_g['is_correct']==0).sum() + 0.5) / (n_real + 1)
        dp  = norm.ppf(hr) - norm.ppf(far)
        c_v = -0.5 * (norm.ppf(hr) + norm.ppf(far))
        mean_conf = g['confidence'].mean() if 'confidence' in g.columns else np.nan
        sdt_rows.append({'participant_id': pid, 'dprime': dp, 'c': c_v,
                         'mean_conf': mean_conf})
    sdt_df = pd.DataFrame(sdt_rows)
    df = df.merge(sdt_df, on='participant_id', how='left')
    df['calibration_gap'] = df['后测表现自评'] / 5 - df['整体正确率']
    has_sdt = True
except Exception as e:
    has_sdt = False

cont_table([
    ('整体正确率',      '整体正确率'),
    ('AI图正确率',      'AI 图正确率'),
    ('真实图正确率',    '真实图正确率'),
    ('dprime',          "d'（SDT 敏感度）"),
    ('c',               'c（判断标准偏向）'),
    ('后测表现自评',    '后测表现自评（1–5）'),
    ('calibration_gap', '信心校准差距（self_perf/5 − acc）'),
], title='4.1 按组别 M (SD)')
w('> 格式：M (SD)\n')

h3('4.2 全样本详细描述')
out_vars = [
    ('整体正确率',      '整体正确率'),
    ('AI图正确率',      'AI 图正确率'),
    ('真实图正确率',    '真实图正确率'),
    ('dprime',          "d'（SDT 敏感度）"),
    ('c',               'c（判断标准偏向）'),
    ('calibration_gap', '信心校准差距'),
    ('后测表现自评',    '后测表现自评（1–5）'),
]
cont_detail(out_vars)

# ══════════════════════════════════════════════════════════════════
h2('五、操纵检查与干预参与（C 组）')

c_df = df[df['组别']==1]
nc = len(c_df)
h3('5.1 阅读了干预材料')
w('| 回答 | n | % |')
w('|---|---|---|')
for code, lbl in [(2,'是'),(1,'不确定'),(0,'否')]:
    n_ = int((c_df['阅读了干预材料']==code).sum())
    w(f'| {lbl} | {n_} | {n_/nc*100:.1f}% |')

h3('5.2 阅读了策略列表')
w('| 回答 | n | % |')
w('|---|---|---|')
for code, lbl in [(1,'是'),(0,'否')]:
    n_ = int((c_df['阅读了策略列表']==code).sum())
    w(f'| {lbl} | {n_} | {n_/nc*100:.1f}% |')

h3('5.3 策略使用程度（C 组，1–5）')
deg = c_df['策略使用程度'].dropna()
if len(deg) > 0:
    w(f'- M = {deg.mean():.2f}, SD = {deg.std(ddof=1):.2f}')
    w(f'- Mdn = {deg.median():.2f}, [min = {deg.min():.0f}, max = {deg.max():.0f}], n = {len(deg)}')

h3('5.4 干预页面停留时长（C 组，秒）')
dur = c_df['干预停留时间(秒)'].dropna()
dur = dur[dur > 0]
if len(dur) > 0:
    w(f'- M = {dur.mean():.1f}s, SD = {dur.std(ddof=1):.1f}s')
    w(f'- Mdn = {dur.median():.1f}s, [min = {dur.min():.0f}s, max = {dur.max():.0f}s], n = {len(dur)}')
    w('')
    w('| 时长区间 | n | % |')
    w('|---|---|---|')
    bins = [(0,30,'< 30s'),(30,60,'30–60s'),(60,90,'60–90s'),(90,180,'90–180s'),(180,9999,'> 180s')]
    for lo,hi,lbl in bins:
        n_ = int(((dur>=lo)&(dur<hi)).sum())
        w(f'| {lbl} | {n_} | {n_/len(dur)*100:.1f}% |')

# ══════════════════════════════════════════════════════════════════
h2('六、策略使用程度综合分析（C 组）')
w(f'> 分析单位：被试（n={nC}，C 组，MC 通过），`策略使用程度` 取值 1–5。\n')

from scipy import stats as _stats

# 重取 c_df（已含 SDT 变量）
c_df = df[df['组别']==1].copy()
deg_col = '策略使用程度'

# ── 6.1 分布 ──────────────────────────────────────────────────────
h3('6.1 分布（C 组）')
deg_all = c_df[deg_col].dropna()
w(f'n = {len(deg_all)},  M = {deg_all.mean():.2f},  SD = {deg_all.std(ddof=1):.2f},  '
  f'Mdn = {deg_all.median():.2f},  [min = {deg_all.min():.0f},  max = {deg_all.max():.0f}]')
w('')
w('| 分值 | n | % |')
w('|---|---|---|')
for v in [1, 2, 3, 4, 5]:
    n_ = int((deg_all == v).sum())
    w(f'| {v} | {n_} | {n_/len(deg_all)*100:.1f}% |')

# ── 6.2 相关矩阵（策略使用程度 × 各结果变量）─────────────────────
h3('6.2 与各结果变量的 Pearson 相关（C 组）')
w('> ◄ *p* < .05；**◄** *p* < .01；***◄*** *p* < .001\n')
w('| 变量 | r | p | n | 方向解读 |')
w('|---|---|---|---|---|')

def _interp(r, p, lbl):
    """自动生成方向解读"""
    if p >= .05: return '不显著'
    dir_ = '↑ 策略↑→成绩↑' if r > 0 else '↑ 策略↑→成绩↓'
    size = '弱' if abs(r)<.3 else ('中' if abs(r)<.5 else '强')
    return f'{dir_}（{size}效应）'

corr_targets = [
    ('整体正确率',      '整体正确率'),
    ('AI图正确率',      'AI 图正确率'),
    ('真实图正确率',    '真实图正确率'),
    ('dprime',          "d'（SDT 敏感度）"),
    ('c',               'c（判断标准偏向，负=偏判AI）'),
    ('mean_conf',       '平均信心评分'),
    ('calibration_gap', '信心校准差距（过度自信+）'),
    ('后测表现自评',    '后测表现自评'),
    ('AI熟悉度',        'AI 熟悉度（前测）'),
    ('前测自评能力',    '前测自评能力'),
]
for col, lbl in corr_targets:
    if col not in c_df.columns: continue
    pair = c_df[[deg_col, col]].dropna()
    if len(pair) < 5: continue
    r_v, p_v = _stats.pearsonr(pair[deg_col], pair[col])
    star = '***◄' if p_v<.001 else ('**◄' if p_v<.01 else ('◄' if p_v<.05 else ''))
    r_s  = f'{r_v:+.3f}'
    p_s  = '< .001' if p_v<.001 else f'{p_v:.3f}'
    interp = _interp(r_v, p_v, lbl)
    w(f'| {lbl} | {r_s} {star} | {p_s} | {len(pair)} | {interp} |')

# ── 6.3 中位数分组比较（低使用 vs 高使用）────────────────────────
h3('6.3 中位数分组比较：低策略使用 vs 高策略使用（C 组）')
mdn = deg_all.median()
w(f'> 中位数 = {mdn:.1f}；低组 ≤ {mdn:.0f}，高组 > {mdn:.0f}\n')

low_g  = c_df[c_df[deg_col] <= mdn]
high_g = c_df[c_df[deg_col] >  mdn]
w(f'低策略使用组 n = {len(low_g)}，高策略使用组 n = {len(high_g)}\n')

w('| 变量 | 低组 M (SD) | 高组 M (SD) | t | df | p | g |')
w('|---|---|---|---|---|---|---|')
for col, lbl in [
    ('整体正确率',      '整体正确率'),
    ('AI图正确率',      'AI 图正确率'),
    ('真实图正确率',    '真实图正确率'),
    ('dprime',          "d'"),
    ('c',               'c（判断偏向）'),
    ('mean_conf',       '平均信心'),
    ('calibration_gap', '信心校准差距'),
    ('后测表现自评',    '后测表现自评'),
]:
    if col not in c_df.columns: continue
    a_ = low_g[col].dropna().values.astype(float)
    b_ = high_g[col].dropna().values.astype(float)
    if len(a_) < 2 or len(b_) < 2: continue
    t_, p_ = _stats.ttest_ind(b_, a_, equal_var=False)
    wdf = ((np.var(a_,ddof=1)/len(a_) + np.var(b_,ddof=1)/len(b_))**2 /
           ((np.var(a_,ddof=1)/len(a_))**2/(len(a_)-1) + (np.var(b_,ddof=1)/len(b_))**2/(len(b_)-1)))
    pool_sd = np.sqrt(((len(a_)-1)*np.std(a_,ddof=1)**2 + (len(b_)-1)*np.std(b_,ddof=1)**2) /
                      (len(a_)+len(b_)-2))
    g_ = (b_.mean()-a_.mean())/pool_sd if pool_sd>0 else np.nan
    star = '***' if p_<.001 else ('**' if p_<.01 else ('*' if p_<.05 else ''))
    p_s  = '< .001' if p_<.001 else f'{p_:.3f}'
    w(f'| {lbl} | {a_.mean():.3f} ({np.std(a_,ddof=1):.3f}) | '
      f'{b_.mean():.3f} ({np.std(b_,ddof=1):.3f}) | '
      f'{t_:.3f} | {wdf:.1f} | {p_s}{star} | {g_:+.3f} |')

# 注：6.4 / 6.5（阅读策略列表 / 干预材料分组比较）在 MC 过滤后全部为"已阅读"，无法比较，已省略

# ══════════════════════════════════════════════════════════════════
h2('七、图像集结构（IMAGE_META）')
w('> 共 21 张有效图像（排除 ai_06 / ai_11 / ai_18）\n')
w('| 类型 | 风格 | 来源 | 可反向搜索 | 图像 ID |')
w('|---|---|---|---|---|')
IMAGE_META = {
  'ai_01': {'type':'AI','style':'illustration','source':'ai-art',    'rs':True},
  'ai_02': {'type':'AI','style':'photograph',  'source':'ai-art',    'rs':True},
  'ai_04': {'type':'AI','style':'cartoon',     'source':'ai-art',    'rs':True},
  'ai_08': {'type':'AI','style':'photograph',  'source':'midjourney','rs':False},
  'ai_09': {'type':'AI','style':'cartoon',     'source':'midjourney','rs':False},
  'ai_13': {'type':'AI','style':'photograph',  'source':'midjourney','rs':False},
  'ai_15': {'type':'AI','style':'photograph',  'source':'nanobanana','rs':False},
  'ai_16': {'type':'AI','style':'illustration','source':'nanobanana','rs':False},
  'ai_19': {'type':'AI','style':'photograph',  'source':'nanobanana','rs':False},
  'real_01':{'type':'Real','style':'illustration','source':'camera', 'rs':True},
  'real_02':{'type':'Real','style':'photograph',  'source':'camera', 'rs':True},
  'real_03':{'type':'Real','style':'cartoon',     'source':'camera', 'rs':True},
  'real_04':{'type':'Real','style':'photograph',  'source':'camera', 'rs':True},
  'real_05':{'type':'Real','style':'illustration','source':'camera', 'rs':True},
  'real_06':{'type':'Real','style':'photograph',  'source':'camera', 'rs':True},
  'real_11':{'type':'Real','style':'photograph',  'source':'website','rs':True},
  'real_12':{'type':'Real','style':'photograph',  'source':'website','rs':True},
  'real_14':{'type':'Real','style':'cartoon',     'source':'website','rs':True},
  'real_15':{'type':'Real','style':'illustration','source':'website','rs':True},
  'real_16':{'type':'Real','style':'photograph',  'source':'website','rs':True},
  'real_20':{'type':'Real','style':'cartoon',     'source':'website','rs':True},
}
for img_id, m in sorted(IMAGE_META.items()):
    photo_flag = '✓ (photo)' if m['style']=='photograph' else 'not_photo'
    rs_flag = '✓' if m['rs'] else '✗'
    w(f"| {m['type']} | {m['style']} / {photo_flag} | {m['source']} | {rs_flag} | `{img_id}` |")

# 小结
w('\n**图像构成摘要**')
w('| | AI 图 (9) | Real 图 (12) | 合计 |')
w('|---|---|---|---|')
ai_m = {k:v for k,v in IMAGE_META.items() if v['type']=='AI'}
re_m = {k:v for k,v in IMAGE_META.items() if v['type']=='Real'}
for sty in ['photograph','illustration','cartoon']:
    n_ai = sum(1 for v in ai_m.values() if v['style']==sty)
    n_re = sum(1 for v in re_m.values() if v['style']==sty)
    w(f'| {sty} | {n_ai} | {n_re} | {n_ai+n_re} |')
w(f'| **合计** | 9 | 12 | 21 |')

# ══════════════════════════════════════════════════════════════════
h2('八、缺失值概览')
w('| 变量 | 缺失 n | 缺失 % |')
w('|---|---|---|')
check_cols = {
    'AI熟悉度': 'AI 熟悉度',
    '前测自评能力': '前测自评能力',
    'AI使用频率(1-5)': 'AI 使用频率',
    '整体正确率': '整体正确率',
    '后测表现自评': '后测表现自评',
    '性别': '性别',
    '年龄段': '年龄段',
    '学历': '学历',
    '阅读了干预材料': '阅读干预材料（全样本）',
    '干预停留时间(秒)': '干预停留时长',
}
for col, lbl in check_cols.items():
    miss = int(df[col].isna().sum()) if col in df.columns else 0
    w(f'| {lbl} | {miss} | {miss/N*100:.1f}% |')

# ══════════════════════════════════════════════════════════════════
w('\n---')
w(f'\n> 注：所有描述统计均基于最终分析样本（n={N}，delete≠1）。'
  ' 连续变量格式为 M (SD)。图像集结构来自 `imageData.ts`。')

# ── 保存 ─────────────────────────────────────────────────────────
with open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print(f'\n✓ 已保存 → {OUT}')
