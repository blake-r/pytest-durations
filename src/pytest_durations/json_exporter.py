"""JSON export for pytest-durations timing data."""
from __future__ import annotations

import json
from collections.abc import Callable
from typing import TYPE_CHECKING

from pytest_durations.types import Category

if TYPE_CHECKING:
    from pytest_durations.typing import CategoryMeasurementsT


def export_json(
    measurements: "CategoryMeasurementsT",
    filename: str,
    format_seconds: Callable[[float], str] | None = None,
) -> None:
    """Export timing measurements to a JSON file.

    :param measurements: Mapping of categories to name → duration list.
    :param filename: Output path or "-" for stdout.
    :param format_seconds: Optional formatter for human-readable durations.
    """
    data: dict[str, dict] = {
        "version": "1.0",
        "categories": {},
    }

    for category, category_measurements in measurements.items():
        category_key = str(category)
        entries = []
        for name, times in category_measurements.items():
            entry: dict = {
                "name": name,
                "calls": len(times),
                "total": sum(times),
                "min": min(times) if times else 0.0,
                "max": max(times) if times else 0.0,
                "med": sorted(times)[len(times) // 2] if times else 0.0,
                "times": times,
            }
            if format_seconds:
                entry["total_hr"] = format_seconds(entry["total"])
                entry["min_hr"] = format_seconds(entry["min"])
                entry["max_hr"] = format_seconds(entry["max"])
                entry["med_hr"] = format_seconds(entry["med"])
            entries.append(entry)
        data["categories"][category_key] = entries

    json_str = json.dumps(data, indent=2, ensure_ascii=False)

    if filename == "-":
        print(json_str)
    else:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(json_str)
