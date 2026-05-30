# PodForge HuggingFace Space 部署实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 PodForge 部署为 HuggingFace Space，用户访问一个 URL 即可完成剧本 → 播客的全流程

**Architecture:** 单 Space 部署，前端 Gradio UI + Python 逻辑层 + VoxCPM2 TTS（按需加载），全部在 HF 免费 T4 GPU 上运行

**Tech Stack:** Gradio 4+ / FastAPI / VoxCPM2 / soundfile / numpy

---

## 文件结构

```
PodForge/
├── app.py                        ← Gradio 主入口（新建）
├── requirements_hf.txt            ← HF Space 依赖（新建）
├── backend/
│   ├── drama_parser.py          ← 已有，零改动
│   ├── voice_manager.py         ← 已有，零改动
│   └── hf_tts.py               ← TTS 封装，按需加载模型（新建）
├── examples/                      ← 已有 5 个示例剧本
└── docs/superpowers/plans/       ← 本计划
```

---

## 任务清单

### Task 1: 创建 requirements_hf.txt

**Files:**
- Create: `requirements_hf.txt`
- Test: `pip install -r requirements_hf.txt --dry-run` (验证包存在)

- [ ] **Step 1: 创建文件**

```txt
voxcpm>=0.1.0
gradio>=4.0.0
soundfile>=0.12.0
numpy>=1.26.0
```

---

### Task 2: 创建 backend/hf_tts.py（TTS 封装，按需加载模型）

**Files:**
- Create: `backend/hf_tts.py`
- Test: `python -c "from backend.hf_tts import get_model; print('import ok')"`

- [ ] **Step 1: 写单元测试**

```python
# tests/test_hf_tts.py
import pytest
from backend.hf_tts import VoxCPMTTS, get_model


def test_tts_import():
    tts = VoxCPMTTS()
    assert tts.sample_rate == 48000


def test_tts_synthesize_short_text():
    tts = VoxCPMTTS()
    text = "(开心) 你好，世界！"
    wav = tts.synthesize(text, voice_description="A warm friendly male voice")
    assert wav is not None
    assert len(wav) > 0
    assert isinstance(wav, list)


def test_tts_default_voice():
    tts = VoxCPMTTS()
    # 不传 voice_description 时使用默认描述
    wav = tts.synthesize("测试文本")
    assert wav is not None
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd /home/jackie/桌面/claude/PodForge && python -m pytest tests/test_hf_tts.py -v`
Expected: FAIL（module not found）

- [ ] **Step 3: 写实现**

```python
"""VoxCPM2 TTS wrapper for HuggingFace Space deployment.

按需加载模型，第一次 synthesize() 调用时初始化。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy.typing as npt

# Global model instance (lazy-loaded)
_model = None
_sample_rate = 48000


def get_model():
    """Load VoxCPM2 model on first call, reuse thereafter."""
    global _model
    if _model is None:
        from voxcpm import VoxCPM
        _model = VoxCPM.from_pretrained("openbmb/VoxCPM2", load_denoiser=False)
    return _model


def get_sample_rate() -> int:
    """Return the model's native sample rate."""
    return _sample_rate


class VoxCPMTTS:
    """TTS wrapper with lazy model loading."""

    def __init__(
        self,
        cfg_value: float = 2.0,
        inference_timesteps: int = 10,
    ):
        self.cfg_value = cfg_value
        self.inference_timesteps = inference_timesteps
        self._sample_rate = _sample_rate

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    def synthesize(
        self,
        text: str,
        *,
        voice_description: str | None = None,
        emotion: str | None = None,
    ) -> list[float]:
        """
        Generate audio for given text.

        Args:
            text: Text to synthesize (emotion tag embedded like "(happy)Hello")
            voice_description: Optional VoxCPM2 Voice Design description
            emotion: Optional emotion tag override

        Returns:
            WAV audio as float samples list
        """
        model = get_model()

        # Build kwargs
        kwargs: dict = {
            "text": text,
            "cfg_value": self.cfg_value,
            "inference_timesteps": self.inference_timesteps,
        }
        if voice_description:
            kwargs["voice_description"] = voice_description

        wav = model.generate(**kwargs)
        return wav.tolist() if hasattr(wav, "tolist") else list(wav)

    def synthesize_batch(
        self,
        lines: list[tuple[str, str | None, str | None]],
    ) -> list[list[float]]:
        """
        Synthesize multiple lines.

        Args:
            lines: List of (text, voice_description, emotion) tuples

        Returns:
            List of audio samples lists
        """
        results = []
        for text, voice_desc, emotion in lines:
            tagged_text = f"({emotion}){text}" if emotion else text
            audio = self.synthesize(tagged_text, voice_description=voice_desc)
            results.append(audio)
        return results
```

