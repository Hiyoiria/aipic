/**
 * ╔══════════════════════════════════════════════════════════════════════╗
 * ║                实验文本内容总汇 / Experiment Content                 ║
 * ║   所有介绍语、阅读材料、问卷题目集中在此文件，方便统一编辑和管理          ║
 * ║   All text content is centralized here for easy editing             ║
 * ╚══════════════════════════════════════════════════════════════════════╝
 *
 * 文件结构 / Structure:
 *   1. UI 界面文本（按钮、标签等）
 *   2. 欢迎页 / 知情同意 文本
 *   3. 前测问卷题目
 *   4. 干预材料（A/B/C三组）
 *   5. 后测问卷题目
 *   6. 结束页文本
 *
 * 每项内容均有 中文(zh) 和 英文(en) 两个版本。
 * 问卷题目的 required 字段控制是否必答。
 */

import type { QuestionDef, Group, InterventionContent } from '@/types';

// ============================================================================
// 类型定义
// ============================================================================

export type Language = 'zh' | 'en';

export interface InterventionImage {
  src: string;
  alt: string;
  caption?: string;
}

// ============================================================================
// 1. UI 界面文本（按钮、标签、提示语等）
// ============================================================================

export const UI_TEXT: Record<Language, Record<string, string>> = {
  zh: {
    // ---------- 欢迎页 ----------
    'welcome.title': '欢迎参加图像感知研究',
    'welcome.langToggle': 'English',
    'welcome.agree': '同意并继续',
    'welcome.disagree': '我不同意',

    // ---------- 前测问卷 ----------
    'pretest.title': '关于您',
    'pretest.desc': '请回答以下关于您的背景和经验的问题。',
    'pretest.next': '下一步',

    // ---------- 干预页 ----------
    'intervention.continue': '继续进入图像判断任务',
    'intervention.wait': '请稍候...',

    // ---------- 图像判断任务 ----------
    'task.loading': '正在加载图片...',
    'task.noMore': '没有更多图片了。',
    'task.question': '您认为这张图片是...',
    'task.ai': 'AI 生成',
    'task.real': '非AI生成',
    'task.confidence': '您对这个判断有多大信心？',
    'task.confidenceMin': '完全猜测',
    'task.confidenceMax': '非常确定',
    'task.strategyLabel': '您主要使用了哪种分析策略？（选填）',
    'task.strategyStyle': '视觉风格 / 纹理',
    'task.strategyAnatomy': '解剖 / 结构细节',
    'task.strategyKnowledge': '知识验证 / 搜索',
    'task.strategyIntuition': '直觉 / 整体感受',
    'task.reasoning': '补充说明（选填）',
    'task.reasoningPlaceholder': '描述您注意到的具体特征...',
    'task.next': '下一张',
    'task.finish': '完成',

    // ---------- 进度条 ----------
    'progress.label': '第 {current} 张，共 {total} 张',

    // ---------- 后测问卷 ----------
    'posttest.title': '后续问题',
    'posttest.desc': '请回答以下关于您在本实验中体验的问题。',
    'posttest.submit': '提交',

    // ---------- 结束页 ----------
    'end.title': '感谢您的参与！',
    'end.desc': '您已成功完成本研究。感谢您的宝贵贡献。',
    'end.results': '您的结果',
    'end.correct': '张图片判断正确',

    // ---------- 图片放大 ----------
    'image.zoom': '放大查看',
    'image.zoomFull': '点击放大查看高清原图',
    'zoom.loading': '正在加载高清原图...',
    'zoom.hint': '拖拽平移，双击重置',

    // ---------- 倒计时 ----------
    'timer.prefix': '请仔细阅读（',
    'timer.suffix': '秒后可以继续）',

    // ---------- 右键菜单（仿真） ----------
    'contextMenu.openImageNewTab': '在新标签页中打开图片',
    'contextMenu.saveImageAs': '图片另存为...',
    'contextMenu.copyImage': '复制图片',
    'contextMenu.searchImageWithGoogle': '使用 Google 搜索图片',

    // ---------- Google Lens 面板 ----------
    'lens.matchesFound': '找到匹配结果',
    'lens.visualMatches': '找到 {count} 个视觉匹配',
    'lens.blockedTitle': '无法访问外部链接',
    'lens.blockedMessage': '由于实验环境限制，当前仅支持查看搜索摘要，无法访问外部原始网站。',
    'lens.blockedOk': '我知道了',
  },

  en: {
    // ---------- Welcome ----------
    'welcome.title': 'Welcome to the Image Perception Study',
    'welcome.langToggle': '中文',
    'welcome.agree': 'Agree and Continue',
    'welcome.disagree': 'I do not agree',

    // ---------- Pre-test Survey ----------
    'pretest.title': 'About You',
    'pretest.desc': 'Please answer the following questions about your background and experience.',
    'pretest.next': 'Next',

    // ---------- Intervention ----------
    'intervention.continue': 'Continue to Image Task',
    'intervention.wait': 'Please wait...',

    // ---------- Image Task ----------
    'task.loading': 'Loading images...',
    'task.noMore': 'No more images.',
    'task.question': 'Do you think this image is...',
    'task.ai': 'AI-Generated',
    'task.real': 'Not AI-Generated',
    'task.confidence': 'How confident are you in this judgment?',
    'task.confidenceMin': 'Complete guess',
    'task.confidenceMax': 'Very confident',
    'task.strategyLabel': 'What strategy did you mainly use? (Optional)',
    'task.strategyStyle': 'Visual Style / Texture',
    'task.strategyAnatomy': 'Anatomy / Structural Details',
    'task.strategyKnowledge': 'Knowledge Verification / Search',
    'task.strategyIntuition': 'Intuition / Overall Feel',
    'task.reasoning': 'Additional Notes (Optional)',
    'task.reasoningPlaceholder': 'Describe specific features you noticed...',
    'task.next': 'Next Image',
    'task.finish': 'Finish',

    // ---------- Progress Bar ----------
    'progress.label': 'Image {current} of {total}',

    // ---------- Post-test Survey ----------
    'posttest.title': 'Follow-up Questions',
    'posttest.desc': 'Please answer the following questions about your experience in this experiment.',
    'posttest.submit': 'Submit',

    // ---------- End Page ----------
    'end.title': 'Thank You!',
    'end.desc': 'You have successfully completed the study. We appreciate your participation.',
    'end.results': 'Your Results',
    'end.correct': 'images correctly identified',

    // ---------- Image Zoom ----------
    'image.zoom': 'Zoom',
    'image.zoomFull': 'Click to zoom (HD)',
    'zoom.loading': 'Loading full resolution...',
    'zoom.hint': 'drag to pan, double-click to reset',

    // ---------- Countdown Timer ----------
    'timer.prefix': 'Please read carefully (',
    'timer.suffix': 's remaining before you can continue)',

    // ---------- Context Menu (simulated) ----------
    'contextMenu.openImageNewTab': 'Open image in new tab',
    'contextMenu.saveImageAs': 'Save image as...',
    'contextMenu.copyImage': 'Copy image',
    'contextMenu.searchImageWithGoogle': 'Search image with Google',

    // ---------- Google Lens Panel ----------
    'lens.matchesFound': 'Matches found',
    'lens.visualMatches': '{count} visual matches found',
    'lens.blockedTitle': 'Cannot Access External Link',
    'lens.blockedMessage': 'Due to experimental environment limitations, only search summaries are available. External websites cannot be accessed.',
    'lens.blockedOk': 'OK',
  },
};

