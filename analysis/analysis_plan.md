# 分析计划文档
## AI生成图像识别实验：统计分析方案与完整代码

---

## 1. 分析维度概览

| 维度 | 分析目标 | 主要方法 |
|------|----------|----------|
| **数据清理** | 确定有效样本 | 完成标记 + 注意力检验过滤 |
| **操纵检验** | 验证干预被吸收 | 描述统计 + χ² 检验 |
| **主效应：准确率** | H1 检验 | 独立样本 t 检验 / Mann-Whitney U |
| **信号检测理论** | 分离灵敏度与响应偏向 | d'、criterion c |
| **信心分析** | H2 检验 | 独立样本 t 检验 |
| **反应时分析** | 策略使用的时间代价 | Mann-Whitney U |
| **工具使用行为** | H3 检验（Lens搜索） | χ² 检验 + Mann-Whitney U |
| **自我效能变化** | H4 检验 | 配对 t 检验 + 组间比较 |
| **图像项目分析** | 找出难/易题目 | 图像级准确率 + 组间差异 |
| **个体差异回归** | H5 检验 | 线性回归 |
| **调节效应** | H6 检验 | 含交互项的回归 |

---

## 2. 数据清理标准

### 2.1 参与者排除标准（按序执行）

1. **未完成实验**：`completed ≠ true` → 排除
2. **注意力检验失败**：`attention_check_answer ≠ 5` → 排除（主分析）
3. **非目标组别**：组B数据（历史测试）→ 分析时仅保留 A、C 两组
4. **操纵检验失败（敏感性分析用）**：组C中 `manipulation_check_strategies = 'no'` → 标记，主分析保留，敏感性分析时排除对比

### 2.2 响应级排除

- 异常反应时：`response_time_ms < 500ms`（点击过快，可能无效）→ 标记并在响应时分析中排除（不影响准确率计算）

---

## 3. 各维度分析原理

### 3.1 独立样本 t 检验（准确率、信心比较）

**原理**：比较两个独立组的均值差异。检验统计量：

$$t = \frac{\bar{X}_C - \bar{X}_A}{\sqrt{s_p^2 \cdot (\frac{1}{n_C} + \frac{1}{n_A})}}$$

前提假设通过 **Levene 方差齐性检验** 验证。若不满足正态性（小样本），改用非参数 **Mann-Whitney U 检验**。

**效应量 Cohen's d**：

$$d = \frac{\bar{X}_C - \bar{X}_A}{s_{pooled}}, \quad s_{pooled} = \sqrt{\frac{(n_C-1)s_C^2 + (n_A-1)s_A^2}{n_C+n_A-2}}$$

解释标准：|d| < 0.2=可忽略，0.2-0.5=小，0.5-0.8=中，>0.8=大。

### 3.2 信号检测理论（SDT）

**原理**：传统准确率混淆了两个独立心理过程：
- **灵敏度（d'）**：参与者区分AI与真实图像的能力，不受回答策略影响
- **响应偏向（criterion c）**：参与者在不确定时倾向于说"AI"还是"真实"

**定义**：
- Hit（击中率）：P(判断=AI | 图像是AI)
- False Alarm（虚报率）：P(判断=AI | 图像是真实)

**计算公式**：

$$d' = Z(\text{Hit Rate}) - Z(\text{FA Rate})$$

$$c = -\frac{1}{2}[Z(\text{Hit Rate}) + Z(\text{FA Rate})]$$

其中 Z(·) 为标准正态分布的反函数（probit 变换）。

**边界修正**：当 Hit Rate=0/1 或 FA Rate=0/1 时，使用 log-linear 修正：

$$p_{corrected} = \frac{n \cdot p + 0.5}{n + 1}$$

**解释**：
- d' > 0：能够区分两类图像；d' = 0：完全无法区分
- c = 0：无偏向；c > 0：保守（倾向于说"真实"）；c < 0：宽松（倾向于说"AI"）

策略培训应提升 d'（灵敏度提升），c 的变化反映判断偏向改变。

### 3.3 χ² 检验（分类变量比较）

**用途**：比较两组间某行为的发生率（如Lens使用率、操纵检验通过率）。

$$\chi^2 = \sum \frac{(O-E)^2}{E}$$

**效应量**：Cramér's V = √(χ²/n)，V<0.1=小，0.1-0.3=中，>0.3=大。

当单元格期望频次<5时，使用 Fisher 精确检验。

### 3.4 配对 t 检验（自我效能前后测）

**原理**：同一参与者在实验前后两次测量，计算差值后对差值均值进行单样本 t 检验。比独立样本 t 更有效，因为消除了个体间差异。

$$t = \frac{\bar{d}}{s_d / \sqrt{n}}$$

其中 $\bar{d}$ = 每人的前后差值均值，$s_d$ = 差值的标准差。

### 3.5 线性回归（个体差异与调节效应）

**主效应回归**（H5）：

$$\text{accuracy} = \beta_0 + \beta_1 \cdot \text{group} + \beta_2 \cdot \text{ai\_familiarity} + \beta_3 \cdot \text{ai\_exposure\_freq} + \beta_4 \cdot \text{ai\_tool\_usage} + \varepsilon$$

**调节效应**（H6）：在上述模型中加入交互项，检验 AI 熟悉度是否调节组别效应：

$$\text{accuracy} = \beta_0 + \beta_1 \cdot \text{group} + \beta_2 \cdot \text{ai\_familiarity} + \beta_3 \cdot (\text{group} \times \text{ai\_familiarity}) + \text{covariates} + \varepsilon$$

若 $\beta_3$ 显著，则存在调节效应。解读时需做**简单斜率分析**：在 ai_familiarity 的高（M+1SD）、中（M）、低（M-1SD）水平下，分别报告组别效应的大小。