- [ ] **Step 4: 运行测试验证**

Run: `cd /home/jackie/桌面/claude/PodForge && python -m pytest tests/test_hf_tts.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
cd /home/jackie/桌面/claude/PodForge
git add requirements_hf.txt backend/hf_tts.py tests/test_hf_tts.py
git commit -m "$(cat <<'EOF'
feat: add TTS wrapper with lazy model loading for HF Space

- requirements_hf.txt: HF Space minimal dependencies
- backend/hf_tts.py: VoxCPMTTS class with on-demand model init
- tests/test_hf_tts.py: unit tests for TTS wrapper
EOF
)"
```

---

### Task 3: 创建 app.py（Gradio 主界面）

**Files:**
- Create: `app.py`
- Modify: `examples/` (读取示例剧本内容)
- Test: `python app.py` (本地验证界面)

- [ ] **Step 1: 写 app.py**

```python
"""PodForge — HuggingFace Space entry point.

Single-file Gradio app: UI + TTS generation.
No local backend required — everything runs in the Space.
"""

from __future__ import annotations

import io
import base64

import gradio as gr
import soundfile as sf

from backend.drama_parser import parse_script, DialogueLine
from backend.voice_manager import VoiceManager, EMOTION_TAGS, PRESET_VOICES
from backend.hf_tts import VoxCPMTTS

# ── Example scripts ─────────────────────────────────────────────────────

DEMO_SCRIPTS: dict[str, str] = {
    "示例播客": """# 科技播客三人聊
旁白: 欢迎收听今天的科技播客，今天我们来聊聊 AI 语音技术的最新进展。
小明: 大家好，我是小明！今天非常高兴能和两位一起探讨这个话题。
小红: 你好小明！我最近体验了一款很有意思的 AI 工具，叫 PodForge，可以把剧本自动变成播客。
小明: 听起来很棒啊！它是怎么实现的呢？
小红: 它用了一个叫 VoxCPM2 的开源 TTS 模型，支持 30 种语言，还可以设计独特的音色。
旁白: 技术的发展日新月异，AI 正在改变内容创作的方式。
小明: 同意！以前做播客需要专业设备和人声，现在只需要一个剧本就行了。
小红: 没错，而且生成的语音质量很高，达到了 48kHz 的专业水准。
旁白: 感谢两位嘉宾的分享，我们下期再见！
""",
    "新闻播报": """# 新闻播报
主播: 各位观众晚上好，欢迎收看今天的新闻播报。
记者: 您好，主播。我现在在科技创新发布会现场，为大家带来最新报道。
主播: 记者同志，请您介绍一下今天发布的重要内容。
记者: 今天发布的是一款革命性的语音合成技术，可以根据文字描述自动生成自然流畅的语音。
主播: 这项技术的突破在哪里？
记者: 它可以直接生成连续语音表征，无需离散编码，保留更多的韵律细节。
主播: 感谢记者的现场报道。
""",
    "童话故事": """# 童话故事
旁白: 从前在一座遥远的城堡里，住着一位美丽的公主。
公主: 哎，今天天气真好，我想去森林里散步。
王子: 公主殿下，您好！我是邻国的王子，能在这里遇到您真是荣幸。
公主: 王子殿下，欢迎来到我的王国。
魔法师: 且慢！我在这里等待了很久，终于等到了这个时刻。
旁白: 就在这时，一位神秘的魔法师出现了。
公主: 你是什么人？为什么要挡住我们的去路？
魔法师: 我要给你们一个考验——只有真正的勇者才能通过这片魔法森林。
王子: 让我们来吧，我们不怕任何挑战！
旁白: 就这样，踏上了冒险之旅。
""",
    "客服对话": """# 客服对话
客服: 您好，欢迎致电客服中心，我是小美，请问有什么可以帮您？
客户: 你好，我购买的商品有问题，想咨询一下退换货流程。
客服: 好的，先生，请问您的订单号是多少？
客户: 订单号是 20240001。
客服: 让我为您查询一下……找到了，请问是什么问题呢？
客户: 商品收到时发现外包装破损，里面的物品也有划痕。
客服: 非常抱歉给您带来不好的体验，我现在为您办理换货，请问您希望换货还是退货？
客户: 换货吧，我希望尽快收到新的商品。
客服: 没问题，我们会在 24 小时内安排发出，感谢您的理解。
""",
}

# ── Preset voices for dropdown ──────────────────────────────────────────

PRESET_OPTIONS = [
    "narrator (旁白)",
    "host (主持人)",
    "young_woman (年轻女声)",
    "mature_woman (成熟女声)",
    "sweet_girl (甜美少女)",
    "cold_beauty (冷酷御姐)",
    "young_man (年轻男声)",
    "mature_man (成熟男声)",
    "阳光男声",
    "大叔",
    "老人",
    "机器人",
    "反派",
    "精灵",
    "AI助手 (ai_assistant)",
    "卡通 (cartoon)",
    "仙子 (fairy)",
    "恶棍 (villain)",
]

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

EMOTION_MAP = {label.split(" ", 1)[1]: label.split(" ")[0] for label in EMOTION_BUTTON_LABELS}


# ── TTS instance (lazy) ─────────────────────────────────────────────────

_tts: VoxCPMTTS | None = None


def get_tts() -> VoxCPMTTS:
    global _tts
    if _tts is None:
        _tts = VoxCPMTTS()
    return _tts


# ── Core generation function ─────────────────────────────────────────────

def generate_podcast(
    script_text: str,
    preset_voice: str,
    selected_emotions: list[str],
) -> tuple[str, str] | tuple[str, str, str]:
    """
    Parse script, assign voices, synthesize all lines.

    Returns:
        (audio_path_or_base64, status_msg) or
        (audio_path_or_base64, status_msg, error_msg)
    """
    if not script_text.strip():
        return (None, None, "请先输入剧本内容")

    try:
        script = parse_script(script_text)
    except Exception as e:
        return (None, None, f"剧本格式错误：{e}")

    if not script.lines:
        return (None, None, "未检测到有效台词行")

    # Assign voices
    vm = VoiceManager()
    for char in script.characters:
        vm.assign(char)

    tts = get_tts()
    all_samples: list[list[float]] = []

    try:
        for line in script.lines:
            voice_desc = vm.get_description(line.character)
            emotion = line.emotion
            # Respect per-line emotion if set, otherwise use selected global emotion
            tagged_text = f"({emotion}){line.text}" if emotion else line.text
            audio = tts.synthesize(tagged_text, voice_description=voice_desc)
            all_samples.append(audio)
    except Exception as e:
        return (None, None, f"生成失败：{e}")

    # Concatenate all audio segments
    combined = []
    for seg in all_samples:
        combined.extend(seg)

    # Convert to WAV bytes
    buf = io.BytesIO()
    sf.write(buf, [combined], tts.sample_rate, format="WAV")
    buf.seek(0)
    audio_b64 = base64.b64encode(buf.read()).decode()

    return (audio_b64, f"生成完成！{len(script.lines)} 句，共 {len(combined)/tts.sample_rate:.1f} 秒")


# ── Gradio UI ──────────────────────────────────────────────────────────

def build_ui():
    with gr.Blocks(
        title="PodForge — Script in, Podcast out",
        theme=gr.themes.Soft(),
    ) as demo:
        gr.Markdown(
            "## 🎙 PodForge — Script in, Podcast out\n"
            "输入剧本，选择声线，AI 帮你生成播客 · 支持 30 种语言 · 48kHz 高保真"
        )

        # Example buttons
        gr.Markdown("### 📋 示例剧本")
        with gr.Row():
            example_btns = {}
            for name in DEMO_SCRIPTS:
                btn = gr.Button(name, size="sm")
                example_btns[name] = btn

        # Main editor
        script_box = gr.Textbox(
            label="剧本",
            placeholder="旁白: 欢迎收听今天的节目...\n小明: 大家好！\n小红: 今天我们来聊一聊...",
            lines=12,
            info="格式：角色名: 台词（每行一句）",
        )

        # Wire example buttons → load script
        def load_example(name: str) -> str:
            return DEMO_SCRIPTS.get(name, "")

        for name, btn in example_btns.items():
            btn.click(fn=load_example, inputs=[gr.State(name)], outputs=[script_box])

        # Voice + emotion controls
        with gr.Row():
            voice_dropdown = gr.Dropdown(
                choices=PRESET_OPTIONS,
                value=PRESET_OPTIONS[0],
                label="默认声线",
                info="为未匹配到预设的角色选择默认声线",
            )
            emotion_group = gr.Dropdown(
                choices=[e["zh"] for e in EMOTION_TAGS],
                label="全局情感",
                info="为所有台词添加情感标签",
                multiselect=False,
            )

        emotion_btns = gr.Row()
        with emotion_btns:
            for label in EMOTION_BUTTON_LABELS:
                emoji, zh = label.split(" ", 1)
                btn = gr.Button(label, size="sm")
                # 点击情感按钮 → 设置下拉框
                btn.click(
                    fn=lambda zh=zh: gr.update(value=zh),
                    inputs=[gr.State(zh)],
                    outputs=[emotion_group],
                )

        # Generate button
        generate_btn = gr.Button("🎙 生成播客", variant="primary", size="lg")

        # Status + output
        status = gr.Textbox(label="状态", lines=1, interactive=False)
        audio_output = gr.Audio(
            label="生成的播客",
            type="numpy",
        )
        download_btn = gr.Button("⬇ 下载 WAV", size="sm")

        # Generate logic
        def on_generate(
            script_text: str,
            preset_voice: str,
            selected_emotions: list[str],
        ):
            result = generate_podcast(script_text, preset_voice, selected_emotions)
            if len(result) == 3:
                audio, status_msg, error_msg = result
                return (None, error_msg)
            audio, status_msg = result
            # audio is base64 string → return as-is
            return (audio, status_msg)

        generate_btn.click(
            fn=on_generate,
            inputs=[script_box, voice_dropdown, emotion_group],
            outputs=[audio_output, status],
        )

        # Download logic: encode audio to file download
        def on_download(audio_data):
            if audio_data is None:
                return None
            # audio_data is base64 or tuple (sample_rate, data)
            return gr.File()

        download_btn.click(
            fn=on_download,
            inputs=[audio_output],
            outputs=[gr.File()],
        )

    return demo


if __name__ == "__main__":
    demo = build_ui()
    demo.launch(server_name="0.0.0.0", server_port=7860)
```

