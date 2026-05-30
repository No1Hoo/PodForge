import pytest

# Mark this module as integration tests - skip if voxcpm not available
pytestmark = pytest.mark.integration


def test_tts_import():
    """Test that VoxCPMTTS can be instantiated."""
    pytest.importorskip("voxcpm")
    from backend.hf_tts import VoxCPMTTS

    tts = VoxCPMTTS()
    assert tts.sample_rate == 48000


def test_tts_synthesize():
    """Integration test: requires GPU and voxcpm installed."""
    pytest.importorskip("voxcpm")
    from backend.hf_tts import VoxCPMTTS

    tts = VoxCPMTTS()
    text = "(开心) 你好，世界！"
    wav = tts.synthesize(text)
    assert wav is not None
    assert len(wav) > 0
    assert isinstance(wav, list)