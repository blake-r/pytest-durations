# Copyright (c) 2022 Oleg Blednov

"""Tests for the baseline comparison module."""
import json

import pytest

from pytest_durations.baseline import (
    BaselineChangeT,
    compare_baseline,
    github_escape_message,
    github_escape_property,
    github_warning_command,
    load_baseline,
    render_comparison,
    save_baseline,
)
from pytest_durations.reporting import format_seconds_clock
from pytest_durations.types import Category

SAMPLE_MEASUREMENTS = {
    Category.TEST_CALL: {
        "test_foo.py::test_bar": [0.04, 0.05, 0.06],
        "test_foo.py::test_baz": [0.01, 0.01, 0.01],
    },
}


def entry(name, calls, total, med):
    return {
        "name": name,
        "calls": calls,
        "total": total,
        "min": med,
        "med": med,
        "p90": med,
        "p95": med,
        "p99": med,
        "max": med,
    }


def baseline_document(entries):
    return {"version": "1.0", "categories": {"test call": entries}}


SAMPLE_BASELINE = baseline_document([
    entry("test_foo.py::test_bar", 3, 0.15, 0.05),
    entry("test_foo.py::test_baz", 3, 0.03, 0.01),
])


@pytest.fixture
def sample_path(tmp_path):
    return tmp_path / "baseline.json"


def test_save_and_load_roundtrip(sample_path):
    save_baseline(SAMPLE_BASELINE, sample_path)
    baseline, warning = load_baseline(sample_path)
    assert warning is None
    assert baseline == SAMPLE_BASELINE


def test_load_missing_file(sample_path):
    baseline, warning = load_baseline(sample_path)
    assert baseline is None
    assert warning is None


def test_load_broken_json(sample_path):
    sample_path.write_text("{not json", encoding="utf-8")
    baseline, warning = load_baseline(sample_path)
    assert baseline is None
    assert "could not read baseline" in warning


def test_load_unsupported_version(sample_path):
    sample_path.write_text(json.dumps({"version": "0.9", "categories": {}}), encoding="utf-8")
    baseline, warning = load_baseline(sample_path)
    assert baseline is None
    assert "unsupported baseline format" in warning


def test_compare_regression_and_improvement():
    old = baseline_document([
        entry("test_foo.py::test_bar", 3, 0.05, 0.05),
        entry("test_foo.py::test_baz", 3, 0.10, 0.10),
    ])
    new = baseline_document([
        entry("test_foo.py::test_bar", 3, 0.11, 0.11),
        entry("test_foo.py::test_baz", 3, 0.07, 0.07),
    ])
    changes = compare_baseline(old, new, metric="sum")
    assert [(c.name, round(c.change, 1)) for c in changes] == [
        ("test_foo.py::test_bar", 120.0),
        ("test_foo.py::test_baz", -30.0),
    ]
    assert changes[0].prev == 0.05
    assert changes[0].now == 0.11


def test_compare_below_threshold_skipped():
    old = baseline_document([entry("test_foo.py::test_bar", 3, 0.10, 0.10)])
    new = baseline_document([entry("test_foo.py::test_bar", 3, 0.11, 0.11)])
    assert compare_baseline(old, new, metric="sum") == []


def test_compare_min_calls_skipped():
    old = baseline_document([entry("test_foo.py::test_bar", 2, 0.10, 0.10)])
    new = baseline_document([entry("test_foo.py::test_bar", 3, 0.50, 0.50)])
    assert compare_baseline(old, new, metric="sum") == []


def test_compare_zero_prev_skipped():
    old = baseline_document([entry("test_foo.py::test_bar", 3, 0.0, 0.0)])
    new = baseline_document([entry("test_foo.py::test_bar", 3, 0.50, 0.50)])
    assert compare_baseline(old, new, metric="sum") == []


def test_compare_new_test_reported_without_change():
    old = baseline_document([])
    new = baseline_document([entry("test_foo.py::test_bar", 3, 0.50, 0.50)])
    changes = compare_baseline(old, new, metric="sum")
    assert changes == [BaselineChangeT("test call", "test_foo.py::test_bar", None, 0.5, None)]


def test_compare_removed_test_ignored():
    old = baseline_document([entry("test_foo.py::test_bar", 3, 0.10, 0.10)])
    new = baseline_document([])
    assert compare_baseline(old, new, metric="sum") == []


def test_compare_sorts_regressions_first():
    old = baseline_document([
        entry("test_foo.py::a", 3, 0.10, 0.10),
        entry("test_foo.py::b", 3, 0.10, 0.10),
        entry("test_foo.py::c", 3, 0.10, 0.10),
    ])
    new = baseline_document([
        entry("test_foo.py::a", 3, 0.50, 0.50),
        entry("test_foo.py::b", 3, 0.30, 0.30),
        entry("test_foo.py::c", 3, 0.05, 0.05),
    ])
    changes = compare_baseline(old, new, metric="sum")
    assert [c.name for c in changes] == ["test_foo.py::a", "test_foo.py::b", "test_foo.py::c"]


def test_render_comparison_alignment_and_new_hidden():
    changes = [
        BaselineChangeT("test call", "test_foo.py::test_bar", 0.05, 0.11, 120.0),
        BaselineChangeT("test call", "test_foo.py::test_baz", 0.03, 0.02, -30.0),
        BaselineChangeT("test call", "test_foo.py::test_new", None, 0.50, None),
    ]
    lines = render_comparison(changes, metric_label="total", format_seconds=format_seconds_clock)
    assert lines[0].startswith("change")
    assert "name" in lines[0]
    assert all(len(line) == len(lines[1]) for line in lines[1:])
    assert "test_new" not in "\n".join(lines)
    assert "+120.0%" in lines[1]
    assert "-30.0%" in lines[2]


def test_github_escapes():
    assert github_escape_message("100% slow\ner") == "100%25 slow%0Aer"
    assert github_escape_property("dir/file:name,x") == "dir/file%3Aname%2Cx"


def test_github_warning_command():
    change = BaselineChangeT("test call", "test_foo.py::test_bar", 0.05, 0.11, 120.0)
    command = github_warning_command(change, file="test_foo.py", line=42)
    assert command == (
        "::warning file=test_foo.py,line=42::"
        "test_foo.py::test_bar slowed by +120.0%25 (prev 0:00:00.050000, now 0:00:00.110000)"
    )


def test_github_warning_command_without_line():
    change = BaselineChangeT("test call", "test_foo.py::test_bar", 0.05, 0.11, 120.0)
    command = github_warning_command(change, file="test_foo.py", line=None)
    assert command.startswith("::warning file=test_foo.py::")
