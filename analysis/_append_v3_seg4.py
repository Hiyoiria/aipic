#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""追加 formal_analysis_v3.py 第四段（八、策略分析 + 词频 + 聚类）"""
import os

TARGET = os.path.join(os.path.dirname(__file__), 'formal_analysis_v3.py')

SEG = '''

# ═══════════════════════════════════════════════════════════════════
# 八、策略使用程度分析 + 自报策略词频/聚类
# ═══════════════════════════════════════════════════════════════════
h2(\'八、策略使用程度分析\')

h3(\'8.1 策略使用程度（strategy_usage_degree）描述与组间比较\')
pr(\'> 仅实验组填写此变量；对照组不适用。\\n\')

deg_c = master[master[\'group\']==\'实验\'][\'strategy_usage_degree\'].dropna()
deg_a = master[master[\'group\']==\'对照\'][\'strategy_usage_degree\'].dropna()

if len(deg_c) > 1:
    pr(f\'**实验组**: n={len(deg_c)}, M={deg_c.mean():.3f}, SD={deg_c.std(ddof=1):.3f}, \')
    pr(f\'Mdn={deg_c.median():.3f}, IQR={float(np.percentile(deg_c,75)-np.percentile(deg_c,25)):.3f}, \')
    pr(f\'min={deg_c.min():.1f}, max={deg_c.max():.1f}\')

# 分布
if len(deg_c) > 1:
    vc = deg_c.value_counts().sort_index()
    dist_rows = [[str(int(k) if k == int(k) else k), str(v), f\'{v/len(deg_c)*100:.1f}%\'] for k, v in vc.items()]
    md_table([\'策略使用程度值\',\'n\',\'%\'], dist_rows)

# 与准确率的相关（实验组）
paired_deg = master[master[\'group\']==\'实验\'][[\'acc_total\',\'strategy_usage_degree\',\'dprime\']].dropna()
if len(paired_deg) > 3:
    r_acc, p_acc = stats.pearsonr(paired_deg[\'acc_total\'], paired_deg[\'strategy_usage_degree\'])
    r_dp,  p_dp  = stats.pearsonr(paired_deg[\'dprime\'],    paired_deg[\'strategy_usage_degree\'])
    md_table(
        [\'因变量\',\'r（与策略使用程度）\',\'*p*\',\'n\'],
        [
            [\'整体正确率\', fmt_r(r_acc), fmt_p(p_acc)+stars(p_acc), str(len(paired_deg))],
            ["d\' (SDT)", fmt_r(r_dp),  fmt_p(p_dp)+stars(p_dp),  str(len(paired_deg))],
        ]
    )

# 回归：strategy_usage_degree → acc_total（实验组）
if len(paired_deg) > 5:
    _m_deg = smf.ols(\'acc_total ~ strategy_usage_degree\', data=paired_deg).fit()
    pr(f\'\\n> **实验组内回归** (acc ~ strategy_usage_degree): \')
    pr(f\'> B={_m_deg.params["strategy_usage_degree"]:.3f}, \')
    pr(f\'SE={_m_deg.bse["strategy_usage_degree"]:.3f}, \')
    pr(f\'t={_m_deg.tvalues["strategy_usage_degree"]:.3f}, \')
    pr(f\'p={fmt_p(_m_deg.pvalues["strategy_usage_degree"])+stars(_m_deg.pvalues["strategy_usage_degree"])}, \')
    pr(f\'R²={_m_deg.rsquared:.3f}\')

h3(\'8.2 逐图策略填写率\')
STRATEGY_KEYWORDS = {
    \'Anatomy\':  [\'手\',\'finger\',\'解剖\',\'手指\',\'脸\',\'face\',\'eye\',\'眼\',\'anatomy\',\'fingers\',\'skin\',\'hair\',\'头发\'],
    \'Style\':    [\'风格\',\'style\',\'texture\',\'纹理\',\'质感\',\'光滑\',\'塑料\',\'背景\',\'光影\',\'颜色\',\'渲染\',\'完美\'],
    \'Knowledge\':[\'搜索\',\'search\',\'google\',\'lens\',\'网站\',\'来源\',\'source\',\'reverse\'],
}

def code_strategy(text):
    if pd.isna(text) or str(text).strip() == \'\': return None
    t = str(text).lower()
    tags = [k for k,ws in STRATEGY_KEYWORDS.items() if any(w in t for w in ws)]
    return \',\'.join(tags) if tags else \'直觉/其他\'

r_strat = r_m.copy()
r_strat[\'strategy_cat\'] = r_strat[\'reasoning\'].apply(code_strategy)
r_strat[\'has_strategy\'] = r_strat[\'strategy_cat\'].notna().astype(int)

fill = r_strat.groupby(\'group\')[\'has_strategy\'].agg(
    填写率=lambda x: f\'{x.mean():.3f}\',
    填写次数=\'sum\', 总次数=\'count\').reset_index()
md_table(list(fill.columns), fill.values.tolist())

h3(\'8.3 策略类别 × 正确率\')
cat_rows = []
for cat in [\'Style\',\'Anatomy\',\'Knowledge\',\'直觉/其他\']:
    for grp in [\'对照\',\'实验\']:
        sub_r = r_strat[(r_strat[\'group\']==grp) &
                        (r_strat[\'strategy_cat\'].notna()) &
                        (r_strat[\'strategy_cat\'].str.contains(cat, na=False))]
        if len(sub_r) > 0:
            cat_rows.append([grp, cat, str(len(sub_r)), f\'{sub_r["is_correct"].mean():.3f}\'])
if cat_rows:
    md_table([\'组别\',\'策略类型\',\'n\',\'正确率\'], cat_rows)

# ═══════════════════════════════════════════════════════════════════
# 九、自报策略文本词频分析
# ═══════════════════════════════════════════════════════════════════
h2(\'九、自报策略文本词频与聚类分析（open_method）\')
pr(\'> 数据来源：后测问卷 open_method（结尾自述策略）。\\n\')

# 合并 post_survey
pid_group = master.set_index(\'participant_id\')[\'group\'].to_dict()
post[\'group\'] = post[\'participant_id\'].map(pid_group)

def is_meaningful(s):
    s = str(s).strip()
    if re.fullmatch(r\'\\d+\', s): return False
    if len(s) <= 2 and not re.search(r\'[\\u4e00-\\u9fff]\', s): return False
    return True

end_text = post[post[\'open_method\'].notna() & post[\'open_method\'].apply(is_meaningful)].copy()
end_text = end_text[end_text[\'participant_id\'].isin(master[\'participant_id\'])].copy()
end_text[\'group\'] = end_text[\'participant_id\'].map(pid_group)

pr(f\'有效策略文本：{len(end_text)} 条（对照={( end_text["group"]=="对照").sum()}，实验={(end_text["group"]=="实验").sum()}）\\n\')

h3(\'9.1 高频词（Top 30）\')

STOP = {\'感觉\',\'一个\',\'这个\',\'因为\',\'然后\',\'所以\',\'看起来\',\'可能\',\'应该\',
        \'比较\',\'有点\',\'一些\',\'这种\',\'看上去\',\'觉得\',\'图片\',\'图像\',\'这张\',
        \'照片\',\'该图\',\'这幅\',\'the\',\'a\',\'is\',\'it\',\'of\',\'in\',\'and\',\'or\',\'to\'}

def tokenize_zh(text):
    text = str(text)
    tokens = re.split(r\'[\\s，。！？、；：,.!?;:\\(\\)（）【】\\[\\]]+\', text)
    return [t.strip() for t in tokens if len(t.strip()) >= 2]

all_tokens = []
for txt in end_text[\'open_method\']:
    all_tokens.extend(tokenize_zh(str(txt)))
all_tokens = [t for t in all_tokens if t not in STOP]
freq = Counter(all_tokens).most_common(30)

md_table([\'排名\',\'词/短语\',\'频次\'],
         [[str(rank), word, str(cnt)] for rank, (word, cnt) in enumerate(freq, 1)])

h3(\'9.2 关键词类别频率\')
KEYWORD_MAP = {
    \'感觉/直觉\':  r\'感觉|直觉|intuition|gut|靠感觉|凭感觉|第一印象\',
    \'手指/解剖\':  r\'手指|手部|解剖|人体|透视|身体\',
    \'纹理/细节\':  r\'纹理|texture|细节|像素|模糊|质感\',
    \'光影/色彩\':  r\'光影|色彩|光线|颜色|阴影|对比|明暗\',
    \'背景/构图\':  r\'背景|构图|合成|融合|整体|比例\',
    \'绘画/风格\':  r\'风格|画风|绘画|插画|动画|style\',
    \'搜索/工具\':  r\'搜索|Google|谷歌|lens|反向|search\',
    \'文字/标志\':  r\'文字|text|字|标志|logo|水印\',
    \'AI特征\':    r\'AI|人工智能|fake|虚假|假|合成|不自然\',
    \'经验/常识\':  r\'经验|常识|日常|生活|了解|熟悉\',
}

def classify_kw(text_series):
    counts = {}
    for lbl, pat in KEYWORD_MAP.items():
        mask = text_series.str.contains(pat, case=False, na=False, regex=True)
        counts[lbl] = mask.sum()
    return pd.Series(counts)

kw_all = classify_kw(end_text[\'open_method\'])
kw_a   = classify_kw(end_text[end_text[\'group\']==\'对照\'][\'open_method\'])
kw_c   = classify_kw(end_text[end_text[\'group\']==\'实验\'][\'open_method\'])
n_all = len(end_text)
n_ea  = (end_text[\'group\']==\'对照\').sum()
n_ec  = (end_text[\'group\']==\'实验\').sum()

kw_rows = []
for lbl in KEYWORD_MAP:
    a_n, c_n, all_n = kw_a.get(lbl,0), kw_c.get(lbl,0), kw_all.get(lbl,0)
    kw_rows.append([lbl, str(all_n), f\'{all_n/n_all:.1%}\' if n_all else \'—\',
                    str(a_n), f\'{a_n/n_ea:.1%}\' if n_ea else \'—\',
                    str(c_n), f\'{c_n/n_ec:.1%}\' if n_ec else \'—\'])
md_table([\'关键词类别\',\'全样本n\',\'全样本%\',\'对照n\',\'对照%\',\'实验n\',\'实验%\'], kw_rows)

h3(\'9.3 策略聚类分析（K-means，基于关键词特征向量）\')
pr(\'> 将每条策略文本编码为关键词出现向量（10维），再用 K-means（k=3）聚类。\\n\')

try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    feature_matrix = np.column_stack([
        end_text[\'open_method\'].str.contains(pat, case=False, na=False, regex=True).astype(int)
        for pat in KEYWORD_MAP.values()
    ])

    if feature_matrix.shape[0] >= 6:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(feature_matrix.astype(float))
        kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_scaled)
        end_text = end_text.copy()
        end_text[\'cluster\'] = labels

        cl_rows = []
        for ci in sorted(end_text[\'cluster\'].unique()):
            sub_c = end_text[end_text[\'cluster\']==ci]
            n_ci = len(sub_c)
            n_exp = (sub_c[\'group\']==\'实验\').sum()
            # 该簇最主要关键词（按均值排序）
            sub_feat = feature_matrix[end_text[\'cluster\']==ci]
            top_kw = [list(KEYWORD_MAP.keys())[i] for i in np.argsort(sub_feat.mean(axis=0))[::-1][:3]]
            cl_rows.append([f\'簇 {ci+1}\', str(n_ci),
                            f\'{n_exp}/{n_ci} ({n_exp/n_ci*100:.0f}%)\',
                            \', \'.join(top_kw)])
        md_table([\'簇\',\'n\',\'实验组比例\',\'主要关键词\'], cl_rows)

        # 各簇准确率（有 acc_total 的）
        sub_acc = end_text.merge(master[[\'participant_id\',\'acc_total\']], on=\'participant_id\', how=\'left\')
        acc_cl_rows = []
        for ci in sorted(sub_acc[\'cluster\'].unique()):
            sc = sub_acc[sub_acc[\'cluster\']==ci][\'acc_total\'].dropna()
            acc_cl_rows.append([f\'簇 {ci+1}\', str(len(sc)), ms(sc.values) if len(sc)>1 else \'—\'])
        if acc_cl_rows:
            md_table([\'簇\',\'n(有准确率)\',\'准确率 M (SD)\'], acc_cl_rows)
    else:
        pr(\'> ⚠ 样本量不足，跳过聚类\')
except ImportError:
    pr(\'> ⚠ scikit-learn 未安装，跳过聚类分析\')
'''

with open(TARGET, 'a', encoding='utf-8') as f:
    f.write(SEG)
print('seg4 OK')
