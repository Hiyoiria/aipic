Study 2 数据分析需求文档（v4 字段对齐版）
=======================

> 整合了此前分析报告中的已有分析 + 论文框架所需的补充分析。A组=对照组，C组=策略干预组（与数据库字段保持一致）。

* * *

一、数据结构
------

### 1.1 被试层级数据

| 字段名                    | 类型            | 来源     | 说明                                                   |
| ---------------------- | ------------- | ------ | ---------------------------------------------------- |
| participant_id         | string        | 原始     | 唯一ID                                                 |
| group                  | categorical   | 原始     | A=对照组, C=策略干预组                                       |
| gender                 | categorical   | 前测     | male/female/prefer-not-to-say                        |
| age                    | categorical   | 前测     | 18-24/25-34/35-44/45-54                              |
| education              | categorical   | 前测     | high-school/some-college/bachelors/masters/doctorate |
| ai_tool_usage          | binary        | 前测     | yes/no                                               |
| ai_exposure_freq       | ordinal       | 前测     | never/rarely/sometimes/often/very-often              |
| ai_familiarity         | ordinal (0-5) | 前测     | AI熟悉度                                                |
| self_assessed_ability  | ordinal (1-5) | 前测     | 前测辨别能力自评（框架中曾用名 pre_self_efficacy）                    |
| ai_literacy_composite  | float         | **计算** | AI素养综合分：(zscore(ai_familiarity)+zscore(ai_tool_num))/2 |
| intervention_duration_s| float         | 系统     | 干预页停留秒数（框架中曾用名 intervention_time）                    |
| self_performance       | ordinal (1-5) | 后测     | 后测实验表现自评（框架中曾用名 post_performance）                    |
| strategy_usage_degree  | ordinal (1-5) | 后测     | 策略运用程度（仅C组）                                          |
| actual_correct         | int           | **计算** | 实际答对数                                                |
| accuracy               | float         | **计算** | actual_correct / 21（代码变量名 acc_total）                 |
| hit_rate               | float         | **计算** | 命中率（正确识别AI图/AI图总数，代码变量名 hr）                          |
| false_alarm_rate       | float         | **计算** | 虚警率（真实图误判为AI/真实图总数，代码变量名 far）                        |
| correct_rejection_rate | float         | **计算** | 1 - false_alarm_rate                                 |
| d_prime                | float         | **计算** | SDT敏感性指标（代码变量名 dprime）                               |
| criterion_c            | float         | **计算** | SDT判断标准（代码变量名 c）                                     |
| calibration_gap        | float         | **计算** | self_performance/5 - accuracy（正=过度自信）                |

> **注**：`post_self_efficacy`（后测辨别能力自评）字段**不存在**于数据库，后测问卷仅有 `self_performance`（表现自评），两者构念不同，不做前后测变化分析。

### 1.2 逐图层级数据

| 字段名                | 类型          | 说明                                                          |
| ------------------ | ----------- | ----------------------------------------------------------- |
| participant_id     | string      |                                                             |
| group              | categorical | A/C                                                         |
| image_id           | string      | 如 ai_02, real_04                                            |
| image_type         | categorical | AI/Real                                                     |
| image_style        | categorical | illustration/photograph/cartoon（来自 imageData.ts/list.csv）  |
| image_source       | categorical | AI侧：ai-art/midjourney/nanobanana；Real侧：camera/website      |
| reverse_searchable | binary      | ai-art=True（有公开URL），midjourney/nanobanana=False，Real全部=True |
| response           | binary      | 1=判为AI (judgment=='AI'), 0=判为Real                          |
| is_correct         | binary      | 判断是否正确（框架中曾用名 correct）                                     |
| confidence         | int (0-5)   | 逐图信心（⚠ 新版实验已移除此题，历史数据保留）                                  |
| reasoning          | text        | 逐图策略自报（选填）                                                  |

* * *

二、数据预处理
-------

