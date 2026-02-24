import mongoose, { Schema, Document } from 'mongoose';

export interface IResponse extends Document {
  participant_id: string;
  image_id: string;
  image_order: number;
  judgment: 'AI' | 'Real';
  correct_answer: 'AI' | 'Real';
  is_correct: boolean;
  confidence?: number;
  reasoning?: string;
  response_time_ms: number;
  submitted_at: Date;
}

const ResponseSchema = new Schema<IResponse>({
  participant_id: { type: String, required: true, index: true },
  image_id: { type: String, required: true },
  image_order: { type: Number, required: true },
  judgment: { type: String, enum: ['AI', 'Real'], required: true },
  correct_answer: { type: String, enum: ['AI', 'Real'], required: true },
  is_correct: { type: Boolean, required: true },
  confidence: { type: Number, min: 0, max: 5, default: 0 },
  reasoning: { type: String, default: '' },
  response_time_ms: { type: Number, required: true },
  submitted_at: { type: Date, default: Date.now },
});

ResponseSchema.index({ participant_id: 1, image_id: 1 }, { unique: true });

export default mongoose.models.Response ||
  mongoose.model<IResponse>('Response', ResponseSchema);
