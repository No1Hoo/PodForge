"use client";

import { PresetInfo, LineResult } from "@/lib/api";

interface Props {
  presets: PresetInfo[];
  lines: LineResult[];
  voiceOverrides: Record<string, string>;
  onOverride: (character: string, description: string) => void;
}

export default function VoicePanel({
  presets,
  lines,
  voiceOverrides,
  onOverride,
}: Props) {
  // Get unique characters from parsed lines
  const characters = Array.from(new Set(lines.map((l) => l.character)));

  if (characters.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-zinc-500 text-sm">
        <p>输入剧本后自动识别角色</p>
      </div>
    );
  }

  // Group presets by category
  const grouped = presets.reduce<Record<string, PresetInfo[]>>((acc, p) => {
    (acc[p.category] ??= []).push(p);
    return acc;
  }, {});

  const categoryLabels: Record<string, string> = {
    female: "女声",
    male: "男声",
    special: "特殊",
    other: "其他",
  };

  return (
    <div className="flex flex-col h-full overflow-auto">
      {/* Character voice assignments */}
      <div className="space-y-3 mb-4">
        <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
          角色声线
        </h3>
        {characters.map((char) => {
          const line = lines.find((l) => l.character === char);
          const currentDesc =
            voiceOverrides[char] || line?.voice_description || "";

          return (
            <div
              key={char}
              className="bg-zinc-800/50 rounded-lg p-3 border border-zinc-700/50"
            >
              <div className="flex items-center gap-2 mb-1.5">
                <span className="w-2 h-2 rounded-full bg-amber-400" />
                <span className="text-sm font-medium text-zinc-200">
                  {char}
                </span>
              </div>
              <input
                type="text"
                value={currentDesc}
                onChange={(e) => onOverride(char, e.target.value)}
                className="w-full text-xs bg-zinc-900 text-zinc-300 rounded px-2 py-1.5 border border-zinc-700 focus:border-amber-500 focus:outline-none"
                placeholder="输入声线描述..."
              />
              {/* Quick preset buttons */}
              <div className="flex flex-wrap gap-1 mt-2">
                {presets.slice(0, 4).map((p) => (
                  <button
                    key={p.key}
                    onClick={() => onOverride(char, p.description)}
                    className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-700/50 text-zinc-400 hover:bg-amber-500/20 hover:text-amber-300 transition-colors"
                  >
                    {p.key}
                  </button>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Preset library */}
      <div>
        <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">
          声线库
        </h3>
        {Object.entries(grouped).map(([cat, items]) => (
          <div key={cat} className="mb-3">
            <p className="text-[10px] text-zinc-500 mb-1">
              {categoryLabels[cat] || cat}
            </p>
            <div className="grid grid-cols-2 gap-1.5">
              {items.map((p) => (
                <button
                  key={p.key}
                  onClick={() => {
                    // Apply to the first character without an override
                    const target =
                      characters.find((c) => !voiceOverrides[c]) ||
                      characters[0];
                    if (target) onOverride(target, p.description);
                  }}
                  className="text-left text-[11px] p-2 rounded bg-zinc-800/30 border border-zinc-700/30 hover:border-amber-500/40 hover:bg-amber-500/10 transition-colors group"
                >
                  <span className="text-zinc-300 group-hover:text-amber-300">
                    {p.key}
                  </span>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
