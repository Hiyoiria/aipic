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

  const totalNeeded = EXPERIMENT_CONFIG.totalImages;

  // If configured count is less than total pool, subsample with 1:1 AI:Real ratio
  const pool = totalNeeded < IMAGE_DATA.length
    ? subsampleImages([...IMAGE_DATA], totalNeeded, seed)
    : [...IMAGE_DATA];

  const shuffled = shuffleImages(pool, seed);

  return NextResponse.json(shuffled);
}
