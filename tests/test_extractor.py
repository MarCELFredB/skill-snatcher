from skill_snatcher.extractor import extract_skill_source


def test_github_url_in_caption():
    caption = "Check out this skill: https://github.com/alice/cool-skill"
    transcript = "Hey everyone welcome to my video about coding."
    result = extract_skill_source(transcript, caption)
    assert result.source_url == "https://github.com/alice/cool-skill"
    assert result.confidence == "high"
    assert result.method == "regex"


def test_github_url_in_transcript():
    caption = ""
    transcript = "So go to https://github.com/bob/my-skill and clone it to get started."
    result = extract_skill_source(transcript, caption)
    assert result.source_url == "https://github.com/bob/my-skill"
    assert result.confidence == "high"
    assert result.method == "regex"


def test_spoken_url_pattern():
    caption = ""
    transcript = "Head over to github dot com slash alice slash my-skill for the source."
    result = extract_skill_source(transcript, caption)
    assert result.source_url == "https://github.com/alice/my-skill"
    assert result.confidence == "medium"


def test_git_clone_command():
    caption = ""
    transcript = "Just run git clone https://github.com/bob/cool-skill.git in your terminal."
    result = extract_skill_source(transcript, caption)
    assert result.source_url == "https://github.com/bob/cool-skill.git"
    assert result.confidence == "high"


def test_raw_skill_md_url():
    caption = "Get it here: https://raw.githubusercontent.com/user/repo/main/SKILL.md"
    transcript = "I built this skill for Claude Code."
    result = extract_skill_source(transcript, caption)
    assert result.source_url is not None
    assert "SKILL.md" in result.source_url


def test_no_match_returns_none():
    caption = "Just a random cooking video."
    transcript = "Today we are making pasta with garlic and olive oil."
    result = extract_skill_source(transcript, caption)
    assert result.source_url is None
    assert result.method == "none"


def test_caption_priority_over_transcript():
    caption = "Link: https://github.com/alice/caption-skill"
    transcript = "Check https://github.com/bob/transcript-skill for more."
    result = extract_skill_source(transcript, caption)
    assert result.source_url == "https://github.com/alice/caption-skill"


def test_skill_name_extraction():
    caption = ""
    transcript = "The skill is called my-awesome-tool and it's at https://github.com/user/my-awesome-tool"
    result = extract_skill_source(transcript, caption)
    assert result.skill_name == "my-awesome-tool"


def test_github_url_with_path():
    caption = "https://github.com/user/repo/tree/main/skills/my-skill"
    transcript = ""
    result = extract_skill_source(transcript, caption)
    assert result.source_url is not None
    assert "github.com/user/repo" in result.source_url
