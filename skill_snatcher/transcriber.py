from __future__ import annotations

import time
from pathlib import Path
from typing import Any


class TranscriptionError(Exception):
    pass


_model_cache: dict[str, Any] = {}


def transcribe(audio_path: Path, model_size: str = "base") -> str:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise TranscriptionError(
            "faster-whisper is not installed. Run: pip install faster-whisper"
        )

    if model_size not in _model_cache:
        _model_cache[model_size] = WhisperModel(
            model_size, device="cpu", compute_type="int8"
        )

    model = _model_cache[model_size]
    start = time.time()

    try:
        segments, _info = model.transcribe(str(audio_path), beam_size=5)
        transcript = " ".join(segment.text for segment in segments).strip()
    except Exception as e:
        raise TranscriptionError(f"Transcription failed: {e}")

    elapsed = time.time() - start

    from rich.console import Console

    Console().print(f"[dim]Transcription completed in {elapsed:.1f}s[/dim]")

    if not transcript:
        raise TranscriptionError("Transcription produced no text.")

    return transcript
