from __future__ import annotations

import sys

import click
from rich.console import Console
from rich.panel import Panel

from . import __version__
from .config import get_skills_dir, get_temp_dir, cleanup_temp_dir, WHISPER_MODEL


console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="skill-snatcher")
def cli():
    """Skill Snatcher - Extract and install Claude Code skills from Instagram reels."""


@cli.command()
@click.argument("url")
@click.option("--skills-dir", type=click.Path(), default=None, help="Custom skills directory.")
@click.option("--force", is_flag=True, help="Overwrite existing skills.")
@click.option("--dry-run", is_flag=True, help="Show what would be installed without installing.")
@click.option("--verbose", is_flag=True, help="Show debug output.")
def grab(url: str, skills_dir: str | None, force: bool, dry_run: bool, verbose: bool):
    """Download an Instagram reel, extract a Claude Code skill reference, and install it."""
    from pathlib import Path
    from .downloader import download, DownloadError
    from .transcriber import transcribe, TranscriptionError
    from .extractor import extract_skill_source
    from .installer import install_skill, InstallError

    skills_path = Path(skills_dir) if skills_dir else get_skills_dir()
    temp_dir = get_temp_dir()

    try:
        # Step 1: Download
        with console.status("[bold blue]Downloading video..."):
            try:
                result = download(url, temp_dir)
            except DownloadError as e:
                console.print(f"[red]Download failed:[/red] {e}")
                sys.exit(1)

        console.print(f"[green]✓[/green] Downloaded: {result.title or 'Untitled'}")
        if verbose and result.caption:
            console.print(f"[dim]Caption: {result.caption[:200]}...[/dim]")

        # Step 2: Transcribe
        with console.status("[bold blue]Transcribing audio..."):
            try:
                transcript = transcribe(result.audio_path, model_size=WHISPER_MODEL)
            except TranscriptionError as e:
                console.print(f"[red]Transcription failed:[/red] {e}")
                sys.exit(1)

        console.print(f"[green]✓[/green] Transcribed ({len(transcript.split())} words)")
        if verbose:
            console.print(f"[dim]Transcript: {transcript[:300]}...[/dim]")

        # Step 3: Extract
        with console.status("[bold blue]Extracting skill reference..."):
            extraction = extract_skill_source(transcript, result.caption)

        if extraction.source_url:
            console.print(
                f"[green]✓[/green] Found skill source: {extraction.source_url} "
                f"[dim](confidence: {extraction.confidence}, method: {extraction.method})[/dim]"
            )
        else:
            console.print(
                Panel(
                    "No skill reference found in the video.\n"
                    "The transcript and caption did not contain a recognizable GitHub URL or skill name.",
                    title="No Skill Found",
                    border_style="yellow",
                )
            )
            sys.exit(1)

        if extraction.skill_name:
            console.print(f"[green]✓[/green] Skill name: {extraction.skill_name}")

        # Step 4: Install
        if dry_run:
            console.print(
                Panel(
                    f"[bold]Would install:[/bold]\n"
                    f"  Source: {extraction.source_url}\n"
                    f"  Name:   {extraction.skill_name or 'derived from URL'}\n"
                    f"  Path:   {skills_path / (extraction.skill_name or 'TBD')}",
                    title="Dry Run",
                    border_style="cyan",
                )
            )
            return

        with console.status("[bold blue]Installing skill..."):
            try:
                install_result = install_skill(
                    source_url=extraction.source_url,
                    skills_dir=skills_path,
                    force=force,
                    skill_name=extraction.skill_name,
                )
            except InstallError as e:
                console.print(f"[red]Installation failed:[/red] {e}")
                sys.exit(1)

        if not install_result.installed:
            console.print(f"[yellow]{install_result.message}[/yellow]")
            sys.exit(1)

        # Summary
        console.print(
            Panel(
                f"[bold green]Skill installed successfully![/bold green]\n\n"
                f"  Name:   {install_result.skill_name}\n"
                f"  Source: {extraction.source_url}\n"
                f"  Path:   {install_result.skill_path}",
                title="skill-snatcher",
                border_style="green",
            )
        )

    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled.[/yellow]")
        sys.exit(130)
    finally:
        cleanup_temp_dir(temp_dir)


@cli.command()
@click.argument("queue_file", type=click.Path())
@click.option("--skills-dir", type=click.Path(), default=None, help="Custom skills directory.")
@click.option("--interval", default=10, help="Seconds between checks (default: 10).")
@click.option("--force", is_flag=True, help="Overwrite existing skills.")
@click.option("--dry-run", is_flag=True, help="Show what would be installed without installing.")
def watch(queue_file: str, skills_dir: str | None, interval: int, force: bool, dry_run: bool):
    """Watch a text file for new Instagram URLs and auto-process them.

    Point QUEUE_FILE at your Google Drive sync'd file, e.g.:

        skill-snatcher watch ~/Google\\ Drive/skill-urls.txt
    """
    from pathlib import Path
    from .watcher import watch as run_watcher

    skills_path = Path(skills_dir) if skills_dir else get_skills_dir()
    run_watcher(
        queue_path=Path(queue_file),
        skills_dir=skills_path,
        interval=interval,
        force=force,
        dry_run=dry_run,
    )
