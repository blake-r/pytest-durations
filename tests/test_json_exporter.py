"""Tests for JSON exporter."""
import json
import tempfile
from pathlib import Path

import pytest

from pytest_durations.json_exporter import export_json
from pytest_durations.types import Category


SAMPLE_MEASUREMENTS = {
    Category.TEST_CALL: {
        "test_foo": [0.001, 0.002],
    },
}


def test_export_json_basic():
    """export_json should write valid JSON with all expected fields."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        path = f.name
    try:
        export_json(measurements=SAMPLE_MEASUREMENTS, filename=path, format_seconds=None)
        data = json.loads(Path(path).read_text())
        assert data["version"] == "1.0"
        assert "test call" in data["categories"]
        entry = data["categories"]["test call"][0]
        assert entry["name"] == "test_foo"
        assert entry["calls"] == 2
        assert entry["total"] == 0.003
        assert entry["min"] == 0.001
        assert entry["max"] == 0.002
        assert "total_hr" not in entry
    finally:
        Path(path).unlink(missing_ok=True)


def test_export_json_with_format():
    """export_json should include human-readable fields when format_seconds is provided."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        path = f.name
    try:
        export_json(measurements=SAMPLE_MEASUREMENTS, filename=path, format_seconds=lambda s: f"{s:.3f}s")
        data = json.loads(Path(path).read_text())
        entry = data["categories"]["test call"][0]
        assert entry["total_hr"] == "0.003s"
        assert entry["min_hr"] == "0.001s"
    finally:
        Path(path).unlink(missing_ok=True)


def test_export_json_stdout(capsys):
    """export_json with filename='-' should print to stdout."""
    export_json(measurements=SAMPLE_MEASUREMENTS, filename="-", format_seconds=None)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["version"] == "1.0"


def test_export_json_empty_measurements():
    """export_json should handle empty measurements gracefully."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        path = f.name
    try:
        export_json(measurements={}, filename=path, format_seconds=None)
        data = json.loads(Path(path).read_text())
        assert data["categories"] == {}
    finally:
        Path(path).unlink(missing_ok=True)
