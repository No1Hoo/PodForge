"use client";

import { useRef } from "react";

interface Props {
  value: string;
  onChange: (value: string) => void;
  characterCount: number;
  lineCount: number;
}

export default function ScriptEditor({
  value,
  onChange,
  characterCount,
  lineCount,
}: Props) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  return (
    <div className="flex flex-col h-full">
      {/* Editor */}
      <div className="flex-1 relative">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full h-full resize-none bg-zinc-900 text-zinc-100 font-mono text-sm p-4 rounded-lg border border-zinc-700 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500/30"
          placeholder={`# 在这里输入剧本...\n# 格式: 角色名: 台词内容\n# 情感: 角色名: (情感) 台词内容\n\n旁白: 欢迎来到今天的节目。\n小明: (开心) 大家好！`}
          spellCheck={false}
        />
      </div>

      {/* Status bar */}
      <div className="flex items-center gap-4 mt-2 px-1 text-xs text-zinc-500">
        <span>
          角色: <span className="text-amber-400 font-medium">{characterCount}</span>
        </span>
        <span>
          台词: <span className="text-amber-400 font-medium">{lineCount}</span>
        </span>
        <span>
          字数: <span className="text-amber-400 font-medium">{value.length}</span>
        </span>
      </div>
    </div>
  );
}
