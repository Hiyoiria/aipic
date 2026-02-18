import mongoose, { Schema, Document } from 'mongoose';

export interface IInteractionLog extends Document {
  participant_id: string;
  image_id: string;
  image_order: number;
  action: 'TRIGGER_MENU' | 'OPEN_LENS' | 'SCROLL_LENS' | 'CLICK_RESULT';
  metadata: Record<string, unknown>;
  client_timestamp: number;
  created_at: Date;
}

const InteractionLogSchema = new Schema<IInteractionLog>({
  participant_id: { type: String, required: true, index: true },
  image_id: { type: String, required: true },
  image_order: { type: Number, required: true },
  action: {
    type: String,
    enum: ['TRIGGER_MENU', 'OPEN_LENS', 'SCROLL_LENS', 'CLICK_RESULT'],
    required: true,
  },
  metadata: { type: Schema.Types.Mixed, default: {} },
  client_timestamp: { type: Number, required: true },
  created_at: { type: Date, default: Date.now },
});

InteractionLogSchema.index({ participant_id: 1, image_id: 1 });

export default mongoose.models.InteractionLog ||
  mongoose.model<IInteractionLog>('InteractionLog', InteractionLogSchema);
