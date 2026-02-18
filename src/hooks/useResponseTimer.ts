'use client';

import { useRef, useCallback } from 'react';

export function useResponseTimer() {
  const startTimeRef = useRef<number | null>(null);

  const startTimer = useCallback(() => {
    startTimeRef.current = performance.now();
  }, []);

  const stopTimer = useCallback((): number => {
    if (startTimeRef.current === null) return 0;
    const elapsed = Math.round(performance.now() - startTimeRef.current);
    startTimeRef.current = null;
    return elapsed;
  }, []);

  const resetTimer = useCallback(() => {
    startTimeRef.current = null;
  }, []);

  return { startTimer, stopTimer, resetTimer };
}
