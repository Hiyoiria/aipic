/**
 * Google Lens 搜索结果数据加载器
 * Loader for pre-cached Google Lens search results
 *
 * 搜索结果数据与实验系统分离：
 * - 数据存放在 src/data/lens-results.json（占位数据或 SerpApi 抓取的真实数据）
 * - 本模块负责加载数据并按配置截取展示数量
 * - 呈现参数集中在 experimentConfig.ts 的 LENS_CONFIG 中
 *
 * 替换数据流程：
 * 1. 使用 SerpApi 脚本批量抓取搜索结果
 * 2. 输出为相同格式的 JSON 文件
 * 3. 替换 src/data/lens-results.json
 * 4. 无需修改任何代码
 */

import type { LensData, LensResult } from '@/types';
import { LENS_CONFIG } from './experimentConfig';
import lensResultsJson from '../data/lens-results.json';

// JSON 文件类型
const lensResults = lensResultsJson as Record<string, LensResult[]>;

/**
 * 获取指定图片的搜索结果
 * 按 LENS_CONFIG.resultsPerImage 截取展示数量
 */
export function getLensData(imageId: string): LensData {
  const allResults = lensResults[imageId] || [];
  const results = allResults.slice(0, LENS_CONFIG.resultsPerImage);
  return { imageId, results };
}
