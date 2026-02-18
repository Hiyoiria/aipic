'use client';

import { useEffect } from 'react';

export function useImagePreloader(nextImageUrl: string | null) {
  useEffect(() => {
    if (!nextImageUrl) return;
    const img = new Image();
    img.src = nextImageUrl;
  }, [nextImageUrl]);
}
