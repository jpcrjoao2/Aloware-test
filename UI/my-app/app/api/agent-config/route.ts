import { readAgentConfig, writeAgentConfig } from '@/lib/agent-config';
import { NextResponse } from 'next/server';

export async function GET() {
  try {
    const config = await readAgentConfig();
    return NextResponse.json(config, { status: 200 });
  } catch (error) {
    console.error('GET /api/agent-config error:', error);
    return NextResponse.json(
      { error: 'Failed to read agent config' },
      { status: 500 }
    );
  }
}

export async function PUT(req: Request) {
  try {
    const body = await req.json();

    const validation = validateAgentConfig(body);
    if (!validation.valid) {
      return NextResponse.json(
        { error: validation.error },
        { status: 400 }
      );
    }

    await writeAgentConfig(body);

    return NextResponse.json(
      { success: true, config: body },
      { status: 200 }
    );
  } catch (error) {
    console.error('PUT /api/agent-config error:', error);
    return NextResponse.json(
      { error: 'Failed to update agent config' },
      { status: 500 }
    );
  }
}

function validateAgentConfig(data: any): { valid: boolean; error?: string } {
  if (!data || typeof data !== 'object') {
    return { valid: false, error: 'Invalid payload' };
  }

  const requiredTopLevel = [
    'assistant',
    'nurse',
    'collect_consent',
    'session_opening_instruction',
  ];

  for (const key of requiredTopLevel) {
    if (!(key in data)) {
      return { valid: false, error: `Missing top-level field: ${key}` };
    }
  }

  const personas = ['assistant', 'nurse'] as const;

  for (const persona of personas) {
    const value = data[persona];

    if (!value || typeof value !== 'object') {
      return { valid: false, error: `Invalid ${persona} config` };
    }

    const requiredPersonaFields = ['name', 'greeting', 'instructions', 'voice', 'tools'];
    for (const field of requiredPersonaFields) {
      if (!(field in value)) {
        return { valid: false, error: `Missing ${persona}.${field}` };
      }
    }

    if (typeof value.name !== 'string') {
      return { valid: false, error: `${persona}.name must be a string` };
    }

    if (typeof value.greeting !== 'string') {
      return { valid: false, error: `${persona}.greeting must be a string` };
    }

    if (typeof value.instructions !== 'string') {
      return { valid: false, error: `${persona}.instructions must be a string` };
    }

    if (!value.voice || typeof value.voice !== 'object') {
      return { valid: false, error: `${persona}.voice must be an object` };
    }

    if (typeof value.voice.model !== 'string') {
      return { valid: false, error: `${persona}.voice.model must be a string` };
    }

    if (typeof value.voice.voice !== 'string') {
      return { valid: false, error: `${persona}.voice.voice must be a string` };
    }

    if (
      value.voice.speed !== undefined &&
      typeof value.voice.speed !== 'number'
    ) {
      return { valid: false, error: `${persona}.voice.speed must be a number` };
    }

    if (!value.tools || typeof value.tools !== 'object' || Array.isArray(value.tools)) {
      return { valid: false, error: `${persona}.tools must be an object` };
    }

    for (const [toolName, enabled] of Object.entries(value.tools)) {
      if (typeof toolName !== 'string' || typeof enabled !== 'boolean') {
        return {
          valid: false,
          error: `${persona}.tools must be a map of boolean values`,
        };
      }
    }
  }

  if (
    !data.collect_consent ||
    typeof data.collect_consent !== 'object'
  ) {
    return { valid: false, error: 'Invalid collect_consent config' };
  }

  if (typeof data.collect_consent.instructions !== 'string') {
    return {
      valid: false,
      error: 'collect_consent.instructions must be a string',
    };
  }

  if (typeof data.collect_consent.greeting !== 'string') {
    return {
      valid: false,
      error: 'collect_consent.greeting must be a string',
    };
  }

  if (typeof data.session_opening_instruction !== 'string') {
    return {
      valid: false,
      error: 'session_opening_instruction must be a string',
    };
  }

  return { valid: true };
}