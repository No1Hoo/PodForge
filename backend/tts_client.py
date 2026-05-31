"""TTS client for communicating with VoxCPM2 server."""

from __future__ import annotations

import base64
import io
import os

import httpx
import numpy as np
import soundfile as sf
from pathlib import Path


class VoxCPMClient:
    """Client for the VoxCPM2 REST API (Colab or local server).

    Reuses a single httpx.AsyncClient for connection pooling.
    Use as an async context manager or call close() when done.
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
    ):
        self.base_url = (
            base_url
            or os.environ.get("PODFORGE_TTS_URL")
            or "http://localhost:8809"
        ).rstrip("/")
        self.timeout = timeout if timeout is not None else float(os.environ.get("PODFORGE_TTS_TIMEOUT", "300"))
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def __aenter__(self) -> VoxCPMClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    async def health(self) -> bool:
        """Check if the TTS server is reachable."""
        try:
            r = await self.client.get(
                f"{self.base_url}/health",
                timeout=5.0,
            )
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

        payload: dict[str, str | float | int] = {
            "text": text,
            "cfg_value": cfg_value,
            "inference_timesteps": inference_timesteps,
        }
        if reference_audio_path:
            payload["reference_wav_path"] = reference_audio_path

        r = await self.client.post(f"{self.base_url}/generate", json=payload)
        r.raise_for_status()
        data = r.json()

        # Server returns audio as base64 or file path
        if "audio_path" in data:
            audio, _sr = sf.read(data["audio_path"])
            return audio
        elif "audio_base64" in data:
            raw = base64.b64decode(data["audio_base64"])
            audio, _sr = sf.read(io.BytesIO(raw))
            return audio
        else:
            raise ValueError(f"Unexpected response format: {data.keys()}")

    async def synthesize_to_file(
        self,
        text: str,
        output_path: str | Path,
        **kwargs: object,
    ) -> Path:
        """Synthesize and save to file."""
        audio = await self.synthesize(text, **kwargs)  # type: ignore[arg-type]
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(output), audio, 48000)
        return output
