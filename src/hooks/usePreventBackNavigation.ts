'use client';

import { useEffect } from 'react';

export function usePreventBackNavigation() {
  useEffect(() => {
    // Push a dummy state so there is history to intercept
    window.history.pushState(null, '', window.location.href);

    const handlePopState = () => {
      // Push state again to cancel back navigation
      window.history.pushState(null, '', window.location.href);
    };

    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault();
    };

    window.addEventListener('popstate', handlePopState);
    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('popstate', handlePopState);
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, []);
}
