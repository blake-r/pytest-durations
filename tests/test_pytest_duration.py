from pytest_duration import __version__


from unittest.mock import Mock, call

from _pytest.terminal import TerminalReporter
import pytest

from tests.plugins.measure_time import _report_measurements

_SAMPLE_SECTION_NAME = "sample section"
_SAMPLE_FIXTURE_NAME = "fixture_sample"


@pytest.fixture
def fake_reporter():
    reporter = Mock(spec=TerminalReporter)
    yield reporter


@pytest.fixture
def sample_measurements():
    sample = {
        "fixture1": [0.1, 0.2, 0.4],
        "fixture2": [1.1, 1.2, 1.4],
    }
    yield sample


def test_version():
    assert __version__ == '0.1.0'


class TestMeasureTime:
    def test_report_measurements(self, fake_reporter, sample_measurements):
        """Show all fixture in the reverse order of their total time."""
        _report_measurements(
            reporter=fake_reporter, section_name=_SAMPLE_SECTION_NAME, measurements=sample_measurements
        )
        assert fake_reporter.line.call_args_list == [
            call("total          name        num avg            min            max           "),
            call("0:00:03.700000    fixture2   3 0:00:01.200000 0:00:01.100000 0:00:01.400000"),
            call("0:00:00.700000    fixture1   3 0:00:00.200000 0:00:00.100000 0:00:00.400000"),
            call("0:00:04.400000 grand total   6 0:00:00.700000 0:00:00.600000 0:00:00.900000"),
        ]

    def test_report_measurements_empty_results(self, fake_reporter):
        """Show header and zeroed footer rows only (empty report)."""
        _report_measurements(reporter=fake_reporter, section_name="sample section", measurements={})
        assert fake_reporter.line.call_args_list == [
            call("total   name        num avg     min     max    "),
            call("0:00:00 grand total   0 0:00:00 0:00:00 0:00:00"),
        ]

    def test_report_measurements_with_time_limit(self, fake_reporter, sample_measurements):
        """Show fixtures with total time more than a limit (1 second)."""
        _report_measurements(
            reporter=fake_reporter, section_name=_SAMPLE_SECTION_NAME, measurements=sample_measurements, min_time=1.0
        )
        assert fake_reporter.line.call_args_list == [
            call("total          name        num avg            min            max           "),
            call("0:00:03.700000    fixture2   3 0:00:01.200000 0:00:01.100000 0:00:01.400000"),
            call("0:00:04.400000 grand total   6 0:00:00.700000 0:00:00.600000 0:00:00.900000"),
        ]

    def test_report_measurements_with_rows_limit(self, fake_reporter, sample_measurements):
        """Report a single line of fixture with the top total time."""
        _report_measurements(
            reporter=fake_reporter, section_name=_SAMPLE_SECTION_NAME, measurements=sample_measurements, max_rows=1
        )
        assert fake_reporter.line.call_args_list == [
            call("total          name        num avg            min            max           "),
            call("0:00:03.700000    fixture2   3 0:00:01.200000 0:00:01.100000 0:00:01.400000"),
            call("0:00:04.400000 grand total   6 0:00:00.700000 0:00:00.600000 0:00:00.900000"),
        ]