### 2.1 排除标准

1. 未完成全部21张
2. 注意力检查未通过（`attention_check_passed == False`）
3. 模式化作答（>80%相同选项）→ 报告标记人数，**根据预实验结果建议保留**（标记了6人但未排除）
4. 干预页面停留<90秒（`intervention_duration_s < 90`）

报告：排除前N人 → 各步排除N → 最终N（A=XX, C=XX）

### 2.2 派生变量计算

    # SDT 边界校正（Loglinear 法，已在代码中实现）
    hr  = (hits + 0.5) / (n_ai + 1)
    far = (fas  + 0.5) / (n_real + 1)
    d_prime    = norm.ppf(hr) - norm.ppf(far)
    criterion_c = -0.5 * (norm.ppf(hr) + norm.ppf(far))

    # AI素养综合分
    ai_literacy_composite = (zscore(ai_familiarity) + zscore(ai_tool_usage_numeric)) / 2

    # 整体信心校准（元认知准确性）
    calibration_gap = self_performance / 5 - accuracy  # 正=过度自信

* * *

三、分析模块
------

### ═══ 分析0：基线检查（论文3.1节） → 输出 T1

**已有**：guided_analysis.py Step 0 已完成。

1. 人口统计 × group 交叉频数表（含百分比）
2. 两组AI素养基线比较：ai_familiarity, self_assessed_ability, ai_literacy_composite 的组间t检验
3. 干预停留时间描述（intervention_duration_s by group）
4. 结论：随机化是否成功（各变量组间均无显著差异）

* * *

### ═══ 分析1：干预主效应（论文4.1节） → 输出 T3, T4

**已有**：guided_analysis.py Step 1 已完成基础t检验。

#### 1a. 组间t检验（已有，保留）

| 指标       | 方法        | 报告                                |
| -------- | --------- | --------------------------------- |
| 总准确率     | Welch's t | M, SD, t, df, p, Hedges' g, 95%CI |
| d'       | Welch's t | 同上                                |
| C        | Welch's t | 同上                                |
| 命中率(HR)  | Welch's t | 同上                                |
| 虚警率(FAR) | Welch's t | 同上                                |

#### 1b. 回归分析（**新增**，论文框架核心要求）

两个回归模型，因变量分别为 accuracy（acc_total）和 d'（dprime）：

* 自变量：group（A=0, C=1）
* 控制变量：gender（虚拟编码，ref=male），age（虚拟编码，ref=18-24），education（虚拟编码，ref=high-school），ai_exposure_freq（ordinal 1-5），self_assessed_ability

输出格式：B / SE / Beta（标准化）/ t / p / VIF + 底部R² / Adj.R² / F / p

**这是参照陈欣雨论文表4-5的核心输出，之前分析报告中没有这个格式的回归表，必须补做。**

#### 1c. ANCOVA / 层次回归（已有 Step 4，整合）

* Model 1：仅 group
* Model 2：+ai_familiarity
* Model 3：+self_assessed_ability

作为分析1的补充，说明"控制AI素养后干预效应方向一致但减弱"，报告斜率同质性检验结果。

* * *

### ═══ 分析2：过度怀疑检验（论文4.4节） → 输出 T6

**已有**：guided_analysis.py Step 2 已完成。

2×2混合ANOVA：DV=正确率，Between=group，Within=image_type (AI/Real)

报告：
* 主效应：group F, p, η²p
* 主效应：image_type F, p, η²p
* 交互效应：F, p, η²p
* 简单效应：AI图上组间差异（t, p, g）、Real图上组间差异（t, p, g）

* * *

### ═══ 分析3：信心与校准（论文4.2节） → 输出 T5

**已有**：guided_analysis.py Step 3 和 Step 5.1 已部分完成，但需重组。

#### 3a. 实验表现自评组间比较

Mann-Whitney U（5分量表序数变量）：比较两组 self_performance
报告：M, SD, U, p, 效应量r

