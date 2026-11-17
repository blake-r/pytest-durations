# Copyright (c) 2022 Oleg Blednov

"""End-to-end tests for the --pytest-durations-baseline option."""
import json

import pytest

BASELINE_NAME = ".pytest_durations_baseline.json"

SAMPLE_TESTFILE = """
    def test_fast():
        assert True
"""

SLOWED_TESTFILE = """
    import time

    def test_fast():
        time.sleep(0.05)
        assert True
"""


def baseline_entry(name, total, calls=3):
    return {
        "name": name,
        "calls": calls,
        "total": total,
        "min": total / calls,
        "med": total / calls,
        "p90": total / calls,
        "p95": total / calls,
        "p99": total / calls,
        "max": total / calls,
    }


@pytest.fixture(autouse=True)
def sample_testfile(pytester):
    pytester.makepyfile(SAMPLE_TESTFILE)


@pytest.fixture
def baseline_file(pytester):
    return pytester.path / BASELINE_NAME


def write_baseline(pytester, entries):
    document = {"version": "1.0", "categories": {"test call": entries}}
    (pytester.path / BASELINE_NAME).write_text(json.dumps(document), encoding="utf-8")


def test_baseline_first_run_writes_file(pytester, sample_testfile, baseline_file):
    """Without an existing baseline the file is created in the rootdir."""
    result = pytester.runpytest("--pytest-durations-baseline")
    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines([f"-- pytest-durations: baseline written to {baseline_file} *"])
    assert baseline_file.exists()
    data = json.loads(baseline_file.read_text())
    assert data["version"] == "1.0"
    assert "test call" in data["categories"]


def test_baseline_explicit_filename(pytester, sample_testfile):
    """A value given to the option selects the baseline file path."""
    result = pytester.runpytest("--pytest-durations-baseline", "custom_baseline.json")
    result.assert_outcomes(passed=1)
    assert (pytester.path / "custom_baseline.json").exists()


def test_baseline_regression_reported(pytester, baseline_file):
    """A slowed test above the threshold is shown and the baseline updated."""
    write_baseline(pytester, [baseline_entry("test_baseline_regression_reported.py::test_fast", 0.001)])
    pytester.makepyfile(SLOWED_TESTFILE)
    result = pytester.runpytest("--pytest-durations-baseline")
    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines([
        "* baseline comparison (by total, threshold 20%) *",
        "*+*.py::test_fast*",
    ])
    data = json.loads(baseline_file.read_text())
    (entry,) = data["categories"]["test call"]
    assert entry["name"] == "test_baseline_regression_reported.py::test_fast"


def test_baseline_no_significant_changes(pytester):
    """Changes below the threshold produce a single status line."""
    write_baseline(pytester, [baseline_entry("whatever.py::test_fast", 10.0)])
    result = pytester.runpytest("--pytest-durations-baseline")
    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(["-- pytest-durations: no significant changes vs baseline *"])


def test_baseline_shown_when_durations_disabled(pytester):
    """Comparison works even with --pytest-durations=0."""
    write_baseline(pytester, [baseline_entry("test_baseline_shown_when_durations_disabled.py::test_fast", 0.001)])
    pytester.makepyfile(SLOWED_TESTFILE)
    result = pytester.runpytest("--pytest-durations", "0", "--pytest-durations-baseline")
    result.assert_outcomes(passed=1)
    result.stdout.no_fnmatch_line("*duration top*")
    result.stdout.fnmatch_lines(["* baseline comparison (by total, threshold 20%) *"])


def test_baseline_broken_file_warns_and_overwrites(pytester, baseline_file):
    """A broken baseline file produces a warning and is replaced."""
    baseline_file.write_text("{not json", encoding="utf-8")
    result = pytester.runpytest("--pytest-durations-baseline")
    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(["-- pytest-durations: could not read baseline *"])
    data = json.loads(baseline_file.read_text())
    assert data["version"] == "1.0"


def test_baseline_xdist_aggregated(pytester, sample_testfile, baseline_file):
    """Under xdist the baseline is written once from aggregated measurements."""
    pytest.importorskip("xdist")
    result = pytester.runpytest("--pytest-durations-baseline", "--numprocesses", "2")
    result.assert_outcomes(passed=1)
    data = json.loads(baseline_file.read_text())
    (entry,) = data["categories"]["test call"]
    assert entry["calls"] == 1
    assert entry["name"].endswith("::test_fast")
