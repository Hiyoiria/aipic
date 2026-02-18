'use client';

import { useState } from 'react';
import { useExperiment } from '@/contexts/ExperimentContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { getWelcomeContent } from '@/lib/experimentContent';
import Button from '@/components/ui/Button';

export default function WelcomePage() {
  const { initParticipant, advancePhase } = useExperiment();
  const { language, setLanguage, t } = useLanguage();
  const [agreed, setAgreed] = useState(false);
  const [loading, setLoading] = useState(false);

  const content = getWelcomeContent(language);

  const handleAgree = async () => {
    setLoading(true);
    try {
      const urlParams = new URLSearchParams(window.location.search);
      const prolificId = urlParams.get('PROLIFIC_PID') || undefined;

      const res = await fetch('/api/participants', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prolific_id: prolificId }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error);

      initParticipant(data.participant_id, data.group, data.image_seed, prolificId);
      advancePhase();
    } catch (error) {
      console.error('Failed to create participant:', error);
      alert('An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 sm:p-8">
      {/* Language toggle */}
      <div className="flex justify-end mb-4">
        <button
          onClick={() => setLanguage(language === 'zh' ? 'en' : 'zh')}
          className="text-sm text-blue-600 hover:text-blue-800 border border-blue-200 rounded-md px-3 py-1.5 hover:bg-blue-50 transition-colors"
        >
          {t('welcome.langToggle')}
        </button>
      </div>

      <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-6">
        {t('welcome.title')}
      </h1>

      <div className="prose prose-gray max-w-none mb-8">
        <h2 className="text-lg font-semibold text-gray-800 mb-3">{content.researchOverview}</h2>
        <p className="text-gray-600 mb-4">{content.researchDesc}</p>

        <h2 className="text-lg font-semibold text-gray-800 mb-3">{content.whatToExpect}</h2>
        <ul className="text-gray-600 space-y-2 mb-4 list-disc list-inside">
          {content.expectations.map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>

        <h2 className="text-lg font-semibold text-gray-800 mb-3">{content.privacyTitle}</h2>
        <ul className="text-gray-600 space-y-2 mb-4 list-disc list-inside">
          {content.privacyItems.map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>
      </div>

      <div className="border-t border-gray-200 pt-6">
        <label className="flex items-start gap-3 cursor-pointer mb-6">
          <input
            type="checkbox"
            checked={agreed}
            onChange={(e) => setAgreed(e.target.checked)}
            className="w-5 h-5 text-blue-600 rounded focus:ring-blue-500 mt-0.5"
          />
          <span className="text-gray-700">{content.consentText}</span>
        </label>

        <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
          <Button onClick={handleAgree} disabled={!agreed} loading={loading} className="w-full sm:w-auto">
            {t('welcome.agree')}
          </Button>
          <Button
            variant="secondary"
            className="w-full sm:w-auto"
            onClick={() => {
              window.location.href = 'about:blank';
            }}
          >
            {t('welcome.disagree')}
          </Button>
        </div>
      </div>
    </div>
  );
}
