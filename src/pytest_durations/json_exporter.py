"""JSON export for pytest-durations timing data."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_durations.typing import CategoryMeasurementsT


def export_json(measurements: CategoryMeasurementsT, filename: str) -> None:
    """Export timing measurements to a JSON file.

    :param measurements: Mapping of categories to name → duration list.
    :param filename: Output path or "-" for stdout.
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
            }
            entries.append(entry)
        data["categories"][category_key] = entries

    json_str = json.dumps(data, indent=2, ensure_ascii=False)

    if filename == "-":
        sys.stdout.write(json_str + "\n")
    else:
        Path(filename).write_text(json_str, encoding="utf-8")
