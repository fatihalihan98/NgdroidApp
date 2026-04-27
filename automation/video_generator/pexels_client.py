"""Pexels stock video search and download."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import requests

PEXELS_VIDEO_SEARCH_URL = "https://api.pexels.com/videos/search"


class PexelsClient:
    def __init__(self, api_key: str) -> None:
        self.session = requests.Session()
        self.session.headers.update({"Authorization": api_key})

    def search_videos(
        self,
        query: str,
        *,
        per_page: int = 10,
        orientation: str = "landscape",
        min_duration: int = 5,
    ) -> list[dict]:
        params = {
            "query": query,
            "per_page": per_page,
            "orientation": orientation,
            "min_duration": min_duration,
        }
        response = self.session.get(PEXELS_VIDEO_SEARCH_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json().get("videos", [])

    @staticmethod
    def pick_best_file(video: dict, *, target_height: int = 1080) -> dict | None:
        files: Iterable[dict] = (
            f for f in video.get("video_files", []) if f.get("file_type") == "video/mp4"
        )
        ranked = sorted(files, key=lambda f: abs((f.get("height") or 0) - target_height))
        return ranked[0] if ranked else None

    def download(self, url: str, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with self.session.get(url, stream=True, timeout=180) as response:
            response.raise_for_status()
            with open(output_path, "wb") as fh:
                for chunk in response.iter_content(chunk_size=1 << 15):
                    if chunk:
                        fh.write(chunk)
        return output_path

    def fetch_clip(
        self,
        query: str,
        output_path: Path,
        *,
        target_height: int = 1080,
        orientation: str = "landscape",
        min_duration: int = 5,
    ) -> Path | None:
        videos = self.search_videos(
            query, orientation=orientation, min_duration=min_duration
        )
        for video in videos:
            file = self.pick_best_file(video, target_height=target_height)
            if file and file.get("link"):
                return self.download(file["link"], output_path)
        return None
