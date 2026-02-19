import type { ImageMeta } from '@/types';

/**
 * Image metadata generated from list.csv.
 * 40 images total: 20 AI + 20 Real.
 *
 * - path: original full-resolution image (used in zoom modal for detail inspection)
 * - thumbPath: optimized WebP thumbnail at 1200px long edge (used for page display)
 */

export interface ImageMetaExtended extends ImageMeta {
  style: 'illustration' | 'photograph' | 'cartoon';
  source: string;
}

export const IMAGE_DATA: ImageMetaExtended[] = [
  // === AI images (20) ===
  { id: 'ai_01', filename: '1.jpg', type: 'AI', path: '/images/ai/1.jpg', thumbPath: '/images/ai/thumb-sm/1.webp', correct_answer: 'AI', style: 'illustration', source: 'ai-art' },
  { id: 'ai_02', filename: '2.jpg', type: 'AI', path: '/images/ai/2.jpg', thumbPath: '/images/ai/thumb-sm/2.webp', correct_answer: 'AI', style: 'photograph', source: 'ai-art' },
  { id: 'ai_03', filename: '3.jpg', type: 'AI', path: '/images/ai/3.jpg', thumbPath: '/images/ai/thumb-sm/3.webp', correct_answer: 'AI', style: 'cartoon', source: 'ai-art' },
  { id: 'ai_04', filename: '4.jpg', type: 'AI', path: '/images/ai/4.jpg', thumbPath: '/images/ai/thumb-sm/4.webp', correct_answer: 'AI', style: 'cartoon', source: 'ai-art' },
  { id: 'ai_05', filename: '5.jpg', type: 'AI', path: '/images/ai/5.jpg', thumbPath: '/images/ai/thumb-sm/5.webp', correct_answer: 'AI', style: 'illustration', source: 'ai-art' },
  { id: 'ai_06', filename: '6.jpg', type: 'AI', path: '/images/ai/6.jpg', thumbPath: '/images/ai/thumb-sm/6.webp', correct_answer: 'AI', style: 'photograph', source: 'ai-art' },
  { id: 'ai_07', filename: '7.png', type: 'AI', path: '/images/ai/7.png', thumbPath: '/images/ai/thumb-sm/7.webp', correct_answer: 'AI', style: 'illustration', source: 'midjourney' },
  { id: 'ai_08', filename: '8.png', type: 'AI', path: '/images/ai/8.png', thumbPath: '/images/ai/thumb-sm/8.webp', correct_answer: 'AI', style: 'photograph', source: 'midjourney' },
  { id: 'ai_09', filename: '9.png', type: 'AI', path: '/images/ai/9.png', thumbPath: '/images/ai/thumb-sm/9.webp', correct_answer: 'AI', style: 'cartoon', source: 'midjourney' },
  { id: 'ai_10', filename: '10.png', type: 'AI', path: '/images/ai/10.png', thumbPath: '/images/ai/thumb-sm/10.webp', correct_answer: 'AI', style: 'photograph', source: 'midjourney' },
  { id: 'ai_11', filename: '11.png', type: 'AI', path: '/images/ai/11.png', thumbPath: '/images/ai/thumb-sm/11.webp', correct_answer: 'AI', style: 'illustration', source: 'midjourney' },
  { id: 'ai_12', filename: '12.png', type: 'AI', path: '/images/ai/12.png', thumbPath: '/images/ai/thumb-sm/12.webp', correct_answer: 'AI', style: 'illustration', source: 'midjourney' },
  { id: 'ai_13', filename: '13.png', type: 'AI', path: '/images/ai/13.png', thumbPath: '/images/ai/thumb-sm/13.webp', correct_answer: 'AI', style: 'photograph', source: 'midjourney' },
  { id: 'ai_14', filename: '14.png', type: 'AI', path: '/images/ai/14.png', thumbPath: '/images/ai/thumb-sm/14.webp', correct_answer: 'AI', style: 'illustration', source: 'nanobanana' },
  { id: 'ai_15', filename: '15.png', type: 'AI', path: '/images/ai/15.png', thumbPath: '/images/ai/thumb-sm/15.webp', correct_answer: 'AI', style: 'photograph', source: 'nanobanana' },
  { id: 'ai_16', filename: '16.png', type: 'AI', path: '/images/ai/16.png', thumbPath: '/images/ai/thumb-sm/16.webp', correct_answer: 'AI', style: 'illustration', source: 'nanobanana' },
  { id: 'ai_17', filename: '17.png', type: 'AI', path: '/images/ai/17.png', thumbPath: '/images/ai/thumb-sm/17.webp', correct_answer: 'AI', style: 'photograph', source: 'nanobanana' },
  { id: 'ai_18', filename: '18.png', type: 'AI', path: '/images/ai/18.png', thumbPath: '/images/ai/thumb-sm/18.webp', correct_answer: 'AI', style: 'cartoon', source: 'nanobanana' },
  { id: 'ai_19', filename: '19.png', type: 'AI', path: '/images/ai/19.png', thumbPath: '/images/ai/thumb-sm/19.webp', correct_answer: 'AI', style: 'photograph', source: 'nanobanana' },
  { id: 'ai_20', filename: '20.png', type: 'AI', path: '/images/ai/20.png', thumbPath: '/images/ai/thumb-sm/20.webp', correct_answer: 'AI', style: 'illustration', source: 'nanobanana' },

  // === Real images (20) ===
  { id: 'real_01', filename: '1.jpg', type: 'Real', path: '/images/human/1.jpg', thumbPath: '/images/human/thumb-sm/1.webp', correct_answer: 'Real', style: 'illustration', source: 'camera' },
  { id: 'real_02', filename: '2.jpg', type: 'Real', path: '/images/human/2.jpg', thumbPath: '/images/human/thumb-sm/2.webp', correct_answer: 'Real', style: 'photograph', source: 'camera' },
  { id: 'real_03', filename: '3.png', type: 'Real', path: '/images/human/3.png', thumbPath: '/images/human/thumb-sm/3.webp', correct_answer: 'Real', style: 'cartoon', source: 'camera' },
  { id: 'real_04', filename: '4.jpg', type: 'Real', path: '/images/human/4.jpg', thumbPath: '/images/human/thumb-sm/4.webp', correct_answer: 'Real', style: 'photograph', source: 'camera' },
  { id: 'real_05', filename: '5.jpg', type: 'Real', path: '/images/human/5.jpg', thumbPath: '/images/human/thumb-sm/5.webp', correct_answer: 'Real', style: 'illustration', source: 'camera' },
  { id: 'real_06', filename: '6.jpg', type: 'Real', path: '/images/human/6.jpg', thumbPath: '/images/human/thumb-sm/6.webp', correct_answer: 'Real', style: 'photograph', source: 'camera' },
  { id: 'real_07', filename: '7.jpg', type: 'Real', path: '/images/human/7.jpg', thumbPath: '/images/human/thumb-sm/7.webp', correct_answer: 'Real', style: 'illustration', source: 'website' },
  { id: 'real_08', filename: '8.webp', type: 'Real', path: '/images/human/8.webp', thumbPath: '/images/human/thumb-sm/8.webp', correct_answer: 'Real', style: 'photograph', source: 'website' },
  { id: 'real_09', filename: '9.jpg', type: 'Real', path: '/images/human/9.jpg', thumbPath: '/images/human/thumb-sm/9.webp', correct_answer: 'Real', style: 'illustration', source: 'website' },
  { id: 'real_10', filename: '10.jpg', type: 'Real', path: '/images/human/10.jpg', thumbPath: '/images/human/thumb-sm/10.webp', correct_answer: 'Real', style: 'illustration', source: 'website' },
  { id: 'real_11', filename: '11.jpg', type: 'Real', path: '/images/human/11.jpg', thumbPath: '/images/human/thumb-sm/11.webp', correct_answer: 'Real', style: 'photograph', source: 'website' },
  { id: 'real_12', filename: '12.jpg', type: 'Real', path: '/images/human/12.jpg', thumbPath: '/images/human/thumb-sm/12.webp', correct_answer: 'Real', style: 'photograph', source: 'website' },
  { id: 'real_13', filename: '13.jpg', type: 'Real', path: '/images/human/13.jpg', thumbPath: '/images/human/thumb-sm/13.webp', correct_answer: 'Real', style: 'illustration', source: 'website' },
  { id: 'real_14', filename: '14.jpg', type: 'Real', path: '/images/human/14.jpg', thumbPath: '/images/human/thumb-sm/14.webp', correct_answer: 'Real', style: 'cartoon', source: 'website' },
  { id: 'real_15', filename: '15.png', type: 'Real', path: '/images/human/15.png', thumbPath: '/images/human/thumb-sm/15.webp', correct_answer: 'Real', style: 'illustration', source: 'website' },
  { id: 'real_16', filename: '16.jpg', type: 'Real', path: '/images/human/16.jpg', thumbPath: '/images/human/thumb-sm/16.webp', correct_answer: 'Real', style: 'photograph', source: 'website' },
  { id: 'real_17', filename: '17.png', type: 'Real', path: '/images/human/17.png', thumbPath: '/images/human/thumb-sm/17.webp', correct_answer: 'Real', style: 'illustration', source: 'website' },
  { id: 'real_18', filename: '18.jpg', type: 'Real', path: '/images/human/18.jpg', thumbPath: '/images/human/thumb-sm/18.webp', correct_answer: 'Real', style: 'photograph', source: 'website' },
  { id: 'real_19', filename: '19.jpg', type: 'Real', path: '/images/human/19.jpg', thumbPath: '/images/human/thumb-sm/19.webp', correct_answer: 'Real', style: 'illustration', source: 'website' },
  { id: 'real_20', filename: '20.png', type: 'Real', path: '/images/human/20.png', thumbPath: '/images/human/thumb-sm/20.webp', correct_answer: 'Real', style: 'cartoon', source: 'website' },
];
