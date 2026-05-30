"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import {
  checkHealth,
  getPresets,
  getEmotions,
  parseScript,
  PresetInfo,
  EmotionInfo,
  LineResult,
} from "@/lib/api";
import { generateStream, CompleteMessage } from "@/lib/ws";
import ScriptEditor from "@/components/ScriptEditor";
import EmotionPicker from "@/components/EmotionPicker";
import VoicePanel from "@/components/VoicePanel";
import AudioPlayer from "@/components/AudioPlayer";
import ProgressTracker from "@/components/ProgressTracker";

const DEMO_SCRIPT = `# PodForge 示例剧本 — 播客对话
旁白: 欢迎来到今天的播客节目。今天我们请到了两位嘉宾。
小明: 大家好！我是小明，今天很高兴来到这里。
小红: (开心) 大家好呀！我是小红，期待今天的讨论。
旁白: 那我们直接开始吧。小明，你最近在忙什么？
小明: (思考) 最近在研究AI语音合成，真的太有意思了。
小红: (惊讶) 真的吗？那你给我们讲讲呗！
小明: 好的。现在的AI已经可以做到非常自然的语音合成了。
小红: (感叹) 这也太厉害了吧！
旁白: 感谢两位的分享。今天的节目就到这里，下期再见！`;

export default function Home() {
  const [script, setScript] = useState("");
  const [ttsStatus, setTtsStatus] = useState<"connected" | "disconnected" | "checking">("checking");
  const [presets, setPresets] = useState<PresetInfo[]>([]);
  const [emotions, setEmotions] = useState<EmotionInfo[]>([]);
  const [parsedLines, setParsedLines] = useState<LineResult[]>([]);
  const [characters, setCharacters] = useState<string[]>([]);
  const [voiceOverrides, setVoiceOverrides] = useState<Record<string, string>>({});
  const [generating, setGenerating] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0, character: "", text: "", eta: 0, elapsed: 0 });
  const [audio, setAudio] = useState<CompleteMessage | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Init
  useEffect(() => {
    checkHealth()
      .then((h) => setTtsStatus(h.tts_server ? "connected" : "disconnected"))
      .catch(() => setTtsStatus("disconnected"));
    getPresets().then(setPresets).catch(console.error);
    getEmotions().then(setEmotions).catch(console.error);
  }, []);

  // Derived state from script (handles empty case)
  const { lines, chars } = useMemo(() => {
    if (!script.trim()) return { lines: [], chars: [] };
    // This is a synchronous derivation, parseScript result is used reactively
    // When script is empty, lines and chars are empty
    return { lines: parsedLines, chars: characters };
  }, [script, parsedLines, characters]);

  // Parse script (debounced) - only runs parse when script is non-empty
  useEffect(() => {
    if (!script.trim()) return;  // Empty script means empty derived state via useMemo

    const timer = setTimeout(() => {
      parseScript(script, voiceOverrides)
        .then((res) => {
          setParsedLines(res.lines);
          setCharacters(res.characters);
        })
        .catch(console.error);
    }, 500);
    return () => clearTimeout(timer);
  }, [script, voiceOverrides]);

  const insertEmotion = useCallback(
    (tag: string) => {
      const el = document.querySelector("textarea") as HTMLTextAreaElement | null;
      if (!el) return;
      const start = el.selectionStart;
      const end = el.selectionEnd;
      const newValue = script.slice(0, start) + tag + script.slice(end);
      setScript(newValue);
      requestAnimationFrame(() => {
        el.selectionStart = el.selectionEnd = start + tag.length;
        el.focus();
      });
    },
    [script]
  );

  const handleGenerate = useCallback(() => {
    if (!script.trim() || generating) return;
    setGenerating(true);
    setAudio(null);
    setError(null);
    setProgress({ current: 0, total: 0, character: "", text: "", eta: 0, elapsed: 0 });

    generateStream({
      script,
      voice_overrides: voiceOverrides,
      onProgress: (msg) => {
        setProgress({
          current: msg.line_index + 1,
          total: parsedLines.length,
          character: msg.character,
          text: msg.text,
          eta: msg.eta_seconds,
          elapsed: msg.elapsed_seconds,
        });
      },
      onComplete: (msg) => {
        setAudio(msg);
        setGenerating(false);
      },
      onError: (msg) => {
        setError(msg.message);
        setGenerating(false);
      },
      onClose: () => setGenerating(false),
    });
  }, [script, voiceOverrides, generating, parsedLines.length]);

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      {/* Header */}
      <header className="border-b border-zinc-800 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-bold tracking-tight">
            <span className="text-amber-400">Pod</span>Forge
          </h1>
          <span className="text-xs text-zinc-500">Script in, Podcast out</span>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span
            className={`w-2 h-2 rounded-full ${
              ttsStatus === "connected"
                ? "bg-green-400"
                : ttsStatus === "checking"
                  ? "bg-yellow-400 animate-pulse"
                  : "bg-red-400"
            }`}
          />
          <span className="text-zinc-400">
            TTS: {ttsStatus === "connected" ? "已连接" : ttsStatus === "checking" ? "检查中..." : "未连接"}
          </span>
        </div>
      </header>

      {/* Main */}
      <main className="flex flex-col lg:flex-row gap-4 p-4 h-[calc(100vh-57px)]">
        {/* Left: Editor */}
        <div className="flex-1 flex flex-col min-w-0 lg:w-3/5">
          <div className="mb-3">
            <EmotionPicker emotions={emotions} onInsert={insertEmotion} />
          </div>
          <div className="flex-1 min-h-0">
            <ScriptEditor
              value={script}
              onChange={setScript}
              characterCount={chars.length}
              lineCount={lines.length}
            />
          </div>
          <div className="flex items-center gap-3 mt-3">
            <button
              onClick={() => setScript(DEMO_SCRIPT)}
              className="px-4 py-2 text-sm rounded-lg bg-zinc-800 text-zinc-300 hover:bg-zinc-700 transition-colors border border-zinc-700"
            >
              加载示例
            </button>
            <button
              onClick={() => {
                setScript("");  // useMemo will derive empty lines/chars
                setVoiceOverrides({});
                setAudio(null);
                setError(null);
              }}
              className="px-4 py-2 text-sm rounded-lg bg-zinc-800 text-zinc-300 hover:bg-zinc-700 transition-colors border border-zinc-700"
            >
              清空
            </button>
            <div className="flex-1" />
            <button
              onClick={handleGenerate}
              disabled={!script.trim() || generating || ttsStatus !== "connected"}
              className="px-6 py-2.5 text-sm font-medium rounded-lg bg-amber-500 text-zinc-900 hover:bg-amber-400 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {generating ? "生成中..." : "生成播客 ▶"}
            </button>
          </div>
        </div>

        {/* Right: Voice + Player */}
        <div className="flex flex-col lg:w-2/5 min-w-0">
          <div className="flex-1 min-h-0 overflow-auto mb-4">
            <VoicePanel
              presets={presets}
              lines={parsedLines}
              voiceOverrides={voiceOverrides}
              onOverride={(char, desc) =>
                setVoiceOverrides((prev) => ({ ...prev, [char]: desc }))
              }
            />
          </div>
          <div className="shrink-0">
            {error && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-sm text-red-400 mb-3">
                {error}
              </div>
            )}
            {generating ? (
              <ProgressTracker
                current={progress.current}
                total={progress.total}
                character={progress.character}
                text={progress.text}
                etaSeconds={progress.eta}
                elapsedSeconds={progress.elapsed}
              />
            ) : audio ? (
              <AudioPlayer
                audioBase64={audio.audio_base64}
                duration={audio.duration}
                sampleRate={audio.sample_rate}
                lineCount={audio.total_lines}
              />
            ) : null}
          </div>
        </div>
      </main>
    </div>
  );
}
