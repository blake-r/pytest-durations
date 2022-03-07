from pathlib import Path

from poetry.core.pyproject import PyProjectTOML

from pytest_durations.__init__ import __version__


def test_version():
    """Package version should be in sync with project version."""
    pyproject_toml = Path(__file__).parent.parent / "pyproject.toml"
    project = PyProjectTOML(pyproject_toml).poetry_config
    assert __version__ == project["version"]