**前提检验**：残差正态性（Shapiro-Wilk）、方差齐性（BP检验）、多重共线性（VIF < 10）。

---

## 4. 完整 Python 分析代码

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Study 2 完整分析脚本 (v2)
============================
前置：先运行 fetch_data.py 下载数据到 analysis/data/

运行：
    python analysis/analyze.py

输出：analysis/output/ 目录下的统计报告、图表、汇总数据集

依赖：
    pip install pandas numpy scipy statsmodels matplotlib seaborn
"""

import os
import sys
import warnings
import pandas as pd
import numpy as np
from scipy import stats
from scipy.special import ndtri   # probit (Z变换)
import statsmodels.formula.api as smf
import statsmodels.stats.api as sms
from statsmodels.stats.outliers_influence import variance_inflation_factor

warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8')

# ─── 路径 ───────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(__file__)
DATA_DIR  = os.path.join(BASE_DIR, 'data')
OUT_DIR   = os.path.join(BASE_DIR, 'output')
os.makedirs(OUT_DIR, exist_ok=True)


# ============================================================
# 工具函数
# ============================================================

def load(name):
    path = os.path.join(DATA_DIR, f'{name}.csv')
    if not os.path.exists(path):
        print(f"  [WARN] 找不到 {path}，跳过。")
        return None
    df = pd.read_csv(path)
    print(f"  加载 {name}: {len(df)} 行 × {len(df.columns)} 列")
    return df


def section(title):
    print(f"\n{'='*62}")
    print(f"  {title}")
    print('='*62)


def save(df, name):
    path = os.path.join(OUT_DIR, f'{name}.csv')
    df.to_csv(path, index=False, encoding='utf-8-sig')
    print(f"  -> 已保存：{path}")


def cohens_d(x, y):
    """计算 Cohen's d（合并标准差）"""
    nx, ny = len(x), len(y)
    sp = np.sqrt(((nx-1)*np.std(x, ddof=1)**2 + (ny-1)*np.std(y, ddof=1)**2) / (nx+ny-2))
    return (np.mean(x) - np.mean(y)) / sp if sp > 0 else np.nan


def cramers_v(chi2, n, dof):
    """计算 Cramér's V"""
    return np.sqrt(chi2 / (n * min(dof, 1))) if n > 0 else np.nan


def sdt_metrics(hits, misses, fas, crs):
    """
    信号检测理论：计算 d' 与 criterion c
    hits   = 将AI图像判断为AI的次数（击中）
    misses = 将AI图像判断为Real的次数（漏报）
    fas    = 将Real图像判断为AI的次数（虚报）
    crs    = 将Real图像判断为Real的次数（正确拒绝）

    使用 log-linear 边界修正，避免 HR 或 FAR = 0/1 导致 Z = ±∞
    """
    n_signal = hits + misses    # AI图像总数
    n_noise  = fas + crs        # Real图像总数

    # log-linear 修正
    hr  = (hits + 0.5) / (n_signal + 1) if n_signal > 0 else 0.5
    far = (fas  + 0.5) / (n_noise  + 1) if n_noise  > 0 else 0.5

    z_hr  = ndtri(hr)
    z_far = ndtri(far)

    d_prime   = z_hr - z_far
    criterion = -0.5 * (z_hr + z_far)
    return round(d_prime, 4), round(criterion, 4), round(hr, 4), round(far, 4)


def report_test(label, stat, p, effect=None, effect_label='d'):
    """统一格式打印检验结果"""
    sig = '***' if p < .001 else ('**' if p < .01 else ('*' if p < .05 else 'n.s.'))
    eff = f", {effect_label}={effect:.3f}" if effect is not None and not np.isnan(effect) else ''
    print(f"  {label}: stat={stat:.4f}, p={p:.4f} {sig}{eff}")


# ============================================================
# 图像元数据（用于图像级分析）
# ============================================================

IMAGE_META = {
    **{f'ai_{i:02d}': {'type': 'AI',   'style': s, 'source': src}
       for i, s, src in [
           (1,'illustration','ai-art'),(2,'photograph','ai-art'),(3,'cartoon','ai-art'),
           (4,'cartoon','ai-art'),(5,'illustration','ai-art'),(6,'photograph','ai-art'),
           (7,'illustration','midjourney'),(8,'photograph','midjourney'),(9,'cartoon','midjourney'),
           (10,'photograph','midjourney'),(11,'illustration','midjourney'),(12,'illustration','midjourney'),
           (13,'photograph','midjourney'),(14,'illustration','nanobanana'),(15,'photograph','nanobanana'),
           (16,'illustration','nanobanana'),(17,'photograph','nanobanana'),(18,'cartoon','nanobanana'),
           (19,'photograph','nanobanana'),(20,'illustration','nanobanana'),
       ]},
    **{f'real_{i:02d}': {'type': 'Real', 'style': s, 'source': src}
       for i, s, src in [
           (1,'illustration','camera'),(2,'photograph','camera'),(3,'cartoon','camera'),
           (4,'photograph','camera'),(5,'illustration','camera'),(6,'photograph','camera'),
           (7,'illustration','website'),(8,'photograph','website'),(9,'illustration','website'),
           (10,'illustration','website'),(11,'photograph','website'),(12,'photograph','website'),
           (13,'illustration','website'),(14,'cartoon','website'),(15,'illustration','website'),
           (16,'photograph','website'),(17,'illustration','website'),(18,'photograph','website'),
           (19,'illustration','website'),(20,'cartoon','website'),
       ]},
}


# ============================================================
# 主分析
# ============================================================

