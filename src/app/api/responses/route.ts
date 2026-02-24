import { NextRequest, NextResponse } from 'next/server';
import { connectToDatabase } from '@/lib/mongodb';
import Response from '@/lib/models/Response';
import { IMAGE_DATA } from '@/lib/imageData';

export async function POST(request: NextRequest) {
  try {
    await connectToDatabase();
    const body = await request.json();

    const {
      participant_id,
      image_id,
      image_order,
      judgment,
      confidence,
      strategy_type,
      reasoning,
      response_time_ms,
    } = body;

    // Look up the correct answer
    const imageMeta = IMAGE_DATA.find((img) => img.id === image_id);
    if (!imageMeta) {
      return NextResponse.json(
        { error: 'Invalid image_id' },
        { status: 400 }
      );
    }

    const correct_answer = imageMeta.correct_answer;
    const is_correct = judgment === correct_answer;

    const response = await Response.create({
      participant_id,
      image_id,
      image_order,
      judgment,
      correct_answer,
      is_correct,
      confidence,
      strategy_type: strategy_type || '',
      reasoning: reasoning || '',
      response_time_ms,
    });

    return NextResponse.json({
      success: true,
      is_correct: response.is_correct,
    });
  } catch (error) {
    console.error('Error saving response:', error);
    return NextResponse.json(
      { error: 'Failed to save response' },
      { status: 500 }
    );
  }
}