// ============================================================================
// 2. 欢迎页 / 知情同意 文本
// ============================================================================

export const WELCOME_CONTENT = {
  zh: {
    researchOverview: '研究概述',
    researchDesc:
      '感谢您对本研究的关注。我们正在研究人们如何评估视觉材料是否由AI生成。在本研究中，您将阅读一些背景信息，查看一系列图像，并回答相关问题。',
    whatToExpect: '研究流程',
    expectations: [
      '预计时长：约10分钟',
      '您将完成一份简短的背景问卷',
      '您将阅读一些说明材料',
      '您将查看并评估一系列图片',
      '您将完成一份简短的后续问卷',
    ],
    privacyTitle: '数据隐私与知情同意',
    privacyItems: [
      '所有收集的数据均为匿名，仅用于学术研究目的',
      '不会收集除您的参与编号以外的任何个人身份信息',
      '您的参与完全自愿',
      '您可以随时退出，不会受到任何处罚',
      '数据将安全存储，并按照数据保护法规进行处理',
    ],
    consentText:
      '我已阅读并理解以上信息。我同意参加本研究，并同意按照上述说明收集和使用我的数据。',
  },
  en: {
    researchOverview: 'Research Overview',
    researchDesc:
      'Thank you for your interest in this research study. We are investigating how people perceive and evaluate different types of images. In this study, you will be asked to read some background information, view a series of images, and answer questions about them.',
    whatToExpect: 'What to Expect',
    expectations: [
      'Estimated duration: approximately 15-20 minutes',
      'You will complete a brief questionnaire about your background',
      'You will read some informational material',
      'You will view and evaluate a series of images',
      'You will complete a short follow-up questionnaire',
    ],
    privacyTitle: 'Data Privacy & Consent',
    privacyItems: [
      'All data collected is anonymous and will be used for academic research purposes only',
      'No personally identifiable information will be collected beyond your participant ID',
      'Your participation is entirely voluntary',
      'You may withdraw at any time without penalty',
      'Data will be stored securely and handled in compliance with data protection regulations',
    ],
    consentText:
      'I have read and understood the information above. I agree to participate in this study and consent to the collection and use of my data as described.',
  },
};

