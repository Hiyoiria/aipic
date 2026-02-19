# Study 2 数据分析指南

## 环境准备

需要 Python 3.8+，安装依赖：

```bash
pip install pandas numpy scipy requests
```

## 第一步：下载数据

运行 `fetch_data.py` 从实验服务器下载所有数据：

```bash
python analysis/fetch_data.py --url https://your-app.zeabur.app --secret your-admin-secret
```

参数说明：
- `--url`：实验网站的部署地址（Zeabur/Vercel 的 URL）
- `--secret`：管理员密钥（即 `.env.local` 中的 `ADMIN_SECRET` 值）

下载完成后，`analysis/data/` 目录下会有 4 个 CSV 文件：

| 文件 | 内容 | 关键字段 |
|------|------|---------|
| `participants.csv` | 被试信息 | participant_id, group, age, gender, education, ai_familiarity, completed |
| `responses.csv` | 每道题的作答 | participant_id, image_id, user_answer, correct_answer, is_correct, confidence, response_time_ms |
| `post-survey.csv` | 后测问卷 | participant_id, manipulation_check_read, strategy_usage_degree, post_self_efficacy, self_performance |
| `interaction-logs.csv` | 交互日志 | participant_id, image_id, action (OPEN_LENS, CLOSE_LENS, RIGHT_CLICK 等), timestamp |

## 第二步：运行分析

```bash
python analysis/analyze.py
```

脚本会读取 `analysis/data/` 下的 CSV，输出分析报告到控制台，并将合并数据集导出到 `analysis/output/`。

### 分析报告各部分说明

| 编号 | 部分 | 内容 |
|------|------|------|
| 1 | Loading Data | 加载数据并显示行列数 |
| 2 | Data Cleaning | 筛选已完成+通过注意力检查的有效被试 |
| 3 | Group Balance | A组（控制）vs C组（策略）人数是否平衡 |
| 4 | Demographics | 年龄、性别、学历、AI工具使用频率等分布 |
| 5 | **Accuracy (Primary DV)** | 主要因变量：两组正确率比较，独立样本t检验，Cohen's d 效应量 |
| 6 | Confidence | 两组信心评分比较，正确/错误试次的信心差异 |
| 7 | Response Time | 两组反应时间（中位数）比较 |
| 8 | Self-Efficacy Pre vs Post | 前后测自我效能感变化，配对t检验 |
| 9 | Google Lens Usage | 两组使用 Google Lens 的比例和频率 |
| 10 | Manipulation Check | 操纵检查：是否阅读了干预材料、策略使用程度 |
| 11 | Export | 导出合并数据集 |

## 输出文件

### `output/participant_summary.csv`

每个有效被试一行，包含以下列：

| 列名 | 含义 |
|------|------|
| participant_id | 被试唯一 ID |
| group | 实验组 (A=控制, C=策略) |
| age, gender, education | 人口统计学信息 |
| ai_tool_usage | AI 工具使用频率 |
| ai_familiarity | AI 熟悉程度 (1-7) |
| self_assessed_ability | 前测自我评估识别能力 (1-7) |
| ai_exposure_freq | AI 内容接触频率 |
| intervention_duration_s | 干预页面停留时间（秒） |
| total_duration_s | 实验总时长（秒） |
| accuracy | 总体正确率 (0-1) |
| accuracy_ai | AI 图片正确率 |
| accuracy_real | 真实图片正确率 |
| confidence | 平均信心评分 |
| median_rt_s | 中位反应时间（秒） |
| manipulation_check_read | 是否阅读了干预材料 |
| strategy_usage_degree | 策略使用程度 (1-7, 仅C组) |
| self_performance | 自评表现 (1-7) |
| post_self_efficacy | 后测自我效能感 (1-7) |
| attention_check_passed | 注意力检查是否通过 |
| lens_open_count | 打开 Google Lens 的次数 |

### `output/valid_responses.csv`

所有有效被试的逐题作答数据，可用于混合效应模型等高级分析。

## 进阶分析建议

### 用 SPSS 做进一步分析

1. 打开 `participant_summary.csv`，group 列用于分组
2. **主效应检验**：独立样本 t 检验 → 分析 > 比较均值 > 独立样本 T 检验（检验变量=accuracy，分组=group）
3. **信号检测论**：分别计算 AI 和 Real 图的 hit rate / false alarm rate → 计算 d' 和 criterion c
4. **协方差分析 (ANCOVA)**：以 ai_familiarity 或 self_assessed_ability 为协变量控制基线差异
5. **交互效应**：2(group) x 2(image_type) 混合方差分析 → accuracy_ai 和 accuracy_real

### 用 R 做进一步分析

```r
library(tidyverse)
library(lme4)

# 读取数据
summary <- read_csv("analysis/output/participant_summary.csv")
responses <- read_csv("analysis/output/valid_responses.csv")

# 主效应
t.test(accuracy ~ group, data = summary)
# 效应量
library(effectsize)
cohens_d(accuracy ~ group, data = summary)

# 混合效应模型（逐题数据）
model <- glmer(is_correct ~ group * correct_answer + (1|participant_id),
               data = responses, family = binomial)
summary(model)
```

### 可视化建议

- 两组正确率箱线图 + 散点图
- AI vs Real 图片正确率的交互图（group x image_type）
- 信心-正确性校准曲线
- Google Lens 使用频率直方图（按组）
- 前后测自我效能感变化图（按组）

### 论文报告格式参考

> 独立样本 t 检验显示，策略组 (M = .XX, SD = .XX) 的总体正确率显著高于/不显著高于控制组 (M = .XX, SD = .XX)，t(df) = X.XX, p = .XXX, Cohen's d = X.XX。
