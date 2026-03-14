import { promises as fs } from 'fs';
import path from 'path';

const CONFIG_PATH = path.join(process.cwd(), '..', '..','livekit-voice-agent','agent_config.json');

export async function readAgentConfig() {
  const file = await fs.readFile(CONFIG_PATH, 'utf-8');
  return JSON.parse(file);
}

export async function writeAgentConfig(config: unknown) {
  await fs.writeFile(CONFIG_PATH, JSON.stringify(config, null, 2), 'utf-8');
}