'use client';

import { useEffect, useState } from 'react';
import { useExperiment } from '@/contexts/ExperimentContext';
import { useLanguage } from '@/contexts/LanguageContext';

export default function EndPage() {
  const { state } = useExperiment();
  const { t } = useLanguage();
  const [saved, setSaved] = useState(false);

  const correctCount = state.responses.filter((r) => r.is_correct).length;
  const totalCount = state.responses.length;

  // Mark participant as completed
  useEffect(() => {
    if (saved || !state.participantId) return;

    const experimentStartTime = state.experimentStartTime || Date.now();
    const totalDurationS = Math.round((Date.now() - experimentStartTime) / 1000);
    // accuracyScore computed for DB record only, not displayed to participant
    const accuracyScore = totalCount > 0 ? correctCount / totalCount : 0;

    fetch(`/api/participants/${state.participantId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        completed: true,
        completed_at: new Date().toISOString(),
        total_duration_s: totalDurationS,
        accuracy_score: Math.round(accuracyScore * 100) / 100,
      }),
    })
      .then(() => setSaved(true))
      .catch((err) => console.error('Failed to mark completion:', err));
  }, [state.participantId, state.experimentStartTime, correctCount, totalCount, saved]);

  // Clear session storage since experiment is done
  useEffect(() => {
    sessionStorage.removeItem('study2_participant_id');
    sessionStorage.removeItem('study2_current_phase');
    sessionStorage.removeItem('study2_group');
    sessionStorage.removeItem('study2_image_seed');
  }, []);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 sm:p-8 text-center">
      <div className="mb-8">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg
            className="w-8 h-8 text-green-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 13l4 4L19 7"
            />
          </svg>
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">{t('end.title')}</h1>
        <p className="text-gray-600">
          {t('end.desc')}
        </p>
      </div>

      <div className="bg-gray-50 rounded-lg p-4 mb-6 inline-block">
        <p className="text-lg font-semibold text-gray-800">
          {correctCount} / {totalCount}
        </p>
        <p className="text-sm text-gray-500">{t('end.correct')}</p>
      </div>
    </div>
  );
}
