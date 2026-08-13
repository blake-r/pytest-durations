"""Tests for JSON exporter."""
import json
import tempfile
from pathlib import Path

from pytest_durations.json_exporter import export_json
from pytest_durations.types import Category


SAMPLE_MEASUREMENTS = {
    Category.TEST_CALL: {
        "test_foo": [0.001, 0.002],
    },
}


def test_export_json_basic():
    """export_json should write valid JSON with summary stats only."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        path = f.name
    try:
        export_json(measurements=SAMPLE_MEASUREMENTS, filename=path)
        data = json.loads(Path(path).read_text())
        assert data["version"] == "1.0"
        assert "test call" in data["categories"]
        entry = data["categories"]["test call"][0]
        assert entry["name"] == "test_foo"
        assert entry["calls"] == 2
        assert entry["total"] == 0.003
        assert entry["min"] == 0.001
        assert entry["max"] == 0.002
        assert "times" not in entry
    finally:
        Path(path).unlink(missing_ok=True)


def test_export_json_stdout(capsys):
    """export_json with filename='-' should print to stdout."""
    export_json(measurements=SAMPLE_MEASUREMENTS, filename="-")
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["version"] == "1.0"


def test_export_json_empty_measurements():
    """export_json should handle empty measurements gracefully."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        path = f.name
    try:
        export_json(measurements={}, filename=path)
        data = json.loads(Path(path).read_text())
        assert data["categories"] == {}
    finally:
        Path(path).unlink(missing_ok=True)
