from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .config import OLLAMA_URL

# Compiled regex patterns in priority order
GITHUB_URL_RE = re.compile(
    r"https?://github\.com/[\w\-\.]+/[\w\-\.]+(?:/[\w\-\./]*)?",
    re.IGNORECASE,
)
GITHUB_GIST_RE = re.compile(
    r"https?://gist\.github\.com/[\w\-]+/[\w]+",
    re.IGNORECASE,
)
GIT_CLONE_RE = re.compile(
    r"git\s+clone\s+(https?://\S+|git@\S+)",
    re.IGNORECASE,
)
SPOKEN_URL_RE = re.compile(
    r"github\s*(?:dot|\.)\s*com\s*(?:slash|/)\s*([\w\-]+)\s*(?:slash|/)\s*([\w\-]+)",
    re.IGNORECASE,
)
RAW_URL_RE = re.compile(
    r"https?://\S+(?:SKILL\.md|/skills?/)",
    re.IGNORECASE,
)
SKILL_NAME_RE = re.compile(
    r"(?:skill|command)\s+(?:is\s+)?(?:called|named)\s+[\"']?([\w\-]+)[\"']?",
    re.IGNORECASE,
)


@dataclass
class ExtractionResult:
    source_url: str | None
    skill_name: str | None
    confidence: str
    method: str


def _clean_github_url(url: str) -> str:
    return url.rstrip("/.,;:!?)\"'")


def _extract_skill_name(text: str, url: str | None) -> str | None:
    match = SKILL_NAME_RE.search(text)
    if match:
        return match.group(1)
    if url and "github.com" in url:
        parts = url.rstrip("/").split("/")
        if len(parts) >= 2:
            return parts[-1].removesuffix(".git")
    return None


def _regex_search(text: str) -> tuple[str | None, str]:
    match = GITHUB_URL_RE.search(text)
    if match:
        return _clean_github_url(match.group(0)), "high"

    match = GITHUB_GIST_RE.search(text)
    if match:
        return _clean_github_url(match.group(0)), "high"

    match = GIT_CLONE_RE.search(text)
    if match:
        return _clean_github_url(match.group(1)), "high"

    match = RAW_URL_RE.search(text)
    if match:
        return _clean_github_url(match.group(0)), "high"

    match = SPOKEN_URL_RE.search(text)
    if match:
        user, repo = match.group(1), match.group(2)
        return f"https://github.com/{user}/{repo}", "medium"

    return None, "low"


def _check_ollama_available() -> bool:
    try:
        import requests

        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        return resp.status_code == 200
    except Exception:
        return False


def _query_ollama(transcript: str, caption: str) -> tuple[str | None, str | None]:
    try:
        import requests

        prompt = (
            "Extract the Claude Code skill source from this transcript. "
            'Return ONLY a JSON object with "url" and "name" fields. '
            "If you can't find either, set them to null.\n\n"
            f"Transcript:\n{transcript}\n\n"
            f"Caption:\n{caption}"
        )
        resp = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": "llama3.2:3b", "prompt": prompt, "stream": False},
            timeout=30,
        )
        if resp.status_code != 200:
            return None, None
        data = resp.json()
        response_text = data.get("response", "")
        # Try to parse JSON from the response
        json_match = re.search(r"\{[^}]+\}", response_text)
        if json_match:
            parsed = json.loads(json_match.group(0))
            return parsed.get("url"), parsed.get("name")
    except Exception:
        pass
    return None, None


def extract_skill_source(transcript: str, caption: str) -> ExtractionResult:
    combined_text = f"{caption}\n{transcript}"

    # Search caption first (higher confidence)
    if caption:
        url, confidence = _regex_search(caption)
        if url:
            skill_name = _extract_skill_name(combined_text, url)
            return ExtractionResult(
                source_url=url,
                skill_name=skill_name,
                confidence=confidence,
                method="regex",
            )

    # Search transcript
    url, confidence = _regex_search(transcript)
    if url:
        skill_name = _extract_skill_name(combined_text, url)
        return ExtractionResult(
            source_url=url,
            skill_name=skill_name,
            confidence=confidence,
            method="regex",
        )

    # Ollama fallback
    if _check_ollama_available():
        url, name = _query_ollama(transcript, caption)
        if url:
            return ExtractionResult(
                source_url=url,
                skill_name=name or _extract_skill_name(combined_text, url),
                confidence="low",
                method="ollama",
            )

    # Nothing found
    skill_name = _extract_skill_name(combined_text, None)
    return ExtractionResult(
        source_url=None,
        skill_name=skill_name,
        confidence="low",
        method="none",
    )
