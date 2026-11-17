# Copyright (c) 2022 Oleg Blednov

"""Baseline comparison: detect test duration regressions across runs."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING, NamedTuple

from pytest_durations.json_exporter import build_json_data
from pytest_durations.reporting import format_seconds_clock

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from pytest_durations.typing import CategoryMeasurementsT

BASELINE_VERSION = "1.0"
DEFAULT_BASELINE_FILENAME = ".pytest_durations_baseline.json"
CHANGE_THRESHOLD_PCT = 20.0
MIN_BASELINE_CALLS = 3

SUM_METRIC_FIELD = "sum"
SUM_METRIC_ENTRY_KEY = "total"


class BaselineChangeT(NamedTuple):
    """A single test duration change compared to the baseline.

    ``prev`` and ``change`` are ``None`` for tests missing from the baseline
    (new tests). ``change`` is a signed percentage.
    """

    category: str
    name: str
    prev: float | None
    now: float
    change: float | None


def load_baseline(path: Path) -> tuple[dict | None, str | None]:
    """Load a baseline file.

    :param path: Baseline file path.
    :return: ``(baseline, warning)``. ``(None, None)`` if the file does not exist;
             ``(None, warning)`` if the file is unreadable or has an unsupported version.
    """
    if not path.exists():
        return None, None
    try:
        baseline = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, f"could not read baseline {path}: {exc}"
    if not isinstance(baseline, dict) or baseline.get("version") != BASELINE_VERSION:
        return None, f"unsupported baseline format in {path}; expected version {BASELINE_VERSION!r}"
    return baseline, None


def build_baseline(measurements: CategoryMeasurementsT) -> dict:
    """Build the baseline document from the current measurements.

    Uses the same document shape as the ``--pytest-durations-json`` export.
    """
    return build_json_data(measurements)


def save_baseline(baseline: dict, path: Path) -> None:
    """Write the baseline document to a file, replacing any previous content."""
    path.write_text(json.dumps(baseline, indent=2, ensure_ascii=False), encoding="utf-8")


def _entry_metric(entry: dict, metric: str) -> float:
    """Resolve a TimeValuesT-style metric name against a baseline entry."""
    key = SUM_METRIC_ENTRY_KEY if metric == SUM_METRIC_FIELD else metric
    return float(entry[key])


def compare_baseline(old: dict, new: dict, *, metric: str) -> list[BaselineChangeT]:
    """Compare a fresh baseline document against the previous one.

    :param old: Previous baseline document (as produced by :func:`build_baseline`).
    :param new: Fresh baseline document.
    :param metric: ``TimeValuesT`` field name to compare by (e.g. ``"sum"``, ``"med"``).
    :return: Changes above the significance threshold, regressions first.
    """
    old_index = {
        (category, entry["name"]): entry
        for category, entries in old.get("categories", {}).items()
        for entry in entries
    }

    changes = []
    for category, entries in new.get("categories", {}).items():
        for entry in entries:
            key = (category, entry["name"])
            prev_entry = old_index.get(key)
            if prev_entry is None:
                changes.append(BaselineChangeT(category, entry["name"], None, _entry_metric(entry, metric), None))
                continue
            if prev_entry.get("calls", 0) < MIN_BASELINE_CALLS:
                continue
            prev = _entry_metric(prev_entry, metric)
            if prev == 0:
                continue
            now = _entry_metric(entry, metric)
            change = (now - prev) / prev * 100
            if abs(change) < CHANGE_THRESHOLD_PCT:
                continue
            changes.append(BaselineChangeT(category, entry["name"], prev, now, change))

    return sorted(changes, key=lambda c: (c.change is None, -(c.change or 0.0)))


def render_comparison(
    changes: list[BaselineChangeT],
    *,
    metric_label: str,
    format_seconds: Callable[[float], str],
) -> list[str]:
    """Render the comparison as aligned table rows (without the separator line).

    New tests (no baseline entry) are not rendered.
    """
    rendered = [
        (f"{change:+.1f}%", name, format_seconds(prev), format_seconds(now))
        for category, name, prev, now, change in changes
        if change is not None and prev is not None
    ]
    header = ("change", "name", "prev", "now")
    rows = [header, *rendered]
    widths = [max(len(row[idx]) for row in rows) for idx in range(len(header))]
    return [
        " ".join(
            f"{value:{'<' if (row_idx == 0 or col_idx == 1) else '>'}{width}}"
            for col_idx, (value, width) in enumerate(zip(row, widths, strict=True))
        )
        for row_idx, row in enumerate(rows)
    ]


def github_escape_message(message: str) -> str:
    """Escape a workflow command message per the GitHub Actions specification."""
    return message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def github_escape_property(value: str) -> str:
    """Escape a workflow command property value per the GitHub Actions specification."""
    return github_escape_message(value).replace(":", "%3A").replace(",", "%2C")


def github_warning_command(change: BaselineChangeT, *, file: str, line: int | None) -> str:
    """Build a ``::warning`` workflow command for a duration regression."""
    message = (
        f"{change.name} slowed by {change.change:+.1f}%"
        f" (prev {format_seconds_clock(change.prev)}, now {format_seconds_clock(change.now)})"
    )
    location = f"file={github_escape_property(file)}"
    if line is not None:
        location += f",line={line}"
    return f"::warning {location}::{github_escape_message(message)}"
