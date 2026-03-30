import os
import shutil
import tempfile
from pathlib import Path


def get_skills_dir() -> Path:
    return Path(os.environ.get("SKILL_SNATCHER_SKILLS_DIR", Path.home() / ".claude" / "skills"))


def get_temp_dir() -> Path:
    return Path(tempfile.mkdtemp(prefix="skill-snatcher-"))


def cleanup_temp_dir(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)


OLLAMA_URL = os.environ.get("SKILL_SNATCHER_OLLAMA_URL", "http://localhost:11434")
WHISPER_MODEL = os.environ.get("SKILL_SNATCHER_WHISPER_MODEL", "base")
