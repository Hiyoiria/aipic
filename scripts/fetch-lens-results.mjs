/**
 * ╔══════════════════════════════════════════════════════════════╗
 * ║   SerpApi Google Lens 搜索结果采集脚本                        ║
 * ║   Fetch Google Lens results for all 40 experiment images     ║
 * ╚══════════════════════════════════════════════════════════════╝
 *
 * 使用方法:
 *   set SERPAPI_KEY=你的key && node scripts/fetch-lens-results.mjs
 *
 * 可选参数:
 *   --dry-run     仅打印将要请求的 URL 列表，不调用 API
 *   --resume      跳过已有结果的图片（断点续采）
 *   --delay=2000  请求间隔毫秒数（默认 2000）
 *   --max=6       每张图保留的最大结果数（默认 6）
 *
 * 输出:
 *   src/data/lens-results.json
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(__dirname, '..');
const OUTPUT_PATH = path.join(PROJECT_ROOT, 'src', 'data', 'lens-results.json');

// ============================================================================
// 图片 GitHub raw URL + 本地缩略图映射
// 仓库: https://github.com/Hiyoiria/study2pic
// ============================================================================

const GITHUB_RAW = 'https://raw.githubusercontent.com/Hiyoiria/study2pic/main';

const IMAGES = [
  // AI images (20)
  { id: 'ai_01', url: `${GITHUB_RAW}/ai/1.jpg`,   thumb: '/images/ai/thumb/1.webp' },
  { id: 'ai_02', url: `${GITHUB_RAW}/ai/2.jpg`,   thumb: '/images/ai/thumb/2.webp' },
  { id: 'ai_03', url: `${GITHUB_RAW}/ai/3.jpg`,   thumb: '/images/ai/thumb/3.webp' },
  { id: 'ai_04', url: `${GITHUB_RAW}/ai/4.jpg`,   thumb: '/images/ai/thumb/4.webp' },
  { id: 'ai_05', url: `${GITHUB_RAW}/ai/5.jpg`,   thumb: '/images/ai/thumb/5.webp' },
  { id: 'ai_06', url: `${GITHUB_RAW}/ai/6.jpg`,   thumb: '/images/ai/thumb/6.webp' },
  { id: 'ai_07', url: `${GITHUB_RAW}/ai/7.png`,   thumb: '/images/ai/thumb/7.webp' },
  { id: 'ai_08', url: `${GITHUB_RAW}/ai/8.png`,   thumb: '/images/ai/thumb/8.webp' },
  { id: 'ai_09', url: `${GITHUB_RAW}/ai/9.png`,   thumb: '/images/ai/thumb/9.webp' },
  { id: 'ai_10', url: `${GITHUB_RAW}/ai/10.png`,  thumb: '/images/ai/thumb/10.webp' },
  { id: 'ai_11', url: `${GITHUB_RAW}/ai/11.png`,  thumb: '/images/ai/thumb/11.webp' },
  { id: 'ai_12', url: `${GITHUB_RAW}/ai/12.png`,  thumb: '/images/ai/thumb/12.webp' },
  { id: 'ai_13', url: `${GITHUB_RAW}/ai/13.png`,  thumb: '/images/ai/thumb/13.webp' },
  { id: 'ai_14', url: `${GITHUB_RAW}/ai/14.png`,  thumb: '/images/ai/thumb/14.webp' },
  { id: 'ai_15', url: `${GITHUB_RAW}/ai/15.png`,  thumb: '/images/ai/thumb/15.webp' },
  { id: 'ai_16', url: `${GITHUB_RAW}/ai/16.png`,  thumb: '/images/ai/thumb/16.webp' },
  { id: 'ai_17', url: `${GITHUB_RAW}/ai/17.png`,  thumb: '/images/ai/thumb/17.webp' },
  { id: 'ai_18', url: `${GITHUB_RAW}/ai/18.png`,  thumb: '/images/ai/thumb/18.webp' },
  { id: 'ai_19', url: `${GITHUB_RAW}/ai/19.png`,  thumb: '/images/ai/thumb/19.webp' },
  { id: 'ai_20', url: `${GITHUB_RAW}/ai/20.png`,  thumb: '/images/ai/thumb/20.webp' },
  // Real images (20)
  { id: 'real_01', url: `${GITHUB_RAW}/human/1.jpg`,   thumb: '/images/human/thumb/1.webp' },
  { id: 'real_02', url: `${GITHUB_RAW}/human/2.jpg`,   thumb: '/images/human/thumb/2.webp' },
  { id: 'real_03', url: `${GITHUB_RAW}/human/3.png`,   thumb: '/images/human/thumb/3.webp' },
  { id: 'real_04', url: `${GITHUB_RAW}/human/4.jpg`,   thumb: '/images/human/thumb/4.webp' },
  { id: 'real_05', url: `${GITHUB_RAW}/human/5.jpg`,   thumb: '/images/human/thumb/5.webp' },
  { id: 'real_06', url: `${GITHUB_RAW}/human/6.jpg`,   thumb: '/images/human/thumb/6.webp' },
  { id: 'real_07', url: `${GITHUB_RAW}/human/7.jpg`,   thumb: '/images/human/thumb/7.webp' },
  { id: 'real_08', url: `${GITHUB_RAW}/human/8.webp`,  thumb: '/images/human/thumb/8.webp' },
  { id: 'real_09', url: `${GITHUB_RAW}/human/9.jpg`,   thumb: '/images/human/thumb/9.webp' },
  { id: 'real_10', url: `${GITHUB_RAW}/human/10.jpg`,  thumb: '/images/human/thumb/10.webp' },
  { id: 'real_11', url: `${GITHUB_RAW}/human/11.jpg`,  thumb: '/images/human/thumb/11.webp' },
  { id: 'real_12', url: `${GITHUB_RAW}/human/12.jpg`,  thumb: '/images/human/thumb/12.webp' },
  { id: 'real_13', url: `${GITHUB_RAW}/human/13.jpg`,  thumb: '/images/human/thumb/13.webp' },
  { id: 'real_14', url: `${GITHUB_RAW}/human/14.jpg`,  thumb: '/images/human/thumb/14.webp' },
  { id: 'real_15', url: `${GITHUB_RAW}/human/15.png`,  thumb: '/images/human/thumb/15.webp' },
  { id: 'real_16', url: `${GITHUB_RAW}/human/16.jpg`,  thumb: '/images/human/thumb/16.webp' },
  { id: 'real_17', url: `${GITHUB_RAW}/human/17.png`,  thumb: '/images/human/thumb/17.webp' },
  { id: 'real_18', url: `${GITHUB_RAW}/human/18.jpg`,  thumb: '/images/human/thumb/18.webp' },
  { id: 'real_19', url: `${GITHUB_RAW}/human/19.jpg`,  thumb: '/images/human/thumb/19.webp' },
  { id: 'real_20', url: `${GITHUB_RAW}/human/20.png`,  thumb: '/images/human/thumb/20.webp' },
];

// ============================================================================
// 工具函数
// ============================================================================

function parseArgs() {
  const args = process.argv.slice(2);
  return {
    dryRun: args.includes('--dry-run'),
    resume: args.includes('--resume'),
    delay: parseInt(args.find(a => a.startsWith('--delay='))?.split('=')[1] || '2000', 10),
    max: parseInt(args.find(a => a.startsWith('--max='))?.split('=')[1] || '6', 10),
  };
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 调用 SerpApi Google Lens 接口
 * 文档: https://serpapi.com/google-lens-api
 */
