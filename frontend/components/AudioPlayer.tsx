"use client";

import { useRef, useEffect, useState, useCallback } from "react";

interface Props {
  audioBase64: string | null;
  duration: number;
  sampleRate: number;
  lineCount: number;
}

export default function AudioPlayer({
  audioBase64,
  duration,
  sampleRate,
  lineCount,
}: Props) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  // Create blob URL from base64
  useEffect(() => {
    if (!audioBase64) {
      return;
    }
    const binary = atob(audioBase64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
    const blob = new Blob([bytes], { type: "audio/wav" });
    const url = URL.createObjectURL(blob);
    setAudioUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [audioBase64]);

  const togglePlay = useCallback(() => {
    const el = audioRef.current;
    if (!el) return;
    if (playing) {
      el.pause();
    } else {
      el.play();
    }
  }, [playing]);

  const handleDownload = useCallback(() => {
    if (!audioUrl) return;
    const a = document.createElement("a");
    a.href = audioUrl;
    a.download = "podforge_output.wav";
    a.click();
  }, [audioUrl]);

  if (!audioBase64) {
    return (
      <div className="h-full flex items-center justify-center text-zinc-500 text-sm">
        <p>生成完成后在这里播放</p>
      </div>
    );
  }

  return (
    <div className="bg-zinc-800/50 rounded-lg p-4 border border-zinc-700/50">
      <audio
        ref={audioRef}
        src={audioUrl || undefined}
        onPlay={() => setPlaying(true)}
        onPause={() => setPlaying(false)}
        onTimeUpdate={() => setCurrentTime(audioRef.current?.currentTime || 0)}
        onEnded={() => setPlaying(false)}
      />

      {/* Info */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <p className="text-sm text-zinc-200 font-medium">生成完成！</p>
          <p className="text-xs text-zinc-500">
            {duration}s · {lineCount} 句 · {sampleRate / 1000}kHz
          </p>
        </div>
        <button
          onClick={handleDownload}
          className="px-3 py-1.5 text-xs rounded-lg bg-zinc-700 text-zinc-300 hover:bg-zinc-600 transition-colors"
        >
          下载 WAV
        </button>
      </div>

      {/* Progress bar */}
      <div className="relative h-8 bg-zinc-900 rounded mb-2 overflow-hidden">
        <div
          className="absolute inset-y-0 left-0 bg-amber-500/20"
          style={{
            width: `${duration > 0 ? (currentTime / duration) * 100 : 0}%`,
          }}
        />
        <input
          type="range"
          min={0}
          max={duration}
          step={0.1}
          value={currentTime}
          onChange={(e) => {
            const t = parseFloat(e.target.value);
            if (audioRef.current) audioRef.current.currentTime = t;
            setCurrentTime(t);
          }}
          className="absolute inset-0 w-full opacity-0 cursor-pointer"
        />
        <div className="absolute inset-0 flex items-center px-3">
          <span className="text-[10px] text-zinc-500 font-mono">
            {currentTime.toFixed(1)}s / {duration}s
          </span>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-center gap-4">
        <button
          onClick={togglePlay}
          className="w-12 h-12 rounded-full bg-amber-500 hover:bg-amber-400 text-zinc-900 flex items-center justify-center transition-colors"
        >
          {playing ? (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <rect x="6" y="4" width="4" height="16" />
              <rect x="14" y="4" width="4" height="16" />
            </svg>
          ) : (
            <svg className="w-5 h-5 ml-0.5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z" />
            </svg>
          )}
        </button>
      </div>
    </div>
  );
}
