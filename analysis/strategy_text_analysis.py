#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
strategy_text_analysis.py
整理受试者的策略文本并做简单文本分析
  - 逐图 reasoning（回答各图时填写的策略/理由）
  - 结尾自述策略（post-survey open_method）
输出：
  analysis/output/strategy_per_image.csv
  analysis/output/strategy_end.csv
  analysis/output/strategy_text_report.md
"""
import sys, io, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
import numpy as np
from collections import Counter

OUT_DIR = 'analysis/output'
os.makedirs(OUT_DIR, exist_ok=True)

# ── 读取数据（final_data/，已完成 MC 过滤）─────────────────────────────────
FINAL_DIR = 'analysis/final_data_1'
enc  = pd.read_csv(os.path.join(FINAL_DIR, 'participants.csv'))
enc['group'] = enc['组别'].map({0: '对照', 1: '实验'})
pid_group = enc.set_index('participant_id')['group'].to_dict()

resp = pd.read_csv(os.path.join(FINAL_DIR, 'responses.csv'))
resp['group'] = resp['participant_id'].map(pid_group)

post = pd.read_csv(os.path.join(FINAL_DIR, 'post_survey.csv'))
post['group'] = post['participant_id'].map(pid_group)

# ── 表1：逐图 reasoning ─────────────────────────────────────────────────────
r_text = resp[resp['reasoning'].notna() & (resp['reasoning'].str.strip() != '')].copy()
r_text = r_text[['participant_id', 'group', 'image_id', 'image_order',
                  'judgment', 'is_correct', 'confidence', 'reasoning']].copy()
r_text['reasoning'] = r_text['reasoning'].str.strip()
r_text = r_text.sort_values(['group', 'participant_id', 'image_order'])
r_text.to_csv(f'{OUT_DIR}/strategy_per_image.csv', index=False, encoding='utf-8-sig')
print(f'逐图 reasoning：{len(r_text)} 条（{r_text["participant_id"].nunique()} 人）')

# ── 表2：结尾自述策略 ────────────────────────────────────────────────────────
end_text = post[post['open_method'].notna()].copy()
# 过滤纯数字噪音（如 "11", "33", "1" 等）
def is_meaningful(s):
    s = str(s).strip()
    if re.fullmatch(r'\d+', s): return False
    if len(s) <= 2 and not re.search(r'[\u4e00-\u9fff]', s): return False
    return True

end_text = end_text[end_text['open_method'].apply(is_meaningful)].copy()
end_text = end_text[['participant_id', 'group',
                      'strategy_usage_degree', 'open_method']].copy()
end_text = end_text.rename(columns={'open_method': 'end_strategy'})
end_text = end_text.sort_values(['group', 'participant_id'])
end_text.to_csv(f'{OUT_DIR}/strategy_end.csv', index=False, encoding='utf-8-sig')
print(f'结尾自述：{len(end_text)} 条（{end_text["participant_id"].nunique()} 人）')

# ════════════════════════════════════════════════════════════════════════════
# 文本分析
# ════════════════════════════════════════════════════════════════════════════

# 关键词 / 主题词典（可扩展）
KEYWORD_MAP = {
    '感觉/直觉':    r'感觉|直觉|intuition|gut|靠感觉|凭感觉|第一印象|说不上来',
    '手指/解剖':    r'手指|手部|解剖|人体|anatomy|透视|身体|指头',
    '纹理/细节':    r'纹理|texture|细节|像素|模糊|清晰|blur|质感|质量',
    '光影/色彩':    r'光影|色彩|光线|颜色|color|阴影|对比|明暗|shadow',
    '背景/构图':    r'背景|构图|合成|融合|图层|逻辑|整体|比例|透视',
    '绘画/风格':    r'风格|画风|绘画|插画|动画|cartoon|风格|style',
    '搜索/工具':    r'搜索|Google|谷歌|lens|反向|search|搜图',
    '文字/标志':    r'文字|text|字|标志|logo|sign|水印|watermark',
    'AI特征':      r'AI|人工智能|fake|虚假|假|合成|不自然|突兀|违和',
    '经验/常识':    r'经验|常识|日常|生活|知道|了解|熟悉',
}

def classify_keywords(text_series):
    """对每个类别计数匹配条数"""
    counts = {}
    for lbl, pat in KEYWORD_MAP.items():
        mask = text_series.str.contains(pat, case=False, na=False, regex=True)
        counts[lbl] = mask.sum()
    return pd.Series(counts)

lines = []

lines.append('# 策略文本分析报告\n')
lines.append(f'样本：对照组 n={sum(v=="对照" for v in pid_group.values())}，'
             f'实验组 n={sum(v=="实验" for v in pid_group.values())}\n')

# ── 1. 逐图 reasoning 概览 ──────────────────────────────────────────────────
lines.append('## 一、逐图理由（reasoning）概览\n')

n_resp_tot = len(resp[resp['participant_id'].isin(pid_group)])
lines.append(f'- 有效图片回答总数：{n_resp_tot} 条\n')
lines.append(f'- 填写了理由：{len(r_text)} 条（填写率 {len(r_text)/n_resp_tot:.1%}），'
             f'涉及 {r_text["participant_id"].nunique()} 人\n\n')

# 按组填写率
for grp in ['对照', '实验']:
    tot_g = len(resp[resp['group'] == grp])
    has_g = len(r_text[r_text['group'] == grp])
    lines.append(f'  - {grp}组：{has_g}/{tot_g} 条 ({has_g/tot_g:.1%})\n')
lines.append('\n')

# 填写理由时的正确率 vs 未填写
r_text_correct  = r_text['is_correct'].mean()
no_text_correct = resp[(resp['reasoning'].isna()) |
                       (resp['reasoning'].str.strip() == '')]['is_correct'].mean()
lines.append(f'- 填写理由时正确率：{r_text_correct:.3f}\n')
lines.append(f'- 未填写理由时正确率：{no_text_correct:.3f}\n\n')

# ── 2. 关键词频率（逐图）──────────────────────────────────────────────────────
lines.append('## 二、逐图理由关键词类别频率\n')

kw_all = classify_keywords(r_text['reasoning'])
kw_A   = classify_keywords(r_text[r_text['group']=='对照']['reasoning'])
kw_C   = classify_keywords(r_text[r_text['group']=='实验']['reasoning'])

lines.append('| 关键词类别 | 全样本 n | 全样本 % | 对照组 n | 对照组 % | 实验组 n | 实验组 % |\n')
lines.append('|:---------|--------:|---------:|-----:|------:|-----:|------:|\n')
n_all = len(r_text)
n_a   = len(r_text[r_text['group']=='对照'])
n_c   = len(r_text[r_text['group']=='实验'])
for lbl in KEYWORD_MAP:
    a_n, c_n, all_n = kw_A[lbl], kw_C[lbl], kw_all[lbl]
    lines.append(f'| {lbl} | {all_n} | {all_n/n_all:.1%} | {a_n} | {a_n/n_a:.1%} | {c_n} | {c_n/n_c:.1%} |\n')
lines.append('\n')

# ── 3. 高频词（简单词频，中英混合分词用空格/标点切）────────────────────────────
lines.append('## 三、高频词（逐图理由，Top 30）\n')

def tokenize_zh(text):
    """简单按标点/空格切词，保留长度≥2的中文片段"""
    text = str(text)
    tokens = re.split(r'[\s，。！？、；：,.!?;:\(\)（）【】\[\]]+', text)
    out = []
    for t in tokens:
        t = t.strip()
        if len(t) >= 2:
            out.append(t)
    return out

stopwords = {'感觉', '一个', '这个', '因为', '然后', '所以', '看起来', '感觉像',
             '觉得', '可能', '应该', '比较', '有点', '一些', '这种', '看上去',
             'the', 'a', 'is', 'it', 'of', 'in', 'and', 'or', 'to', 'that',
             '图片', '图像', '这张', '这幅', '这个图', '该图', '照片', '这张图'}

all_tokens = []
for txt in r_text['reasoning']:
    all_tokens.extend(tokenize_zh(txt))
all_tokens = [t for t in all_tokens if t not in stopwords]
freq = Counter(all_tokens).most_common(30)

lines.append('| 排名 | 词/短语 | 频次 |\n')
lines.append('|:---:|:------|----:|\n')
for rank, (word, cnt) in enumerate(freq, 1):
    lines.append(f'| {rank} | {word} | {cnt} |\n')
lines.append('\n')

# ── 4. 结尾自述策略 ──────────────────────────────────────────────────────────
lines.append('## 四、结尾自述策略（open_method）\n')

lines.append(f'填写人数：{len(end_text)}（其中对照组 {(end_text["group"]=="对照").sum()} 人，'
             f'实验组 {(end_text["group"]=="实验").sum()} 人）\n\n')

kw_end_A = classify_keywords(end_text[end_text['group']=='对照']['end_strategy'])
kw_end_C = classify_keywords(end_text[end_text['group']=='实验']['end_strategy'])
kw_end   = classify_keywords(end_text['end_strategy'])
n_ea = (end_text['group']=='对照').sum()
n_ec = (end_text['group']=='实验').sum()
n_et = len(end_text)

lines.append('### 4.1 关键词类别频率（结尾策略）\n')
lines.append('| 关键词类别 | 全样本 n | 全样本 % | 对照组 n | 对照组 % | 实验组 n | 实验组 % |\n')
lines.append('|:---------|--------:|---------:|-----:|------:|-----:|------:|\n')
for lbl in KEYWORD_MAP:
    a_n, c_n, all_n = kw_end_A[lbl], kw_end_C[lbl], kw_end[lbl]
    lines.append(f'| {lbl} | {all_n} | {all_n/n_et:.1%} | {a_n} | {a_n/n_ea:.1%} | {c_n} | {c_n/n_ec:.1%} |\n')
lines.append('\n')

lines.append('### 4.2 结尾策略原文列表\n\n')
lines.append('| 参与者 | 组别 | 策略使用程度 | 自述策略 |\n')
lines.append('|:------|:---:|:-----------:|:-------|\n')
for _, row in end_text.iterrows():
    pid_short = row['participant_id'][:8] + '…'
    deg = row['strategy_usage_degree'] if pd.notna(row['strategy_usage_degree']) else '—'
    lines.append(f"| {pid_short} | {row['group']} | {deg} | {row['end_strategy']} |\n")
lines.append('\n')

# ── 5. 主题归纳（人工分类后统计）────────────────────────────────────────────
lines.append('## 五、策略主题分布（两来源合并）\n')

all_strat = pd.concat([
    r_text[['participant_id','group','reasoning']].rename(columns={'reasoning':'text'}),
    end_text[['participant_id','group','end_strategy']].rename(columns={'end_strategy':'text'})
], ignore_index=True)

kw_combined = classify_keywords(all_strat['text'])
n_tot = len(all_strat)

lines.append(f'合并条数：{n_tot}（逐图理由 {len(r_text)} + 结尾自述 {len(end_text)}）\n\n')
lines.append('| 策略主题 | 出现次数 | 占比 |\n')
lines.append('|:--------|-------:|---------:|\n')
for lbl, cnt in kw_combined.sort_values(ascending=False).items():
    lines.append(f'| {lbl} | {cnt} | {cnt/n_tot:.1%} |\n')
lines.append('\n')

# ── 6. 样例摘录（每类选2条代表性文本）──────────────────────────────────────
lines.append('## 六、各主题代表性文本摘录\n\n')
for lbl, pat in KEYWORD_MAP.items():
    matched = r_text[r_text['reasoning'].str.contains(pat, case=False, na=False, regex=True)]
    if matched.empty:
        continue
    lines.append(f'**{lbl}**\n\n')
    for _, row in matched.head(3).iterrows():
        pid_short = row['participant_id'][:8] + '…'
        correct = '✓' if row['is_correct'] else '✗'
        lines.append(f'- [{row["group"]}组 {pid_short} / {row["image_id"]} {correct}] {row["reasoning"]}\n')
    lines.append('\n')

# 写文件
report_path = f'{OUT_DIR}/strategy_text_report.md'
with open(report_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f'\n输出文件：')
print(f'  {OUT_DIR}/strategy_per_image.csv')
print(f'  {OUT_DIR}/strategy_end.csv')
print(f'  {OUT_DIR}/strategy_text_report.md')