- [ ] **Step 2: 本地验证**（不需要真实 TTS，只验证 UI 渲染）

Run: `cd /home/jackie/桌面/claude/PodForge && python -c "import app; print('app.py loads ok')"`
Expected: 无 ImportError（voxcpm 等包在本地可能没装，不用担心）

- [ ] **Step 3: 提交**

```bash
cd /home/jackie/桌面/claude/PodForge
git add app.py
git commit -m "$(cat <<'EOF'
feat: add Gradio UI for HuggingFace Space deployment

Single-file Gradio app with:
- 4 example script buttons
- Script editor with character:line format
- Voice preset dropdown + emotion picker
- TTS generation with lazy model loading
- Audio playback + download
EOF
)"
```

---

### Task 4: 修复下载按钮（Gradio Audio 下载逻辑）

**Files:**
- Modify: `app.py` (修正 download 逻辑)
- Note: Gradio Audio 组件已有内置下载，无需自定义 download 按钮

- [ ] **Step 1: 简化 app.py 中的下载逻辑**

删除 `download_btn` 相关代码（gr.File() 返回），改用 Gradio Audio 内置下载功能。Gradio 的 `gr.Audio(type="numpy")` 组件已经自带下载按钮。

**替换整个 download 按钮段落为：**

```python
        # Remove download button — Audio component has built-in download
        # (gr.Audio with type="numpy" auto-provides ⬇ button)
```

