export type ToolMap = Record<string, boolean>;

export interface VoiceConfig {
  model: string;
  voice: string;
  speed: number;
}

export interface PersonaConfig {
  name: string;
  greeting: string;
  instructions: string;
  voice: VoiceConfig;
  tools: ToolMap;
}

export interface TaskConfig {
  instructions: string;
  greeting: string;
}

export interface AgentConfig {
  assistant: PersonaConfig;
  nurse: PersonaConfig;
  collect_consent: TaskConfig;
}