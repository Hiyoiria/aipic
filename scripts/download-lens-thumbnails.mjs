/**
 * Download all Google Lens thumbnail images to local public/images/lens/
 * and update lens-results.json to use local paths.
 *
 * Run ONCE from a network that can access Google (VPN / overseas).
 *
 *   node scripts/download-lens-thumbnails.mjs
 *   node scripts/download-lens-thumbnails.mjs --dry-run   # preview only
 */

import fs from 'fs';
import path from 'path';
import https from 'https';
import http from 'http';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(__dirname, '..');
const JSON_PATH = path.join(PROJECT_ROOT, 'src', 'data', 'lens-results.json');
const OUTPUT_DIR = path.join(PROJECT_ROOT, 'public', 'images', 'lens');

const DRY_RUN = process.argv.includes('--dry-run');
const DELAY_MS = 200; // polite delay between downloads

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function download(url, dest) {
  return new Promise((resolve, reject) => {
    const mod = url.startsWith('https') ? https : http;
    const file = fs.createWriteStream(dest);
    mod
      .get(url, { timeout: 15000 }, (res) => {
        if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
          // follow redirect
          file.close();
          fs.unlinkSync(dest);
          return download(res.headers.location, dest).then(resolve, reject);
        }
        if (res.statusCode !== 200) {
          file.close();
          fs.unlinkSync(dest);
          return reject(new Error(`HTTP ${res.statusCode} for ${url}`));
        }
        res.pipe(file);
        file.on('finish', () => file.close(resolve));
      })
      .on('error', (err) => {
        file.close();
        if (fs.existsSync(dest)) fs.unlinkSync(dest);
        reject(err);
      });
  });
}

async function main() {
  const data = JSON.parse(fs.readFileSync(JSON_PATH, 'utf-8'));

  if (!DRY_RUN) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  let total = 0;
  let downloaded = 0;
  let skipped = 0;
  let failed = 0;

  // Collect all tasks
  const tasks = [];
  for (const [imageId, results] of Object.entries(data)) {
    results.forEach((result, idx) => {
      if (result.thumbnailUrl && !result.thumbnailUrl.startsWith('/images/')) {
        tasks.push({ imageId, idx, result });
      }
    });
  }
  total = tasks.length;
  console.log(`Found ${total} external thumbnails to download.`);

  if (DRY_RUN) {
    console.log('Dry run — no files will be downloaded or modified.');
    tasks.slice(0, 5).forEach((t) =>
      console.log(`  ${t.imageId}_${t.idx}: ${t.result.thumbnailUrl}`)
    );
    if (tasks.length > 5) console.log(`  ... and ${tasks.length - 5} more`);
    return;
  }

  for (const { imageId, idx, result } of tasks) {
    const localName = `${imageId}_${idx}.jpg`;
    const localPath = path.join(OUTPUT_DIR, localName);
    const publicPath = `/images/lens/${localName}`;

    // Skip if already downloaded
    if (fs.existsSync(localPath)) {
      result.thumbnailUrl = publicPath;
      skipped++;
      continue;
    }

    try {
      await download(result.thumbnailUrl, localPath);
      result.thumbnailUrl = publicPath;
      downloaded++;
      process.stdout.write(`\r  Downloaded ${downloaded + skipped}/${total}`);
      await sleep(DELAY_MS);
    } catch (err) {
      console.warn(`\n  FAIL ${localName}: ${err.message}`);
      failed++;
    }
  }

  // Write updated JSON
  fs.writeFileSync(JSON_PATH, JSON.stringify(data, null, 2) + '\n', 'utf-8');

  console.log(`\n\nDone!`);
  console.log(`  Downloaded: ${downloaded}`);
  console.log(`  Skipped (already existed): ${skipped}`);
  console.log(`  Failed: ${failed}`);
  console.log(`  Output: ${OUTPUT_DIR}`);
  console.log(`  Updated: ${JSON_PATH}`);
}

main().catch(console.error);
