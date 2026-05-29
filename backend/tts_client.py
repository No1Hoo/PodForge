"""TTS client for communicating with VoxCPM2 server."""

from __future__ import annotations

import httpx
import numpy as np
import soundfile as sf
from pathlib import Path


class VoxCPMClient:
    """Client for the VoxCPM2 REST API (Colab or local server)."""

    def __init__(self, base_url: str = "http://localhost:8809", timeout: float = 120.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def health(self) -> bool:
        """Check if the TTS server is reachable."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{self.base_url}/health")
                return r.status_code == 200
        except httpx.RequestError:
            return False

    async def synthesize(
        self,
        text: str,
        *,
        voice_description: str | None = None,
        reference_audio_path: str | None = None,
        cfg_value: float = 2.0,
        inference_timesteps: int = 10,
    ) -> np.ndarray:
        """Synthesize speech from text.

        Args:
            text: The text to synthesize.
            voice_description: Voice Design description (placed in parentheses).
            reference_audio_path: Path to reference audio for voice cloning.
            cfg_value: Classifier-free guidance value.
            inference_timesteps: Number of diffusion steps.

        Returns:
            Audio samples as numpy array.
        """
        # Prepend voice description for Voice Design mode
        if voice_description and not reference_audio_path:
            text = f"({voice_description}){text}"

        payload = {
            "text": text,
            "cfg_value": cfg_value,
            "inference_timesteps": inference_timesteps,
        }
        if reference_audio_path:
            payload["reference_wav_path"] = reference_audio_path

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(f"{self.base_url}/generate", json=payload)
            r.raise_for_status()
            data = r.json()

        # Server returns audio as base64 or file path
        if "audio_path" in data:
            audio, _sr = sf.read(data["audio_path"])
            return audio
        elif "audio_base64" in data:
            import base64
            raw = base64.b64decode(data["audio_base64"])
            import io
            audio, _sr = sf.read(io.BytesIO(raw))
            return audio
        else:
            raise ValueError(f"Unexpected response format: {data.keys()}")

    async def synthesize_to_file(
        self,
        text: str,
        output_path: str | Path,
        **kwargs,
    ) -> Path:
        """Synthesize and save to file."""
        audio = await self.synthesize(text, **kwargs)
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(output), audio, 48000)
        return output
