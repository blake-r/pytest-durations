# Copyright (c) 2022 Oleg Blednov

"""JSON export for pytest-durations timing data."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from pytest_durations.reporting import TimeValuesT

if TYPE_CHECKING:
    from pytest_durations.typing import CategoryMeasurementsT


def build_json_data(measurements: CategoryMeasurementsT) -> dict:
    """Build the export document shared by JSON export and baseline files."""
    data: dict[str, dict] = {
        "version": "1.0",
        "categories": {},
    }

    for category, category_measurements in measurements.items():
        category_key = str(category)
        entries = []
        for name, times in category_measurements.items():
            stats = TimeValuesT.from_times(name=name, times=times)
            entry: dict = {
                "name": stats.name,
                "calls": stats.calls,
                "total": stats.sum,
                "min": stats.min,
                "med": stats.med,
                "p90": stats.p90,
                "p95": stats.p95,
                "p99": stats.p99,
                "max": stats.max,
            }
            entries.append(entry)
        data["categories"][category_key] = entries

    return data


def export_json(measurements: CategoryMeasurementsT, filename: str) -> None:
    """Export timing measurements to a JSON file.

    :param measurements: Mapping of categories to name → duration list.
    :param filename: Output path or "-" for stdout.
    """
    json_str = json.dumps(build_json_data(measurements), indent=2, ensure_ascii=False)

    if filename == "-":
        sys.stdout.write(json_str + "\n")
    else:
        Path(filename).write_text(json_str, encoding="utf-8")
