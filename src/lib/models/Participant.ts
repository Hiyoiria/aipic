import mongoose, { Schema, Document } from 'mongoose';

export interface IParticipant extends Document {
  participant_id: string;
  prolific_id?: string;
  group: 'A' | 'C';
  created_at: Date;
  completed_at?: Date;
  completed: boolean;
  consent_given: boolean;
  consent_timestamp?: Date;
  intervention_duration_s: number;
  total_duration_s: number;
  age: string;
  gender: string;
  education: string;
  ai_tool_usage: string;
  ai_familiarity: number;
  self_assessed_ability: number;
  ai_exposure_freq: string;
  accuracy_score?: number;
  image_seed: string;
  current_phase: number;
}

const ParticipantSchema = new Schema<IParticipant>({
  participant_id: { type: String, required: true, unique: true, index: true },
  prolific_id: { type: String, sparse: true },
  group: { type: String, enum: ['A', 'C'], required: true },
  created_at: { type: Date, default: Date.now },
  completed_at: Date,
  completed: { type: Boolean, default: false },
  consent_given: { type: Boolean, default: false },
  consent_timestamp: Date,
  intervention_duration_s: { type: Number, default: 0 },
  total_duration_s: { type: Number, default: 0 },
  age: { type: String, default: '' },
  gender: { type: String, default: '' },
  education: { type: String, default: '' },
  ai_tool_usage: { type: String, default: '' },
  ai_familiarity: { type: Number, default: 0 },
  self_assessed_ability: { type: Number, default: 0 },
  ai_exposure_freq: { type: String, default: '' },
  accuracy_score: Number,
  image_seed: { type: String, required: true },
  current_phase: { type: Number, default: 0 },
});

export default mongoose.models.Participant ||
  mongoose.model<IParticipant>('Participant', ParticipantSchema);
