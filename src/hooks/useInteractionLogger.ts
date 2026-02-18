'use client';

import { useCallback } from 'react';
import type { InteractionAction } from '@/types';

interface LogParams {
  participantId: string | null;
  imageId: string;
  imageOrder: number;
}

export function useInteractionLogger({ participantId, imageId, imageOrder }: LogParams) {
  const logInteraction = useCallback(
    (action: InteractionAction, metadata?: Record<string, unknown>) => {
      if (!participantId) return;

      // Fire-and-forget
      fetch('/api/interaction-logs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          participant_id: participantId,
          image_id: imageId,
          image_order: imageOrder,
          action,
          metadata: metadata || {},
          client_timestamp: Date.now(),
        }),
      }).catch((err) => console.error('Failed to log interaction:', err));
    },
    [participantId, imageId, imageOrder]
  );

  return { logInteraction };
}
