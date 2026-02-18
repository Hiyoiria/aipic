import seedrandom from 'seedrandom';
import type { ImageMeta, Group } from '@/types';

/**
 * Block randomization for group assignment.
 * Ensures balanced A/C allocation using blocks of 2.
 */
export function getNextGroupAssignment(
  currentCounts: { A: number; C: number }
): Group {
  const total = currentCounts.A + currentCounts.C;
  const blockIndex = Math.floor(total / 2);

  // Determine which groups are already assigned in the current block
  const assignedInBlock: Group[] = [];
  if (currentCounts.A > blockIndex) assignedInBlock.push('A');
  if (currentCounts.C > blockIndex) assignedInBlock.push('C');

  const remaining = (['A', 'C'] as const).filter(
    (g) => !assignedInBlock.includes(g)
  );

  // Pick randomly from remaining groups in the block
  return remaining[Math.floor(Math.random() * remaining.length)];
}

/**
 * Fisher-Yates shuffle with a seeded PRNG.
 * Same seed always produces the same order.
 */
export function shuffleImages(images: ImageMeta[], seed: string): ImageMeta[] {
  const rng = seedrandom(seed);
  const shuffled = [...images];

  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }

  return shuffled;
}

/**
 * 从图片池中随机抽取指定数量的图片，保证 AI:Real = 1:1
 * Subsample images from the pool, maintaining 1:1 AI:Real ratio.
 *
 * @param images - 全部图片池
 * @param totalCount - 需要的图片总数（必须为偶数）
 * @param seed - 随机种子（保证可复现）
 * @returns 抽取后的图片数组（未打乱顺序，需再调用 shuffleImages）
 */
export function subsampleImages(
  images: ImageMeta[],
  totalCount: number,
  seed: string
): ImageMeta[] {
  const aiImages = images.filter((img) => img.type === 'AI');
  const realImages = images.filter((img) => img.type === 'Real');

  const halfCount = Math.floor(totalCount / 2);

  // If requesting more than available, use all
  const aiCount = Math.min(halfCount, aiImages.length);
  const realCount = Math.min(halfCount, realImages.length);

  // Use seeded RNG for reproducible subsampling
  const rng = seedrandom(seed + '_subsample');

  const selectedAI = seededSample(aiImages, aiCount, rng);
  const selectedReal = seededSample(realImages, realCount, rng);

  return [...selectedAI, ...selectedReal];
}

/**
 * Seeded random sample without replacement.
 */
function seededSample<T>(arr: T[], count: number, rng: () => number): T[] {
  const pool = [...arr];
  const result: T[] = [];

  for (let i = 0; i < count && pool.length > 0; i++) {
    const idx = Math.floor(rng() * pool.length);
    result.push(pool.splice(idx, 1)[0]);
  }

  return result;
}
