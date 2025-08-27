#!/usr/bin/env python3
"""Ensure version is synchronized between across the project."""
import logging
import re
from pathlib import Path

PYPROJECT_TOML_PATH = Path("pyproject.toml")
INIT_PY_PATH = Path("src/pytest_durations/__init__.py")
README_MD_PATH = Path("README.md")

log = logging.getLogger("check_version")


def main() -> None:
    """Entry point. Checks version consistency across project files."""
    errors = []

    try:
        pyproject_version = get_pyproject_version()
    except Exception as e:   # noqa: BLE001
        errors.append(f"Error getting pyproject version: {e}")
        pyproject_version = None

    try:
        project_version = get_project_version()
    except Exception as e:   # noqa: BLE001
        errors.append(f"Error getting project (__init__.py) version: {e}")
        project_version = None

    try:
        readme_version = get_readme_version()
    except Exception as e:   # noqa: BLE001
        errors.append(f"Error getting README version: {e}")
        readme_version = None

    if errors:
        for error in errors:
            log.error(error)
        msg = "Version check failed due to errors."
        raise SystemExit(msg)

    # Check synchronization
    if not (pyproject_version == project_version == readme_version):
        msg = (
            f"Version mismatch detected!\n"
            f"  Pyproject: {pyproject_version}\n"
            f"  Project:   {project_version}\n"
            f"  Readme:    {readme_version}\n"
            f"Versions are not synchronized."
        )
        raise SystemExit(msg)

    log.info("All versions are synchronized to %s", project_version)


def get_pyproject_version() -> str:
    """Extract the version from pyproject.toml."""
    text = PYPROJECT_TOML_PATH.read_text()
    # Regex to find version = "x.x.x"
    match = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
    if not match:
        msg = "version string not found in pyproject.toml"
        raise ValueError(msg)
    return match.group(1)


def get_project_version() -> str:
    """Extract the __version__ string from __init__.py using regex."""
    text = INIT_PY_PATH.read_text()
    # Regex to find __version__ = "x.x.x"
    match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
    if not match:
        msg = "__version__ string not found in __init__.py"
        raise ValueError(msg)
    return match.group(1)


def get_readme_version() -> str:
    """Extract the latest version from the Change Log in README.md."""
    text = README_MD_PATH.read_text()
    # Adjust regex if needed for exact format and line endings
    # This pattern looks for the first version number after "## Change Log\n### "
    pat = re.compile(r"## Change Log\s+### (\d+\.\d+\.\d+)")
    match = pat.search(text)
    if not match:
        msg = "Version pattern not found in README.md Change Log"
        raise ValueError(msg)
    return match.group(1)


if __name__ == "__main__":
    main()