#### 3b. ~~能力自评前后变化~~ → **放弃**

post_self_efficacy 字段不存在，self_performance 与 self_assessed_ability 构念不同，不做替代分析。

#### 3c. 信心校准分析（核心）

**方法1：calibration_gap 组间比较**

* calibration_gap = self_performance/5 - accuracy
* 组间 Welch's t
* 报告：C组 M(SD), A组 M(SD), t, p

**方法2：高信心错误率**（已有，非常好的指标）

* 高信心错误率 = confidence≥4 且判断错误的比例
* 组间 Welch's t
* 预实验结果：C=0.121, A=0.282, p=0.0005 → ⚠ 仅历史数据，新版已移除confidence

**方法3：校准曲线**（已有）

* 各信心等级(0-5) → 实际正确率（仅历史数据）

#### 3d. calibration_gap 回归（**新增**）

以 calibration_gap 为因变量，同1b控制变量结构。

* * *

### ═══ 分析4：逐图与图像类型分析（论文4.4节） → 输出 F1, F2

**已有**：guided_analysis.py Step 5.2 已完成基础分析。

#### 4a. 逐图正确率

* 每张图按组的正确率 → 分组柱状图
* 对每张图做 Fisher 精确检验（group × is_correct），报告 OR, p，标注 p<0.05

#### 4b. 按风格类型（illustration / photograph / cartoon）

3（style）× 2（group）交互分析：OLS 或分别做组间 t 检验，检验干预在哪种风格下效果更显著

#### 4c. 按反向可检索性（reverse_searchable）

定义：ai-art 来源 = True，midjourney/nanobanana = False，Real全部 = True

* 分 reverse_searchable=True/False 子集，各做组间 t 检验
* 解读：策略组在不可反向搜索图片上的提升是否更依赖视觉策略？

#### 4d. 按AI生成模型（探索性，仅AI图）

分 ai-art / midjourney / nanobanana 三组，做 accuracy 单因素 ANOVA

* * *

### ═══ 分析5：AI素养的调节效应（从 Step 4 扩展）

**已有**：guided_analysis.py 发现 group × self_assessed_ability 交互显著（p=0.0024）。

#### 5a. AI素养与正确率的相关（已有）

全样本 Pearson r：ai_familiarity, self_assessed_ability, ai_literacy_composite 分别与 accuracy

#### 5b. 调节效应分析（**新增**）

* 回归模型：accuracy ~ group + self_assessed_ability_c + group × self_assessed_ability_c + 控制变量
* 简单斜率：在低(-1SD) / 均值 / 高(+1SD) 自评能力水平下，group 的效应 B, SE, t, p
* Johnson-Neyman 区间：交互项显著边界点
* **解读方向**：干预对低AI素养者效果更大（β=-0.071, p=0.002）

* * *

### ═══ 分析6：个体特征异质性分析（论文4.5节） → 输出 T7, T8

**新增**（参照陈欣雨论文）。

#### 分组维度

| 维度     | 划分                                               |
| ------ | ------------------------------------------------ |
| 性别     | male / female（排除 prefer-not-to-say）              |
| 年龄     | ≤34岁 / ≥35岁                                      |
| 学历     | some-college及以下 / bachelors / masters及以上         |
| AI接触频率 | 低频（never+rarely+sometimes）/ 高频（often+very-often） |
| 前测能力自评 | 低自评(1-2) / 高自评(3-5)                              |

#### 辨别能力异质性 → T7

对每个子群：`DV=acc_total ~ group_c`，报告 B, t, N, R²
Chow 检验：F = [(RSS_pool−RSS_1−RSS_2)/k] / [(RSS_1+RSS_2)/(n1+n2−2k)]

#### 信心校准异质性 → T8

同上逻辑，DV 改为 calibration_gap

* * *

### ═══ 分析7：策略使用过程分析（讨论部分支撑）

**已有**：guided_analysis.py Step 5.3-5.4。

