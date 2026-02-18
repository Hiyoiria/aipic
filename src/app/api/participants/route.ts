import { NextRequest, NextResponse } from 'next/server';
import { v4 as uuidv4 } from 'uuid';
import { connectToDatabase } from '@/lib/mongodb';
import Participant from '@/lib/models/Participant';
import { getNextGroupAssignment } from '@/lib/randomization';

export async function POST(request: NextRequest) {
  try {
    await connectToDatabase();

    const body = await request.json();
    const prolificId = body.prolific_id || undefined;

    // Block randomization: get group counts and assign next group
    const counts = await Participant.aggregate([
      { $group: { _id: '$group', count: { $sum: 1 } } },
    ]);

    const currentCounts = { A: 0, C: 0 };
    for (const c of counts) {
      const id = c._id as string;
      if (id === 'A' || id === 'C') {
        currentCounts[id] = c.count;
      }
    }

    const group = getNextGroupAssignment(currentCounts);
    const participantId = uuidv4();
    const imageSeed = participantId;

    const participant = await Participant.create({
      participant_id: participantId,
      prolific_id: prolificId,
      group,
      image_seed: imageSeed,
      consent_given: true,
      consent_timestamp: new Date(),
      current_phase: 1,
    });

    return NextResponse.json({
      participant_id: participant.participant_id,
      group: participant.group,
      image_seed: participant.image_seed,
    });
  } catch (error) {
    console.error('Error creating participant:', error);
    const message = error instanceof Error ? error.message : String(error);
    return NextResponse.json(
      { error: 'Failed to create participant', detail: message },
      { status: 500 }
    );
  }
}
