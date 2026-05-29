/**
 * WebSocket manager for PodForge streaming generation
 */

import { getWsUrl } from "./api";

export interface ProgressMessage {
  type: "progress";
  line_index: number;
  character: string;
  text: string;
  status: string;
  elapsed_seconds: number;
  eta_seconds: number;
}

export interface CompleteMessage {
  type: "complete";
  audio_base64: string;
  duration: number;
  sample_rate: number;
  total_lines: number;
}

export interface ErrorMessage {
  type: "error";
  message: string;
}

export type StreamMessage = ProgressMessage | CompleteMessage | ErrorMessage;

interface GenerateStreamOptions {
  script: string;
  voice_overrides?: Record<string, string>;
  cfg_value?: number;
  inference_timesteps?: number;
  onProgress?: (msg: ProgressMessage) => void;
  onComplete?: (msg: CompleteMessage) => void;
  onError?: (msg: ErrorMessage) => void;
  onClose?: () => void;
}

export function generateStream(opts: GenerateStreamOptions): WebSocket {
  const ws = new WebSocket(getWsUrl());

  ws.onopen = () => {
    ws.send(
      JSON.stringify({
        script: opts.script,
        voice_overrides: opts.voice_overrides || {},
        cfg_value: opts.cfg_value || 2.0,
        inference_timesteps: opts.inference_timesteps || 10,
      })
    );
  };

  ws.onmessage = (event) => {
    const msg: StreamMessage = JSON.parse(event.data);
    switch (msg.type) {
      case "progress":
        opts.onProgress?.(msg as ProgressMessage);
        break;
      case "complete":
        opts.onComplete?.(msg as CompleteMessage);
        break;
      case "error":
        opts.onError?.(msg as ErrorMessage);
        break;
    }
  };

  ws.onerror = () => {
    opts.onError?.({ type: "error", message: "WebSocket connection error" });
  };

  ws.onclose = () => {
    opts.onClose?.();
  };

  return ws;
}
