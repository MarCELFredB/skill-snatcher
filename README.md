# skill-snatcher

Extract and install Claude Code skills from Instagram reels — fully local, fully free.

## How It Works

1. **Download** — Fetches the video audio and caption from an Instagram reel/post using yt-dlp
2. **Transcribe** — Converts speech to text locally using faster-whisper (no API keys needed)
3. **Extract** — Scans the transcript and caption for GitHub URLs and skill references using regex (with optional Ollama fallback)
4. **Install** — Clones the skill repo and installs it into your Claude Code skills directory

## Installation

```bash
# Clone and install
git clone https://github.com/marcelfredb/skill-snatcher.git
cd skill-snatcher
pip install -e .
```

### Prerequisites

- **Python 3.10+**
- **ffmpeg** — Required by yt-dlp for audio extraction. Install via your package manager:
  ```bash
  # macOS
  brew install ffmpeg
  # Ubuntu/Debian
  sudo apt install ffmpeg
  # Windows
  winget install ffmpeg
  ```
- **Git** — For cloning skill repositories

## Usage

```bash
# Grab a skill from an Instagram reel
skill-snatcher grab https://www.instagram.com/reel/ABC123/

# Preview without installing
skill-snatcher grab https://www.instagram.com/reel/ABC123/ --dry-run

# Install to a custom directory
skill-snatcher grab https://www.instagram.com/reel/ABC123/ --skills-dir ./my-skills

# Overwrite an existing skill
skill-snatcher grab https://www.instagram.com/reel/ABC123/ --force

# Verbose output for debugging
skill-snatcher grab https://www.instagram.com/reel/ABC123/ --verbose
```

### Expected Output

```
✓ Downloaded: Cool Claude Skill Tutorial
  Transcription completed in 12.3s
✓ Transcribed (245 words)
✓ Found skill source: https://github.com/user/cool-skill (confidence: high, method: regex)
✓ Skill name: cool-skill
╭─ skill-snatcher ─────────────────────────╮
│ Skill installed successfully!             │
│                                           │
│   Name:   cool-skill                      │
│   Source: https://github.com/user/cool-skill │
│   Path:   /home/user/.claude/skills/cool-skill │
╰───────────────────────────────────────────╯
```

## Options

| Flag | Description |
|------|-------------|
| `--skills-dir PATH` | Custom skills installation directory |
| `--force` | Overwrite existing skills |
| `--dry-run` | Show what would be installed without doing it |
| `--verbose` | Show debug output (transcript, caption) |

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `SKILL_SNATCHER_SKILLS_DIR` | `~/.claude/skills/` | Skills installation directory |
| `SKILL_SNATCHER_WHISPER_MODEL` | `base` | Whisper model size (`tiny`, `base`, `small`, `medium`, `large`) |
| `SKILL_SNATCHER_OLLAMA_URL` | `http://localhost:11434` | Ollama API endpoint |

## Ollama Integration (Optional)

If regex extraction finds no skill references, skill-snatcher can use a local Ollama instance as a fallback. This is entirely optional — the tool works fine without it.

```bash
# Install Ollama (https://ollama.ai)
# Pull the model
ollama pull llama3.2:3b

# skill-snatcher will auto-detect Ollama if running
```

## Troubleshooting

**"No audio file was produced"** — Make sure ffmpeg is installed and on your PATH.

**"This post appears to be private"** — The Instagram post must be public. Private posts require authentication which is not supported.

**"yt-dlp is not installed"** — Run `pip install -e .` to install all dependencies.

**"faster-whisper is not installed"** — Run `pip install -e .` to install all dependencies.

**First run is slow** — The whisper model (~150 MB) downloads automatically on first use. Subsequent runs use the cached model.

## License

MIT
