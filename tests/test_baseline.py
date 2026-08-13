"""Tests for baseline comparison module."""
import json
from pathlib import Path

import pytest

from pytest_durations.baseline import compare_to_baseline, format_github_annotation, load_baseline, save_baseline
from pytest_durations.types import Category


class TestLoadBaseline:
    def test_load_existing(self, tmp_path: Path) -> None:
        path = tmp_path / "baseline.json"
        data = {
            "version": "1.0",
            "categories": {
                "test call": [
                    {"name": "test_foo", "total": 1.0, "calls": 1},
                ],
            },
        }
        path.write_text(json.dumps(data))
        baseline = load_baseline(path)
        assert baseline == {"test call": {"test_foo": 1.0}}

    def test_load_missing(self, tmp_path: Path) -> None:
        path = tmp_path / "missing.json"
        assert load_baseline(path) is None


class TestSaveBaseline:
    def test_save_and_load(self, tmp_path: Path) -> None:
        path = tmp_path / "baseline.json"
        measurements = {
            Category.TEST_CALL: {
                "test_foo": [0.1, 0.2],
            },
        }
        save_baseline(measurements, path)
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["categories"]["test call"][0]["total"] == pytest.approx(0.3)
        assert data["categories"]["test call"][0]["calls"] == 2


class TestCompareToBaseline:
    def test_no_regression(self) -> None:
        measurements = {
            Category.TEST_CALL: {
                "test_foo": [0.9, 0.1],
            },
        }
        baseline = {"test call": {"test_foo": 1.0}}
        regressions = compare_to_baseline(measurements, baseline, threshold=0.1)
        assert regressions == []

    def test_regression_detected(self) -> None:
        measurements = {
            Category.TEST_CALL: {
                "test_foo": [1.5],
            },
        }
        baseline = {"test call": {"test_foo": 1.0}}
        regressions = compare_to_baseline(measurements, baseline, threshold=0.1)
        assert len(regressions) == 1
        assert regressions[0]["delta"] == 0.5

    def test_new_test_ignored(self) -> None:
        measurements = {
            Category.TEST_CALL: {
                "test_bar": [2.0],
            },
        }
        baseline = {"test call": {}}
        regressions = compare_to_baseline(measurements, baseline, threshold=0.1)
        assert regressions == []

    def test_sort_order(self) -> None:
        measurements = {
            Category.TEST_CALL: {
                "test_a": [2.0],
                "test_b": [1.5],
            },
        }
        baseline = {"test call": {"test_a": 1.0, "test_b": 1.0}}
        regressions = compare_to_baseline(measurements, baseline, threshold=0.1)
        assert [r["name"] for r in regressions] == ["test_a", "test_b"]


class TestFormatGithubAnnotation:
    def test_format(self) -> None:
        regression = {
            "category": "test_call",
            "name": "test_foo",
            "baseline": 1.0,
            "current": 1.5,
            "delta": 0.5,
        }
        annotation = format_github_annotation(regression)
        assert "::warning title=Duration Regression::" in annotation
        assert "test_call" in annotation
        assert "test_foo" in annotation
        assert "50.0%" in annotation
