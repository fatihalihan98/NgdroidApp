"""Generate narrated stock-footage videos via Pexels + ElevenLabs.

Usage:
    cp .env.example .env  # then fill in API keys
    pip install -r requirements.txt
    python main.py sample_script.json --output output/final.mp4

Script JSON schema:
    [
        {"text": "narration line", "query": "pexels search query"},
        ...
    ]
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from elevenlabs_client import ElevenLabsClient
from pexels_client import PexelsClient
from video_builder import build_video


def load_script(script_path: Path) -> list[dict]:
    data = json.loads(script_path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError("Script must be a non-empty list of {text, query} objects.")
    for index, entry in enumerate(data):
        if "text" not in entry or "query" not in entry:
            raise ValueError(f"Entry {index} must contain 'text' and 'query'.")
    return data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a video from a script using Pexels + ElevenLabs."
    )
    parser.add_argument("script", type=Path, help="Path to script JSON file")
    parser.add_argument(
        "--output", type=Path, default=Path("output/final.mp4"), help="Output video path"
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        default=Path("output/workdir"),
        help="Working directory for intermediate clips and audio",
    )
    parser.add_argument(
        "--music", type=Path, default=None, help="Optional background music file"
    )
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument(
        "--orientation",
        default="landscape",
        choices=["landscape", "portrait", "square"],
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()

    pexels_key = os.environ.get("PEXELS_API_KEY")
    eleven_key = os.environ.get("ELEVENLABS_API_KEY")
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
    model_id = os.environ.get("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")

    if not pexels_key or not eleven_key:
        raise SystemExit(
            "PEXELS_API_KEY and ELEVENLABS_API_KEY must be set (see .env.example)."
        )

    pexels = PexelsClient(pexels_key)
    eleven = ElevenLabsClient(eleven_key, voice_id, model_id=model_id)

    script = load_script(args.script)
    args.workdir.mkdir(parents=True, exist_ok=True)

    segments: list[tuple[Path, Path]] = []
    total = len(script)
    for index, entry in enumerate(script, start=1):
        clip_path = args.workdir / f"clip_{index:02d}.mp4"
        audio_path = args.workdir / f"voice_{index:02d}.mp3"

        print(f"[{index}/{total}] Generating voiceover...")
        eleven.synthesize(entry["text"], audio_path)

        print(f"[{index}/{total}] Fetching Pexels clip for {entry['query']!r}...")
        downloaded = pexels.fetch_clip(
            entry["query"],
            clip_path,
            target_height=args.height,
            orientation=args.orientation,
        )
        if not downloaded:
            raise RuntimeError(f"No Pexels clip found for query: {entry['query']!r}")

        segments.append((clip_path, audio_path))

    print("Assembling final video...")
    build_video(
        segments,
        args.output,
        target_size=(args.width, args.height),
        fps=args.fps,
        background_music=args.music,
    )
    print(f"Done: {args.output}")


if __name__ == "__main__":
    main()