async function fetchLensResults(imageUrl, apiKey) {
  const params = new URLSearchParams({
    engine: 'google_lens',
    url: imageUrl,
    api_key: apiKey,
  });

  const response = await fetch(`https://serpapi.com/search?${params}`);

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`SerpApi ${response.status}: ${text.slice(0, 200)}`);
  }

  return response.json();
}

/**
 * 从 SerpApi 响应中提取 visual_matches，转换为系统所需格式
 */
function extractResults(serpData, fallbackThumb, maxResults) {
  const matches = serpData.visual_matches || [];

  return matches.slice(0, maxResults).map(match => ({
    title: match.title || 'Untitled',
    source: match.source || extractDomain(match.link),
    link: match.link || '',
    thumbnailUrl: match.thumbnail || fallbackThumb,
    snippet: match.snippet || '',
  }));
}

function extractDomain(url) {
  try {
    return new URL(url).hostname.replace('www.', '');
  } catch {
    return '';
  }
}

// ============================================================================
// 主流程
// ============================================================================

async function main() {
  const opts = parseArgs();
  const SERPAPI_KEY = process.env.SERPAPI_KEY || '16e1a649a976b70c284ed88e38da4686feeee2357da4265498d74a126eb85ff0';

  console.log('=== Google Lens 搜索结果采集 ===');
  console.log(`    图片来源: ${GITHUB_RAW}`);
  console.log(`    输出文件: ${OUTPUT_PATH}\n`);

  // 检查 API Key
  if (!SERPAPI_KEY && !opts.dryRun) {
    console.error('缺少 SERPAPI_KEY 环境变量\n');
    console.error('Windows:  set SERPAPI_KEY=你的key && node scripts/fetch-lens-results.mjs');
    console.error('Mac/Linux: SERPAPI_KEY=你的key node scripts/fetch-lens-results.mjs');
    console.error('\n或先用 --dry-run 查看将要请求的列表');
    process.exit(1);
  }

  // 加载已有数据（用于 --resume）
  let existing = {};
  if (opts.resume && fs.existsSync(OUTPUT_PATH)) {
    existing = JSON.parse(fs.readFileSync(OUTPUT_PATH, 'utf-8'));
    const existCount = Object.keys(existing).filter(k => existing[k].length > 0).length;
    console.log(`已加载现有数据: ${existCount} 张图片有结果\n`);
  }

  // 确定需要采集的图片
  const toFetch = opts.resume
    ? IMAGES.filter(img => !existing[img.id] || existing[img.id].length === 0)
    : IMAGES;

  console.log(`总图片数: ${IMAGES.length}`);
  console.log(`待采集数: ${toFetch.length}`);
  console.log(`每张保留: ${opts.max} 条结果`);
  console.log(`请求间隔: ${opts.delay}ms\n`);

  // --dry-run 模式
  if (opts.dryRun) {
    console.log('--- DRY RUN ---\n');
    toFetch.forEach((img, i) => {
      console.log(`  ${String(i + 1).padStart(2)}. ${img.id.padEnd(8)} ${img.url}`);
    });
    console.log(`\n共 ${toFetch.length} 次 SerpApi 请求`);
    return;
  }

  // 开始采集
  const results = { ...existing };
  let success = 0;
  let failed = 0;
  const failures = [];

  for (let i = 0; i < toFetch.length; i++) {
    const img = toFetch[i];
    const progress = `[${String(i + 1).padStart(2)}/${toFetch.length}]`;

    try {
      process.stdout.write(`${progress} ${img.id.padEnd(8)} `);

      const serpData = await fetchLensResults(img.url, SERPAPI_KEY);
      const extracted = extractResults(serpData, img.thumb, opts.max);

      results[img.id] = extracted;
      success++;

      console.log(`${extracted.length} 条结果`);

      // 每次成功立即保存（防止中途失败丢数据）
      fs.writeFileSync(OUTPUT_PATH, JSON.stringify(results, null, 2));

    } catch (err) {
      failed++;
      failures.push(img.id);
      console.log(`失败: ${err.message}`);
    }

    // 请求间隔
    if (i < toFetch.length - 1) {
      await sleep(opts.delay);
    }
  }

  // 最终保存
  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(results, null, 2));

  console.log('\n=== 完成 ===');
  console.log(`成功: ${success}  失败: ${failed}`);
  console.log(`输出: ${OUTPUT_PATH}`);

  const totalWithResults = Object.keys(results).filter(k => results[k].length > 0).length;
  console.log(`共 ${totalWithResults}/40 张图片有搜索结果`);

  if (failures.length > 0) {
    console.log(`\n失败的图片: ${failures.join(', ')}`);
    console.log('可用 --resume 重试失败的图片');
  }
}

main().catch(err => {
  console.error('脚本执行失败:', err);
  process.exit(1);
});
