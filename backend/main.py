"""FastAPI backend for PodForge."""

from __future__ import annotations

import io
import logging

import numpy as np
import soundfile as sf
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .drama_parser import parse_script
from .tts_client import VoxCPMClient
from .voice_manager import VoiceManager

logger = logging.getLogger("podforge")

app = FastAPI(
    title="PodForge",
    description="Script in, Podcast out. AI-powered multi-character audio drama generator.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Config ──────────────────────────────────────────────────────────────────

TTS_BASE_URL = "http://localhost:8809"
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


# ── Routes ──────────────────────────────────────────────────────────────────


@app.get("/health", response_model=HealthResponse)
async def health():
    tts = VoxCPMClient(TTS_BASE_URL)
    tts_ok = await tts.health()
    return HealthResponse(
        status="ok" if tts_ok else "degraded",
        tts_server=tts_ok,
    )


@app.post("/parse")
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
    tts = VoxCPMClient(TTS_BASE_URL)

    all_audio: list[np.ndarray] = []
    silence = np.zeros(int(SAMPLE_RATE * 0.3))  # 300ms pause between lines

    for line in script.lines:
        desc = vm.get_description(line.character)

        # Build text with emotion prefix if present
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

    # Concatenate and write WAV
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


# ── Entrypoint ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8080, reload=True)
