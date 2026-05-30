"""VoxCPM2 TTS wrapper for HuggingFace Space deployment.

按需加载模型，第一次 synthesize() 调用时初始化。
"""

from __future__ import annotations

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
    ) -> list[float]:
        """
        Generate audio for given text.

        Args:
            text: Text to synthesize (emotion tag embedded like "(happy)Hello")
            voice_description: Optional VoxCPM2 Voice Design description

        Returns:
            WAV audio as float samples list
        """
        model = get_model()

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
        """Synthesize multiple lines."""
        results = []
        for text, voice_desc, emotion in lines:
            tagged_text = f"({emotion}){text}" if emotion else text
            audio = self.synthesize(tagged_text, voice_description=voice_desc)
            results.append(audio)
        return results