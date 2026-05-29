"use client";

import { EmotionInfo } from "@/lib/api";

interface Props {
  emotions: EmotionInfo[];
  onInsert: (tag: string) => void;
}

export default function EmotionPicker({ emotions, onInsert }: Props) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {emotions.map((em) => (
        <button
          key={em.en}
          onClick={() => onInsert(`(${em.zh})`)}
          className="inline-flex items-center gap-1 px-2.5 py-1 text-xs rounded-full bg-zinc-800 text-zinc-300 hover:bg-amber-500/20 hover:text-amber-300 transition-colors border border-zinc-700 hover:border-amber-500/40"
          title={`${em.en} / ${em.zh}`}
        >
          <span>{em.emoji}</span>
          <span>{em.zh}</span>
        </button>
      ))}
    </div>
  );
}
