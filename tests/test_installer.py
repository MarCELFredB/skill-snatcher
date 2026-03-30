from pathlib import Path
from unittest.mock import patch, MagicMock

from skill_snatcher.installer import install_skill, _derive_skill_name


def test_skill_name_from_github_url():
    assert _derive_skill_name("https://github.com/user/my-skill") == "my-skill"
    assert _derive_skill_name("https://github.com/user/my-skill.git") == "my-skill"
    assert _derive_skill_name("https://github.com/user/repo/") == "repo"


def test_install_no_overwrite(tmp_path):
    skills_dir = tmp_path / "skills"
    existing = skills_dir / "my-skill"
    existing.mkdir(parents=True)
    (existing / "SKILL.md").write_text("existing")

    result = install_skill(
        source_url="https://github.com/user/my-skill",
        skills_dir=skills_dir,
        force=False,
    )
    assert not result.installed
    assert "--force" in result.message


def test_install_force_overwrite(tmp_path):
    skills_dir = tmp_path / "skills"
    existing = skills_dir / "my-skill"
    existing.mkdir(parents=True)
    (existing / "SKILL.md").write_text("old content")

    clone_dir_holder = {}

    def mock_run(cmd, **kwargs):
        clone_dir = Path(cmd[-1])
        clone_dir_holder["dir"] = clone_dir
        clone_dir.mkdir(parents=True, exist_ok=True)
        (clone_dir / "SKILL.md").write_text("new content")
        mock_result = MagicMock()
        mock_result.returncode = 0
        return mock_result

    with patch("skill_snatcher.installer.subprocess.run", side_effect=mock_run):
        result = install_skill(
            source_url="https://github.com/user/my-skill",
            skills_dir=skills_dir,
            force=True,
        )

    assert result.installed
    assert (skills_dir / "my-skill" / "SKILL.md").read_text() == "new content"


def test_install_from_github_with_skill_md(tmp_path):
    skills_dir = tmp_path / "skills"

    def mock_run(cmd, **kwargs):
        clone_dir = Path(cmd[-1])
        clone_dir.mkdir(parents=True, exist_ok=True)
        subdir = clone_dir / "my-skill"
        subdir.mkdir()
        (subdir / "SKILL.md").write_text("# My Skill")
        (subdir / "helper.py").write_text("print('hello')")
        mock_result = MagicMock()
        mock_result.returncode = 0
        return mock_result

    with patch("skill_snatcher.installer.subprocess.run", side_effect=mock_run):
        result = install_skill(
            source_url="https://github.com/user/my-skill",
            skills_dir=skills_dir,
        )

    assert result.installed
    assert (skills_dir / "my-skill" / "SKILL.md").exists()
    assert (skills_dir / "my-skill" / "helper.py").exists()


def test_install_from_raw_url(tmp_path):
    skills_dir = tmp_path / "skills"
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = "# My Skill\nDo something cool."
    mock_resp.raise_for_status = MagicMock()

    with patch("skill_snatcher.installer.requests.get", return_value=mock_resp):
        result = install_skill(
            source_url="https://raw.githubusercontent.com/user/repo/main/SKILL.md",
            skills_dir=skills_dir,
            skill_name="my-raw-skill",
        )

    assert result.installed
    content = (skills_dir / "my-raw-skill" / "SKILL.md").read_text()
    assert "Do something cool" in content
