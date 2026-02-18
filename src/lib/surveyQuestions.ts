import type { QuestionDef } from '@/types';
import type { Language } from '@/contexts/LanguageContext';

const PRE_TEST_QUESTIONS_EN: QuestionDef[] = [
  {
    id: 'age',
    type: 'radio',
    label: 'What is your age range?',
    options: [
      { value: '18-24', label: '18-24' },
      { value: '25-34', label: '25-34' },
      { value: '35-44', label: '35-44' },
      { value: '45-54', label: '45-54' },
      { value: '55+', label: '55 or older' },
    ],
    required: true,
  },
  {
    id: 'gender',
    type: 'radio',
    label: 'What is your gender?',
    options: [
      { value: 'male', label: 'Male' },
      { value: 'female', label: 'Female' },
      { value: 'non-binary', label: 'Non-binary / Third gender' },
      { value: 'prefer-not-to-say', label: 'Prefer not to say' },
    ],
    required: true,
  },
  {
    id: 'education',
    type: 'radio',
    label: 'What is the highest level of education you have completed?',
    options: [
      { value: 'high-school', label: 'High school or equivalent' },
      { value: 'some-college', label: 'Some college / Associate degree' },
      { value: 'bachelors', label: "Bachelor's degree" },
      { value: 'masters', label: "Master's degree" },
      { value: 'doctorate', label: 'Doctorate or professional degree' },
    ],
    required: true,
  },
  {
    id: 'ai_tool_usage',
    type: 'radio',
    label: 'Have you ever used an AI image generation tool (e.g., Midjourney, DALL-E, Stable Diffusion)?',
    options: [
      { value: 'never', label: 'Never' },
      { value: 'once-or-twice', label: 'Once or twice' },
      { value: 'occasionally', label: 'Occasionally (a few times)' },
      { value: 'regularly', label: 'Regularly' },
    ],
    required: true,
  },
  {
    id: 'ai_familiarity',
    type: 'likert',
    label: 'How familiar are you with AI-generated images?',
    likertMin: 'Not at all familiar',
    likertMax: 'Very familiar',
    likertCount: 5,
    required: true,
  },
  {
    id: 'self_assessed_ability',
    type: 'likert',
    label: 'How would you rate your ability to distinguish AI-generated images from real photos?',
    likertMin: 'Very poor',
    likertMax: 'Excellent',
    likertCount: 5,
    required: true,
  },
  {
    id: 'ai_exposure_freq',
    type: 'radio',
    label: 'How often do you encounter AI-generated content (images, text, video) in your daily life?',
    options: [
      { value: 'never', label: 'Never' },
      { value: 'rarely', label: 'Rarely (less than once a week)' },
      { value: 'sometimes', label: 'Sometimes (a few times a week)' },
      { value: 'often', label: 'Often (daily)' },
      { value: 'very-often', label: 'Very often (multiple times a day)' },
    ],
    required: true,
  },
];

const PRE_TEST_QUESTIONS_ZH: QuestionDef[] = [
  {
    id: 'age',
    type: 'radio',
    label: '您的年龄范围是？',
    options: [
      { value: '18-24', label: '18-24岁' },
      { value: '25-34', label: '25-34岁' },
      { value: '35-44', label: '35-44岁' },
      { value: '45-54', label: '45-54岁' },
      { value: '55+', label: '55岁及以上' },
    ],
    required: true,
  },
  {
    id: 'gender',
    type: 'radio',
    label: '您的性别是？',
    options: [
      { value: 'male', label: '男' },
      { value: 'female', label: '女' },
      { value: 'non-binary', label: '非二元性别' },
      { value: 'prefer-not-to-say', label: '不愿透露' },
    ],
    required: true,
  },
  {
    id: 'education',
    type: 'radio',
    label: '您的最高学历是？',
    options: [
      { value: 'high-school', label: '高中或同等学历' },
      { value: 'some-college', label: '大专' },
      { value: 'bachelors', label: '本科' },
      { value: 'masters', label: '硕士' },
      { value: 'doctorate', label: '博士或专业学位' },
    ],
    required: true,
  },
  {
    id: 'ai_tool_usage',
    type: 'radio',
    label: '您是否使用过AI图像生成工具（如Midjourney、DALL-E、Stable Diffusion）？',
    options: [
      { value: 'never', label: '从未使用过' },
      { value: 'once-or-twice', label: '使用过一两次' },
      { value: 'occasionally', label: '偶尔使用（几次）' },
      { value: 'regularly', label: '经常使用' },
    ],
    required: true,
  },
  {
    id: 'ai_familiarity',
    type: 'likert',
    label: '您对AI生成图像的熟悉程度如何？',
    likertMin: '完全不熟悉',
    likertMax: '非常熟悉',
    likertCount: 5,
    required: true,
  },
  {
    id: 'self_assessed_ability',
    type: 'likert',
    label: '您如何评价自己区分AI生成图像和真实照片的能力？',
    likertMin: '非常差',
    likertMax: '非常好',
    likertCount: 5,
    required: true,
  },
  {
    id: 'ai_exposure_freq',
    type: 'radio',
    label: '您在日常生活中多久接触到AI生成的内容（图像、文字、视频）？',
    options: [
      { value: 'never', label: '从不' },
      { value: 'rarely', label: '很少（每周不到一次）' },
      { value: 'sometimes', label: '有时（每周几次）' },
      { value: 'often', label: '经常（每天）' },
      { value: 'very-often', label: '非常频繁（每天多次）' },
    ],
    required: true,
  },
];

