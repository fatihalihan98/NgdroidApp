"""Combine downloaded clips and TTS audio into a single video."""
from __future__ import annotations

from pathlib import Path

from moviepy.editor import (
    AudioFileClip,
    CompositeAudioClip,
    VideoFileClip,
    concatenate_videoclips,
)


def _fit_to_size(clip: VideoFileClip, target_size: tuple[int, int]) -> VideoFileClip:
    target_w, target_h = target_size
    target_ratio = target_w / target_h
    clip_ratio = clip.w / clip.h

    if abs(clip_ratio - target_ratio) < 1e-3:
        return clip.resize(target_size)

    if clip_ratio > target_ratio:
        new_w = int(clip.h * target_ratio)
        x_center = clip.w / 2
        clip = clip.crop(x1=x_center - new_w / 2, x2=x_center + new_w / 2)
    else:
        new_h = int(clip.w / target_ratio)
        y_center = clip.h / 2
        clip = clip.crop(y1=y_center - new_h / 2, y2=y_center + new_h / 2)

    return clip.resize(target_size)


def build_segment(
    clip_path: Path,
    audio_path: Path,
    *,
    target_size: tuple[int, int] = (1920, 1080),
):
    audio = AudioFileClip(str(audio_path))
    video = VideoFileClip(str(clip_path)).set_audio(None)

    if video.duration < audio.duration:
        loops = int(audio.duration // video.duration) + 1
        video = concatenate_videoclips([video] * loops)

    video = video.subclip(0, audio.duration)
    video = _fit_to_size(video, target_size)
    return video.set_audio(audio)


def build_video(
    segments: list[tuple[Path, Path]],
    output_path: Path,
    *,
    target_size: tuple[int, int] = (1920, 1080),
    fps: int = 30,
    background_music: Path | None = None,
    music_volume: float = 0.12,
) -> Path:
    clips = [build_segment(clip, audio, target_size=target_size) for clip, audio in segments]
    final = concatenate_videoclips(clips, method="compose")

    if background_music is not None:
        music = (
            AudioFileClip(str(background_music))
            .volumex(music_volume)
            .subclip(0, final.duration)
        )
        final = final.set_audio(CompositeAudioClip([final.audio, music]))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    final.write_videofile(
        str(output_path),
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        threads=4,
    )
    return output_path
