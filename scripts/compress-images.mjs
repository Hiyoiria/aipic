/**
 * 图像压缩脚本
 * 运行方式: node scripts/compress-images.mjs
 *
 * 效果：
 *   - intervention/*.png  → intervention/*.webp  (质量80，预计从 1-2MB 压至 100-300KB)
 *   - ai/thumb/*.webp     → 原地重压缩            (800px max edge，质量75)
 *   - human/thumb/*.webp  → 原地重压缩            (800px max edge，质量75)
 */

import sharp from 'sharp';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PUBLIC = path.join(__dirname, '..', 'public', 'images');

// ── 工具 ──────────────────────────────────────────────────────

function kb(bytes) {
  return (bytes / 1024).toFixed(0) + 'KB';
}

async function compressFile(src, dest, opts) {
  const before = fs.statSync(src).size;
  let s = sharp(src);
  if (opts.resize) s = s.resize(opts.resize, opts.resize, { fit: 'inside', withoutEnlargement: true });
  await s.webp({ quality: opts.quality }).toFile(dest + '.tmp');
  fs.renameSync(dest + '.tmp', dest);
  const after = fs.statSync(dest).size;
  console.log(`  ${path.basename(src)} → ${path.basename(dest)}  ${kb(before)} → ${kb(after)}  (${Math.round((1 - after/before)*100)}%↓)`);
}

async function recompressWebp(file, maxEdge, quality) {
  const before = fs.statSync(file).size;
  const buf = await sharp(file)
    .resize(maxEdge, maxEdge, { fit: 'inside', withoutEnlargement: true })
    .webp({ quality })
    .toBuffer();
  // 先删再写，绕过 Windows 只读锁
  fs.unlinkSync(file);
  fs.writeFileSync(file, buf);
  const after = fs.statSync(file).size;
  console.log(`  ${path.basename(file)}  ${kb(before)} → ${kb(after)}  (${Math.round((1 - after/before)*100)}%↓)`);
}

// ── 1. 干预图 PNG → WebP ──────────────────────────────────────

console.log('\n[1] 干预图 PNG → WebP (quality=80, max 1200px)');
const interventionDir = path.join(PUBLIC, 'intervention');
for (const file of fs.readdirSync(interventionDir)) {
  if (!file.endsWith('.png')) continue;
  const src  = path.join(interventionDir, file);
  const dest = path.join(interventionDir, file.replace('.png', '.webp'));
  await compressFile(src, dest, { resize: 1200, quality: 80 });
}

// ── 2. 任务图缩略图重压缩 → 输出到 thumb-sm/ ─────────────────

for (const sub of ['ai/thumb', 'human/thumb']) {
  const srcDir  = path.join(PUBLIC, sub);
  const destDir = path.join(PUBLIC, sub.replace('thumb', 'thumb-sm'));
  fs.mkdirSync(destDir, { recursive: true });
  console.log(`\n[2] ${sub} → ${sub.replace('thumb','thumb-sm')} (max 800px, quality=72)`);
  for (const file of fs.readdirSync(srcDir)) {
    if (!file.endsWith('.webp')) continue;
    const srcFile  = path.join(srcDir, file);
    const destFile = path.join(destDir, file);
    const before = fs.statSync(srcFile).size;
    const buf = await sharp(srcFile)
      .resize(800, 800, { fit: 'inside', withoutEnlargement: true })
      .webp({ quality: 72 })
      .toBuffer();
    fs.writeFileSync(destFile, buf);
    const after = fs.statSync(destFile).size;
    console.log(`  ${file}  ${kb(before)} → ${kb(after)}  (${Math.round((1 - after/before)*100)}%↓)`);
  }
}

console.log('\n完成！请重新部署以生效。');
console.log('注意：experimentContent.ts 中的干预图路径已需更新为 .webp 后缀。');
