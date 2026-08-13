"""Baseline comparison for detecting test slowdowns across runs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_durations.typing import CategoryMeasurementsT


def load_baseline(path: str | Path) -> dict[str, dict[str, float]] | None:
    """Load a baseline JSON file and return category → name → total mapping.

    :param path: Path to the baseline JSON file.
    :return: Baseline data or None if the file does not exist.
    """
    filepath = Path(path)
    if not filepath.exists():
        return None
    with filepath.open("r", encoding="utf-8") as f:
        data = json.load(f)
    # Flatten: category → name → total
    baseline: dict[str, dict[str, float]] = {}
    for category_str, entries in data.get("categories", {}).items():
        baseline[category_str] = {entry["name"]: entry["total"] for entry in entries}
    return baseline


def compare_to_baseline(
    measurements: "CategoryMeasurementsT",
    baseline: dict[str, dict[str, float]],
    threshold: float = 0.1,
) -> list[dict]:
    """Compare current measurements against a baseline.

    :param measurements: Current timing measurements.
    :param baseline: Baseline data from a previous run.
    :param threshold: Minimum relative slowdown to report (e.g., 0.1 = 10%).
    :return: List of regressions with category, name, baseline, current, and delta.
    """
    regressions: list[dict] = []
    for category, category_measurements in measurements.items():
        category_str = str(category)
        baseline_entries = baseline.get(category_str, {})
        for name, times in category_measurements.items():
            if not times:
                continue
            current = sum(times)
            previous = baseline_entries.get(name)
            if previous is None:
                continue  # New test, no baseline
            if previous == 0:
                continue  # Avoid division by zero
            delta = (current - previous) / previous
            if delta > threshold:
                regressions.append({
                    "category": category_str,
                    "name": name,
                    "baseline": previous,
                    "current": current,
                    "delta": delta,
                })
    regressions.sort(key=lambda r: r["delta"], reverse=True)
    return regressions


def save_baseline(measurements: "CategoryMeasurementsT", path: str | Path) -> None:
    """Save current measurements as a baseline JSON file.

    :param measurements: Current timing measurements.
    :param path: Output path for the baseline file.
    """
    data: dict[str, dict] = {"version": "1.0", "categories": {}}
    for category, category_measurements in measurements.items():
        category_str = str(category)
        entries = []
        for name, times in category_measurements.items():
            entries.append({
                "name": name,
                "total": sum(times),
                "calls": len(times),
            })
        data["categories"][category_str] = entries

    filepath = Path(path)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with filepath.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def format_github_annotation(regression: dict) -> str:
    """Format a regression as a GitHub Actions workflow command.

    See: https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#setting-a-notice-message
    """
    return (
        f"::warning title=Duration Regression::{regression['category']} '{regression['name']}' "
        f"slowed by {regression['delta']*100:.1f}% "
        f"({regression['baseline']:.3f}s → {regression['current']:.3f}s)"
    )
