"""Tests for the voice manager."""

import pytest

from backend.voice_manager import VoiceManager, PRESET_VOICES


class TestVoiceManager:
    def test_preset_match_narrator(self):
        vm = VoiceManager()
        va = vm.assign("Narrator")
        assert va.preset_name == "narrator"
        assert "narrator" in va.description.lower() or "professional" in va.description.lower()

    def test_preset_match_chinese(self):
        vm = VoiceManager()
        va = vm.assign("旁白")
        assert va.preset_name == "旁白"

    def test_auto_assign_unknown(self):
        vm = VoiceManager()
        va = vm.assign("SomeRandomCharacter")
        assert va.preset_name is None
        assert len(va.description) > 0

    def test_override_priority(self):
        vm = VoiceManager(overrides={"小明": "Custom voice for Xiao Ming"})
        va = vm.assign("小明")
        assert va.description == "Custom voice for Xiao Ming"
        assert va.preset_name == "custom"

    def test_same_character_same_voice(self):
        vm = VoiceManager()
        va1 = vm.assign("小明")
        va2 = vm.assign("小明")
        assert va1.description == va2.description

    def test_assign_all(self):
        vm = VoiceManager()
        assignments = vm.assign_all(["小明", "小红", "旁白"])
        assert len(assignments) == 3
        assert "小明" in assignments
