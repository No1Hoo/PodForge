<div align="center">

# PodForge

**Script in, Podcast out.**

AI-powered multi-character audio drama generator built on [VoxCPM2](https://github.com/OpenBMB/VoxCPM).

Turn any script into a fully voiced podcast or audio drama — with unique character voices, emotions, and studio-quality 48kHz output.

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![VoxCPM2](https://img.shields.io/badge/Powered_by-VoxCPM2-orange.svg)](https://github.com/OpenBMB/VoxCPM)

---

## ⚡ Try It Now — No Install Needed

**Use PodForge instantly on HuggingFace Spaces:**

[![Open in Spaces](https://huggingface.co/datasets/gradio-app/repo-files/main/params-badge.svg)](https://huggingface.co/spaces)

> ⚠️ First "Generate" click triggers VoxCPM2 model loading (~30-60 seconds). Subsequent requests are instant.

</div>

---

## What is PodForge?

PodForge takes a plain-text script with character names and dialogue, and produces a complete multi-voice audio file. No audio engineering skills needed.

```
Input:                          Output:
┌─────────────────────┐        ┌─────────────────────┐
│ 小明: 你好啊！       │  ───►  │  ▶ 48kHz WAV        │
│ 小红: (开心) 你好！  │        │  3 distinct voices   │
│ 旁白: 他们聊了起来。 │        │  Emotion-aware TTS   │
└─────────────────────┘        └─────────────────────┘
```

### Key Features

- **Voice Design** — Create unique character voices from natural-language descriptions (no reference audio needed)
- **Emotion Control** — Add `(happy)`, `(sad)`, `(angry)`, `(whisper)` tags to control tone
- **30 Languages** — Supports Chinese, English, Japanese, Korean, and 26 more
- **48kHz Studio Quality** — Built on VoxCPM2's AudioVAE V2 with native super-resolution
- **CLI + Web UI** — Use from terminal or browser
- **Cloud GPU Ready** — Runs on Google Colab (free T4) or any CUDA server

## Quick Start

### Deploy Your Own Space

1. Go to [huggingface.co/new-space](https://huggingface.co/new-space)
2. Select **Gradio** SDK, **T4 GPU** hardware
3. Connect your GitHub repo: `No1Hoo/PodForge`
4. HF builds automatically → your Space is live at `https://username-podforge.hf.space`

### Local Development

```bash
pip install -r requirements_hf.txt
python app.py   # starts Gradio on http://localhost:7860
```

### 1. Start the TTS Server

**Option A: Google Colab (free GPU)**

Open [`colab/voxcpm_server.ipynb`](colab/voxcpm_server.ipynb) in Colab, run all cells, and copy the public URL.

**Option B: Local GPU**

```bash
pip install voxcpm
# The server starts automatically when you run PodForge
```

### 2. Install PodForge

```bash
git clone https://github.com/YOUR_USER/PodForge.git
cd PodForge
pip install -r requirements.txt
```

### 3. Generate Audio

**CLI:**

```bash
python scripts/generate.py \
  --script examples/demo_drama.txt \
  --output demo.wav \
  --tts-url https://your-colab-url.ngrok.io
```

**Python API:**

```python
import asyncio
from backend.drama_parser import parse_script
from backend.tts_client import VoxCPMClient
from backend.voice_manager import VoiceManager

async def main():
    script = parse_script("""
    小明: 你好啊！最近怎么样？
    小红: (开心) 很好呀！好久不见！
    """)

    vm = VoiceManager()
    vm.assign_all(script.characters)
    tts = VoxCPMClient("http://localhost:8809")

    for line in script.lines:
        desc = vm.get_description(line.character)
        text = f"({line.emotion}){line.text}" if line.emotion else line.text
        await tts.synthesize_to_file(text, f"{line.character}.wav", voice_description=desc)

asyncio.run(main())
```

**Web UI:**

```bash
# Start backend (port 8080)
cd backend && python -m uvicorn backend.main:app --port 8080

# Start frontend (port 3000)
cd frontend && npm install && npm run dev
```

Open `http://localhost:3000` → load a demo script → pick voices → click **生成播客**.

## Script Format

```text
# Comments start with #
CharacterName: Dialogue text
CharacterName: (emotion) Dialogue text with emotion control
```

> **Tip:** Spaces users can click the example script buttons to load a demo instantly.

### Supported Emotions

| Tag | Effect |
|-----|--------|
| `(happy)` / `(开心)` | Cheerful, upbeat |
| `(sad)` / `(悲伤)` | Melancholic, slow |
| `(angry)` / `(愤怒)` | Intense, loud |
| `(whisper)` / `(悄悄话)` | Soft, intimate |
| `(thinking)` / `(思考)` | Contemplative pause |
| `(surprised)` / `(惊讶)` | Exclamatory |

## Architecture

```
┌─────────────────────────┐
│   Next.js Frontend      │
│   Script Editor + UI    │◄── Emotion picker, voice panel
└───────────┬─────────────┘
            │ REST + WebSocket
┌───────────▼─────────────┐
│   FastAPI Backend       │
│   Parse → Voice → TTS   │◄── 27 presets, 10 emotions
└───────────┬─────────────┘
            │ HTTP
┌───────────▼─────────────┐
│   VoxCPM2 Server        │
│   (Colab / Local GPU)   │
│   Voice Design + Clone  │
└─────────────────────────┘
```

## Project Structure

```
PodForge/
├── backend/
│   ├── drama_parser.py    # Script parser
│   ├── voice_manager.py   # Voice assignment & presets
│   ├── tts_client.py      # VoxCPM2 API client
│   └── main.py            # FastAPI server
├── scripts/
│   └── generate.py        # CLI tool
├── colab/
│   ├── voxcpm_server.ipynb # Colab notebook (GPU server)
│   └── voxcpm_server.py    # Standalone server script
├── frontend/               # Next.js web UI
│   ├── app/page.tsx         # Main page
│   ├── components/          # 6 React components
│   └── lib/                 # API client + WebSocket
├── examples/
│   ├── demo_drama.txt       # Podcast demo
│   ├── news_broadcast.txt   # News broadcast
│   ├── fairy_tale.txt       # Fairy tale story
│   ├── customer_service.txt # Customer service
│   └── podcast_3hosts.txt   # 3-host tech podcast
├── app.py                   # Gradio UI for HuggingFace Space
├── requirements_hf.txt      # HuggingFace Space dependencies
└── README.md
```

## Roadmap

- [x] Script parser with emotion support
- [x] Voice Design auto-assignment (27 presets)
- [x] CLI tool
- [x] Google Colab server
- [x] Web UI (Next.js + TypeScript + Tailwind)
- [x] Real-time progress (WebSocket streaming)
- [x] Preset voice library (27 voices, 10 emotions)
- [ ] BGM mixing
- [ ] RSS podcast feed export
- [ ] Multi-language script support

## Credits

- [VoxCPM2](https://github.com/OpenBMB/VoxCPM) by OpenBMB — the TTS engine powering PodForge
- [MiniCPM-4](https://github.com/OpenBMB/MiniCPM) — backbone language model

## License

Apache-2.0 — free for commercial use.
