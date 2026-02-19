'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { useExperiment } from '@/contexts/ExperimentContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { getInterventionContent } from '@/lib/experimentContent';
import { EXPERIMENT_CONFIG } from '@/lib/experimentConfig';
import CountdownTimer from '@/components/ui/CountdownTimer';
import Button from '@/components/ui/Button';

export default function InterventionPage() {
  const { state, advancePhase } = useExperiment();
  const { language, t } = useLanguage();
  const [timerDone, setTimerDone] = useState(false);
  const [loading, setLoading] = useState(false);
  const startTimeRef = useRef(Date.now());

  // 利用用户阅读干预材料的时间，在后台预加载所有任务图片
  useEffect(() => {
    if (!state.imageSeed) return;
    fetch(`/api/images?seed=${state.imageSeed}`)
      .then((res) => res.json())
      .then((images: Array<{ thumbPath: string }>) => {
        images.forEach((img) => {
          const el = new Image();
          el.src = img.thumbPath;
        });
      })
      .catch(() => {/* 预加载失败不影响主流程 */});
  }, [state.imageSeed]);

  const allContent = getInterventionContent(language);
  const content = state.group ? allContent[state.group] : null;

  const handleTimerComplete = useCallback(() => {
    setTimerDone(true);
  }, []);

  const handleNext = async () => {
    if (!state.participantId) return;
    setLoading(true);

    const durationS = Math.round((Date.now() - startTimeRef.current) / 1000);

    try {
      const res = await fetch(`/api/participants/${state.participantId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          intervention_duration_s: durationS,
          current_phase: 3,
        }),
      });

      if (!res.ok) throw new Error('Failed to save');
      advancePhase();
    } catch (error) {
      console.error('Failed to save intervention duration:', error);
      alert('An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (!content) {
    return <div className="text-center text-gray-500">Loading...</div>;
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 sm:p-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">{content.title}</h1>

      {content.sections.map((section, sIdx) => (
        <div key={sIdx} className="mb-6">
          {section.heading && (
            <h2 className="text-lg font-semibold text-gray-800 mb-3">{section.heading}</h2>
          )}
          {section.paragraphs.map((paragraph, pIdx) => (
            <p key={pIdx} className="text-gray-600 mb-4 leading-relaxed [&_strong]:text-red-600 [&_strong]:font-bold"
              dangerouslySetInnerHTML={{ __html: paragraph }}
            />
          ))}
          {section.images && section.images.length > 0 && (
            <div className="space-y-4 my-4">
              {section.images.map((img, iIdx) => (
                <figure key={iIdx} className="text-center">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={img.src}
                    alt={img.alt}
                    className="w-full sm:w-auto mx-auto rounded-lg border border-gray-200 shadow-sm"
                    style={{ maxWidth: '100%', height: 'auto' }}
                    loading="eager"
                    fetchPriority="high"
                  />
                  {img.caption && (
                    <figcaption className="text-xs sm:text-sm text-gray-500 mt-2 italic px-2">
                      {img.caption}
                    </figcaption>
                  )}
                </figure>
              ))}
            </div>
          )}
        </div>
      ))}

      <div className="mt-8 border-t border-gray-200 pt-6 space-y-4">
        {!timerDone && (
          <CountdownTimer seconds={EXPERIMENT_CONFIG.interventionMinStaySeconds} onComplete={handleTimerComplete} />
        )}

        <div className="flex justify-end">
          <Button onClick={handleNext} disabled={!timerDone} loading={loading} className="w-full sm:w-auto">
            {timerDone ? t('intervention.continue') : t('intervention.wait')}
          </Button>
        </div>
      </div>
    </div>
  );
}
