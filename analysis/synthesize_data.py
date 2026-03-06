#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合成数据生成器 — 基于真实数据分布扩张，用于分析预演
运行: python analysis/synthesize_data.py

输出（格式与真实 CSV 完全一致）:
  analysis/data/participants_synth.csv
  analysis/data/responses_synth.csv
  analysis/data/post-survey_synth.csv
  analysis/data/interaction-logs_synth.csv
  analysis/data/participants_combined.csv  ← 真实 + 合成，供分析脚本直接使用
  (其余3个combined同理)

调参说明:
  SYNTH_CONFIG["target_g"]    → 干预效应量，调小 (0.3/0.5) 模拟效应衰减
  SYNTH_CONFIG["n_complete"]  → 目标完成者总数
  SYNTH_CONFIG["seed"]        → 随机种子，改变得到不同样本

生成逻辑（4层）:
  Layer 1  人口统计 + AI素养  （经验分布 + 截断正态）
  Layer 2  个体准确率         （基线 + 组别效应 + 素养效应 + 随机效应）
  Layer 3  逐图判断 + 置信度 + 反应时  （1-PL IRT + 条件采样）
  Layer 4  后测问卷 + Lens 行为  （条件概率）
"""
import sys, os, uuid, math, warnings
from datetime import datetime, timezone, timedelta
import pandas as pd
import numpy as np
from scipy.special import expit  # sigmoid

sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
OUT_DIR  = DATA_DIR  # 合成 CSV 写入同一目录

# ═══════════════════════════════════════════════════════════════════
# ① 配置区 — 修改这里调整合成参数
# ═══════════════════════════════════════════════════════════════════
SYNTH_CONFIG = {
    "n_complete"   : 60,    # 目标完成者总数（A:30, C:30）
    "target_g"     : 0.78,  # 干预 Hedges' g。可改 0.3 / 0.5 / 0.78
    "seed"         : 17,    # 随机种子
    "group_ratio"  : 0.50,  # C 组比例
    "include_dropout": False,# 只生成完成者（非完成者不计入参与者）
    "n_images"     : 21,    # 24 张删去 3 张 >90% 正确率后剩余
    "start_date"   : "2026-03-01T08:00:00Z",  # 合成数据的起始时间
}

# ═══════════════════════════════════════════════════════════════════
# ② 图像难度参数（来自真实数据 n=19 的每张图正确率）
# ═══════════════════════════════════════════════════════════════════
# β_j = logit(1 - p_j)；p_j 越低 → 图像越难（β越高）
IMAGE_DIFFICULTY = {
    # AI 图（已移除正确率>90% 的 ai_06=94.7%, ai_11=94.7%, ai_18=100%）
    'ai_01': 0.842, 'ai_02': 0.526, 'ai_04': 0.842,
    'ai_08': 0.474, 'ai_09': 0.895, 'ai_13': 0.684,
    'ai_15': 0.421, 'ai_16': 0.526, 'ai_19': 0.737,
    # Real 图（12张，无一超过90%正确率）
    'real_01': 0.474, 'real_02': 0.789, 'real_03': 0.684, 'real_04': 0.684,
    'real_05': 0.526, 'real_06': 0.842, 'real_11': 0.737, 'real_12': 0.895,
    'real_14': 0.421, 'real_15': 0.263, 'real_16': 0.895, 'real_20': 0.579,
}  # 共 21 张（AI:9, Real:12）
IMAGE_IDS = list(IMAGE_DIFFICULTY.keys())

# 把正确率转换为难度参数 β（以图像平均难度为中心）
# β_j = logit(p_avg) - logit(p_j)
# β<0 → 容易（高正确率），β>0 → 困难（低正确率），β=0 → 平均难度
# 这样当 θ_i = logit(acc_i) 时，在平均难度图上 P(correct) = acc_i
_p_avg = sum(IMAGE_DIFFICULTY.values()) / len(IMAGE_DIFFICULTY)
_logit_p_avg = math.log(_p_avg / (1 - _p_avg))

def _beta(p):
    p = min(max(p, 0.001), 0.999)
    return _logit_p_avg - math.log(p / (1 - p))  # centered at avg difficulty

IMG_BETA = {img: _beta(p) for img, p in IMAGE_DIFFICULTY.items()}

# ═══════════════════════════════════════════════════════════════════
# ③ 辅助函数
# ═══════════════════════════════════════════════════════════════════
rng = np.random.default_rng(SYNTH_CONFIG['seed'])

def new_uuid():
    return str(uuid.UUID(bytes=rng.bytes(16), version=4))

def ts(base_dt: datetime, delta_s) -> str:
    """生成 UTC 时间戳字符串，格式与真实数据一致"""
    t = base_dt + timedelta(seconds=int(delta_s))
    return t.strftime('%a %b %d %Y %H:%M:%S GMT+0000 (Coordinated Universal Time)')

def trunc_normal(mu, sigma, lo, hi, size=1):
    """截断正态分布"""
    from scipy.stats import truncnorm
    a, b = (lo - mu) / sigma, (hi - mu) / sigma
    return truncnorm.rvs(a, b, loc=mu, scale=sigma, size=size,
                         random_state=rng.integers(1e9))

def round_likert(arr, lo=1, hi=5):
    return np.clip(np.round(arr).astype(int), lo, hi)

# Fisher-Yates shuffle（与真实系统一致）
def shuffle_images(seed_str):
    imgs = IMAGE_IDS.copy()
    # 用 uuid 字符串的 hash 作种子
    local = np.random.default_rng(abs(hash(seed_str)) % (2**31))
    for i in range(len(imgs)-1, 0, -1):
        j = local.integers(0, i+1)
        imgs[i], imgs[j] = imgs[j], imgs[i]
    return imgs

# ═══════════════════════════════════════════════════════════════════
# ④ Layer 1：参与者层
# ═══════════════════════════════════════════════════════════════════
def gen_participants(n_complete, target_g, group_ratio, include_dropout,
                     start_dt):
    """生成参与者表，返回 DataFrame"""

    n_C = round(n_complete * group_ratio)
    n_A = n_complete - n_C
    groups = ['C'] * n_C + ['A'] * n_A
    rng.shuffle(groups)

    # include_dropout=False 时只生成完成者（符合"从抓取开始就不要"的要求）
    n_total = n_complete

    rows = []
    t_offset = 0  # 累计时间偏移（秒）

    # 先生成完成者
    for i, group in enumerate(groups):
        pid = new_uuid()
        t_offset += rng.integers(300, 3600)  # 每人间隔 5–60 min

        # 人口统计
        age = rng.choice(['18-24','25-34','35-44','45-54'],
                         p=[0.50, 0.25, 0.08, 0.17])
        gender = rng.choice(['male','female','prefer-not-to-say'], p=[0.47,0.42,0.11])
        edu = rng.choice(['high-school','some-college','bachelors','masters','doctorate'],
                         p=[0.08, 0.13, 0.33, 0.33, 0.13])
        ai_tool = rng.choice(['yes','no'], p=[0.83, 0.17])
        ai_exp  = rng.choice(['never','rarely','sometimes','often','very-often'],
                             p=[0.04, 0.13, 0.25, 0.21, 0.37])

        # AI 素养（相关）
        ai_fam  = round_likert(trunc_normal(3.1, 1.6, 1, 5))[0]
        # self_assessed 与 ai_fam 相关 r≈0.55
        sa_noise = rng.normal(0, 1.1)
        self_ab = round_likert([0.55 * ai_fam + 0.45 * 3.0 + sa_noise], 1, 5)[0]

        # 干预时长：A组极短，C组按log-normal
        if group == 'A':
            intv_dur = int(rng.integers(3, 10))
        else:
            intv_dur = int(np.clip(rng.lognormal(3.0, 0.8), 5, 180))

        total_dur = int(np.clip(rng.lognormal(6.4, 0.7), 120, 2500))
        consent_ts = ts(start_dt, t_offset)

        rows.append({
            '_id': new_uuid(),
            'participant_id': pid,
            'group': group,
            'completed': True,
            'consent_given': True,
            'consent_timestamp': consent_ts,
            'intervention_duration_s': intv_dur,
            'total_duration_s': total_dur,
            'age': age,
            'gender': gender,
            'education': edu,
            'ai_tool_usage': ai_tool,
            'ai_familiarity': ai_fam,
            'self_assessed_ability': self_ab,
            'ai_exposure_freq': ai_exp,
            'image_seed': pid,
            'current_phase': 5,
            'created_at': consent_ts,
            '__v': 0,
            '_synth': True,   # 标记为合成数据（分析时可过滤）
        })

    # include_dropout=False：只生成完成者，不生成中途退出者
    # （"从抓取开始就不要"非完成者）

    df = pd.DataFrame(rows)
    return df

# ── 逐图策略文本模板（用于生成 reasoning 字段）──────────────────────
# C 组（接受策略训练）以较高概率填写具体策略；A 组偶尔填写直觉描述
_STRATEGY_TEMPLATES = {
    'Style_C':    ['背景质感不自然，偏向AI渲染', '光影太均匀，像AI生成',
                   '风格过于完美和干净', '纹理不对，太光滑了',
                   '颜色过渡异常均匀', '整体感觉太"完美"，AI风格'],
    'Anatomy_C':  ['手指形状有点异常', '脸部细节有些奇怪',
                   '眼睛的反光不自然', '头发纹理有问题，太规整',
                   '身体比例感觉不对', '耳朵细节渲染有误'],
    'Knowledge_C':['用Lens搜索了图片来源', '根据背景知识判断场景真实性',
                   '与已知图片对比后判断', '搜索确认了拍摄地点'],
    'Style_A':    ['背景感觉有点假', '看着太光滑了'],
    'Anatomy_A':  ['手看起来有点奇怪'],
    'Intuition':  ['感觉像AI生成的', '直觉判断', '看起来比较真实', '第一印象判断'],
}

def _gen_reasoning(group, rng):
    """以一定概率生成逐图策略文本，反映实验中的 per-image 策略自报"""
    p_report = 0.45 if group == 'C' else 0.12
    if rng.random() > p_report:
        return None
    if group == 'C':
        cat = rng.choice(['Style_C', 'Anatomy_C', 'Knowledge_C'], p=[0.40, 0.40, 0.20])
    else:
        cat = rng.choice(['Style_A', 'Anatomy_A', 'Intuition'], p=[0.25, 0.20, 0.55])
    templates = _STRATEGY_TEMPLATES[cat]
    return str(rng.choice(templates))

# ═══════════════════════════════════════════════════════════════════
# ⑤ Layer 2 + 3：个体准确率 + 逐图响应
# ═══════════════════════════════════════════════════════════════════
def gen_responses(p_df, target_g, n_images, start_dt):
    """
    p_df: 仅包含完成者（completed=True）的参与者 DataFrame
    返回: responses DataFrame
    """
    pooled_sd = 0.155   # 真实数据 pooled SD
    group_effect = target_g * pooled_sd   # C 组准确率提升量

    # 置信度条件概率（来自真实数据校准）
    # correct=True → 偏高置信度；correct=False → 偏低
    conf_given_correct = [0.05, 0.10, 0.20, 0.25, 0.40]
    conf_given_wrong   = [0.20, 0.25, 0.30, 0.15, 0.10]

    # A组校准偏差 +0.065 → 错误时稍微给高一点置信度
    conf_given_wrong_A = [0.15, 0.22, 0.30, 0.18, 0.15]
    conf_given_wrong_C = [0.22, 0.27, 0.30, 0.12, 0.09]

    rows = []
    t_base = 0

    for _, person in p_df[p_df['completed'] == True].iterrows():
        pid = person['participant_id']
        group = person['group']
        saa = person['self_assessed_ability'] if not pd.isna(person['self_assessed_ability']) else 3

        # Layer 2: 个体准确率（base = 真实 A 组均值 0.62）
        base = 0.62
        g_eff = group_effect if group == 'C' else 0.0
        lit_eff = 0.04 * (saa - 3)
        noise = rng.normal(0, 0.10)
        acc_i = float(np.clip(base + g_eff + lit_eff + noise, 0.25, 0.99))

        # 个体能力 θ（logit scale）
        theta = math.log(acc_i / (1 - acc_i))

        # 图像顺序
        ordered_imgs = shuffle_images(pid)

        # 每人的时间基准（在consent之后随机偏移）
        t_base += rng.integers(30, 300)

        for order, img_id in enumerate(ordered_imgs, 1):
            beta_j = IMG_BETA[img_id]

            # Layer 3a: 1-PL IRT → P(correct)
            p_correct = expit(theta - beta_j)
            is_correct = bool(rng.random() < p_correct)

            # 正确答案
            correct_answer = 'AI' if img_id.startswith('ai_') else 'Real'
            judgment = correct_answer if is_correct else ('Real' if correct_answer == 'AI' else 'AI')

            # Layer 3b: 置信度（条件采样）
            if group == 'A':
                probs = conf_given_correct if is_correct else conf_given_wrong_A
            else:
                probs = conf_given_correct if is_correct else conf_given_wrong_C
            confidence = int(rng.choice([1,2,3,4,5], p=probs))

            # Layer 3c: 反应时（log-normal）
            mu_rt = 9.8 if group == 'C' else 9.7
            rt_ms = int(np.clip(rng.lognormal(mu_rt, 1.0), 2000, 300000))

            # 逐图策略自报（per-image reasoning）
            reasoning = _gen_reasoning(group, rng)

            t_base += rt_ms / 1000 + rng.integers(2, 15)
            sub_ts = ts(datetime.fromisoformat(SYNTH_CONFIG['start_date'].replace('Z','+00:00')), t_base)

            rows.append({
                '_id': new_uuid(),
                'participant_id': pid,
                'image_id': img_id,
                'image_order': order,
                'judgment': judgment,
                'correct_answer': correct_answer,
                'is_correct': is_correct,
                'confidence': confidence,
                'reasoning': reasoning,
                'response_time_ms': rt_ms,
                'submitted_at': sub_ts,
                '__v': 0,
            })

    return pd.DataFrame(rows)

# ═══════════════════════════════════════════════════════════════════
# ⑥ Layer 4a：后测问卷
# ═══════════════════════════════════════════════════════════════════
def gen_postsurvey(p_df, start_dt):
    rows = []
    t_base = 0
    for _, person in p_df[p_df['completed'] == True].iterrows():
        pid = person['participant_id']
        group = person['group']
        t_base += rng.integers(600, 3600)

        # manipulation_check_read
        if group == 'C':
            mc_read = rng.choice(['yes','no'], p=[0.91, 0.09])
        else:
            mc_read = rng.choice(['yes','no','not_sure'], p=[0.35, 0.57, 0.08])

        # manipulation_check_strategies（仅C组）
        mc_strat = None
        strat_deg = None
        if group == 'C':
            mc_strat = rng.choice(['yes','no'], p=[0.82, 0.18])
            strat_deg = float(round_likert(trunc_normal(3.9, 1.2, 1, 5))[0])

        # self_performance
        if group == 'C':
            sp = round_likert(trunc_normal(3.5, 0.7, 1, 5))[0]
        else:
            sp = round_likert(trunc_normal(3.1, 1.1, 1, 5))[0]

        # attention check（97% 答对=5）
        attn = 5 if rng.random() < 0.97 else int(rng.integers(1, 5))
        attn_passed = (attn == 5)

        sub_ts = ts(datetime.fromisoformat(SYNTH_CONFIG['start_date'].replace('Z','+00:00')), t_base)

        rows.append({
            '_id': new_uuid(),
            'participant_id': pid,
            'manipulation_check_read': mc_read,
            'manipulation_check_strategies': mc_strat,
            'strategy_usage_degree': strat_deg,
            'open_method': None,
            'self_performance': int(sp),
            'attention_check_answer': attn,
            'attention_check_passed': attn_passed,
            'submitted_at': sub_ts,
            '__v': 0,
        })

    return pd.DataFrame(rows)

# ═══════════════════════════════════════════════════════════════════
# ⑦ Layer 4b：Lens 交互日志
# ═══════════════════════════════════════════════════════════════════
def gen_logs(p_df, r_df, start_dt):
    rows = []
    t_base = 0
    for _, person in p_df[p_df['completed'] == True].iterrows():
        pid = person['participant_id']
        group = person['group']

        # 是否使用 Lens
        p_use = 0.67 if group == 'C' else 0.36
        if rng.random() > p_use:
            continue

        # 使用次数
        n_open = int(rng.poisson(9.0 if group == 'C' else 1.5))
        n_open = max(1, n_open)

        # 在哪些图上使用（随机选）
        person_imgs = r_df[r_df['participant_id'] == pid][['image_id','image_order']]
        chosen = person_imgs.sample(min(n_open, len(person_imgs)),
                                    replace=False,
                                    random_state=int(rng.integers(1e9)))

        t_base += rng.integers(60, 600)

        for _, img_row in chosen.iterrows():
            img_id = img_row['image_id']
            img_ord = img_row['image_order']

            # TRIGGER_MENU
            t_base += rng.integers(2, 30)
            ct = ts(datetime.fromisoformat(SYNTH_CONFIG['start_date'].replace('Z','+00:00')), t_base)
            rows.append({'_id': new_uuid(), 'participant_id': pid,
                         'image_id': img_id, 'image_order': int(img_ord),
                         'action': 'TRIGGER_MENU',
                         'client_timestamp': int(t_base * 1000),
                         'created_at': ct, '__v': 0})

            # OPEN_LENS
            t_base += rng.integers(1, 5)
            ct = ts(datetime.fromisoformat(SYNTH_CONFIG['start_date'].replace('Z','+00:00')), t_base)
            rows.append({'_id': new_uuid(), 'participant_id': pid,
                         'image_id': img_id, 'image_order': int(img_ord),
                         'action': 'OPEN_LENS',
                         'client_timestamp': int(t_base * 1000),
                         'created_at': ct, '__v': 0})

            # SCROLL_LENS / CLICK_RESULT（C组深度使用）
            if group == 'C' and rng.random() < 0.30:
                t_base += rng.integers(3, 15)
                ct = ts(datetime.fromisoformat(SYNTH_CONFIG['start_date'].replace('Z','+00:00')), t_base)
                rows.append({'_id': new_uuid(), 'participant_id': pid,
                             'image_id': img_id, 'image_order': int(img_ord),
                             'action': 'SCROLL_LENS',
                             'client_timestamp': int(t_base * 1000),
                             'created_at': ct, '__v': 0})
                if rng.random() < 0.40:
                    t_base += rng.integers(2, 10)
                    ct = ts(datetime.fromisoformat(SYNTH_CONFIG['start_date'].replace('Z','+00:00')), t_base)
                    rows.append({'_id': new_uuid(), 'participant_id': pid,
                                 'image_id': img_id, 'image_order': int(img_ord),
                                 'action': 'CLICK_RESULT',
                                 'client_timestamp': int(t_base * 1000),
                                 'created_at': ct, '__v': 0})

    return pd.DataFrame(rows)

# ═══════════════════════════════════════════════════════════════════
# ⑧ 主流程
# ═══════════════════════════════════════════════════════════════════
def main():
    cfg = SYNTH_CONFIG
    start_dt = datetime.fromisoformat(cfg['start_date'].replace('Z', '+00:00'))

    print(f'合成参数: n_complete={cfg["n_complete"]}, target_g={cfg["target_g"]}, seed={cfg["seed"]}')

    # --- 生成 ---
    print('生成参与者...')
    p_synth = gen_participants(cfg['n_complete'], cfg['target_g'],
                               cfg['group_ratio'], cfg['include_dropout'], start_dt)

    print('生成图像响应...')
    r_synth = gen_responses(p_synth, cfg['target_g'], cfg['n_images'], start_dt)

    print('生成后测问卷...')
    ps_synth = gen_postsurvey(p_synth, start_dt)

    print('生成交互日志...')
    lg_synth = gen_logs(p_synth, r_synth, start_dt)

    # --- 保存合成数据 ---
    p_out  = os.path.join(OUT_DIR, 'participants_synth.csv')
    r_out  = os.path.join(OUT_DIR, 'responses_synth.csv')
    ps_out = os.path.join(OUT_DIR, 'post-survey_synth.csv')
    lg_out = os.path.join(OUT_DIR, 'interaction-logs_synth.csv')

    p_synth.drop(columns=['_synth'], errors='ignore').to_csv(p_out,  index=False, encoding='utf-8-sig')
    r_synth.to_csv(r_out,  index=False, encoding='utf-8-sig')
    ps_synth.to_csv(ps_out, index=False, encoding='utf-8-sig')
    lg_synth.to_csv(lg_out, index=False, encoding='utf-8-sig')

    # --- 合并真实 + 合成 ---
    p_real  = pd.read_csv(os.path.join(DATA_DIR, 'participants.csv'))
    r_real  = pd.read_csv(os.path.join(DATA_DIR, 'responses.csv'))
    ps_real = pd.read_csv(os.path.join(DATA_DIR, 'post-survey.csv'))
    lg_real = pd.read_csv(os.path.join(DATA_DIR, 'interaction-logs.csv'))

    p_synth['_synth'] = True
    p_real['_synth']  = False
    r_synth['_synth'] = True
    r_real['_synth']  = False

    p_comb  = pd.concat([p_real,  p_synth.drop(columns=['_synth'])], ignore_index=True)
    r_comb  = pd.concat([r_real,  r_synth.drop(columns=['_synth'])], ignore_index=True)
    ps_comb = pd.concat([ps_real, ps_synth],   ignore_index=True)
    lg_comb = pd.concat([lg_real, lg_synth],   ignore_index=True)

    _combined_files = [
        (p_comb,  'participants_combined.csv'),
        (r_comb,  'responses_combined.csv'),
        (ps_comb, 'post-survey_combined.csv'),
        (lg_comb, 'interaction-logs_combined.csv'),
    ]
    for df, fname in _combined_files:
        fpath = os.path.join(OUT_DIR, fname)
        try:
            df.to_csv(fpath, index=False, encoding='utf-8-sig')
        except PermissionError:
            print(f'  ⚠ 无法写入 {fname}（文件可能在其他程序中打开，请关闭后重试）')

    # --- 快速验证 ---
    completers = p_synth[p_synth['completed'] == True]
    gA = completers[completers['group'] == 'A']
    gC = completers[completers['group'] == 'C']

    acc_by_p = r_synth.groupby('participant_id')['is_correct'].mean()
    acc_df = acc_by_p.reset_index(name='acc').merge(
        completers[['participant_id','group']], on='participant_id', how='left')

    acc_A = acc_df[acc_df['group'] == 'A']['acc'].values
    acc_C = acc_df[acc_df['group'] == 'C']['acc'].values

    from scipy import stats as sst
    t, p = sst.ttest_ind(acc_C, acc_A, equal_var=False)

    import math as _math
    n1, n2 = len(acc_C), len(acc_A)
    s = _math.sqrt(((n1-1)*acc_C.std(ddof=1)**2+(n2-1)*acc_A.std(ddof=1)**2)/(n1+n2-2))
    d = (acc_C.mean()-acc_A.mean())/s if s else float('nan')
    g_actual = d*(1-3/(4*(n1+n2-2)-1))

    print(f'\n── 合成数据验证 ──────────────────────')
    print(f'  完成者: A={len(gA)}, C={len(gC)}  | 目标: A={round(cfg["n_complete"]*(1-cfg["group_ratio"]))}, C={round(cfg["n_complete"]*cfg["group_ratio"])}')
    print(f'  Group A 正确率: {acc_A.mean():.3f} (SD={acc_A.std(ddof=1):.3f})')
    print(f'  Group C 正确率: {acc_C.mean():.3f} (SD={acc_C.std(ddof=1):.3f})')
    print(f'  Welch t={t:.3f}, p={p:.4f}')
    print(f'  Hedges\' g 实际={g_actual:.3f}  目标={cfg["target_g"]}')
    print(f'  图像响应总数: {len(r_synth)}  (期望={cfg["n_complete"]*cfg["n_images"]}，21张×60人)')
    print(f'  后测问卷: {len(ps_synth)} 条')
    print(f'  交互日志: {len(lg_synth)} 条')
    print(f'\n── 合并数据 ──────────────────────────')
    print(f'  participants_combined: {len(p_comb)} 行')
    print(f'  responses_combined:    {len(r_comb)} 行')
    print(f'\n  文件输出至: {OUT_DIR}')

if __name__ == '__main__':
    main()
