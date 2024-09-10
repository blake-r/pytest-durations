from pathlib import Path

from poetry.core.pyproject.toml import PyProjectTOML

from pytest_durations.__init__ import __version__

_REPOSITORY_ROOT = Path(__file__).parent.parent


def test_pyproject_version():
    """Package version should be in sync with project version."""
    pyproject_toml = _REPOSITORY_ROOT / "pyproject.toml"
    project = PyProjectTOML(pyproject_toml).poetry_config
    assert __version__ == project["version"]


def test_changelog_version():
    """Readme file should contain a changelog for the version."""
    changelog_markdown = "## Change Log"
    version_markdown = f"### {__version__} ("
    version_found = False
    with open(_REPOSITORY_ROOT / "README.md", "rt") as fp:
        changelog_found = False
        for line in fp:
            if not changelog_found:
                if line.startswith(changelog_markdown):
                    changelog_found = True
                continue
            if line.startswith(version_markdown):
                version_found = True
                break
    assert version_found is True
