"""
VoxCPM2 TTS Server for Google Colab

Run this notebook in Google Colab with a T4 GPU (free tier).
It starts a FastAPI server that PodForge's backend connects to.

Usage:
1. Open in Colab: https://colab.research.google.com/github/YOUR_USER/PodForge/blob/main/colab/voxcpm_server.ipynb
2. Run all cells
3. Copy the ngrok URL and set it as TTS_BASE_URL in the backend
"""

# %% [markdown]
# # PodForge — VoxCPM2 TTS Server
#
# This notebook starts a VoxCPM2 server on Google Colab's free GPU.
# Run all cells, then copy the public URL to connect from PodForge.

# %% Install dependencies
# !pip install voxcpm fastapi uvicorn pyngrok soundfile numpy

# %% Download model (first run only, ~4GB)
# from voxcpm import VoxCPM
# model = VoxCPM.from_pretrained("openbmb/VoxCPM2", load_denoiser=False)

# %% Start TTS server
"""
import io
import base64
import numpy as np
import soundfile as sf
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pyngrok import ngrok
import uvicorn
import threading

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Load model
model = VoxCPM.from_pretrained("openbmb/VoxCPM2", load_denoiser=False)


class TTSRequest(BaseModel):
    text: str
    cfg_value: float = 2.0
    inference_timesteps: int = 10
    reference_wav_path: str | None = None


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/generate")
async def generate(req: TTSRequest):
    kwargs = {
        "text": req.text,
        "cfg_value": req.cfg_value,
        "inference_timesteps": req.inference_timesteps,
    }
    if req.reference_wav_path:
        kwargs["reference_wav_path"] = req.reference_wav_path

    wav = model.generate(**kwargs)

    # Encode to WAV bytes
    buf = io.BytesIO()
    sf.write(buf, wav, model.tts_model.sample_rate, format="WAV")
    buf.seek(0)
    audio_b64 = base64.b64encode(buf.read()).decode()

    return {
        "audio_base64": audio_b64,
        "sample_rate": model.tts_model.sample_rate,
        "duration_seconds": len(wav) / model.tts_model.sample_rate,
    }


# Start ngrok tunnel
public_url = ngrok.connect(8809)
print(f"Public URL: {public_url}")

# Run server in background thread
def run_server():
    uvicorn.run(app, host="0.0.0.0", port=8809)

thread = threading.Thread(target=run_server, daemon=True)
thread.start()

print("TTS server running! Copy the URL above and paste it into PodForge.")
"""