// ============================================================================
// 3. 前测问卷题目
//    required: true/false 控制是否必答
// ============================================================================

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
      { value: 'doctorate', label: '博士及以上' },
    ],
    required: true,
  },
  {
    id: 'ai_tool_usage',
    type: 'radio',
    label: '您是否使用过AI图像生成功能（如豆包、元宝中的生图功能；Nanobanana；Midjourney）？',
    options: [
      { value: 'yes', label: '是' },
      { value: 'no', label: '否' },
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
    label: '您如何评价自己区分AI生成图像和真实图像的能力？',
    likertMin: '非常差',
    likertMax: '非常好',
    likertCount: 5,
    required: true,
  },
  {
    id: 'ai_exposure_freq',
    type: 'radio',
    label: '您在日常生活中接触到AI生成视觉内容的频率（图像、视频）？',
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
      { value: 'yes', label: 'Yes' },
      { value: 'no', label: 'No' },
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

// ============================================================================
// 4. 干预材料（A组=控制组，C组=策略组）
// ============================================================================

const INTERVENTION_CONTENT_ZH: Record<'A' | 'C', InterventionContent> = {
  A: {
    title: '关于AI生成图像',
    sections: [
      {
        paragraphs: [
          '近年来，人工智能在图像生成领域取得了显著进展。现代AI系统可以根据文字描述生成高度逼真的图像，而这在十年前几乎是不可能的。',
          '这些AI图像生成器通过学习数百万张现有图像中的模式来工作。通过"训练"过程，AI分析真实照片和艺术作品中的统计模式，学习理解光线、透视、纹理和构图等概念。',
          'AI生成的图像现已广泛应用于广告、娱乐、教育和艺术等领域。一些艺术家将AI作为创作工具，而企业则用它进行产品可视化和营销素材制作。'
        ],
      },
    ],
  },
  C: {
    title: '识别AI生成图像的策略',
    sections: [
      {
        paragraphs: [
          '在本节中，我们将介绍三种关键策略，帮助您区分AI生成和人类生成的图像。请仔细阅读每种策略并研究所提供的示例。',
        ],
      },
      {
        heading: '策略一：检查人体解剖细节',
        paragraphs: [
          'AI系统在生成准确的人体结构方面常常存在困难，以手部为例的常见问题包括：<strong>手指数量不正确、手指长度或位置不自然、手指融合或合并，以及物理上不可能的手部姿势</strong>。',
          '除了手部，还要注意其他解剖不一致之处，如<strong>不对称的面部特征、异常的耳朵形状、看起来过于整齐或不规则的牙齿，以及头发向皮肤过渡不自然等。 </strong>',
        ],
        images: [
          {
            src: '/images/intervention/anatomy.webp',
            alt: 'AI生成图像中的解剖异常示例',
            caption: '注意不规则的手指数量和不自然的手部姿势——这些是AI生成的常见迹象。',
          },
        ],
      },
      {
        heading: '策略二：检查风格和纹理',
        paragraphs: [
          'AI生成的图像有时会表现出<strong>不一致的纹理或过度光滑、类似塑料的质感</strong>。注意纹理突然变化的区域、表面看起来过于完美或过于光滑的地方，以及仔细检查时变形或不连贯的图案。',
          '注意图像的<strong>整体"感觉"</strong>。AI图像有时具有一种<strong>不自然的光滑度或光泽</strong>，与真实照片中的自然缺陷不同。',
        ],
        images: [
          {
            src: '/images/intervention/style.webp',
            alt: 'AI生成图像中的风格示例',
            caption: '比较不同区域的纹理质量——AI图像通常显示出不一致的细节水平。',
          },
        ],
      },
      {
        heading: '策略三：利用外部知识',
        paragraphs: [
          '反向图片搜索是判断图像真伪的有力工具。通过<strong>将图片提交给搜索引擎</strong>，您可以查看该图像在互联网上是否有已知来源。如果搜索结果指向AI艺术平台（如Midjourney社区、ArtStation、Civitai等），该图像很可能是AI生成的。',
          '相反，如果搜索结果指向新闻网站、图库（Shutterstock、Getty Images）或明确署名的摄影师、画师，则更可能是真实照片。',
          '在本实验中，您可以通过<strong>右键点击（电脑）或长按（手机）</strong>图片来使用模拟的Google Lens搜索功能。',
        ],
        images: [
          {
            src: '/images/intervention/knowledge.webp',
            alt: '反向图片搜索示例',
            caption: '右键点击图片并选择"使用Google搜索图片"，通过搜索结果来源判断图片真伪。',
          },
        ],
      },
      {
        paragraphs: [
          '请记住：没有单一的策略是万无一失的。最有效的方法是结合多种策略——检查手部和身体结构、检查纹理和表面、利用反向搜图查看来源。通过练习和关注这些细节，您可以显著提高区分AI生成图像和真实照片的能力。',
        ],
      },
    ],
  },
};

const INTERVENTION_CONTENT_EN: Record<'A' | 'C', InterventionContent> = {
  A: {
    title: 'About AI-Generated Images',
    sections: [
      {
        paragraphs: [
          'Artificial intelligence has made remarkable progress in the field of image generation over the past few years. Modern AI systems can create highly realistic images from text descriptions, a capability that was nearly impossible just a decade ago.',
          'These AI image generators work by learning patterns from millions of existing images. Through a process called "training," the AI analyzes the statistical patterns in real photographs and artworks, learning to understand concepts like lighting, perspective, texture, and composition.',
          'The technology behind AI image generation has evolved through several approaches. Early methods used Generative Adversarial Networks (GANs), where two neural networks compete with each other — one generating images and the other trying to distinguish them from real ones. More recent approaches use diffusion models, which gradually transform random noise into coherent images.',
          'AI-generated images are now used in various fields including advertising, entertainment, education, and art. Some artists use AI as a creative tool, while businesses use it for product visualization and marketing materials.',
          'As this technology continues to develop, it raises important questions about authenticity, copyright, and the nature of creativity. Researchers across the world are studying how people interact with and perceive AI-generated visual content.',
        ],
      },
    ],
  },
  C: {
    title: 'Strategies for Identifying AI-Generated Images',
    sections: [
      {
        paragraphs: [
          'Research has identified several effective strategies for distinguishing AI-generated images from real photographs. In this section, we will introduce three key strategies that can help you identify AI-generated content. Please read each strategy carefully and study the examples provided.',
        ],
      },
      {
        heading: 'Strategy 1: Examine Human Anatomical Details',
        paragraphs: [
          'AI systems often struggle with generating accurate human anatomy, particularly hands and fingers. Common issues include: incorrect number of fingers, unnatural finger lengths or positions, fused or merged fingers, and awkward hand poses that would be physically impossible.',
          'Beyond hands, look for other anatomical inconsistencies such as asymmetric facial features, unusual ear shapes, teeth that look too uniform or irregularly shaped, and hair that transitions unnaturally into skin.',
        ],
        images: [
          {
            src: '/images/intervention/anatomy.webp',
            alt: 'Example of anatomical anomalies in AI-generated images',
            caption: 'Notice the irregular finger count and unnatural hand positioning — common signs of AI generation.',
          },
        ],
      },
      {
        heading: 'Strategy 2: Check Art Style and Texture Consistency',
        paragraphs: [
          'AI-generated images sometimes exhibit inconsistent textures or an overly smooth, plastic-like quality. Look for areas where the texture suddenly changes, surfaces that appear too perfect or too smooth, and patterns that become distorted or incoherent upon close inspection.',
          'Pay attention to the overall "feel" of the image. AI images sometimes have an uncanny smoothness or an artificial sheen that differs from the natural imperfections found in real photographs.',
        ],
        images: [
          {
            src: '/images/intervention/style.webp',
            alt: 'Example of texture inconsistencies in AI-generated images',
            caption: 'Compare the texture quality across different areas — AI images often show inconsistent detail levels.',
          },
        ],
      },
      {
        heading: 'Strategy 3: Use Reverse Image Search (External Knowledge)',
        paragraphs: [
          'Reverse image search is a powerful tool for verifying image authenticity. By submitting an image to a search engine (such as Google Lens), you can check whether the image has known sources on the internet. If search results point to AI art platforms (such as the Midjourney community, ArtStation, Civitai, etc.), the image is likely AI-generated.',
          'Conversely, if results point to news websites, stock photo libraries (Shutterstock, Getty Images), or photographer portfolios, it is more likely a real photograph. In this experiment, you can right-click (on computer) or long-press (on mobile) an image to use the simulated Google Lens search feature.',
        ],
        images: [
          {
            src: '/images/intervention/knowledge.webp',
            alt: 'Reverse image search example',
            caption: 'Right-click on an image and select "Search image with Google" to check the source of the image through search results.',
          },
        ],
      },
      {
        paragraphs: [
          'Remember: no single strategy is foolproof. The most effective approach is to combine multiple strategies — examine hands and anatomy, check textures and surfaces, and use reverse image search to verify sources. With practice and attention to these details, you can significantly improve your ability to distinguish AI-generated images from real photographs.',
        ],
      },
    ],
  },
};

// ============================================================================
// 5. 后测问卷题目
//    required: true/false 控制是否必答
//    conditionalGroups: 仅对指定组显示（不设则全部显示）
// ============================================================================

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
    type: 'radio',
    label: '材料中是否提到了"检查风格与纹理"这一策略？',
    options: [
      { value: 'yes', label: '是' },
      { value: 'no', label: '否' },
    ],
    required: true,
    conditionalGroups: ['C'] as Group[],
  },
  {
    id: 'strategy_usage_degree',
    type: 'likert',
    label: '在做判断时，您在多大程度上使用了材料中提到的策略？',
    likertMin: '完全没有使用',
    likertMax: '大量使用',
    likertCount: 5,
    required: true,
    conditionalGroups: ['C'] as Group[],
  },
  {
    id: 'open_method',
    type: 'textarea',
    label: '您主要使用了什么方法来判断图像是真实照片还是AI生成的？',
    maxLength: 500,
    required: false,
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
    id: 'post_self_efficacy',
    type: 'likert',
    label: '完成本实验后，您如何评价自己当前区分AI生成图像和真实照片的能力？',
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
    type: 'radio',
    label: 'Did the material mention the strategy of "checking art style and texture"?',
    options: [
      { value: 'yes', label: 'Yes' },
      { value: 'no', label: 'No' },
    ],
    required: true,
    conditionalGroups: ['C'] as Group[],
  },
  {
    id: 'strategy_usage_degree',
    type: 'likert',
    label: 'To what extent did you use the strategies from the material when making your judgments?',
    likertMin: 'Not at all',
    likertMax: 'Used extensively',
    likertCount: 5,
    required: true,
    conditionalGroups: ['C'] as Group[],
  },
  {
    id: 'open_method',
    type: 'textarea',
    label: 'What methods did you primarily use to judge whether images were real or AI-generated?',
    maxLength: 500,
    required: false,
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
    id: 'post_self_efficacy',
    type: 'likert',
    label: 'After completing this experiment, how would you rate your current ability to distinguish AI-generated images from real photos?',
    likertMin: 'Very poor',
    likertMax: 'Excellent',
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

// ============================================================================
// 导出函数 / Export Functions
// ============================================================================

export function getPreTestQuestions(lang: Language): QuestionDef[] {
  return lang === 'zh' ? PRE_TEST_QUESTIONS_ZH : PRE_TEST_QUESTIONS_EN;
}

export function getPostTestQuestions(lang: Language): QuestionDef[] {
  return lang === 'zh' ? POST_TEST_QUESTIONS_ZH : POST_TEST_QUESTIONS_EN;
}

export function getInterventionContent(lang: Language): Record<'A' | 'C', InterventionContent> {
  return lang === 'zh' ? INTERVENTION_CONTENT_ZH : INTERVENTION_CONTENT_EN;
}

export function getWelcomeContent(lang: Language) {
  return lang === 'zh' ? WELCOME_CONTENT.zh : WELCOME_CONTENT.en;
}
