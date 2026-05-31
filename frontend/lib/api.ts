/**
 * PodForge API client
 *
 * In development, requests go through Next.js rewrites proxy (/api/* → backend).
 * Set NEXT_PUBLIC_API_URL to bypass the proxy and hit the backend directly.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

export interface LineResult {
  character: string;
  text: string;
  emotion: string | null;
  voice_description: string;
  audio_index: number;
}

export interface ParseResponse {
  title: string;
  characters: string[];
  lines: LineResult[];
  total_duration_seconds: number;
}

export interface PresetInfo {
  key: string;
  name: string;
  description: string;
  category: string;
}

export interface EmotionInfo {
  en: string;
  zh: string;
  emoji: string;
}

export interface HealthResponse {
  status: string;
  tts_server: boolean;
  tts_base_url: string;
}

export interface TTSConfig {
  base_url: string;
  timeout_seconds: number;
}

export async function checkHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function getPresets(): Promise<PresetInfo[]> {
  const res = await fetch(`${API_BASE}/presets`);
  return res.json();
}

export async function getEmotions(): Promise<EmotionInfo[]> {
  const res = await fetch(`${API_BASE}/emotions`);
  return res.json();
}

export async function getTTSConfig(): Promise<TTSConfig> {
  const res = await fetch(`${API_BASE}/tts-config`);
  if (!res.ok) throw new Error(`TTS config fetch failed: ${res.statusText}`);
  return res.json();
}

export async function updateTTSConfig(config: TTSConfig): Promise<TTSConfig> {
  const res = await fetch(`${API_BASE}/tts-config`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
  if (!res.ok) throw new Error(`TTS config update failed: ${res.statusText}`);
  return res.json();
}

export async function parseScript(
  script: string,
  voice_overrides?: Record<string, string>
): Promise<ParseResponse> {
  const res = await fetch(`${API_BASE}/parse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ script, voice_overrides }),
  });
  if (!res.ok) throw new Error(`Parse failed: ${res.statusText}`);
  return res.json();
}

export async function generateAudio(
  script: string,
  voice_overrides?: Record<string, string>,
  cfg_value = 2.0,
  inference_timesteps = 10
): Promise<Blob> {
  const res = await fetch(`${API_BASE}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ script, voice_overrides, cfg_value, inference_timesteps }),
  });
  if (!res.ok) throw new Error(`Generate failed: ${res.statusText}`);
  return res.blob();
}

export function getWsUrl(): string {
  // WebSocket can't go through Next.js rewrites, connect directly to backend
  const wsBase =
    process.env.NEXT_PUBLIC_WS_URL ||
    process.env.NEXT_PUBLIC_API_URL?.replace(/^http/, "ws") ||
    "ws://localhost:8080";
  return `${wsBase}/generate-stream`;
}
