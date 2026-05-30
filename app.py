"""PodForge — Script in, Podcast out

Gradio UI for HuggingFace Space deployment.
Single-file app with UI + TTS all in one.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import gradio as gr
import soundfile as sf

from backend.drama_parser import parse_script
from backend.voice_manager import VoiceManager, EMOTION_TAGS, PRESET_VOICES
from backend.hf_tts import VoxCPMTTS

# ── Example scripts ────────────────────────────────────────────────────────────

DEMO_SCRIPTS: dict[str, str] = {
    "示例播客": Path("examples/demo_drama.txt").read_text(encoding="utf-8"),
    "新闻播报": Path("examples/news_broadcast.txt").read_text(encoding="utf-8"),
    "童话故事": Path("examples/fairy_tale.txt").read_text(encoding="utf-8"),
    "客服对话": Path("examples/customer_service.txt").read_text(encoding="utf-8"),
}

# ── TTS lazy loader ─────────────────────────────────────────────────────────

_tts: VoxCPMTTS | None = None


def get_tts() -> VoxCPMTTS:
    """Load VoxCPM2 model on first call, reuse thereafter."""
    global _tts
    if _tts is None:
        _tts = VoxCPMTTS()
    return _tts


# ── Core generation logic ───────────────────────────────────────────────────

def generate_podcast(script_text: str) -> tuple[str, str]:
    """
    Parse script, synthesize all lines, return audio path + status.

    Returns:
        Tuple of (wav_file_path, status_message)
    """
    if not script_text.strip():
        return "", "请先输入剧本内容"

    try:
        script = parse_script(script_text)
    except Exception as e:
        return "", f"剧本解析错误：{e}"

    if not script.lines:
        return "", "未检测到有效台词行，请确保格式为：角色名: 台词"

    vm = VoiceManager()
    for char in script.characters:
        vm.assign(char)

    tts = get_tts()
    all_samples: list[list[float]] = []

    try:
        for line in script.lines:
            voice_desc = vm.get_description(line.character)
            tagged = f"({line.emotion}){line.text}" if line.emotion else line.text
            audio = tts.synthesize(tagged, voice_description=voice_desc)
            all_samples.append(audio)
    except Exception as e:
        return "", f"生成失败：{e}"

    # Combine all segments
    combined: list[float] = []
    for seg in all_samples:
        combined.extend(seg)

    # Write to temporary WAV file (HF Space has no persistent storage)
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False, mode="wb")
    sf.write(tmp, [combined], tts.sample_rate, format="WAV")
    tmp.close()
    wav_path = tmp.name

    duration = len(combined) / tts.sample_rate
    return wav_path, f"生成完成！{len(script.lines)} 句，共 {duration:.1f} 秒"


# ── Gradio UI ───────────────────────────────────────────────────────────────

PRESET_OPTIONS = list(PRESET_VOICES.keys())

EMOTION_BUTTON_LABELS = [
    "😊 开心",
    "😢 悲伤",
    "😠 愤怒",
    "😲 惊讶",
    "🤫 悄悄话",
    "🤔 思考",
    "🤩 兴奋",
    "🥰 温柔",
    "😐 严肃",
    "😄 幽默",
]

EMOTION_VALUES = [e["en"] for e in EMOTION_TAGS]


def make_load_script_fn(script_key: str):
    """Factory: return a fn that loads the demo script into the textbox."""
    def fn():
        return DEMO_SCRIPTS[script_key]
    return fn


with gr.Blocks(title="PodForge — Script in, Podcast out") as demo:
    gr.Markdown(
        "## 🎙 PodForge — Script in, Podcast out\n\n"
        "输入剧本，选择声线和情感，点击生成按钮即可获得播客音频。"
    )

    # ── Example scripts row ──────────────────────────────────────────────────
    gr.Markdown("### 📋 示例剧本")
    with gr.Row():
        demo_buttons = []
        for key in DEMO_SCRIPTS:
            btn = gr.Button(key, size="sm")
            demo_buttons.append(btn)

    # ── Script editor ────────────────────────────────────────────────────────
    gr.Markdown("### ✏️ 剧本编辑器")
    script_box = gr.Textbox(
        lines=12,
        placeholder=(
            "格式示例：\n"
            "小明: 你好！\n"
            "小红: (happy) 很高兴见到你！\n"
            "\n"
            "支持情感标签：happy, sad, angry, surprised, whisper, thinking, excited, gentle, serious, humorous"
        ),
        label="剧本内容",
    )

    # Wire demo buttons to script box
    for key, btn in zip(DEMO_SCRIPTS, demo_buttons):
        btn.click(fn=make_load_script_fn(key), outputs=[script_box])

    # ── Voice & Emotion selection ───────────────────────────────────────────
    gr.Markdown("### 🎤 声线与情感")

    with gr.Row():
        voice_dropdown = gr.Dropdown(
            choices=PRESET_OPTIONS,
            value=PRESET_OPTIONS[0] if PRESET_OPTIONS else None,
            label="预设声线",
            info="为未匹配到预设的角色选择默认声线",
        )
        emotion_dropdown = gr.Dropdown(
            choices=EMOTION_VALUES,
            value=None,
            label="情感标签",
            info="当前选中情感（可点击下方按钮快速选择）",
        )

    # Emotion buttons in a row
    gr.Markdown("#### 快速情感选择")
    with gr.Row():
        for label, value in zip(EMOTION_BUTTON_LABELS, EMOTION_VALUES):
            btn = gr.Button(label, size="sm", variant="secondary")
            btn.click(
                fn=lambda v=value: gr.update(value=v),
                outputs=[emotion_dropdown],
            )

    # ── Generate button ─────────────────────────────────────────────────────
    generate_btn = gr.Button("🎙 生成播客", variant="primary", size="lg")

    # ── Output section ──────────────────────────────────────────────────────
    status_box = gr.Textbox(
        label="状态",
        lines=1,
        interactive=False,
        placeholder="等待生成...",
    )
    audio_output = gr.Audio(
        label="生成的播客",
        type="filepath",
        interactive=False,
    )

    # ── Generation event ─────────────────────────────────────────────────────
    generate_btn.click(
        fn=generate_podcast,
        inputs=[script_box],
        outputs=[audio_output, status_box],
    )

    # ── Footer ──────────────────────────────────────────────────────────────
    gr.Markdown(
        "\n---\n"
        "Powered by **VoxCPM2** · "
        "Built with **Gradio** · "
        "[GitHub](https://github.com/No1Hoo/PodForge)\n"
    )


if __name__ == "__main__":
    demo.launch()