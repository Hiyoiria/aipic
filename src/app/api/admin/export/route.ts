import { NextRequest, NextResponse } from 'next/server';
import { connectToDatabase } from '@/lib/mongodb';
import Participant from '@/lib/models/Participant';
import Response from '@/lib/models/Response';
import PostSurvey from '@/lib/models/PostSurvey';
import InteractionLog from '@/lib/models/InteractionLog';

function toCsv(data: Record<string, unknown>[]): string {
  if (data.length === 0) return '';
  const headers = Object.keys(data[0]);
  const rows = data.map((row) =>
    headers
      .map((h) => {
        const val = row[h];
        const str = val === null || val === undefined ? '' : String(val);
        return str.includes(',') || str.includes('"') || str.includes('\n')
          ? `"${str.replace(/"/g, '""')}"`
          : str;
      })
      .join(',')
  );
  return [headers.join(','), ...rows].join('\n');
}

export async function GET(request: NextRequest) {
  const secret = request.headers.get('x-admin-secret');
  if (secret !== process.env.ADMIN_SECRET) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const collection = request.nextUrl.searchParams.get('collection');

  try {
    await connectToDatabase();

    let data;
    switch (collection) {
      case 'participants':
        data = await Participant.find().lean();
        break;
      case 'responses':
        data = await Response.find().lean();
        break;
      case 'post-survey':
        data = await PostSurvey.find().lean();
        break;
      case 'interaction-logs':
        data = await InteractionLog.find().lean();
        break;
      default:
        return NextResponse.json(
          { error: 'Invalid collection. Use: participants, responses, post-survey, interaction-logs' },
          { status: 400 }
        );
    }

    const csv = toCsv(data as Record<string, unknown>[]);

    return new NextResponse(csv, {
      headers: {
        'Content-Type': 'text/csv; charset=utf-8',
        'Content-Disposition': `attachment; filename=${collection}_${Date.now()}.csv`,
      },
    });
  } catch (error) {
    console.error('Error exporting data:', error);
    return NextResponse.json(
      { error: 'Failed to export data' },
      { status: 500 }
    );
  }
}