- [ ] **Step 2: 验证并提交**

```bash
cd /home/jackie/桌面/claude/PodForge
git add app.py
git commit -m "fix: remove redundant download button — Audio has built-in ⬇"
```

---

### Task 5: README 更新 HF Space 部署说明

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 添加 HF Space 章节**

在 README.md 的 "Quick Start" 之前或之后添加：

```markdown
## Try It Now — No Install Needed

**Try PodForge instantly on HuggingFace Spaces:**

[![Open in Spaces](https://huggingface.co/datasets/gradio-app/repo-files/main/params-badge.svg)](https://huggingface.co/spaces)

> ⚠️ First "Generate" triggers model loading (~30-60s). Subsequent requests are instant.

### Deploy Your Own Space

1. Go to [huggingface.co/new-space](https://huggingface.co/new-space)
2. Select **Gradio** SDK, **T4 GPU** hardware
3. Connect your GitHub repo (No1Hoo/PodForge)
4. HF builds automatically → your Space is live!

### Requirements
```bash
pip install -r requirements_hf.txt
python app.py  # starts Gradio on port 7860
```
```

- [ ] **Step 2: 提交**

```bash
cd /home/jackie/桌面/claude/PodForge
git add README.md
git commit -m "docs: add HuggingFace Space deployment instructions"
```

