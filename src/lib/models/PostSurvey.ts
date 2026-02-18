import mongoose, { Schema, Document } from 'mongoose';

export interface IPostSurvey extends Document {
  participant_id: string;
  manipulation_check_read: string;
  manipulation_check_strategies: string[];
  strategy_usage_degree?: number;
  open_method: string;
  self_performance: number;
  post_self_efficacy: number;
  attention_check_answer: number;
  attention_check_passed: boolean;
  submitted_at: Date;
}

const PostSurveySchema = new Schema<IPostSurvey>({
  participant_id: { type: String, required: true, unique: true, index: true },
  manipulation_check_read: { type: String, required: true },
  manipulation_check_strategies: { type: [String], default: [] },
  strategy_usage_degree: Number,
  open_method: { type: String, default: '' },
  self_performance: { type: Number, required: true, min: 1, max: 5 },
  post_self_efficacy: { type: Number, required: true, min: 1, max: 5 },
  attention_check_answer: { type: Number, required: true },
  attention_check_passed: { type: Boolean, required: true },
  submitted_at: { type: Date, default: Date.now },
});

export default mongoose.models.PostSurvey ||
  mongoose.model<IPostSurvey>('PostSurvey', PostSurveySchema);
