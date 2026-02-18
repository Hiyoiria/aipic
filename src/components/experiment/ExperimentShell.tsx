'use client';

import { useEffect } from 'react';
import { useExperiment } from '@/contexts/ExperimentContext';
import { usePreventBackNavigation } from '@/hooks/usePreventBackNavigation';
import WelcomePage from './WelcomePage';
import PreTestSurvey from './PreTestSurvey';
import InterventionPage from './InterventionPage';
import ImageTask from './ImageTask';
import PostTestSurvey from './PostTestSurvey';
import EndPage from './EndPage';
import type { Group } from '@/types';

export default function ExperimentShell() {
  const { state, initParticipant, setPhase, setImageList, setRecovering } = useExperiment();

  usePreventBackNavigation();

  // Session recovery on mount
  useEffect(() => {
    const savedId = sessionStorage.getItem('study2_participant_id');
    const savedPhase = sessionStorage.getItem('study2_current_phase');
    const savedGroup = sessionStorage.getItem('study2_group');
    const savedSeed = sessionStorage.getItem('study2_image_seed');

    if (savedId && savedPhase && savedGroup && savedSeed) {
      setRecovering(true);
      initParticipant(savedId, savedGroup as Group, savedSeed);
      setPhase(parseInt(savedPhase, 10));

      // If recovering into image task, fetch image list and determine position
      if (parseInt(savedPhase, 10) === 3) {
        fetch(`/api/images?seed=${savedSeed}`)
          .then((res) => res.json())
          .then((images) => {
            setImageList(images);
            // Count already submitted responses to determine position
            return fetch(`/api/participants/${savedId}`);
          })
          .then((res) => res.json())
          .then(() => {
            setRecovering(false);
          })
          .catch(() => {
            setRecovering(false);
          });
      } else {
        setRecovering(false);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (state.isRecovering) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Restoring your session...</p>
        </div>
      </div>
    );
  }

  const renderPhase = () => {
    switch (state.currentPhase) {
      case 0:
        return <WelcomePage />;
      case 1:
        return <PreTestSurvey />;
      case 2:
        return <InterventionPage />;
      case 3:
        return <ImageTask />;
      case 4:
        return <PostTestSurvey />;
      case 5:
        return <EndPage />;
      default:
        return <WelcomePage />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-3 py-4 sm:px-4 sm:py-8">
        {renderPhase()}
      </div>
    </div>
  );
}
