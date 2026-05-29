"use client";

interface Props {
  current: number;
  total: number;
  character: string;
  text: string;
  etaSeconds: number;
  elapsedSeconds: number;
}

export default function ProgressTracker({
  current,
  total,
  character,
  text,
  etaSeconds,
  elapsedSeconds,
}: Props) {
  const pct = total > 0 ? Math.round((current / total) * 100) : 0;

  return (
    <div className="bg-zinc-800/50 rounded-lg p-4 border border-zinc-700/50">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-zinc-300">
          生成中... {current}/{total}
        </span>
        <span className="text-xs text-zinc-500">
          {elapsedSeconds.toFixed(0)}s 已用 · ~{etaSeconds.toFixed(0)}s 剩余
        </span>
      </div>

      {/* Progress bar */}
      <div className="w-full h-2 bg-zinc-700 rounded-full overflow-hidden mb-3">
        <div
          className="h-full bg-gradient-to-r from-amber-500 to-amber-400 rounded-full transition-all duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>

      {/* Current line */}
      <div className="flex items-center gap-2 text-xs">
        <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
        <span className="text-amber-400 font-medium">{character}</span>
        <span className="text-zinc-400 truncate">{text}</span>
      </div>
    </div>
  );
}
