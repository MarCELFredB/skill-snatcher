from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


class DownloadError(Exception):
    pass


@dataclass
class DownloadResult:
    audio_path: Path
    caption: str
    title: str
    url: str


def download(url: str, output_dir: Path) -> DownloadResult:
    try:
        import yt_dlp
    except ImportError:
        raise DownloadError("yt-dlp is not installed. Run: pip install yt-dlp")

    opts = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "0",
            }
        ],
        "outtmpl": str(output_dir / "%(id)s.%(ext)s"),
        "writeinfojson": True,
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as e:
        msg = str(e)
        if "Private" in msg or "login" in msg.lower():
            raise DownloadError("This post appears to be private or requires login.")
        if "404" in msg or "not found" in msg.lower():
            raise DownloadError("Post not found. Check the URL and try again.")
        raise DownloadError(f"Download failed: {msg}")
    except Exception as e:
        raise DownloadError(f"Download failed: {e}")

    wav_files = list(output_dir.glob("*.wav"))
    if not wav_files:
        raise DownloadError("No audio file was produced. Is ffmpeg installed?")

    audio_path = wav_files[0]

    caption = ""
    title = ""
    info_files = list(output_dir.glob("*.info.json"))
    if info_files:
        try:
            info = json.loads(info_files[0].read_text())
            caption = info.get("description", "") or ""
            title = info.get("title", "") or ""
        except (json.JSONDecodeError, OSError):
            pass

    return DownloadResult(
        audio_path=audio_path,
        caption=caption,
        title=title,
        url=url,
    )
