import type { InterventionContent } from '@/types';
import type { Language } from '@/contexts/LanguageContext';

const CONTENT_EN: Record<'A' | 'C', InterventionContent> = {
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
            src: '/images/intervention/anatomy.png',
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
            src: '/images/intervention/style.png',
            alt: 'Example of texture inconsistencies in AI-generated images',
            caption: 'Compare the texture quality across different areas — AI images often show inconsistent detail levels.',
          },
        ],
      },
      {
        heading: 'Strategy 3: Use Reverse Image Search for Verification',
        paragraphs: [
          'Reverse image search tools like Google Lens can help verify the source and authenticity of an image. By searching for an image online, you can check whether it originates from a known, credible source or if it has been artificially generated.',
          'If a reverse search returns matching results from reputable sources (such as news outlets, stock photo sites, or personal portfolios), the image is more likely to be real. AI-generated images typically lack traceable origins and may not appear in any search results.',
        ],
        images: [
          {
            src: '/images/intervention/knowledge.png',
            alt: 'Example of using reverse image search to verify image authenticity',
            caption: 'Reverse image search can reveal the original source of a real photo, while AI-generated images typically have no traceable origin.',
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

const CONTENT_ZH: Record<'A' | 'C', InterventionContent> = {
  A: {
    title: '关于AI生成图像',
    sections: [
      {
        paragraphs: [
          '近年来，人工智能在图像生成领域取得了显著进展。现代AI系统可以根据文字描述生成高度逼真的图像，而这在十年前几乎是不可能的。',
          '这些AI图像生成器通过学习数百万张现有图像中的模式来工作。通过"训练"过程，AI分析真实照片和艺术作品中的统计模式，学习理解光线、透视、纹理和构图等概念。',
          'AI图像生成背后的技术经历了多种方法的演变。早期方法使用生成对抗网络（GAN），其中两个神经网络相互竞争——一个负责生成图像，另一个则尝试区分生成图像和真实图像。更新的方法使用扩散模型，将随机噪声逐步转化为连贯的图像。',
          'AI生成的图像现已广泛应用于广告、娱乐、教育和艺术等领域。一些艺术家将AI作为创作工具，而企业则用它进行产品可视化和营销素材制作。',
          '随着这项技术的持续发展，它引发了关于真实性、版权和创造力本质的重要问题。世界各地的研究人员正在研究人们如何与AI生成的视觉内容互动和感知。',
        ],
      },
    ],
  },
  C: {
    title: '识别AI生成图像的策略',
    sections: [
      {
        paragraphs: [
          '研究发现了几种有效的策略来区分AI生成的图像和真实照片。在本节中，我们将介绍三种关键策略，帮助您识别AI生成的内容。请仔细阅读每种策略并研究所提供的示例。',
        ],
      },
      {
        heading: '策略一：检查人体解剖细节',
        paragraphs: [
          'AI系统在生成准确的人体结构方面常常存在困难，特别是手和手指。常见问题包括：手指数量不正确、手指长度或位置不自然、手指融合或合并，以及物理上不可能的手部姿势。',
          '除了手部，还要注意其他解剖不一致之处，如不对称的面部特征、异常的耳朵形状、看起来过于整齐或不规则的牙齿，以及头发向皮肤过渡不自然等。',
        ],
        images: [
          {
            src: '/images/intervention/anatomy.png',
            alt: 'AI生成图像中的解剖异常示例',
            caption: '注意不规则的手指数量和不自然的手部形态——这些是AI生成的常见迹象。',
          },
        ],
      },
      {
        heading: '策略二：检查画风和纹理一致性',
        paragraphs: [
          'AI生成的图像有时会表现出不一致的纹理或过度光滑、类似塑料的质感。注意纹理突然变化的区域、表面看起来过于完美或过于光滑的地方，以及仔细检查时变形或不连贯的图案。',
          '注意图像的整体"感觉"。AI图像有时具有一种不自然的光滑度或人工光泽，与真实照片中的自然缺陷不同。',
        ],
        images: [
          {
            src: '/images/intervention/style.png',
            alt: 'AI生成图像中的纹理不一致示例',
            caption: '注意风格与纹理的不自然之处——AI图像在细节衔接处常出现破绽。',
          },
        ],
      },
      {
        heading: '策略三：利用反向搜索验证来源',
        paragraphs: [
          '反向图片搜索工具（如Google Lens）可以帮助验证图像的来源和真实性。通过在线搜索图像，您可以检查它是否来自已知的可信来源，还是人工生成的。',
          '如果反向搜索返回来自权威来源（如新闻媒体、图库网站或个人作品集）的匹配结果，则该图像更可能是真实的。AI生成的图像通常缺乏可追溯的来源，在搜索结果中可能找不到任何匹配。',
        ],
        images: [
          {
            src: '/images/intervention/knowledge.png',
            alt: '使用反向图片搜索验证图像真实性的示例',
            caption: '反向搜索可以揭示真实照片的原始来源，而AI生成的图像通常没有可追溯的出处。',
          },
        ],
      },
      {
        paragraphs: [
          '请记住：没有单一的策略是万无一失的。最有效的方法是结合多种策略——检查手部和身体结构、检查纹理和表面、利用反向搜索验证来源。通过练习和关注这些细节，您可以显著提高区分AI生成图像和真实照片的能力。',
        ],
      },
    ],
  },
};

export function getInterventionContent(lang: Language): Record<'A' | 'C', InterventionContent> {
  return lang === 'zh' ? CONTENT_ZH : CONTENT_EN;
}

export const INTERVENTION_CONTENT = CONTENT_EN;
