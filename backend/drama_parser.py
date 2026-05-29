"""Drama script parser for PodForge.

Parses scripts in the format:
    CharacterName: Dialogue text
    CharacterName: (emotion) Dialogue text

Lines starting with # are comments. Blank lines are ignored.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DialogueLine:
    character: str
    text: str
    emotion: str | None = None


@dataclass
class Script:
    title: str
    lines: list[DialogueLine]

    @property
    def characters(self) -> list[str]:
        seen: dict[str, None] = {}
        for line in self.lines:
            seen.setdefault(line.character, None)
        return list(seen.keys())


_LINE_RE = re.compile(r"^(?P<name>[^:]+):\s*(?P<body>.+)$")
_EMOTION_RE = re.compile(r"^\((?P<emotion>[^)]+)\)\s*(?P<text>.+)$")


def parse_line(raw: str) -> DialogueLine | None:
    """Parse a single script line. Returns None for comments / blanks."""
    stripped = raw.strip()
    if not stripped or stripped.startswith("#"):
        return None

    m = _LINE_RE.match(stripped)
    if not m:
        return None

    character = m.group("name").strip()
    body = m.group("body").strip()

    em = _EMOTION_RE.match(body)
    if em:
        return DialogueLine(
            character=character,
            text=em.group("text").strip(),
            emotion=em.group("emotion").strip(),
        )

    return DialogueLine(character=character, text=body)


def parse_script(source: str, *, title: str = "Untitled") -> Script:
    """Parse a full script string."""
    lines: list[DialogueLine] = []
    for raw_line in source.splitlines():
        parsed = parse_line(raw_line)
        if parsed is not None:
            lines.append(parsed)
    return Script(title=title, lines=lines)


def parse_script_file(path: str | Path) -> Script:
    """Parse a script from a file path."""
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    title = p.stem.replace("_", " ").replace("-", " ").title()
    return parse_script(text, title=title)
