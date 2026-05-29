"""FastAPI backend for PodForge."""

from __future__ import annotations

import base64
import io
import logging
import os
import time

import numpy as np
import soundfile as sf
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .drama_parser import parse_script
from .tts_client import VoxCPMClient
from .voice_manager import (
    EMOTION_TAGS,
    PRESET_CATEGORIES,
    PRESET_VOICES,
    VoiceManager,
)

logger = logging.getLogger("podforge")

app = FastAPI(
    title="PodForge",
    description="Script in, Podcast out. AI-powered multi-character audio drama generator.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Config ──────────────────────────────────────────────────────────────────

TTS_BASE_URL = os.environ.get("PODFORGE_TTS_URL", "http://localhost:8809")
SAMPLE_RATE = 48000


# ── Models ──────────────────────────────────────────────────────────────────


class GenerateRequest(BaseModel):
    script: str
    cfg_value: float = 2.0
    inference_timesteps: int = 10
    voice_overrides: dict[str, str] | None = None


class LineResult(BaseModel):
    character: str
    text: str
    emotion: str | None
    voice_description: str
    audio_index: int


class GenerateResponse(BaseModel):
    title: str
    characters: list[str]
    lines: list[LineResult]
    total_duration_seconds: float


class HealthResponse(BaseModel):
    status: str
    tts_server: bool


class PresetInfo(BaseModel):
    key: str
    name: str
    description: str
    category: str


class EmotionInfo(BaseModel):
    en: str
    zh: str
    emoji: str


# ── Routes ──────────────────────────────────────────────────────────────────


@app.get("/health", response_model=HealthResponse)
async def health():
    async with VoxCPMClient(TTS_BASE_URL) as tts:
        tts_ok = await tts.health()
    return HealthResponse(
        status="ok" if tts_ok else "degraded",
        tts_server=tts_ok,
    )


@app.get("/presets", response_model=list[PresetInfo])
async def get_presets():
    """Return all preset voice descriptions with categories."""
    return [
        PresetInfo(key=k, name=k, description=PRESET_VOICES[k], category=PRESET_CATEGORIES.get(k, "other"))
        for k in sorted(PRESET_VOICES)
    ]


@app.get("/emotions", response_model=list[EmotionInfo])
async def get_emotions():
    """Return all supported emotion tags."""
    return [EmotionInfo(**e) for e in EMOTION_TAGS]


@app.post("/parse", response_model=GenerateResponse)
async def parse(req: GenerateRequest):
    """Parse a script and return character/voice info without generating audio."""
    script = parse_script(req.script)
    vm = VoiceManager(overrides=req.voice_overrides or {})
    vm.assign_all(script.characters)

    lines = []
    for i, line in enumerate(script.lines):
        va = vm.assign(line.character)
        lines.append(LineResult(
            character=line.character,
            text=line.text,
            emotion=line.emotion,
            voice_description=va.description,
            audio_index=i,
        ))

    return GenerateResponse(
        title=script.title,
        characters=script.characters,
        lines=lines,
        total_duration_seconds=0.0,
    )


@app.post("/generate")
async def generate(req: GenerateRequest):
    """Generate audio for an entire script. Returns concatenated WAV."""
    script = parse_script(req.script)
    if not script.lines:
        raise HTTPException(400, "Script is empty or has no valid dialogue lines.")

    vm = VoiceManager(overrides=req.voice_overrides or {})
    vm.assign_all(script.characters)

    async with VoxCPMClient(TTS_BASE_URL) as tts:
        all_audio: list[np.ndarray] = []
        silence = np.zeros(int(SAMPLE_RATE * 0.3))

        for line in script.lines:
            desc = vm.get_description(line.character)
            text = line.text
            if line.emotion:
                text = f"({line.emotion}){text}"

            try:
                audio = await tts.synthesize(
                    text=text,
                    voice_description=desc,
                    cfg_value=req.cfg_value,
                    inference_timesteps=req.inference_timesteps,
                )
                all_audio.append(audio)
                all_audio.append(silence)
            except Exception as e:
                logger.error("TTS failed for line: %s — %s", line.text[:40], e)
                raise HTTPException(502, f"TTS failed: {e}")

    if not all_audio:
        raise HTTPException(500, "No audio was generated.")

    combined = np.concatenate(all_audio)
    buf = io.BytesIO()
    sf.write(buf, combined, SAMPLE_RATE, format="WAV")
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="audio/wav",
        headers={"Content-Disposition": 'attachment; filename="podforge_output.wav"'},
    )


@app.websocket("/generate-stream")
async def generate_stream(ws: WebSocket):
    """Generate audio line-by-line, pushing progress via WebSocket.

    Client sends: GenerateRequest JSON
    Server pushes:
      {"type":"progress","line_index":N,"character":"...","status":"done"}
      {"type":"complete","audio_base64":"...","duration":N.N}
      {"type":"error","message":"..."}
    """
    await ws.accept()

    try:
        raw = await ws.receive_text()
        req = GenerateRequest.model_validate_json(raw)
    except Exception as e:
        await ws.send_json({"type": "error", "message": f"Invalid request: {e}"})
        await ws.close()
        return

    script = parse_script(req.script)
    if not script.lines:
        await ws.send_json({"type": "error", "message": "Script is empty."})
        await ws.close()
        return

    vm = VoiceManager(overrides=req.voice_overrides or {})
    vm.assign_all(script.characters)

    all_audio: list[np.ndarray] = []
    silence = np.zeros(int(SAMPLE_RATE * 0.3))
    t0 = time.monotonic()

    async with VoxCPMClient(TTS_BASE_URL) as tts:
        for i, line in enumerate(script.lines):
            desc = vm.get_description(line.character)
            text = line.text
            if line.emotion:
                text = f"({line.emotion}){text}"

            try:
                audio = await tts.synthesize(
                    text=text,
                    voice_description=desc,
                    cfg_value=req.cfg_value,
                    inference_timesteps=req.inference_timesteps,
                )
                all_audio.append(audio)
                all_audio.append(silence)

                elapsed = time.monotonic() - t0
                avg_per_line = elapsed / (i + 1)
                remaining = avg_per_line * (len(script.lines) - i - 1)

                await ws.send_json({
                    "type": "progress",
                    "line_index": i,
                    "character": line.character,
                    "text": line.text[:50],
                    "status": "done",
                    "elapsed_seconds": round(elapsed, 1),
                    "eta_seconds": round(remaining, 1),
                })
            except Exception as e:
                logger.error("TTS failed for line %d: %s", i, e)
                await ws.send_json({
                    "type": "error",
                    "message": f"Failed at line {i}: {e}",
                })
                await ws.close()
                return

    # Concatenate and send final audio
    combined = np.concatenate(all_audio)
    buf = io.BytesIO()
    sf.write(buf, combined, SAMPLE_RATE, format="WAV")
    buf.seek(0)
    audio_b64 = base64.b64encode(buf.read()).decode()

    await ws.send_json({
        "type": "complete",
        "audio_base64": audio_b64,
        "duration": round(len(combined) / SAMPLE_RATE, 1),
        "sample_rate": SAMPLE_RATE,
        "total_lines": len(script.lines),
    })
    await ws.close()


# ── Entrypoint ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8080, reload=True)
