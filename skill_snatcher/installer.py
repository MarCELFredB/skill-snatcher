from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import requests

from .config import get_temp_dir, cleanup_temp_dir


class InstallError(Exception):
    pass


@dataclass
class InstallResult:
    installed: bool
    skill_path: Path | None
    skill_name: str
    message: str


def _derive_skill_name(source_url: str) -> str:
    name = source_url.rstrip("/").split("/")[-1]
    return name.removesuffix(".git").removesuffix(".md")


def _is_raw_url(url: str) -> bool:
    return url.endswith(".md") or "raw.githubusercontent.com" in url


def install_skill(
    source_url: str,
    skills_dir: Path,
    force: bool = False,
    skill_name: str | None = None,
) -> InstallResult:
    skill_name = skill_name or _derive_skill_name(source_url)
    target_dir = skills_dir / skill_name

    if target_dir.exists() and not force:
        return InstallResult(
            installed=False,
            skill_path=target_dir,
            skill_name=skill_name,
            message=f"Skill '{skill_name}' already exists at {target_dir}. Use --force to overwrite.",
        )

    if target_dir.exists() and force:
        shutil.rmtree(target_dir)

    skills_dir.mkdir(parents=True, exist_ok=True)

    if _is_raw_url(source_url):
        return _install_from_raw_url(source_url, target_dir, skill_name)

    return _install_from_git(source_url, target_dir, skill_name)


def _install_from_git(
    source_url: str, target_dir: Path, skill_name: str
) -> InstallResult:
    tmp = get_temp_dir()
    clone_dir = tmp / "repo"

    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", source_url, str(clone_dir)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            raise InstallError(f"git clone failed: {result.stderr.strip()}")

        # Search for SKILL.md
        skill_files = sorted(
            clone_dir.rglob("SKILL.md"),
            key=lambda p: len(p.parts),
        )

        if skill_files:
            skill_src = skill_files[0].parent
        else:
            skill_src = clone_dir

        # Copy to target, excluding .git
        shutil.copytree(
            skill_src,
            target_dir,
            ignore=shutil.ignore_patterns(".git"),
        )

        return InstallResult(
            installed=True,
            skill_path=target_dir,
            skill_name=skill_name,
            message=f"Skill '{skill_name}' installed to {target_dir}",
        )
    except subprocess.TimeoutExpired:
        raise InstallError("git clone timed out after 60 seconds.")
    except InstallError:
        raise
    except Exception as e:
        raise InstallError(f"Installation failed: {e}")
    finally:
        cleanup_temp_dir(tmp)


def _install_from_raw_url(
    source_url: str, target_dir: Path, skill_name: str
) -> InstallResult:
    try:
        resp = requests.get(source_url, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        raise InstallError(f"Failed to download {source_url}: {e}")

    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "SKILL.md").write_text(resp.text)

    return InstallResult(
        installed=True,
        skill_path=target_dir,
        skill_name=skill_name,
        message=f"Skill '{skill_name}' installed to {target_dir}",
    )
