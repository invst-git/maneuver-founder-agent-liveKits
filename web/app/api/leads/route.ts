import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

type LeadRecord = {
  event: string;
  lead: Record<string, unknown>;
};

function getLeadsFilePath() {
  const configuredPath = process.env.LEADS_FILE;

  if (configuredPath) {
    return path.isAbsolute(configuredPath)
      ? configuredPath
      : path.join(process.cwd(), configuredPath);
  }

  return path.join(process.cwd(), '..', 'data', 'leads.jsonl');
}

function ensureFile(filePath: string) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });

  if (!fs.existsSync(filePath)) {
    fs.writeFileSync(filePath, '', 'utf8');
  }
}

function readJsonLines(filePath: string): LeadRecord[] {
  ensureFile(filePath);

  const content = fs.readFileSync(filePath, 'utf8').trim();

  if (!content) {
    return [];
  }

  return content
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => JSON.parse(line) as LeadRecord);
}

export async function GET() {
  try {
    const filePath = getLeadsFilePath();
    const records = readJsonLines(filePath);

    return NextResponse.json({
      count: records.length,
      records,
    });
  } catch (error) {
    return NextResponse.json(
      {
        error: 'Failed to read leads.',
        details: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 },
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const requiredKey = process.env.LEADS_API_KEY;

    if (requiredKey) {
      const providedKey = request.headers.get('x-leads-api-key');

      if (providedKey !== requiredKey) {
        return NextResponse.json(
          { error: 'Unauthorized.' },
          { status: 401 },
        );
      }
    }

    const body = await request.json();
    const filePath = getLeadsFilePath();

    ensureFile(filePath);

    const record = {
      event: 'manual_post_to_leads_endpoint',
      lead: body,
    };

    fs.appendFileSync(filePath, JSON.stringify(record) + '\n', 'utf8');

    return NextResponse.json({
      saved: true,
      record,
    });
  } catch (error) {
    return NextResponse.json(
      {
        error: 'Failed to save lead.',
        details: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 },
    );
  }
}