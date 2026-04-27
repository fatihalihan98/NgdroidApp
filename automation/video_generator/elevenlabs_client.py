"""ElevenLabs text-to-speech client."""
from __future__ import annotations

from pathlib import Path

import requests

ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"


class ElevenLabsClient:
    def __init__(
        self,
        api_key: str,
        voice_id: str,
        model_id: str = "eleven_multilingual_v2",
        stability: float = 0.5,
        similarity_boost: float = 0.75,
    ) -> None:
        self.api_key = api_key
        self.voice_id = voice_id
        self.model_id = model_id
        self.stability = stability
        self.similarity_boost = similarity_boost

    def synthesize(self, text: str, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        url = ELEVENLABS_TTS_URL.format(voice_id=self.voice_id)
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        payload = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": self.stability,
                "similarity_boost": self.similarity_boost,
            },
        }
        response = requests.post(url, headers=headers, json=payload, timeout=180)
        response.raise_for_status()
        output_path.write_bytes(response.content)
        return output_path
