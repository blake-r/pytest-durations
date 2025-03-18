from contextlib import contextmanager, ExitStack
from typing import Any, Iterable, Optional, TYPE_CHECKING, Tuple

import pytest

from pytest_durations.helpers import _get_fixture_key, _get_test_key, _is_shared_fixture
from pytest_durations.measure import MeasureDuration
from pytest_durations.options import DEFAULT_RESULT_LOG
from pytest_durations.reporting import get_report_rows, get_report_max_widths
from pytest_durations.ticker import get_current_ticks

if TYPE_CHECKING:
    from _pytest.config import Config, ExitCode
    from _pytest.fixtures import FixtureDef, SubRequest
    from _pytest.nodes import Item
    from _pytest.terminal import TerminalReporter
    from pytest_durations.types import MeasurementsT


class Category:
    """Measurement category constants."""

    __slots__ = ()
    FIXTURE_SETUP = "fixture"
    TEST_CALL = "test"
    TEST_SETUP = "setup"
    TEST_TEARDOWN = "teardown"

    @classmethod
    def report_items(cls) -> Iterable[Tuple[str, str]]:
        yield cls.FIXTURE_SETUP, "fixture"
        yield cls.TEST_CALL, "test call"
        yield cls.TEST_SETUP, "test setup"
        yield cls.TEST_TEARDOWN, "test teardown"


class PytestDurationPlugin:
    measurements: "MeasurementsT"
    shared_fixture_duration: float
    last_fixture_teardown_start: float

    def __init__(self):
        super().__init__()
        self.measurements = {category: {} for category, _ in Category.report_items()}
        self.shared_fixture_duration = 0.0
        self.last_fixture_teardown_start = 0.0

    @pytest.hookimpl(hookwrapper=True)
    def pytest_fixture_setup(self, fixturedef: "FixtureDef", request: "SubRequest") -> Optional[Any]:
        """Measure fixture setup execution duration."""
        fixture_key = _get_fixture_key(fixturedef)

        with self._measure(Category.FIXTURE_SETUP, fixture_key) as measurement:
            yield

        if _is_shared_fixture(fixturedef):
            # for shared fixtures, store their last setup duration
            self.shared_fixture_duration += measurement.duration

    def pytest_fixture_post_finalizer(self, fixturedef: "FixtureDef", request: "SubRequest") -> None:
        """Calculate fixture teardown execution duration."""
        teardown_end = get_current_ticks()
        if _is_shared_fixture(fixturedef):
            # for shared scope fixture teardowns, store their last duration
            duration = teardown_end - self.last_fixture_teardown_start
            self.shared_fixture_duration += duration
        # last fixture duration should always be updated
        self.last_fixture_teardown_start = teardown_end

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_call(self, item: "Item") -> None:
        """Measure test execution duration."""
        with self._measure(Category.TEST_CALL, _get_test_key(item)):
            yield

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_setup(self, item: "Item") -> None:
        """Measure test fixtures preparing time.

        Excludes time taken by setting up of shared fixtures.
        """
        with self._measure(Category.TEST_SETUP, _get_test_key(item)) as measurement:
            yield
            # subtract time taken by shared fixture initializations (if any)
            measurement.duration -= self.shared_fixture_duration
        self.shared_fixture_duration = 0.0

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_teardown(self, item: "Item") -> None:
        """Measure test fixture cleaning up time.

        Excludes time taken by tearing down of shared fixtures.
        """
        with self._measure(Category.TEST_TEARDOWN, _get_test_key(item)) as measurement:
            self.last_fixture_teardown_start = get_current_ticks()
            yield
            # subtract time taken by shared fixture finalizations (if any)
            measurement.duration -= self.shared_fixture_duration
        self.shared_fixture_duration = 0.0

    def pytest_terminal_summary(
        self,
        terminalreporter: "TerminalReporter",
        exitstatus: "ExitCode",
        config: "Config",
    ) -> None:
        """Write the measured time to a terminal reporter or to a file."""
        result_log = config.getoption("--pytest-resultlog")
        with ExitStack() as stack:
            if result_log != DEFAULT_RESULT_LOG:
                result_log_fp = stack.enter_context(open(result_log, mode="at"))
                terminalreporter = type(terminalreporter)(config=config, file=result_log_fp)
            self._report_summary(terminalreporter=terminalreporter, config=config)

    def _report_summary(self, terminalreporter: "TerminalReporter", config: "Config") -> None:
        """Write time report to the specified terminal reporter."""
        fullwidth = terminalreporter._tw.fullwidth
        durations = config.getoption("--pytest-durations")
        durations_min = config.getoption("--pytest-durations-min")
        reports = []
        widths = [0] * 5
        for category, name in Category.report_items():
            category_report_rows = get_report_rows(
                measurements=self.measurements[category],
                duration_min=durations_min,
                durations=durations,
            )
            reports.append((f"{name} duration top", category_report_rows))
            widths = [max(*a) for a in zip(widths, get_report_max_widths(category_report_rows))]
        fullwidth = max(fullwidth, sum(widths) + len(widths) - 1)
        for section_name, category_report_rows in reports:
            terminalreporter.write_sep(sep="=", title=section_name, fullwidth=fullwidth)
            for idx, row in enumerate(category_report_rows):
                content = " ".join(f"{col: {'>' if idx else '<'}{width}}" for col, width in zip(row, widths))
                terminalreporter.line(content)

    @contextmanager
    def _measure(self, category: str, key: str) -> Iterable["MeasureDuration"]:
        """Measure wrapping block exeution time and put it into a dict."""
        measurements = self.measurements[category]

        with MeasureDuration() as measurement:
            yield measurement

        try:
            measurements[key].append(measurement.duration)
        except KeyError:
            measurements[key] = [measurement.duration]
