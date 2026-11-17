# Copyright (c) 2022 Oleg Blednov

"""End-to-end tests for GitHub Actions annotations."""
import json

import pytest

BASELINE_NAME = ".pytest_durations_baseline.json"

SLOWED_TESTFILE = """
    import time

    def test_fast():
        time.sleep(0.05)
        assert True
"""


def baseline_entry(name, total, calls=3):
    med = total / calls
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


@pytest.fixture
def github_actions(monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")


def write_baseline(pytester, entries):
    document = {"version": "1.0", "categories": {"test call": entries}}
    (pytester.path / BASELINE_NAME).write_text(json.dumps(document), encoding="utf-8")


def test_github_actions_warning_emitted(pytester, github_actions):
    """A regression produces a ::warning workflow command with file and line."""
    pytester.makepyfile(SLOWED_TESTFILE)
    write_baseline(pytester, [baseline_entry("test_github_actions_warning_emitted.py::test_fast", 0.001)])
    result = pytester.runpytest("--pytest-durations-baseline")
    result.assert_outcomes(passed=1)
    stdout = result.stdout.str()
    assert "::warning file=test_github_actions_warning_emitted.py,line=" in stdout
    assert "slowed by +" in stdout
    assert "%25 (prev" in stdout


def test_no_annotations_without_github_actions(pytester, monkeypatch):
    """Without GITHUB_ACTIONS=true no workflow commands are emitted."""
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    pytester.makepyfile(SLOWED_TESTFILE)
    write_baseline(pytester, [baseline_entry("test_no_annotations_without_github_actions.py::test_fast", 0.001)])
    result = pytester.runpytest("--pytest-durations-baseline")
    result.assert_outcomes(passed=1)
    assert "::warning" not in result.stdout.str()


def test_improvements_not_annotated(pytester, github_actions):
    """Speedups stay silent in GitHub Actions."""
    pytester.makepyfile("def test_fast():\n    assert True\n")
    write_baseline(pytester, [baseline_entry("test_improvements_not_annotated.py::test_fast", 10.0)])
    result = pytester.runpytest("--pytest-durations-baseline")
    result.assert_outcomes(passed=1)
    assert "::warning" not in result.stdout.str()
