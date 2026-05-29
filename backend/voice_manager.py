"""Voice manager for PodForge.

Maps character names to VoxCPM2 Voice Design descriptions.
Provides preset templates and auto-assignment logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Preset voice descriptions for common character archetypes.
# VoxCPM2 Voice Design format: natural-language description of the voice.
PRESET_VOICES: dict[str, str] = {
    # Narrator / host
    "narrator": "A professional male narrator with a warm, clear, and authoritative voice, moderate pace",
    "host": "A friendly and energetic male host with a natural conversational tone",
    "旁白": "一位专业男播音员，声音温暖清晰，语速适中，富有磁性",
    "主持人": "一位亲和力强的男主持人，语调自然活泼",
    # Female archetypes
    "young_woman": "A young woman in her 20s, gentle and sweet voice, slightly higher pitch",
    "mature_woman": "A mature woman in her 30s, confident and elegant voice, warm and soothing",
    "girl": "A teenage girl, cheerful and lively voice, bright and energetic",
    "sweet_girl": "A sweet young girl with a cute bubbly voice, innocent and adorable",
    "cold_beauty": "A cold and elegant woman with a crisp clear voice, composed and slightly aloof",
    "温柔女声": "一位年轻女性，声音温柔甜美，略带磁性",
    "知性女声": "一位成熟女性，声音知性优雅，温暖而有感染力",
    # Male archetypes
    "young_man": "A young man in his 20s, clear and energetic voice, natural and friendly",
    "mature_man": "A middle-aged man, deep and steady voice, authoritative yet approachable",
    "uncle": "A middle-aged man with a warm, fatherly voice, slightly deep and comforting",
    "boy": "A teenage boy, bright and enthusiastic voice, youthful energy",
    "阳光男声": "一位年轻男性，声音阳光开朗，充满活力",
    "大叔": "一位中年男性，声音沉稳浑厚，有磁性",
    # Specialty
    "robot": "A robotic voice with slight metallic resonance, measured and precise",
    "whisper": "A soft whispering voice, intimate and gentle, very quiet and close",
    "villain": "A menacing deep voice with slow deliberate delivery, intimidating and dark",
    "fairy": "A light ethereal female voice with a magical sparkle, soft and enchanting",
    "cartoon": "A high-pitched cartoonish voice with exaggerated expression and rapid delivery",
    "ai_assistant": "A calm and neutral AI assistant voice, clear and professional with a friendly undertone",
    "老人": "一位老年人，声音沧桑沙哑，语速缓慢，充满人生阅历",
    "机器人": "机器人声音，带有轻微金属质感，语速均匀",
    "反派": "一个低沉阴险的声音，语速缓慢，充满威胁感",
    "精灵": "一个空灵的女声，带有魔法般的轻盈感，温柔而迷人",
}

# Category mapping for each preset (used by frontend)
PRESET_CATEGORIES: dict[str, str] = {
    "narrator": "male",
    "host": "male",
    "旁白": "male",
    "主持人": "male",
    "young_woman": "female",
    "mature_woman": "female",
    "girl": "female",
    "sweet_girl": "female",
    "cold_beauty": "female",
    "温柔女声": "female",
    "知性女声": "female",
    "young_man": "male",
    "mature_man": "male",
    "uncle": "male",
    "boy": "male",
    "阳光男声": "male",
    "大叔": "male",
    "robot": "special",
    "whisper": "special",
    "villain": "special",
    "fairy": "special",
    "cartoon": "special",
    "ai_assistant": "special",
    "老人": "male",
    "机器人": "special",
    "反派": "special",
    "精灵": "special",
}

# Supported emotion tags (bilingual)
EMOTION_TAGS: list[dict[str, str]] = [
    {"en": "happy", "zh": "开心", "emoji": "😊"},
    {"en": "sad", "zh": "悲伤", "emoji": "😢"},
    {"en": "angry", "zh": "愤怒", "emoji": "😠"},
    {"en": "surprised", "zh": "惊讶", "emoji": "😲"},
    {"en": "whisper", "zh": "悄悄话", "emoji": "🤫"},
    {"en": "thinking", "zh": "思考", "emoji": "🤔"},
    {"en": "excited", "zh": "兴奋", "emoji": "🤩"},
    {"en": "gentle", "zh": "温柔", "emoji": "🥰"},
    {"en": "serious", "zh": "严肃", "emoji": "😐"},
    {"en": "humorous", "zh": "幽默", "emoji": "😄"},
]

# Auto-assignment pool: when a character name doesn't match any preset,
# cycle through these generic voices.
_AUTO_POOL = [
    "A young adult with a clear, natural, and pleasant voice",
    "A friendly person with a warm and engaging conversational tone",
    "A confident speaker with a smooth and articulate voice",
    "A cheerful individual with an expressive and lively voice",
    "A calm and composed person with a gentle, soothing voice",
    "A professional speaker with a polished and clear delivery",
    "A spirited young person with an energetic and dynamic voice",
    "A thoughtful individual with a measured and melodic voice",
]


@dataclass
class VoiceAssignment:
    character: str
    description: str
    preset_name: str | None = None


@dataclass
class VoiceManager:
    """Manages character-to-voice mappings."""

    overrides: dict[str, str] = field(default_factory=dict)
    _assignments: dict[str, VoiceAssignment] = field(default_factory=dict)
    _auto_index: int = 0

    def _match_preset(self, name: str) -> str | None:
        """Try to match a character name to a preset voice."""
        lower = name.lower().strip()
        # Direct match
        if lower in PRESET_VOICES:
            return lower
        # Partial match
        for key in PRESET_VOICES:
            if key in lower or lower in key:
                return key
        return None

    def assign(self, character: str) -> VoiceAssignment:
        """Get or create a voice assignment for a character."""
        if character in self._assignments:
            return self._assignments[character]

        # User override takes priority
        if character in self.overrides:
            va = VoiceAssignment(
                character=character,
                description=self.overrides[character],
                preset_name="custom",
            )
            self._assignments[character] = va
            return va

        # Try preset match
        preset_key = self._match_preset(character)
        if preset_key is not None:
            va = VoiceAssignment(
                character=character,
                description=PRESET_VOICES[preset_key],
                preset_name=preset_key,
            )
            self._assignments[character] = va
            return va

        # Auto-assign from pool
        desc = _AUTO_POOL[self._auto_index % len(_AUTO_POOL)]
        self._auto_index += 1
        va = VoiceAssignment(
            character=character,
            description=desc,
            preset_name=None,
        )
        self._assignments[character] = va
        return va

    def assign_all(self, characters: list[str]) -> dict[str, VoiceAssignment]:
        """Assign voices to all characters."""
        for c in characters:
            self.assign(c)
        return dict(self._assignments)

    def get_description(self, character: str) -> str:
        """Get the voice description for a character (assigns if needed)."""
        return self.assign(character).description