const POST_TEST_QUESTIONS_EN: QuestionDef[] = [
  {
    id: 'manipulation_check_read',
    type: 'radio',
    label: 'Did you read material about strategies for identifying AI-generated images during the experiment?',
    options: [
      { value: 'yes', label: 'Yes' },
      { value: 'no', label: 'No' },
      { value: 'not_sure', label: 'Not sure' },
    ],
    required: true,
  },
  {
    id: 'manipulation_check_strategies',
    type: 'checkbox',
    label: 'Which strategies do you remember from the material? (Select all that apply)',
    options: [
      { value: 'anatomy', label: 'Human anatomical details (hands, fingers, etc.)' },
      { value: 'texture', label: 'Art style / texture inconsistencies' },
      { value: 'text', label: 'Text / symbols anomalies' },
      { value: 'lighting', label: 'Lighting inconsistencies' },
      { value: 'background', label: 'Background blur patterns' },
      { value: 'none', label: "I don't remember any" },
    ],
    required: true,
    conditionalGroups: ['C'],
  },
  {
    id: 'strategy_usage_degree',
    type: 'likert',
    label: 'To what extent did you use the strategies from the material when making your judgments?',
    likertMin: 'Not at all',
    likertMax: 'Used extensively',
    likertCount: 5,
    required: true,
    conditionalGroups: ['C'],
  },
  {
    id: 'open_method',
    type: 'textarea',
    label: 'What methods did you primarily use to judge whether images were real or AI-generated?',
    maxLength: 500,
    required: true,
  },
  {
    id: 'self_performance',
    type: 'likert',
    label: 'How well do you think you performed in this experiment?',
    likertMin: 'Very poorly',
    likertMax: 'Very well',
    likertCount: 5,
    required: true,
  },
  {
    id: 'attention_check',
    type: 'likert',
    label: 'To ensure data quality, please select "Strongly Agree" (5) for this question.',
    likertMin: 'Strongly Disagree',
    likertMax: 'Strongly Agree',
    likertCount: 5,
    required: true,
  },
];

const POST_TEST_QUESTIONS_ZH: QuestionDef[] = [
  {
    id: 'manipulation_check_read',
    type: 'radio',
    label: '在实验过程中，您是否阅读了关于识别AI生成图像策略的材料？',
    options: [
      { value: 'yes', label: '是' },
      { value: 'no', label: '否' },
      { value: 'not_sure', label: '不确定' },
    ],
    required: true,
  },
  {
    id: 'manipulation_check_strategies',
    type: 'checkbox',
    label: '您还记得材料中提到的哪些策略？（可多选）',
    options: [
      { value: 'anatomy', label: '人体解剖细节（手、手指等）' },
      { value: 'texture', label: '画风/纹理不一致' },
      { value: 'text', label: '文字/符号异常' },
      { value: 'lighting', label: '光线不一致' },
      { value: 'background', label: '背景模糊模式' },
      { value: 'none', label: '我不记得任何策略' },
    ],
    required: true,
    conditionalGroups: ['C'],
  },
  {
    id: 'strategy_usage_degree',
    type: 'likert',
    label: '在做判断时，您在多大程度上使用了材料中提到的策略？',
    likertMin: '完全没有使用',
    likertMax: '大量使用',
    likertCount: 5,
    required: true,
    conditionalGroups: ['C'],
  },
  {
    id: 'open_method',
    type: 'textarea',
    label: '您主要使用了什么方法来判断图像是真实照片还是AI生成的？',
    maxLength: 500,
    required: true,
  },
  {
    id: 'self_performance',
    type: 'likert',
    label: '您觉得自己在这个实验中表现如何？',
    likertMin: '非常差',
    likertMax: '非常好',
    likertCount: 5,
    required: true,
  },
  {
    id: 'attention_check',
    type: 'likert',
    label: '为确保数据质量，请在此题选择"非常同意"（5）。',
    likertMin: '非常不同意',
    likertMax: '非常同意',
    likertCount: 5,
    required: true,
  },
];

export function getPreTestQuestions(lang: Language): QuestionDef[] {
  return lang === 'zh' ? PRE_TEST_QUESTIONS_ZH : PRE_TEST_QUESTIONS_EN;
}

export function getPostTestQuestions(lang: Language): QuestionDef[] {
  return lang === 'zh' ? POST_TEST_QUESTIONS_ZH : POST_TEST_QUESTIONS_EN;
}

export const PRE_TEST_QUESTIONS = PRE_TEST_QUESTIONS_EN;
export const POST_TEST_QUESTIONS = POST_TEST_QUESTIONS_EN;
