'use client';

import React, { createContext, useContext, useReducer, useCallback, useEffect } from 'react';
import type { ExperimentState, ExperimentAction, Group, ImageMeta, ResponseData } from '@/types';

const initialState: ExperimentState = {
  participantId: null,
  prolificId: null,
  group: null,
  imageSeed: null,
  currentPhase: 0,
  imageList: [],
  currentImageIndex: 0,
  responses: [],
  experimentStartTime: null,
  isRecovering: false,
  isLoading: false,
};

function experimentReducer(state: ExperimentState, action: ExperimentAction): ExperimentState {
  switch (action.type) {
    case 'INIT_PARTICIPANT':
      return {
        ...state,
        participantId: action.payload.participantId,
        group: action.payload.group,
        imageSeed: action.payload.imageSeed,
        prolificId: action.payload.prolificId || null,
        currentPhase: 0,
        experimentStartTime: Date.now(),
      };
    case 'ADVANCE_PHASE':
      return {
        ...state,
        currentPhase: state.currentPhase + 1,
      };
    case 'SET_PHASE':
      return {
        ...state,
        currentPhase: action.payload,
      };
    case 'SET_IMAGE_LIST':
      return {
        ...state,
        imageList: action.payload,
      };
    case 'ADVANCE_IMAGE':
      return {
        ...state,
        currentImageIndex: state.currentImageIndex + 1,
      };
    case 'ADD_RESPONSE':
      return {
        ...state,
        responses: [...state.responses, action.payload],
      };
    case 'SET_RECOVERING':
      return {
        ...state,
        isRecovering: action.payload,
      };
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload,
      };
    case 'SET_START_TIME':
      return {
        ...state,
        experimentStartTime: action.payload,
      };
    default:
      return state;
  }
}

interface ExperimentContextValue {
  state: ExperimentState;
  initParticipant: (participantId: string, group: Group, imageSeed: string, prolificId?: string) => void;
  advancePhase: () => void;
  setPhase: (phase: number) => void;
  setImageList: (images: ImageMeta[]) => void;
  advanceImage: () => void;
  addResponse: (response: ResponseData) => void;
  setRecovering: (recovering: boolean) => void;
  setLoading: (loading: boolean) => void;
}

const ExperimentContext = createContext<ExperimentContextValue | null>(null);

export function ExperimentProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(experimentReducer, initialState);

  // Persist key state to sessionStorage
  useEffect(() => {
    if (state.participantId) {
      sessionStorage.setItem('study2_participant_id', state.participantId);
      sessionStorage.setItem('study2_current_phase', String(state.currentPhase));
      if (state.group) sessionStorage.setItem('study2_group', state.group);
      if (state.imageSeed) sessionStorage.setItem('study2_image_seed', state.imageSeed);
    }
  }, [state.participantId, state.currentPhase, state.group, state.imageSeed]);

  const initParticipant = useCallback(
    (participantId: string, group: Group, imageSeed: string, prolificId?: string) => {
      dispatch({ type: 'INIT_PARTICIPANT', payload: { participantId, group, imageSeed, prolificId } });
    },
    []
  );

  const advancePhase = useCallback(() => {
    dispatch({ type: 'ADVANCE_PHASE' });
  }, []);

  const setPhase = useCallback((phase: number) => {
    dispatch({ type: 'SET_PHASE', payload: phase });
  }, []);

  const setImageList = useCallback((images: ImageMeta[]) => {
    dispatch({ type: 'SET_IMAGE_LIST', payload: images });
  }, []);

  const advanceImage = useCallback(() => {
    dispatch({ type: 'ADVANCE_IMAGE' });
  }, []);

  const addResponse = useCallback((response: ResponseData) => {
    dispatch({ type: 'ADD_RESPONSE', payload: response });
  }, []);

  const setRecovering = useCallback((recovering: boolean) => {
    dispatch({ type: 'SET_RECOVERING', payload: recovering });
  }, []);

  const setLoading = useCallback((loading: boolean) => {
    dispatch({ type: 'SET_LOADING', payload: loading });
  }, []);

  return (
    <ExperimentContext.Provider
      value={{
        state,
        initParticipant,
        advancePhase,
        setPhase,
        setImageList,
        advanceImage,
        addResponse,
        setRecovering,
        setLoading,
      }}
    >
      {children}
    </ExperimentContext.Provider>
  );
}

export function useExperiment() {
  const context = useContext(ExperimentContext);
  if (!context) {
    throw new Error('useExperiment must be used within an ExperimentProvider');
  }
  return context;
}