def main():

    # ──────────────────────────────────────────────────────
    # §0  加载数据
    # ──────────────────────────────────────────────────────
    section("§0  加载数据")
    participants   = load('participants')
    responses      = load('responses')
    post_survey    = load('post-survey')
    interaction_logs = load('interaction-logs')

    if participants is None or responses is None:
        print("\n错误：participants.csv 和 responses.csv 是必需文件。")
        print("请先运行 fetch_data.py 下载数据。")
        return

    # ──────────────────────────────────────────────────────
    # §1  数据清理与筛选
    # ──────────────────────────────────────────────────────
    section("§1  数据清理")

    print(f"\n  原始参与者总数：{len(participants)}")

    # 1-a 仅保留 A / C 组（排除历史测试的 B 组）
    ac = participants[participants['group'].isin(['A', 'C'])].copy()
    print(f"  A/C 组参与者：{len(ac)}")

    # 1-b 完成实验
    completed = ac[ac['completed'] == True].copy()
    print(f"  已完成实验：{len(completed)}")
    print(f"  未完成（排除）：{len(ac) - len(completed)}")

    # 1-c 注意力检验
    if post_survey is not None and 'attention_check_passed' in post_survey.columns:
        failed_attn = post_survey[post_survey['attention_check_passed'] == False]['participant_id'].tolist()
        print(f"  注意力检验失败：{len(failed_attn)}")
        valid = completed[~completed['participant_id'].isin(failed_attn)].copy()
    else:
        valid = completed.copy()
        failed_attn = []

    print(f"\n  ✓ 有效分析样本：{len(valid)} 人")
    valid_ids = set(valid['participant_id'])

    # 1-d 组C操纵检验失败者标记（用于敏感性分析）
    manip_fail_ids = set()
    if post_survey is not None and 'manipulation_check_strategies' in post_survey.columns:
        c_ps = post_survey[post_survey['participant_id'].isin(
            valid[valid['group'] == 'C']['participant_id']
        )]
        # 新版字段为 yes/no，旧版为 array；统一处理
        def passed_manip(val):
            if pd.isna(val):
                return False
            v = str(val).strip().lower()
            # 新版：'yes' 通过
            if v in ('yes', 'no'):
                return v == 'yes'
            # 旧版：包含 'texture' 算通过
            return 'texture' in v
        fail_mask = ~c_ps['manipulation_check_strategies'].apply(passed_manip)
        manip_fail_ids = set(c_ps[fail_mask]['participant_id'])
        print(f"  C组操纵检验失败（标记，不排除）：{len(manip_fail_ids)} 人")

    # 1-e 过滤响应数据
    resp = responses[responses['participant_id'].isin(valid_ids)].copy()
    resp['is_correct'] = resp['is_correct'].astype(bool)
    resp['response_time_s'] = resp['response_time_ms'] / 1000
    print(f"  有效响应条数：{len(resp)}")

    # 添加图像元数据
    resp['img_type']   = resp['image_id'].map(lambda x: IMAGE_META.get(x, {}).get('type'))
    resp['img_style']  = resp['image_id'].map(lambda x: IMAGE_META.get(x, {}).get('style'))
    resp['img_source'] = resp['image_id'].map(lambda x: IMAGE_META.get(x, {}).get('source'))

    # ──────────────────────────────────────────────────────
    # §2  样本描述
    # ──────────────────────────────────────────────────────
    section("§2  样本描述与组别平衡")

    group_n = valid['group'].value_counts().sort_index()
    print(f"\n  组A（控制组）：N={group_n.get('A',0)}")
    print(f"  组C（策略组）：N={group_n.get('C',0)}")

    print("\n  人口统计：")
    for col in ['age', 'gender', 'education', 'ai_tool_usage', 'ai_exposure_freq']:
        if col not in valid.columns:
            continue
        print(f"\n  [{col}]")
        counts = valid[col].value_counts(dropna=False)
        for val, cnt in counts.items():
            print(f"    {val}: {cnt} ({cnt/len(valid)*100:.1f}%)")

    for col in ['ai_familiarity', 'self_assessed_ability']:
        if col not in valid.columns:
            continue
        vals = pd.to_numeric(valid[col], errors='coerce').dropna()
        if len(vals):
            print(f"\n  [{col}] M={vals.mean():.2f}, SD={vals.std():.2f}, "
                  f"range=[{vals.min():.0f}–{vals.max():.0f}]")

    # 检验两组在协变量上是否均衡（教育、AI熟悉度）
    print("\n  组间基线均衡性检验：")
    edu_map = {'high-school':1,'some-college':2,'bachelors':3,'masters':4,'doctorate':5}
    valid['edu_num'] = valid['education'].map(edu_map)
    for col in ['ai_familiarity', 'self_assessed_ability', 'edu_num']:
        if col not in valid.columns:
            continue
        a_vals = pd.to_numeric(valid[valid['group']=='A'][col], errors='coerce').dropna()
        c_vals = pd.to_numeric(valid[valid['group']=='C'][col], errors='coerce').dropna()
        if len(a_vals) > 1 and len(c_vals) > 1:
            t, p = stats.ttest_ind(a_vals, c_vals)
            d = cohens_d(c_vals, a_vals)
            report_test(f"  基线 {col}", t, p, d)

    # ──────────────────────────────────────────────────────
    # §3  操纵检验
    # ──────────────────────────────────────────────────────
    section("§3  操纵检验")

    if post_survey is not None:
        ps = post_survey[post_survey['participant_id'].isin(valid_ids)].copy()

        # 3-a 是否阅读了材料
        print("\n  [3-a] 自报阅读干预材料情况（manipulation_check_read）")
        for g in ['A', 'C']:
            g_ids = valid[valid['group']==g]['participant_id']
            g_ps  = ps[ps['participant_id'].isin(g_ids)]
            if 'manipulation_check_read' in g_ps.columns:
                vc = g_ps['manipulation_check_read'].value_counts(dropna=False)
                yes_rate = vc.get('yes', 0) / len(g_ps) * 100 if len(g_ps) else 0
                print(f"    组{g}: 是={vc.get('yes',0)}, 否={vc.get('no',0)}, "
                      f"不确定={vc.get('not_sure',0)} | 确认率={yes_rate:.1f}%")

        # 3-b 组C策略记忆检验（是否记得"检查风格与纹理"）
        print("\n  [3-b] 策略记忆检验（组C，manipulation_check_strategies）")
        c_ids = valid[valid['group']=='C']['participant_id']
        c_ps  = ps[ps['participant_id'].isin(c_ids)]
        if 'manipulation_check_strategies' in c_ps.columns and len(c_ps):
            passed = c_ps['manipulation_check_strategies'].apply(passed_manip)
            pass_n = passed.sum()
            print(f"    通过：{pass_n}/{len(c_ps)} ({pass_n/len(c_ps)*100:.1f}%)")
            print(f"    未通过：{len(c_ps)-pass_n}/{len(c_ps)}")

        # 3-c 策略使用程度（组C）
        if 'strategy_usage_degree' in ps.columns:
            su = pd.to_numeric(c_ps['strategy_usage_degree'], errors='coerce').dropna()
            if len(su):
                print(f"\n  [3-c] 策略使用程度（组C，1-5分）：M={su.mean():.2f}, SD={su.std():.2f}")

    # ──────────────────────────────────────────────────────
    # §4  准确率分析（主假设 H1）
    # ──────────────────────────────────────────────────────
    section("§4  准确率分析（H1：组C > 组A）")

    # 每人准确率
    acc_pp = (resp.groupby('participant_id')['is_correct']
              .mean().reset_index().rename(columns={'is_correct':'accuracy'}))
    acc_pp = acc_pp.merge(valid[['participant_id','group']], on='participant_id')

    print("\n  各组准确率描述统计：")
    for g in ['A','C']:
        sub = acc_pp[acc_pp['group']==g]['accuracy']
        if len(sub):
            ci = sub.sem() * 1.96
            print(f"    组{g}（N={len(sub)}）：M={sub.mean():.4f}, SD={sub.std():.4f}, "
                  f"95%CI=[{sub.mean()-ci:.4f}, {sub.mean()+ci:.4f}]")

    a_acc = acc_pp[acc_pp['group']=='A']['accuracy']
    c_acc = acc_pp[acc_pp['group']=='C']['accuracy']

    if len(a_acc) > 1 and len(c_acc) > 1:
        # Levene 方差齐性
        lev_stat, lev_p = stats.levene(a_acc, c_acc)
        equal_var = lev_p > 0.05
        print(f"\n  Levene 检验：F={lev_stat:.4f}, p={lev_p:.4f} "
              f"→ {'方差齐（使用 equal_var=True）' if equal_var else '方差不齐（使用 Welch t）'}")

        # t 检验
        t_stat, p_val = stats.ttest_ind(c_acc, a_acc, equal_var=equal_var)
        d = cohens_d(c_acc, a_acc)
        report_test("  独立样本 t 检验（C vs A）", t_stat, p_val, d)

        # 非参数备选（Mann-Whitney U）
        u_stat, u_p = stats.mannwhitneyu(c_acc, a_acc, alternative='two-sided')
        r = 1 - 2*u_stat / (len(c_acc)*len(a_acc))   # rank-biserial r
        report_test("  Mann-Whitney U（非参数）", u_stat, u_p, r, 'r')

    # 准确率按图像类型分解
    print("\n  按图像类型（AI/Real）拆解：")
    for img_type in ['AI','Real']:
        type_resp = resp[resp['correct_answer']==img_type]
        for g in ['A','C']:
            g_ids = valid[valid['group']==g]['participant_id']
            sub   = type_resp[type_resp['participant_id'].isin(g_ids)]
            if len(sub):
                print(f"    {img_type} 图像，组{g}：{sub['is_correct'].mean():.4f} "
                      f"({sub['is_correct'].sum()}/{len(sub)})")

    # ──────────────────────────────────────────────────────
    # §5  信号检测理论（SDT）
    # ──────────────────────────────────────────────────────
    section("§5  信号检测理论（d' 与 criterion c）")
    print("  说明：d'=灵敏度（越大越能区分），c=响应偏向（>0倾向说'Real'，<0倾向说'AI'）\n")

    sdt_rows = []
    for g in ['A','C']:
        g_resp = resp[resp['participant_id'].isin(
            valid[valid['group']==g]['participant_id']
        )]
        hits    = int(((g_resp['correct_answer']=='AI')  & (g_resp['judgment']=='AI')).sum())
        misses  = int(((g_resp['correct_answer']=='AI')  & (g_resp['judgment']=='Real')).sum())
        fas     = int(((g_resp['correct_answer']=='Real') & (g_resp['judgment']=='AI')).sum())
        crs     = int(((g_resp['correct_answer']=='Real') & (g_resp['judgment']=='Real')).sum())
        dp, c, hr, far = sdt_metrics(hits, misses, fas, crs)
        print(f"  组{g}：Hit={hits}, Miss={misses}, FA={fas}, CR={crs}")
        print(f"    击中率={hr:.4f}, 虚报率={far:.4f}")
        print(f"    d'={dp:.4f}, criterion c={c:.4f}")
        sdt_rows.append({'group':g, 'hits':hits,'misses':misses,'fas':fas,'crs':crs,
                         'hit_rate':hr,'fa_rate':far,'d_prime':dp,'criterion_c':c})

    sdt_df = pd.DataFrame(sdt_rows)
    save(sdt_df, 'sdt_results')

    # 逐人 SDT（用于组间比较）
    print("\n  逐人 d' 计算（组间比较）：")
    per_person_sdt = []
    for pid, grp in valid[['participant_id','group']].values:
        r_p = resp[resp['participant_id']==pid]
        h   = int(((r_p['correct_answer']=='AI')   & (r_p['judgment']=='AI')).sum())
        m   = int(((r_p['correct_answer']=='AI')   & (r_p['judgment']=='Real')).sum())
        fa  = int(((r_p['correct_answer']=='Real')  & (r_p['judgment']=='AI')).sum())
        cr  = int(((r_p['correct_answer']=='Real')  & (r_p['judgment']=='Real')).sum())
        dp, c, hr, far = sdt_metrics(h, m, fa, cr)
        per_person_sdt.append({'participant_id':pid,'group':grp,
                               'd_prime':dp,'criterion_c':c,'hit_rate':hr,'fa_rate':far})
    sdt_pp = pd.DataFrame(per_person_sdt)

    for g in ['A','C']:
        sub = sdt_pp[sdt_pp['group']==g]['d_prime']
        if len(sub):
            print(f"    组{g} d'：M={sub.mean():.4f}, SD={sub.std():.4f}")

    if len(sdt_pp[sdt_pp['group']=='A']) > 1 and len(sdt_pp[sdt_pp['group']=='C']) > 1:
        a_dp = sdt_pp[sdt_pp['group']=='A']['d_prime']
        c_dp = sdt_pp[sdt_pp['group']=='C']['d_prime']
        t_dp, p_dp = stats.ttest_ind(c_dp, a_dp)
        d_dp = cohens_d(c_dp, a_dp)
        report_test("  d' 组间 t 检验（C vs A）", t_dp, p_dp, d_dp)

    save(sdt_pp, 'sdt_per_participant')

    # ──────────────────────────────────────────────────────
    # §6  信心分析（H2）
    # ──────────────────────────────────────────────────────
    section("§6  信心分析（H2：组C信心 > 组A）")

    conf_pp = (resp.groupby('participant_id')['confidence']
               .mean().reset_index().rename(columns={'confidence':'mean_confidence'}))
    conf_pp = conf_pp.merge(valid[['participant_id','group']], on='participant_id')

    for g in ['A','C']:
        sub = conf_pp[conf_pp['group']==g]['mean_confidence']
        if len(sub):
            print(f"  组{g}：M={sub.mean():.2f}, SD={sub.std():.2f}")

    a_conf = conf_pp[conf_pp['group']=='A']['mean_confidence']
    c_conf = conf_pp[conf_pp['group']=='C']['mean_confidence']
    if len(a_conf) > 1 and len(c_conf) > 1:
        t_c, p_c = stats.ttest_ind(c_conf, a_conf)
        d_c = cohens_d(c_conf, a_conf)
        report_test("  信心 t 检验（C vs A）", t_c, p_c, d_c)

    # 信心校准：正确 vs 错误判断的信心
    print("\n  信心校准（正确 vs 错误判断）：")
    correct_conf   = resp[resp['is_correct']==True]['confidence']
    incorrect_conf = resp[resp['is_correct']==False]['confidence']
    print(f"    正确判断信心：M={correct_conf.mean():.2f}, SD={correct_conf.std():.2f}")
    print(f"    错误判断信心：M={incorrect_conf.mean():.2f}, SD={incorrect_conf.std():.2f}")
    if len(correct_conf) > 1 and len(incorrect_conf) > 1:
        t_cal, p_cal = stats.ttest_ind(correct_conf, incorrect_conf)
        report_test("  校准 t 检验（正确 vs 错误）", t_cal, p_cal)

    # ──────────────────────────────────────────────────────
    # §7  反应时分析
    # ──────────────────────────────────────────────────────
    section("§7  反应时分析（策略使用的时间代价）")

    # 排除过快（<500ms）的响应用于反应时分析
    resp_rt = resp[resp['response_time_ms'] >= 500].copy()
    rt_pp = (resp_rt.groupby('participant_id')['response_time_s']
             .median().reset_index().rename(columns={'response_time_s':'median_rt_s'}))
    rt_pp = rt_pp.merge(valid[['participant_id','group']], on='participant_id')

    for g in ['A','C']:
        sub = rt_pp[rt_pp['group']==g]['median_rt_s']
        if len(sub):
            print(f"  组{g}：中位数={sub.median():.2f}s, M={sub.mean():.2f}s, SD={sub.std():.2f}s")

    a_rt = rt_pp[rt_pp['group']=='A']['median_rt_s']
    c_rt = rt_pp[rt_pp['group']=='C']['median_rt_s']
    if len(a_rt) > 1 and len(c_rt) > 1:
        # 反应时通常非正态，优先使用 Mann-Whitney
        u_rt, p_rt = stats.mannwhitneyu(c_rt, a_rt, alternative='two-sided')
        r_rt = 1 - 2*u_rt / (len(c_rt)*len(a_rt))
        report_test("  反应时 Mann-Whitney U（C vs A）", u_rt, p_rt, r_rt, 'r')

    # 反应时与准确率相关
    rt_acc = (resp_rt.groupby('participant_id')
              .agg(median_rt=('response_time_s','median'), accuracy=('is_correct','mean'))
              .reset_index())
    r_rt_acc, p_rt_acc = stats.spearmanr(rt_acc['median_rt'], rt_acc['accuracy'])
    print(f"\n  反应时 vs 准确率（Spearman r）：r={r_rt_acc:.4f}, p={p_rt_acc:.4f}")

    # ──────────────────────────────────────────────────────
    # §8  Google Lens 使用分析（H3）
    # ──────────────────────────────────────────────────────
    section("§8  Google Lens 使用分析（H3：组C使用率 > 组A）")

    if interaction_logs is not None and len(interaction_logs) > 0:
        logs = interaction_logs[interaction_logs['participant_id'].isin(valid_ids)].copy()
        print(f"  有效交互日志：{len(logs)} 条")

        lens_opens = logs[logs['action']=='OPEN_LENS']
        lens_users = set(lens_opens['participant_id'])

        # 使用率（二分变量）→ χ² 检验
        print("\n  Lens 打开率：")
        ct = []
        for g in ['A','C']:
            g_ids   = set(valid[valid['group']==g]['participant_id'])
            used    = len(g_ids & lens_users)
            not_used = len(g_ids) - used
            total   = len(g_ids)
            rate    = used/total*100 if total else 0
            print(f"    组{g}：{used}/{total} ({rate:.1f}%) 使用了 Lens")
            ct.append([used, not_used])

        if len(ct) == 2:
            chi2, p_chi, dof, _ = stats.chi2_contingency(ct)
            v = cramers_v(chi2, sum(ct[0])+sum(ct[1]), dof)
            report_test("  χ²检验（Lens 使用率）", chi2, p_chi, v, "V")

        # 打开次数（连续）→ Mann-Whitney
        opens_pp = (lens_opens.groupby('participant_id').size()
                    .reset_index(name='lens_opens'))
        opens_pp = valid[['participant_id','group']].merge(opens_pp, on='participant_id', how='left')
        opens_pp['lens_opens'] = opens_pp['lens_opens'].fillna(0).astype(int)

        print("\n  所有参与者（含0）的 Lens 打开次数：")
        for g in ['A','C']:
            sub = opens_pp[opens_pp['group']==g]['lens_opens']
            print(f"    组{g}：M={sub.mean():.2f}, SD={sub.std():.2f}, 中位数={sub.median():.0f}")

        a_opens = opens_pp[opens_pp['group']=='A']['lens_opens']
        c_opens = opens_pp[opens_pp['group']=='C']['lens_opens']
        if len(a_opens) > 1 and len(c_opens) > 1:
            u_l, p_l = stats.mannwhitneyu(c_opens, a_opens, alternative='two-sided')
            r_l = 1 - 2*u_l / (len(c_opens)*len(a_opens))
            report_test("  Lens 次数 Mann-Whitney U（C vs A）", u_l, p_l, r_l, 'r')

        # Lens 使用与准确率的关系
        acc_lens = acc_pp.merge(opens_pp[['participant_id','lens_opens']], on='participant_id')
        r_la, p_la = stats.spearmanr(acc_lens['lens_opens'], acc_lens['accuracy'])
        print(f"\n  Lens 使用次数 vs 准确率（Spearman r）：r={r_la:.4f}, p={p_la:.4f}")

        # 行为细分
        print("\n  各类交互事件计数：")
        for act, cnt in logs['action'].value_counts().items():
            print(f"    {act}：{cnt}")
    else:
        opens_pp = valid[['participant_id','group']].copy()
        opens_pp['lens_opens'] = 0
        print("  无交互日志数据。")

    # ──────────────────────────────────────────────────────
    # §9  自我效能前后测（H4）
    # ──────────────────────────────────────────────────────
    section("§9  自我效能变化分析（H4）")

    se_cols = ['participant_id','group','self_assessed_ability']
    se_valid = valid[[c for c in se_cols if c in valid.columns]].copy()
    se_valid['self_assessed_ability'] = pd.to_numeric(
        se_valid['self_assessed_ability'], errors='coerce')

    if post_survey is not None:
        ps_se = post_survey[post_survey['participant_id'].isin(valid_ids)].copy()

        # post_self_efficacy 字段（如存在）
        if 'post_self_efficacy' in ps_se.columns:
            ps_se['post_self_efficacy'] = pd.to_numeric(ps_se['post_self_efficacy'], errors='coerce')
            se_merged = se_valid.merge(
                ps_se[['participant_id','post_self_efficacy','self_performance']],
                on='participant_id', how='inner'
            ).dropna(subset=['self_assessed_ability','post_self_efficacy'])
            se_merged['se_change'] = se_merged['post_self_efficacy'] - se_merged['self_assessed_ability']

            print("\n  前测（self_assessed_ability）vs 后测（post_self_efficacy）：")
            for g in ['A','C']:
                sub = se_merged[se_merged['group']==g]
                if len(sub) > 1:
                    print(f"\n  组{g}（N={len(sub)}）：")
                    print(f"    前测：M={sub['self_assessed_ability'].mean():.2f}, "
                          f"SD={sub['self_assessed_ability'].std():.2f}")
                    print(f"    后测：M={sub['post_self_efficacy'].mean():.2f}, "
                          f"SD={sub['post_self_efficacy'].std():.2f}")
                    print(f"    变化量：M={sub['se_change'].mean():.2f}, "
                          f"SD={sub['se_change'].std():.2f}")
                    t_se, p_se = stats.ttest_rel(
                        sub['self_assessed_ability'], sub['post_self_efficacy'])
                    report_test(f"  配对 t（前vs后，组{g}）", t_se, p_se)

            # 组间变化量比较
            a_chg = se_merged[se_merged['group']=='A']['se_change']
            c_chg = se_merged[se_merged['group']=='C']['se_change']
            if len(a_chg) > 1 and len(c_chg) > 1:
                t_chg, p_chg = stats.ttest_ind(c_chg, a_chg)
                d_chg = cohens_d(c_chg, a_chg)
                report_test("\n  变化量组间比较（C vs A）", t_chg, p_chg, d_chg)
        else:
            print("  [警告] post_self_efficacy 字段不在当前数据集中，跳过前后对比。")
            print("         使用 self_performance（后测自评表现）作为替代：")
            if 'self_performance' in ps_se.columns:
                ps_se['self_performance'] = pd.to_numeric(ps_se['self_performance'], errors='coerce')
                for g in ['A','C']:
                    g_ids = valid[valid['group']==g]['participant_id']
                    sub   = ps_se[ps_se['participant_id'].isin(g_ids)]['self_performance'].dropna()
                    if len(sub):
                        print(f"    组{g} self_performance：M={sub.mean():.2f}, SD={sub.std():.2f}")

    # ──────────────────────────────────────────────────────
    # §10  图像项目分析
    # ──────────────────────────────────────────────────────
    section("§10  图像项目分析（哪些图片更难区分）")

    img_acc = (resp.groupby('image_id')['is_correct']
               .agg(['mean','count','sum'])
               .rename(columns={'mean':'accuracy','count':'n_resp','sum':'n_correct'})
               .reset_index())
    img_acc['img_type']   = img_acc['image_id'].map(lambda x: IMAGE_META.get(x, {}).get('type'))
    img_acc['img_style']  = img_acc['image_id'].map(lambda x: IMAGE_META.get(x, {}).get('style'))
    img_acc['img_source'] = img_acc['image_id'].map(lambda x: IMAGE_META.get(x, {}).get('source'))
    img_acc = img_acc.sort_values('accuracy')

    print("\n  最难的5张图（准确率最低）：")
    print(img_acc.head(5)[['image_id','img_type','img_style','accuracy','n_resp']].to_string(index=False))
    print("\n  最易的5张图（准确率最高）：")
    print(img_acc.tail(5)[['image_id','img_type','img_style','accuracy','n_resp']].to_string(index=False))

    # 按图像风格分组
    print("\n  按图像风格的准确率：")
    style_acc = (resp.groupby('img_style')['is_correct']
                 .agg(['mean','count']).rename(columns={'mean':'accuracy','count':'n'}).reset_index())
    print(style_acc.to_string(index=False))

    # 图像类型 × 实验组的准确率交叉表
    print("\n  图像类型 × 实验组 准确率：")
    cross = pd.pivot_table(
        resp.merge(valid[['participant_id','group']], on='participant_id'),
        values='is_correct', index='group', columns='img_type',
        aggfunc='mean'
    )
    print(cross.round(4))

    save(img_acc, 'image_accuracy')

    # ──────────────────────────────────────────────────────
    # §11  个体差异回归（H5）
    # ──────────────────────────────────────────────────────
    section("§11  个体差异线性回归（H5）")

    # 构建回归用数据集
    reg_df = acc_pp.copy()
    for col in ['ai_familiarity','self_assessed_ability','ai_tool_usage',
                'age','education','ai_exposure_freq','intervention_duration_s']:
        if col in valid.columns:
            reg_df = reg_df.merge(valid[['participant_id', col]], on='participant_id', how='left')

    # 编码
    reg_df['group_num'] = (reg_df['group'] == 'C').astype(int)   # A=0, C=1
    reg_df['ai_familiarity']       = pd.to_numeric(reg_df['ai_familiarity'], errors='coerce')
    reg_df['self_assessed_ability']= pd.to_numeric(reg_df['self_assessed_ability'], errors='coerce')
    reg_df['ai_tool_num']          = (reg_df.get('ai_tool_usage','no') == 'yes').astype(int)

    freq_map = {'never':0,'rarely':1,'sometimes':2,'often':3,'very-often':4}
    reg_df['freq_num'] = reg_df.get('ai_exposure_freq', pd.Series(dtype=str)).map(freq_map)

    reg_clean = reg_df.dropna(subset=['accuracy','group_num','ai_familiarity']).copy()
    print(f"\n  回归有效样本量：{len(reg_clean)}")

    if len(reg_clean) > 10:
        formula = 'accuracy ~ group_num + ai_familiarity + freq_num + ai_tool_num'
        model = smf.ols(formula, data=reg_clean).fit()
        print("\n  回归结果（因变量：准确率）：")
        print(model.summary2().tables[1].round(4))
        print(f"\n  R²={model.rsquared:.4f}, 调整R²={model.rsquared_adj:.4f}, "
              f"F({int(model.df_model)},{int(model.df_resid)})={model.fvalue:.4f}, p={model.f_pvalue:.4f}")

        # VIF 多重共线性诊断
        X_vif = reg_clean[['group_num','ai_familiarity','freq_num','ai_tool_num']].dropna()
        X_vif = X_vif.assign(const=1)
        vif_df = pd.DataFrame({
            'feature': X_vif.columns[:-1],
            'VIF': [variance_inflation_factor(X_vif.values, i) for i in range(len(X_vif.columns)-1)]
        })
        print("\n  VIF 多重共线性诊断（<10为可接受）：")
        print(vif_df.to_string(index=False))

    # ──────────────────────────────────────────────────────
    # §12  调节效应分析（H6）
    # ──────────────────────────────────────────────────────
    section("§12  调节效应：AI熟悉度是否调节策略培训效果（H6）")

    if len(reg_clean) > 10:
        # 中心化（解释交互项）
        reg_clean = reg_clean.copy()
        reg_clean['group_c']     = reg_clean['group_num'] - reg_clean['group_num'].mean()
        reg_clean['famil_c']     = reg_clean['ai_familiarity'] - reg_clean['ai_familiarity'].mean()
        reg_clean['interaction'] = reg_clean['group_c'] * reg_clean['famil_c']

        formula_mod = 'accuracy ~ group_c + famil_c + interaction + freq_num + ai_tool_num'
        model_mod = smf.ols(formula_mod, data=reg_clean).fit()
        print("\n  调节回归结果：")
        print(model_mod.summary2().tables[1].round(4))

        int_coef = model_mod.params.get('interaction', np.nan)
        int_p    = model_mod.pvalues.get('interaction', np.nan)
        print(f"\n  交互项 β={int_coef:.4f}, p={int_p:.4f}")
        if not np.isnan(int_p) and int_p < 0.05:
            print("  → 显著调节效应！下面进行简单斜率分析：")
            sd_famil = reg_clean['famil_c'].std()
            for label, val in [('高熟悉度(M+1SD)', sd_famil),
                               ('均值(M)',         0),
                               ('低熟悉度(M-1SD)', -sd_famil)]:
                slope = model_mod.params['group_c'] + int_coef * val
                print(f"    {label}：组别效应斜率 = {slope:.4f}")
        else:
            print("  → 无显著调节效应。")

    # ──────────────────────────────────────────────────────
    # §13  敏感性分析（排除操纵检验失败者）
    # ──────────────────────────────────────────────────────
    section("§13  敏感性分析（仅组C中操纵检验通过者）")

    if manip_fail_ids:
        valid_sens = valid[~valid['participant_id'].isin(manip_fail_ids)]
        resp_sens  = resp[resp['participant_id'].isin(valid_sens['participant_id'])]
        acc_sens   = (resp_sens.groupby('participant_id')['is_correct']
                      .mean().reset_index().rename(columns={'is_correct':'accuracy'}))
        acc_sens   = acc_sens.merge(valid_sens[['participant_id','group']], on='participant_id')

        print(f"\n  敏感性分析样本量（排除 {len(manip_fail_ids)} 名C组操纵失败者）：")
        for g in ['A','C']:
            sub = acc_sens[acc_sens['group']==g]['accuracy']
            print(f"    组{g}（N={len(sub)}）：M={sub.mean():.4f}, SD={sub.std():.4f}")

        a_s = acc_sens[acc_sens['group']=='A']['accuracy']
        c_s = acc_sens[acc_sens['group']=='C']['accuracy']
        if len(a_s) > 1 and len(c_s) > 1:
            t_s, p_s = stats.ttest_ind(c_s, a_s)
            d_s = cohens_d(c_s, a_s)
            report_test("  敏感性 t 检验（C vs A）", t_s, p_s, d_s)
    else:
        print("  无操纵检验失败者，跳过敏感性分析。")

    # ──────────────────────────────────────────────────────
    # §14  导出汇总数据集
    # ──────────────────────────────────────────────────────
    section("§14  导出汇总数据集")

    summary = valid[['participant_id','group','age','gender','education',
                      'ai_tool_usage','ai_familiarity','self_assessed_ability',
                      'ai_exposure_freq','intervention_duration_s','total_duration_s']].copy()

    summary = summary.merge(acc_pp[['participant_id','accuracy']], on='participant_id', how='left')

    # 按图像类型的准确率
    for img_type in ['AI','Real']:
        type_acc = (resp[resp['correct_answer']==img_type]
                    .groupby('participant_id')['is_correct'].mean()
                    .reset_index().rename(columns={'is_correct':f'acc_{img_type.lower()}'}))
        summary = summary.merge(type_acc, on='participant_id', how='left')

    # 信心
    summary = summary.merge(
        conf_pp[['participant_id','mean_confidence']], on='participant_id', how='left')

    # 反应时
    summary = summary.merge(
        rt_pp[['participant_id','median_rt_s']], on='participant_id', how='left')

    # SDT
    summary = summary.merge(
        sdt_pp[['participant_id','d_prime','criterion_c']], on='participant_id', how='left')

    # 后测问卷
    if post_survey is not None:
        keep_cols = ['participant_id','manipulation_check_read','manipulation_check_strategies',
                     'strategy_usage_degree','self_performance','post_self_efficacy',
                     'attention_check_passed']
        keep_cols = [c for c in keep_cols if c in post_survey.columns]
        summary = summary.merge(post_survey[keep_cols], on='participant_id', how='left')

    # Lens 使用量
    summary = summary.merge(
        opens_pp[['participant_id','lens_opens']], on='participant_id', how='left')
    summary['lens_opens'] = summary['lens_opens'].fillna(0).astype(int)

    # 操纵检验标记
    summary['manip_check_passed'] = ~summary['participant_id'].isin(manip_fail_ids)

    save(summary, 'participant_summary')
    save(resp, 'valid_responses')

    print(f"\n  汇总数据集列：{list(summary.columns)}")
    print(f"\n{'='*62}")
    print(f"  分析完成！输出文件保存在 {OUT_DIR}")
    print(f"{'='*62}")


