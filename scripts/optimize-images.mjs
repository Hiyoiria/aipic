import sharp from 'sharp';
import fs from 'fs';
import path from 'path';

const LONG_EDGE = 1200;
const QUALITY = 85;

const dirs = [
  { src: 'public/images/ai', dest: 'public/images/ai/thumb' },
  { src: 'public/images/human', dest: 'public/images/human/thumb' },
];

async function processImage(srcPath, destPath) {
  const meta = await sharp(srcPath).metadata();
  const isLandscape = (meta.width || 0) >= (meta.height || 0);

  const resizeOpts = isLandscape
    ? { width: LONG_EDGE, withoutEnlargement: true }
    : { height: LONG_EDGE, withoutEnlargement: true };

  await sharp(srcPath)
    .resize(resizeOpts)
    .webp({ quality: QUALITY })
    .toFile(destPath);

  const srcStat = fs.statSync(srcPath);
  const destStat = fs.statSync(destPath);
  const reduction = ((1 - destStat.size / srcStat.size) * 100).toFixed(1);

  console.log(
    `  ${path.basename(srcPath).padEnd(12)} ${(srcStat.size / 1024).toFixed(0).padStart(6)}KB -> ${(destStat.size / 1024).toFixed(0).padStart(5)}KB  (${reduction}% smaller)`
  );
}

async function main() {
  let totalSrcSize = 0;
  let totalDestSize = 0;

  for (const { src, dest } of dirs) {
    fs.mkdirSync(dest, { recursive: true });

    const files = fs.readdirSync(src).filter((f) => {
      const ext = path.extname(f).toLowerCase();
      return ['.jpg', '.jpeg', '.png', '.webp'].includes(ext);
    });

    console.log(`\nProcessing ${src}/ (${files.length} images):`);

    for (const file of files) {
      const srcPath = path.join(src, file);
      const baseName = path.parse(file).name;
      const destPath = path.join(dest, `${baseName}.webp`);

      try {
        await processImage(srcPath, destPath);
        totalSrcSize += fs.statSync(srcPath).size;
        totalDestSize += fs.statSync(destPath).size;
      } catch (err) {
        console.error(`  ERROR processing ${file}: ${err.message}`);
      }
    }
  }

  console.log(`\n========================================`);
  console.log(`Total: ${(totalSrcSize / 1024 / 1024).toFixed(1)}MB -> ${(totalDestSize / 1024 / 1024).toFixed(1)}MB`);
  console.log(`Overall reduction: ${((1 - totalDestSize / totalSrcSize) * 100).toFixed(1)}%`);
}

main().catch(console.error);
