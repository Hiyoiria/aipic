import { NextRequest, NextResponse } from 'next/server';
import { connectToDatabase } from '@/lib/mongodb';
import InteractionLog from '@/lib/models/InteractionLog';

export async function POST(request: NextRequest) {
  try {
    await connectToDatabase();
    const body = await request.json();

    const { participant_id, image_id, image_order, action, metadata, client_timestamp } = body;

    if (!participant_id || !image_id || !action) {
      return NextResponse.json(
        { error: 'Missing required fields: participant_id, image_id, action' },
        { status: 400 }
      );
    }

    const validActions = ['TRIGGER_MENU', 'OPEN_LENS', 'SCROLL_LENS', 'CLICK_RESULT'];
    if (!validActions.includes(action)) {
      return NextResponse.json(
        { error: 'Invalid action type' },
        { status: 400 }
      );
    }

    await InteractionLog.create({
      participant_id,
      image_id,
      image_order: image_order || 0,
      action,
      metadata: metadata || {},
      client_timestamp: client_timestamp || Date.now(),
    });

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error saving interaction log:', error);
    return NextResponse.json(
      { error: 'Failed to save interaction log' },
      { status: 500 }
    );
  }
}