# ─── 入口 ───────────────────────────────────────────────────
if __name__ == '__main__':
    main()
```

---

## 5. 结果报告规范

每个检验结果应按以下格式报告：

**t 检验**：t(df) = X.XX, p = .XXX, Cohen's d = X.XX, 95% CI [X.XX, X.XX]

**Mann-Whitney U**：U = XXXX, p = .XXX, rank-biserial r = X.XX

**χ² 检验**：χ²(df) = X.XX, p = .XXX, Cramér's V = X.XX

**信号检测理论**：d' = X.XX, c = X.XX（组A）；d' = X.XX, c = X.XX（组C）

**显著性水平**：α = .05（双尾）；同时报告精确 p 值。效应量解释参考 Cohen(1988) 标准。

---

## 6. 多重比较说明

本研究设定主假设 H1（准确率组间差异）为**首要检验**，α = .05。其他分析（信心、反应时、Lens 使用等）作为**探索性/次要检验**，结果需谨慎解读，不做多重比较校正，但应在报告中注明其探索性质。

---

## 7. 软件与运行环境

```
Python >= 3.10
pandas >= 2.0
numpy >= 1.24
scipy >= 1.11
statsmodels >= 0.14
```

安装依赖：
```bash
pip install pandas numpy scipy statsmodels
```

运行分析：
```bash
# 先下载数据
python analysis/fetch_data.py

# 执行分析
python analysis/analyze.py
```
