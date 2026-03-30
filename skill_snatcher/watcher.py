from __future__ import annotations

import time
from pathlib import Path

from rich.console import Console

console = Console()

# Marker appended to processed URLs so we don't reprocess them
DONE_MARKER = " [done]"
ERROR_MARKER = " [error]"


def _find_queue_file(queue_path: Path) -> Path:
    """Resolve the queue file path, creating it if needed."""
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    if not queue_path.exists():
        queue_path.write_text("")
    return queue_path


def _get_pending_urls(queue_path: Path) -> list[tuple[int, str]]:
    """Return list of (line_index, url) for unprocessed lines."""
    lines = queue_path.read_text().splitlines()
    pending = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.endswith(DONE_MARKER) and not stripped.endswith(ERROR_MARKER):
            pending.append((i, stripped))
    return pending


def _mark_line(queue_path: Path, line_index: int, marker: str) -> None:
    """Append a marker to a specific line in the queue file."""
    lines = queue_path.read_text().splitlines()
    if line_index < len(lines):
        lines[line_index] = lines[line_index].rstrip() + marker
    queue_path.write_text("\n".join(lines) + "\n")


def watch(
    queue_path: Path,
    skills_dir: Path,
    interval: int = 10,
    force: bool = False,
    dry_run: bool = False,
) -> None:
    """Watch a queue file for new Instagram URLs and process them."""
    from .downloader import download, DownloadError
    from .transcriber import transcribe, TranscriptionError
    from .extractor import extract_skill_source
    from .installer import install_skill, InstallError
    from .config import get_temp_dir, cleanup_temp_dir, WHISPER_MODEL

    queue_file = _find_queue_file(queue_path)
    console.print(f"[bold green]Watching:[/bold green] {queue_file}")
    console.print(f"[dim]Checking every {interval}s. Press Ctrl+C to stop.[/dim]\n")

    try:
        while True:
            pending = _get_pending_urls(queue_file)

            for line_index, url in pending:
                console.rule(f"[bold blue]Processing: {url}")
                temp_dir = get_temp_dir()

                try:
                    # Download
                    with console.status("[bold blue]Downloading..."):
                        result = download(url, temp_dir)
                    console.print(f"[green]✓[/green] Downloaded: {result.title or 'Untitled'}")

                    # Transcribe
                    with console.status("[bold blue]Transcribing..."):
                        transcript = transcribe(result.audio_path, model_size=WHISPER_MODEL)
                    console.print(f"[green]✓[/green] Transcribed ({len(transcript.split())} words)")

                    # Extract
                    extraction = extract_skill_source(transcript, result.caption)
                    if not extraction.source_url:
                        console.print("[yellow]No skill reference found. Skipping.[/yellow]")
                        _mark_line(queue_file, line_index, ERROR_MARKER)
                        continue

                    console.print(f"[green]✓[/green] Found: {extraction.source_url}")

                    # Install
                    if dry_run:
                        console.print(f"[cyan]Dry run — would install {extraction.skill_name}[/cyan]")
                    else:
                        install_result = install_skill(
                            source_url=extraction.source_url,
                            skills_dir=skills_dir,
                            force=force,
                            skill_name=extraction.skill_name,
                        )
                        if install_result.installed:
                            console.print(f"[green]✓[/green] Installed: {install_result.skill_path}")
                        else:
                            console.print(f"[yellow]{install_result.message}[/yellow]")

                    _mark_line(queue_file, line_index, DONE_MARKER)

                except (DownloadError, TranscriptionError, InstallError) as e:
                    console.print(f"[red]Error:[/red] {e}")
                    _mark_line(queue_file, line_index, ERROR_MARKER)
                except Exception as e:
                    console.print(f"[red]Unexpected error:[/red] {e}")
                    _mark_line(queue_file, line_index, ERROR_MARKER)
                finally:
                    cleanup_temp_dir(temp_dir)

            time.sleep(interval)

    except KeyboardInterrupt:
        console.print("\n[yellow]Watcher stopped.[/yellow]")
