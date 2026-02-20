import { NextRequest, NextResponse } from 'next/server';
import { IMAGE_DATA } from '@/lib/imageData';
import { shuffleImages, subsampleImages } from '@/lib/randomization';
import { EXPERIMENT_CONFIG } from '@/lib/experimentConfig';

export async function GET(request: NextRequest) {
  const seed = request.nextUrl.searchParams.get('seed');

  if (!seed) {
    return NextResponse.json(
      { error: 'Missing seed parameter' },
      { status: 400 }
    );
  }

  let pool;
  if (EXPERIMENT_CONFIG.fixedImageIds) {
    const idSet = new Set(EXPERIMENT_CONFIG.fixedImageIds);
    pool = IMAGE_DATA.filter(img => idSet.has(img.id));
  } else {
    const totalNeeded = EXPERIMENT_CONFIG.totalImages;
    pool = totalNeeded < IMAGE_DATA.length
      ? subsampleImages([...IMAGE_DATA], totalNeeded, seed)
      : [...IMAGE_DATA];
  }

  const shuffled = shuffleImages(pool, seed);

  return NextResponse.json(shuffled);
}