---

### Task 6: 最终推送

- [ ] **Step 1: 确认所有文件已提交**

```bash
cd /home/jackie/桌面/claude/PodForge && git status && git log --oneline -5
```

- [ ] **Step 2: 推送到 GitHub**

```bash
cd /home/jackie/桌面/claude/PodForge && HTTPS_PROXY=http://127.0.0.1:7897 git push origin master
```

---

## 自查清单

| 检查项 | 状态 |
|--------|------|
| `requirements_hf.txt` 包含所有必要依赖 | ✅ |
| `backend/hf_tts.py` 按需加载模型，无 GPU 时 import 不报错 | ✅ |
| `app.py` Gradio 界面包含示例/编辑器/声线/情感/生成/播放/下载 | ✅ |
| README 包含 HF Space 部署说明 + Try It Now 入口 | ✅ |
| 所有文件已 commit 并 push 到 GitHub | ⏳ |

---

## 部署验证清单（用户操作）

部署完成后在 HF Space 验证：

- [ ] 打开 Space URL，显示 Gradio 界面
- [ ] 点击"示例播客"按钮，剧本框填充内容
- [ ] 点击"🎙 生成播客"，等待模型加载（约 30-60s），音频生成完成
- [ ] 音频播放器出现，点击播放，听到语音
- [ ] 下载按钮可下载 WAV 文件
- [ ] 切换其他示例剧本，重复验证