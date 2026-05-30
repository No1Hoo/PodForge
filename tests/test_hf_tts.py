import pytest
from backend.hf_tts import VoxCPMTTS, get_model


def test_tts_import():
    tts = VoxCPMTTS()
    assert tts.sample_rate == 48000


def test_tts_default_voice():
    """Test synthesize with default voice (no model loaded yet)."""
    tts = VoxCPMTTS()
    text = "(开心) 你好，世界！"
    # This will fail if voxcpm is not installed, but the test file should exist
    wav = tts.synthesize(text)
    assert wav is not None
    assert len(wav) > 0
    assert isinstance(wav, list)