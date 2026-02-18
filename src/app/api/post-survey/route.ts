import { NextRequest, NextResponse } from 'next/server';
import { connectToDatabase } from '@/lib/mongodb';
import PostSurvey from '@/lib/models/PostSurvey';

export async function POST(request: NextRequest) {
  try {
    await connectToDatabase();
    const body = await request.json();

    const {
      participant_id,
      manipulation_check_read,
      manipulation_check_strategies,
      strategy_usage_degree,
      open_method,
      self_performance,
      post_self_efficacy,
      attention_check_answer,
    } = body;

    const attention_check_passed = attention_check_answer === 5;

    const postSurvey = await PostSurvey.create({
      participant_id,
      manipulation_check_read,
      manipulation_check_strategies: manipulation_check_strategies || [],
      strategy_usage_degree,
      open_method,
      self_performance,
      post_self_efficacy,
      attention_check_answer,
      attention_check_passed,
    });

    return NextResponse.json({
      success: true,
      attention_check_passed: postSurvey.attention_check_passed,
    });
  } catch (error) {
    console.error('Error saving post-survey:', error);
    return NextResponse.json(
      { error: 'Failed to save post-survey' },
      { status: 500 }
    );
  }
}