#### 7a. 逐图策略自报填写率

* 两组填写率对比（C组 vs A组）

#### 7b. 策略类别分布

* 按 Style/Anatomy/Knowledge/直觉-其他 编码
* 两组分布差异 + 各策略类别对应正确率

#### 7c. 有/无策略描述与正确率

* 分组比较有/无策略描述的正确率差异
* C组策略使用程度（strategy_usage_degree） × accuracy 相关

**此部分不单独成节，作为讨论中"干预机制"的证据。**

* * *

四、输出物清单
-------

| 编号  | 内容                          | 论文位置    | 来源      |
| --- | --------------------------- | ------- | ------- |
| T1  | 样本基本信息 + AI素养基线             | 3.1     | 已有+格式调整 |
| T2  | 图像材料信息                      | 3.2     | 需整理     |
| T3  | 干预对 accuracy 的回归表           | 4.1     | **新增**  |
| T4  | 干预对 d' 的回归表                 | 4.1     | **新增**  |
| T5  | 干预对 calibration_gap 的回归表    | 4.2     | **新增**  |
| T6  | 命中率/正确拒绝率/SDT汇总             | 4.1+4.4 | 已有+整合   |
| T7  | 辨别能力异质性分析                   | 4.5     | **新增**  |
| T8  | 信心校准异质性分析                   | 4.5     | **新增**  |
| F1  | 逐图正确率柱状图（含Fisher p值标注）      | 4.4     | 已有+美化   |
| F2  | 分组×逐图正确率柱状图                 | 4.4     | 已有+美化   |
| F3  | 相关性热力图                      | 4.3     | **新增**  |
| F4  | 校准曲线图                       | 4.2     | 已有+美化   |
| F5  | AI素养调节效应图（简单斜率）             | 补充分析    | **新增**  |

* * *

五、已有 vs 新增 总结
-------------

| 分析           | 已有报告覆盖         | 需新增/调整                |
| ------------ | -------------- | --------------------- |
| 基线检查         | ✅ 完整           | 格式调整为论文表格             |
| t检验主效应       | ✅ 完整           | 保留                    |
| SDT全指标       | ✅ 完整           | 保留                    |
| 2×2混合ANOVA   | ✅ 完整           | 保留                    |
| 回归分析（控制变量）   | ⚠ 有ANCOVA但格式不同 | **需按陈欣雨表4格式重新输出**     |
| 信心校准         | ⚠ 部分有          | 补充 calibration_gap 回归 |
| 高信心错误率       | ✅ 完整（历史数据）     | 保留（新版已移除confidence题）  |
| 校准曲线         | ✅ 完整（历史数据）     | 保留                    |
| 逐图分析         | ✅ 完整           | 补充Fisher检验p值标注        |
| 按风格/可检索性分析   | ❌ 无            | **新增**                |
| AI素养调节效应     | ⚠ 发现了交互，未做简单斜率 | **补充简单斜率+图**          |
| 相关性热力图       | ❌ 无            | **新增**                |
| 异质性分析+Chow检验 | ❌ 无            | **新增**                |
| 策略使用过程分析     | ✅ 完整           | 保留作为讨论支撑              |

* * *

六、执行顺序
------

    Step 0  数据清洗 + 排除 → T1
    Step 1  计算派生变量
    Step 2  分析0：基线检查 → T1
    Step 3  分析1：t检验 + 回归 → T3, T4, T6
    Step 4  分析2：2×2 ANOVA（过度怀疑）
    Step 5  分析3：信心校准全套 → T5, F4
    Step 6  分析4：逐图 + 风格 + 可检索性 → F1, F2
    Step 7  分析5：AI素养调节效应 → F5
    Step 8  分析3补充：相关性矩阵 → F3
    Step 9  分析6：异质性 + Chow → T7, T8
    Step 10 分析7：策略使用（供讨论）
    Step 11 汇总检查
