from unittest.mock import Mock, call, create_autospec

import pytest
from _pytest.terminal import TerminalReporter

from pytest_duration.reporting import report_measurements

_SAMPLE_SECTION_NAME = "sample section"


@pytest.fixture
def fake_reporter():
    reporter = create_autospec(TerminalReporter, instance=True)
    yield reporter


@pytest.fixture
def sample_measurements():
    sample = {
        "fixture1": [0.1, 0.2, 0.4],
        "fixture2": [1.1, 1.2, 1.4],
    }
    yield sample


def test_report_measurements(fake_reporter, sample_measurements):
    """Show all fixture in the reverse order of their total time."""
    report_measurements(
        reporter=fake_reporter, section_name=_SAMPLE_SECTION_NAME, measurements=sample_measurements,
    )
    assert fake_reporter.line.call_args_list == [
        call("total          name        num avg            min            max           "),
        call("0:00:03.700000    fixture2   3 0:00:01.200000 0:00:01.100000 0:00:01.400000"),
        call("0:00:00.700000    fixture1   3 0:00:00.200000 0:00:00.100000 0:00:00.400000"),
        call("0:00:04.400000 grand total   6 0:00:00.700000 0:00:00.600000 0:00:00.900000"),
    ]


def test_report_measurements_empty_results(fake_reporter):
    """Show header and zeroed footer rows only (empty report)."""
    report_measurements(reporter=fake_reporter, section_name="sample section", measurements={},)
    assert fake_reporter.line.call_args_list == [
        call("total   name        num avg     min     max    "),
        call("0:00:00 grand total   0 0:00:00 0:00:00 0:00:00"),
    ]


def test_report_measurements_with_time_limit(fake_reporter, sample_measurements):
    """Show fixtures with total time more than a limit (1 second)."""
    report_measurements(
        reporter=fake_reporter, section_name=_SAMPLE_SECTION_NAME, measurements=sample_measurements, min_duration=1.0,
    )
    assert fake_reporter.line.call_args_list == [
        call("total          name        num avg            min            max           "),
        call("0:00:03.700000    fixture2   3 0:00:01.200000 0:00:01.100000 0:00:01.400000"),
        call("0:00:04.400000 grand total   6 0:00:00.700000 0:00:00.600000 0:00:00.900000"),
    ]


def test_report_measurements_with_rows_limit(fake_reporter, sample_measurements):
    """Report a single line of fixture with the top total time."""
    report_measurements(
        reporter=fake_reporter, section_name=_SAMPLE_SECTION_NAME, measurements=sample_measurements, durations=1,
    )
    assert fake_reporter.line.call_args_list == [
        call("total          name        num avg            min            max           "),
        call("0:00:03.700000    fixture2   3 0:00:01.200000 0:00:01.100000 0:00:01.400000"),
        call("0:00:04.400000 grand total   6 0:00:00.700000 0:00:00.600000 0:00:00.900000"),
    ]
