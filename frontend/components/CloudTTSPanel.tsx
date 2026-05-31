"use client";

import { useState } from "react";
import { TTSConfig } from "@/lib/api";

interface Props {
  config: TTSConfig | null;
  applying: boolean;
  onApply: (baseUrl: string, timeoutSeconds: number) => Promise<void>;
  onRefresh: () => Promise<void>;
}

const DEFAULT_TIMEOUT = 600;

function loadSavedUrl(key: string): string {
  if (typeof window === "undefined") return "";
  return window.localStorage.getItem(key) || "";
}

export default function CloudTTSPanel({
  config,
  applying,
  onApply,
  onRefresh,
}: Props) {
  const [kaggleUrl, setKaggleUrl] = useState(() => loadSavedUrl("podforge:kaggleTtsUrl"));
  const [colabUrl, setColabUrl] = useState(() => loadSavedUrl("podforge:colabTtsUrl"));
  const [customUrl, setCustomUrl] = useState(config?.base_url || "");
  const [message, setMessage] = useState("");

  const timeoutSeconds = config?.timeout_seconds || DEFAULT_TIMEOUT;

  async function applyUrl(baseUrl: string) {
    const trimmed = baseUrl.trim();
    if (!trimmed) {
      setMessage("请输入 TTS URL");
      return;
    }
    setMessage("切换中...");
    try {
      await onApply(trimmed, timeoutSeconds);
      setCustomUrl(trimmed);
      setMessage("已切换");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "切换失败");
    }
  }

  return (
    <section className="border-b border-zinc-800 bg-zinc-900/80 px-6 py-3">
      <div className="grid gap-3 lg:grid-cols-[1fr_1fr_1fr_auto]">
        <label className="min-w-0">
          <span className="mb-1 block text-xs text-zinc-500">Kaggle URL</span>
          <input
            value={kaggleUrl}
            onChange={(e) => {
              setKaggleUrl(e.target.value);
              window.localStorage.setItem("podforge:kaggleTtsUrl", e.target.value);
            }}
            placeholder="https://...ngrok-free.dev"
            className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-xs text-zinc-200 outline-none focus:border-amber-500"
          />
        </label>

        <label className="min-w-0">
          <span className="mb-1 block text-xs text-zinc-500">Colab URL</span>
          <input
            value={colabUrl}
            onChange={(e) => {
              setColabUrl(e.target.value);
              window.localStorage.setItem("podforge:colabTtsUrl", e.target.value);
            }}
            placeholder="https://...ngrok-free.dev"
            className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-xs text-zinc-200 outline-none focus:border-amber-500"
          />
        </label>

        <label className="min-w-0">
          <span className="mb-1 block text-xs text-zinc-500">当前 URL</span>
          <input
            value={customUrl || config?.base_url || ""}
            onChange={(e) => setCustomUrl(e.target.value)}
            placeholder={config?.base_url || "http://localhost:8809"}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-xs text-zinc-200 outline-none focus:border-amber-500"
          />
        </label>

        <div className="flex flex-wrap items-end gap-2">
          <button
            onClick={() => applyUrl(kaggleUrl)}
            disabled={applying}
            className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-xs text-zinc-200 hover:bg-zinc-700 disabled:opacity-40"
          >
            用 Kaggle
          </button>
          <button
            onClick={() => applyUrl(colabUrl)}
            disabled={applying}
            className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-xs text-zinc-200 hover:bg-zinc-700 disabled:opacity-40"
          >
            用 Colab
          </button>
          <button
            onClick={() => applyUrl(customUrl || config?.base_url || "")}
            disabled={applying}
            className="rounded-lg bg-amber-500 px-3 py-2 text-xs font-medium text-zinc-950 hover:bg-amber-400 disabled:opacity-40"
          >
            应用
          </button>
          <button
            onClick={onRefresh}
            disabled={applying}
            className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-xs text-zinc-200 hover:bg-zinc-700 disabled:opacity-40"
          >
            检查
          </button>
        </div>
      </div>
      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-zinc-500">
        <span>Backend: {config?.base_url || "未加载"}</span>
        <span>Timeout: {timeoutSeconds}s</span>
        {message && <span className="text-amber-400">{message}</span>}
      </div>
    </section>
  );
}
