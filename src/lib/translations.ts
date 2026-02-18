import type { Language } from '@/contexts/LanguageContext';

export const UI_TEXT: Record<Language, Record<string, string>> = {
  zh: {
    // WelcomePage
    'welcome.title': '欢迎参加图像感知研究',
    'welcome.langToggle': 'English',
    'welcome.researchOverview': '研究概述',
    'welcome.researchDesc': '感谢您对本研究的关注。我们正在研究人们如何感知和评估不同类型的图像。在本研究中，您将阅读一些背景信息，查看一系列图像，并回答相关问题。',
    'welcome.whatToExpect': '研究流程',
    'welcome.expect1': '预计时长：约15-20分钟',
    'welcome.expect2': '您将完成一份简短的背景问卷',
    'welcome.expect3': '您将阅读一些说明材料',
    'welcome.expect4': '您将查看并评估一系列图片',
    'welcome.expect5': '您将完成一份简短的后续问卷',
    'welcome.privacy': '数据隐私与知情同意',
    'welcome.privacy1': '所有收集的数据均为匿名，仅用于学术研究目的',
    'welcome.privacy2': '不会收集除您的参与编号以外的任何个人身份信息',
    'welcome.privacy3': '您的参与完全自愿',
    'welcome.privacy4': '您可以随时退出，不会受到任何处罚',
    'welcome.privacy5': '数据将安全存储，并按照数据保护法规进行处理',
    'welcome.consent': '我已阅读并理解以上信息。我同意参加本研究，并同意按照上述说明收集和使用我的数据。',
    'welcome.agree': '同意并继续',
    'welcome.disagree': '我不同意',

    // PreTestSurvey
    'pretest.title': '关于您',
    'pretest.desc': '请回答以下关于您的背景和经验的问题。',
    'pretest.next': '下一步',

    // InterventionPage
    'intervention.continue': '继续进入图像判断任务',
    'intervention.wait': '请稍候...',
    'intervention.timer': '请仔细阅读',
    'intervention.timerRemaining': '秒后可以继续',

    // ImageTask
    'task.loading': '正在加载图片...',
    'task.noMore': '没有更多图片了。',
    'task.question': '您认为这张图片是...',
    'task.ai': 'AI 生成',
    'task.real': '真实照片',
    'task.confidence': '您对这个判断有多大信心？',
    'task.confidenceMin': '完全猜测',
    'task.confidenceMax': '非常确定',
    'task.reasoning': '您做出此判断的主要依据是什么？（选填）',
    'task.reasoningPlaceholder': '描述您注意到的特征...',
    'task.next': '下一张',
    'task.finish': '完成',

    // ProgressBar
    'progress.label': '第 {current} 张，共 {total} 张',

    // PostTestSurvey
    'posttest.title': '后续问题',
    'posttest.desc': '请回答以下关于您在本实验中体验的问题。',
    'posttest.submit': '提交',

    // EndPage
    'end.title': '感谢您的参与！',
    'end.desc': '您已成功完成本研究。感谢您的宝贵贡献。',
    'end.results': '您的结果',
    'end.correct': '张图片判断正确',

    // ImageDisplay
    'image.zoom': '放大查看',
    'image.zoomFull': '点击放大查看高清原图',

    // ImageZoomModal
    'zoom.loading': '正在加载高清原图...',
    'zoom.hint': '拖拽平移，双击重置',

    // CountdownTimer
    'timer.prefix': '请仔细阅读（',
    'timer.suffix': '秒后可以继续）',
  },

  en: {
    // WelcomePage
    'welcome.title': 'Welcome to the Image Perception Study',
    'welcome.langToggle': '中文',
    'welcome.researchOverview': 'Research Overview',
    'welcome.researchDesc': 'Thank you for your interest in this research study. We are investigating how people perceive and evaluate different types of images. In this study, you will be asked to read some background information, view a series of images, and answer questions about them.',
    'welcome.whatToExpect': 'What to Expect',
    'welcome.expect1': 'Estimated duration: approximately 15-20 minutes',
    'welcome.expect2': 'You will complete a brief questionnaire about your background',
    'welcome.expect3': 'You will read some informational material',
    'welcome.expect4': 'You will view and evaluate a series of images',
    'welcome.expect5': 'You will complete a short follow-up questionnaire',
    'welcome.privacy': 'Data Privacy & Consent',
    'welcome.privacy1': 'All data collected is anonymous and will be used for academic research purposes only',
    'welcome.privacy2': 'No personally identifiable information will be collected beyond your participant ID',
    'welcome.privacy3': 'Your participation is entirely voluntary',
    'welcome.privacy4': 'You may withdraw at any time without penalty',
    'welcome.privacy5': 'Data will be stored securely and handled in compliance with data protection regulations',
    'welcome.consent': 'I have read and understood the information above. I agree to participate in this study and consent to the collection and use of my data as described.',
    'welcome.agree': 'Agree and Continue',
    'welcome.disagree': 'I do not agree',

    // PreTestSurvey
    'pretest.title': 'About You',
    'pretest.desc': 'Please answer the following questions about your background and experience.',
    'pretest.next': 'Next',

    // InterventionPage
    'intervention.continue': 'Continue to Image Task',
    'intervention.wait': 'Please wait...',
    'intervention.timer': 'Please read carefully',
    'intervention.timerRemaining': 's remaining before you can continue',

    // ImageTask
    'task.loading': 'Loading images...',
    'task.noMore': 'No more images.',
    'task.question': 'Do you think this image is...',
    'task.ai': 'AI-Generated',
    'task.real': 'Real Photo',
    'task.confidence': 'How confident are you in this judgment?',
    'task.confidenceMin': 'Complete guess',
    'task.confidenceMax': 'Very confident',
    'task.reasoning': 'What is your main reason for this judgment? (Optional)',
    'task.reasoningPlaceholder': 'Describe what you noticed...',
    'task.next': 'Next Image',
    'task.finish': 'Finish',

    // ProgressBar
    'progress.label': 'Image {current} of {total}',

    // PostTestSurvey
    'posttest.title': 'Follow-up Questions',
    'posttest.desc': 'Please answer the following questions about your experience in this experiment.',
    'posttest.submit': 'Submit',

    // EndPage
    'end.title': 'Thank You!',
    'end.desc': 'You have successfully completed the study. We appreciate your participation.',
    'end.results': 'Your Results',
    'end.correct': 'images correctly identified',

    // ImageDisplay
    'image.zoom': 'Zoom',
    'image.zoomFull': 'Click to zoom (HD)',

    // ImageZoomModal
    'zoom.loading': 'Loading full resolution...',
    'zoom.hint': 'drag to pan, double-click to reset',

    // CountdownTimer
    'timer.prefix': 'Please read carefully (',
    'timer.suffix': 's remaining before you can continue)',
  },
};
