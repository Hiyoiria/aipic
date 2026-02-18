'use client';

import { useState } from 'react';
import { useExperiment } from '@/contexts/ExperimentContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { getPreTestQuestions } from '@/lib/experimentContent';
import RadioGroup from '@/components/ui/RadioGroup';
import LikertScale from '@/components/ui/LikertScale';
import Button from '@/components/ui/Button';

export default function PreTestSurvey() {
  const { state, advancePhase } = useExperiment();
  const { language, t } = useLanguage();
  const [answers, setAnswers] = useState<Record<string, string | number>>({});
  const [loading, setLoading] = useState(false);

  const questions = getPreTestQuestions(language);

  const allAnswered = questions.every((q) => {
    // Skip validation for non-required questions
    if (!q.required) return true;

    const val = answers[q.id];
    if (q.type === 'likert') return typeof val === 'number' && val > 0;
    return val !== undefined && val !== '';
  });

  const handleSubmit = async () => {
    if (!allAnswered || !state.participantId) return;
    setLoading(true);

    try {
      const res = await fetch(`/api/participants/${state.participantId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          age: answers.age,
          gender: answers.gender,
          education: answers.education,
          ai_tool_usage: answers.ai_tool_usage,
          ai_familiarity: answers.ai_familiarity,
          self_assessed_ability: answers.self_assessed_ability,
          ai_exposure_freq: answers.ai_exposure_freq,
          current_phase: 2,
        }),
      });

      if (!res.ok) throw new Error('Failed to save');
      advancePhase();
    } catch (error) {
      console.error('Failed to save pre-test survey:', error);
      alert('An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 sm:p-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">{t('pretest.title')}</h1>
      <p className="text-gray-500 mb-8">{t('pretest.desc')}</p>

      {questions.map((question) => {
        if (question.type === 'radio' && question.options) {
          return (
            <RadioGroup
              key={question.id}
              label={question.label}
              name={question.id}
              options={question.options}
              value={(answers[question.id] as string) || ''}
              onChange={(val) => setAnswers((prev) => ({ ...prev, [question.id]: val }))}
              required={question.required}
            />
          );
        }

        if (question.type === 'likert') {
          return (
            <LikertScale
              key={question.id}
              label={question.label}
              name={question.id}
              value={(answers[question.id] as number) || 0}
              onChange={(val) => setAnswers((prev) => ({ ...prev, [question.id]: val }))}
              min={question.likertMin}
              max={question.likertMax}
              count={question.likertCount}
              required={question.required}
            />
          );
        }

        return null;
      })}

      <div className="mt-8 flex justify-end">
        <Button onClick={handleSubmit} disabled={!allAnswered} loading={loading} className="w-full sm:w-auto">
          {t('pretest.next')}
        </Button>
      </div>
    </div>
  );
}
