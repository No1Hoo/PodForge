"""CLI tool for PodForge — generate audio from drama scripts."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.drama_parser import parse_script_file
from backend.tts_client import VoxCPMClient
from backend.voice_manager import VoiceManager

SAMPLE_RATE = 48000


async def generate(
    script_path: str,
    output_path: str,
    tts_url: str,
    cfg_value: float,
    timesteps: int,
) -> None:
    """Generate audio from a drama script."""
    import numpy as np
    import soundfile as sf

    # Parse script
    script = parse_script_file(script_path)
    print(f"Script: {script.title}")
    print(f"Characters: {', '.join(script.characters)}")
    print(f"Lines: {len(script.lines)}")
    print()

    # Assign voices
    vm = VoiceManager()
    vm.assign_all(script.characters)

    for char in script.characters:
        va = vm.assign(char)
        print(f"  {char}: {va.description[:60]}...")
    print()

    # Generate audio
    tts = VoxCPMClient(tts_url)
    if not await tts.health():
        print(f"ERROR: TTS server not reachable at {tts_url}")
        print("Start the server first: python -m backend.main")
        sys.exit(1)

    all_audio: list[np.ndarray] = []
    silence = np.zeros(int(SAMPLE_RATE * 0.3))

    for i, line in enumerate(script.lines):
        desc = vm.get_description(line.character)
        text = line.text
        if line.emotion:
            text = f"({line.emotion}){text}"

        print(f"  [{i+1}/{len(script.lines)}] {line.character}: {line.text[:40]}...")
        audio = await tts.synthesize(
            text=text,
            voice_description=desc,
            cfg_value=cfg_value,
            inference_timesteps=timesteps,
        )
        all_audio.append(audio)
        all_audio.append(silence)

    # Write output
    combined = np.concatenate(all_audio)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out), combined, SAMPLE_RATE)
    duration = len(combined) / SAMPLE_RATE
    print(f"\nDone! {duration:.1f}s audio saved to {out}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="podforge",
        description="PodForge — Script in, Podcast out.",
    )
    parser.add_argument("--script", "-s", required=True, help="Path to script file")
    parser.add_argument("--output", "-o", default="output.wav", help="Output WAV path")
    parser.add_argument("--tts-url", default="http://localhost:8809", help="TTS server URL")
    parser.add_argument("--cfg", type=float, default=2.0, help="CFG value")
    parser.add_argument("--timesteps", type=int, default=10, help="Inference timesteps")
    args = parser.parse_args()

    asyncio.run(generate(
        script_path=args.script,
        output_path=args.output,
        tts_url=args.tts_url,
        cfg_value=args.cfg,
        timesteps=args.timesteps,
    ))


if __name__ == "__main__":
    main()
