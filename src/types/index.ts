// ===== Participant =====
export type Group = 'A' | 'C';

export interface ParticipantData {
  participant_id: string;
  prolific_id?: string;
  group: Group;
  created_at: string;
  completed_at?: string;
  completed: boolean;
  consent_given: boolean;
  consent_timestamp?: string;
  intervention_duration_s: number;
  total_duration_s: number;
  // Demographics
  age: string;
  gender: string;
  education: string;
  ai_tool_usage: string;
  ai_familiarity: number;
  self_assessed_ability: number;
  ai_exposure_freq: string;
  // Computed
  accuracy_score?: number;
  image_seed: string;
  current_phase: number;
}

// ===== Image =====
export type ImageType = 'AI' | 'Real';

export interface ImageMeta {
  id: string;
  filename: string;
  type: ImageType;
  path: string;
  thumbPath: string;
  correct_answer: ImageType;
}

// ===== Response =====
export interface ResponseData {
  participant_id: string;
  image_id: string;
  image_order: number;
  judgment: ImageType;
  correct_answer: ImageType;
  is_correct: boolean;
  confidence?: number;
  reasoning?: string;
  response_time_ms: number;
}

// ===== Post Survey =====
export interface PostSurveyData {
  participant_id: string;
  manipulation_check_read: string;
  manipulation_check_strategies: string[];
  strategy_usage_degree?: number;
  open_method: string;
  self_performance: number;
  attention_check_answer: number;
  attention_check_passed: boolean;
}

// ===== Survey Questions =====
export type QuestionType = 'radio' | 'likert' | 'checkbox' | 'textarea';

export interface QuestionOption {
  value: string;
  label: string;
}

export interface QuestionDef {
  id: string;
  type: QuestionType;
  label: string;
  options?: QuestionOption[];
  required: boolean;
  likertMin?: string;
  likertMax?: string;
  likertCount?: number;
  maxLength?: number;
  conditionalGroups?: Group[];
}

// ===== Intervention Content =====
export interface InterventionImage {
  src: string;
  alt: string;
  caption?: string;
}

export interface InterventionContent {
  title: string;
  sections: InterventionSection[];
}

export interface InterventionSection {
  heading?: string;
  paragraphs: string[];
  images?: InterventionImage[];
}

// ===== Interaction Log (Google Lens simulation) =====
export type InteractionAction = 'TRIGGER_MENU' | 'OPEN_LENS' | 'SCROLL_LENS' | 'CLICK_RESULT';

export interface InteractionLogData {
  participant_id: string;
  image_id: string;
  image_order: number;
  action: InteractionAction;
  metadata?: Record<string, unknown>;
  client_timestamp: number;
}

// ===== Lens Search Result =====
export interface LensResult {
  title: string;
  source: string;
  link: string;
  thumbnailUrl: string;
  snippet?: string;
}

export interface LensData {
  imageId: string;
  results: LensResult[];
}

// ===== Experiment Context =====
export interface ExperimentState {
  participantId: string | null;
  prolificId: string | null;
  group: Group | null;
  imageSeed: string | null;
  currentPhase: number;
  imageList: ImageMeta[];
  currentImageIndex: number;
  responses: ResponseData[];
  experimentStartTime: number | null;
  isRecovering: boolean;
  isLoading: boolean;
}

export type ExperimentAction =
  | { type: 'INIT_PARTICIPANT'; payload: { participantId: string; group: Group; imageSeed: string; prolificId?: string } }
  | { type: 'ADVANCE_PHASE' }
  | { type: 'SET_PHASE'; payload: number }
  | { type: 'SET_IMAGE_LIST'; payload: ImageMeta[] }
  | { type: 'ADVANCE_IMAGE' }
  | { type: 'ADD_RESPONSE'; payload: ResponseData }
  | { type: 'SET_RECOVERING'; payload: boolean }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_START_TIME'; payload: number };
