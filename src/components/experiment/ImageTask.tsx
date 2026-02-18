'use client';

import { useState, useEffect, useCallback } from 'react';
import { useExperiment } from '@/contexts/ExperimentContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { useResponseTimer } from '@/hooks/useResponseTimer';
import { useImagePreloader } from '@/hooks/useImagePreloader';
import ImageDisplay from './ImageDisplay';
import ProgressBar from './ProgressBar';
import LikertScale from '@/components/ui/LikertScale';
import TextArea from '@/components/ui/TextArea';
import Button from '@/components/ui/Button';
import type { ImageType } from '@/types';

export default function ImageTask() {
  const { state, setImageList, advanceImage, addResponse, advancePhase } = useExperiment();
  const { t } = useLanguage();
  const { startTimer, stopTimer, resetTimer } = useResponseTimer();

  const [judgment, setJudgment] = useState<ImageType | ''>('');
  const [confidence, setConfidence] = useState(0);
  const [reasoning, setReasoning] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);

  useEffect(() => {
    if (state.imageSeed && state.imageList.length === 0) {
      fetch(`/api/images?seed=${state.imageSeed}`)
        .then((res) => res.json())
        .then((images) => setImageList(images))
        .catch((err) => console.error('Failed to load images:', err));
    }
  }, [state.imageSeed, state.imageList.length, setImageList]);

  const nextImage =
    state.currentImageIndex < state.imageList.length - 1
      ? state.imageList[state.currentImageIndex + 1]
      : null;
  useImagePreloader(nextImage?.thumbPath ?? null);

  const totalImages = state.imageList.length;
  const currentImage = state.imageList[state.currentImageIndex];

  const handleImageLoad = useCallback(() => {
    setImageLoaded(true);
    startTimer();
  }, [startTimer]);

  const canProceed = judgment !== '' && confidence > 0;

  const handleNext = async () => {
    if (!canProceed || !currentImage || !state.participantId) return;
    setSubmitting(true);

    const responseTimeMs = stopTimer();

    const responseData = {
      participant_id: state.participantId,
      image_id: currentImage.id,
      image_order: state.currentImageIndex + 1,
      judgment: judgment as ImageType,
      correct_answer: currentImage.correct_answer,
      is_correct: judgment === currentImage.correct_answer,
      confidence,
      reasoning,
      response_time_ms: responseTimeMs,
    };

    try {
      const res = await fetch('/api/responses', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(responseData),
      });

      if (!res.ok) throw new Error('Failed to save response');

      addResponse(responseData);

      if (state.currentImageIndex >= totalImages - 1) {
        await fetch(`/api/participants/${state.participantId}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ current_phase: 4 }),
        });
        advancePhase();
      } else {
        advanceImage();
        setJudgment('');
        setConfidence(0);
        setReasoning('');
        setImageLoaded(false);
        resetTimer();
      }
    } catch (error) {
      console.error('Failed to save response:', error);
      alert('An error occurred. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (state.imageList.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">{t('task.loading')}</p>
      </div>
    );
  }

  if (!currentImage) {
    return <div className="text-center text-gray-500">{t('task.noMore')}</div>;
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 sm:p-8">
      <ProgressBar current={state.currentImageIndex + 1} total={totalImages} />

      <ImageDisplay
        thumbSrc={currentImage.thumbPath}
        fullSrc={currentImage.path}
        alt={`Image ${state.currentImageIndex + 1}`}
        imageId={currentImage.id}
        imageOrder={state.currentImageIndex + 1}
        participantId={state.participantId}
        onLoad={handleImageLoad}
      />

      {imageLoaded && (
        <div className="space-y-6">
          <fieldset>
            <legend className="text-base font-medium text-gray-900 mb-3">
              {t('task.question')}
              <span className="text-red-500 ml-1">*</span>
            </legend>
            <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
              {(['AI', 'Real'] as const).map((option) => (
                <label
                  key={option}
                  className={`flex-1 flex items-center justify-center gap-2 p-4 rounded-lg border-2 cursor-pointer transition-all min-h-[56px] ${
                    judgment === option
                      ? option === 'AI'
                        ? 'border-purple-500 bg-purple-50 text-purple-700'
                        : 'border-green-500 bg-green-50 text-green-700'
                      : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <input
                    type="radio"
                    name="judgment"
                    value={option}
                    checked={judgment === option}
                    onChange={() => setJudgment(option)}
                    className="sr-only"
                  />
                  <span className="text-lg font-medium">
                    {option === 'AI' ? t('task.ai') : t('task.real')}
                  </span>
                </label>
              ))}
            </div>
          </fieldset>

          <LikertScale
            label={t('task.confidence')}
            name="confidence"
            value={confidence}
            onChange={setConfidence}
            min={t('task.confidenceMin')}
            max={t('task.confidenceMax')}
            count={5}
            required
          />

          <TextArea
            label={t('task.reasoning')}
            name="reasoning"
            value={reasoning}
            onChange={setReasoning}
            placeholder={t('task.reasoningPlaceholder')}
            maxLength={200}
          />

          <div className="flex justify-end pt-4">
            <Button onClick={handleNext} disabled={!canProceed} loading={submitting} className="w-full sm:w-auto">
              {state.currentImageIndex < totalImages - 1 ? t('task.next') : t('task.finish')}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
