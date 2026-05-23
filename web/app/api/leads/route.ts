import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

type LeadRecord = {
  lead_id: string;
  [key: string]: unknown;
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

function compactLeadRecord(value: unknown): LeadRecord | null {
  if (!value || typeof value !== 'object') {
    return null;
  }

  const maybeSnapshot = value as Record<string, unknown>;
  const source =
    maybeSnapshot.lead && typeof maybeSnapshot.lead === 'object'
      ? (maybeSnapshot.lead as Record<string, unknown>)
      : maybeSnapshot;

  if (typeof source.lead_id !== 'string' || !source.lead_id) {
    return null;
  }

  const record = { ...source };
  delete record.event;
  delete record.transcript;

  return record as LeadRecord;
}

function readJsonLines(filePath: string): LeadRecord[] {
  ensureFile(filePath);

  const content = fs.readFileSync(filePath, 'utf8').trim();

  if (!content) {
    return [];
  }

  const recordsById = new Map<string, LeadRecord>();

  content
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .forEach((line) => {
      const record = compactLeadRecord(JSON.parse(line));

      if (record) {
        recordsById.set(record.lead_id, record);
      }
    });

  return Array.from(recordsById.values());
}

function upsertLeadRecord(filePath: string, lead: LeadRecord) {
  const recordsById = new Map(readJsonLines(filePath).map((record) => [record.lead_id, record]));
  recordsById.set(lead.lead_id, lead);

  fs.writeFileSync(
    filePath,
    Array.from(recordsById.values())
      .map((record) => JSON.stringify(record))
      .join('\n') + '\n',
    'utf8'
  );
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
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const requiredKey = process.env.LEADS_API_KEY;

    if (requiredKey) {
      const providedKey = request.headers.get('x-leads-api-key');

      if (providedKey !== requiredKey) {
        return NextResponse.json({ error: 'Unauthorized.' }, { status: 401 });
      }
    }

    const body = await request.json();
    const lead = compactLeadRecord(body);

    if (!lead) {
      return NextResponse.json(
        { error: 'Lead record must include a non-empty lead_id.' },
        { status: 400 }
      );
    }

    const filePath = getLeadsFilePath();

    ensureFile(filePath);

    upsertLeadRecord(filePath, lead);

    return NextResponse.json({
      saved: true,
      record: lead,
    });
  } catch (error) {
    return NextResponse.json(
      {
        error: 'Failed to save lead.',
        details: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}
