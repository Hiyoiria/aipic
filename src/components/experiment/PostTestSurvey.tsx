'use client';

import { useState } from 'react';
import { useExperiment } from '@/contexts/ExperimentContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { getPostTestQuestions } from '@/lib/experimentContent';
import RadioGroup from '@/components/ui/RadioGroup';
import LikertScale from '@/components/ui/LikertScale';
import CheckboxGroup from '@/components/ui/CheckboxGroup';
import TextArea from '@/components/ui/TextArea';
import Button from '@/components/ui/Button';

export default function PostTestSurvey() {
  const { state, advancePhase } = useExperiment();
  const { language, t } = useLanguage();
  const [answers, setAnswers] = useState<Record<string, string | number | string[]>>({});
  const [loading, setLoading] = useState(false);

  const questions = getPostTestQuestions(language);

  // Filter questions based on group
  const visibleQuestions = questions.filter((q) => {
    if (!q.conditionalGroups) return true;
    return state.group && q.conditionalGroups.includes(state.group);
  });

  const allAnswered = visibleQuestions.every((q) => {
    // Skip validation for non-required questions
    if (!q.required) return true;

    const val = answers[q.id];
    if (q.type === 'likert') return typeof val === 'number' && val > 0;
    if (q.type === 'checkbox') return Array.isArray(val) && val.length > 0;
    if (q.type === 'textarea') return typeof val === 'string' && val.trim().length > 0;
    return val !== undefined && val !== '';
  });

  const handleSubmit = async () => {
    if (!allAnswered || !state.participantId) return;
    setLoading(true);

    try {
      const res = await fetch('/api/post-survey', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          participant_id: state.participantId,
          manipulation_check_read: answers.manipulation_check_read || '',
          manipulation_check_strategies: answers.manipulation_check_strategies || [],
          strategy_usage_degree: answers.strategy_usage_degree || null,
          open_method: answers.open_method || '',
          self_performance: answers.self_performance || 0,
          post_self_efficacy: answers.post_self_efficacy || 0,
          attention_check_answer: answers.attention_check || 0,
        }),
      });

      if (!res.ok) throw new Error('Failed to save');

      // Update participant phase
      await fetch(`/api/participants/${state.participantId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ current_phase: 5 }),
      });

      advancePhase();
    } catch (error) {
      console.error('Failed to save post-survey:', error);
      alert('An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 sm:p-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">{t('posttest.title')}</h1>
      <p className="text-gray-500 mb-8">
        {t('posttest.desc')}
      </p>

      {visibleQuestions.map((question) => {
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

        if (question.type === 'checkbox' && question.options) {
          return (
            <CheckboxGroup
              key={question.id}
              label={question.label}
              name={question.id}
              options={question.options}
              values={(answers[question.id] as string[]) || []}
              onChange={(vals) => setAnswers((prev) => ({ ...prev, [question.id]: vals }))}
              required={question.required}
            />
          );
        }

        if (question.type === 'textarea') {
          return (
            <TextArea
              key={question.id}
              label={question.label}
              name={question.id}
              value={(answers[question.id] as string) || ''}
              onChange={(val) => setAnswers((prev) => ({ ...prev, [question.id]: val }))}
              maxLength={question.maxLength}
              required={question.required}
            />
          );
        }

        return null;
      })}

      <div className="mt-8 flex justify-end">
        <Button onClick={handleSubmit} disabled={!allAnswered} loading={loading} className="w-full sm:w-auto">
          {t('posttest.submit')}
        </Button>
      </div>
    </div>
  );
}
