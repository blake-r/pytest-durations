from contextlib import contextmanager
from typing import Any, Iterable, NoReturn, Optional, TYPE_CHECKING, Tuple

import pytest

from pytest_durations.helpers import _get_fixture_key, _get_test_key, _is_shared_fixture
from pytest_durations.measure import MeasureDuration
from pytest_durations.reporting import report_measurements
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

    def pytest_fixture_post_finalizer(self, fixturedef: "FixtureDef", request: "SubRequest") -> NoReturn:
        """Calculate fixture teardown execution duration."""
        teardown_end = get_current_ticks()
        if _is_shared_fixture(fixturedef):
            # for shared scope fixture teardowns, store their last duration
            duration = teardown_end - self.last_fixture_teardown_start
            self.shared_fixture_duration += duration
        # last fixture duration should always be updated
        self.last_fixture_teardown_start = teardown_end

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_call(self, item: "Item") -> NoReturn:
        """Measure test execution duration."""
        with self._measure(Category.TEST_CALL, _get_test_key(item)):
            yield

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_setup(self, item: "Item") -> NoReturn:
        """Measure test fixtures preparing time.

        Excludes time taken by setting up of shared fixtures.
        """
        with self._measure(Category.TEST_SETUP, _get_test_key(item)) as measurement:
            yield
            # subtract time taken by shared fixture initializations (if any)
            measurement.duration -= self.shared_fixture_duration
        self.shared_fixture_duration = 0.0

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_teardown(self, item: "Item") -> NoReturn:
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
    ) -> NoReturn:
        """Add the fixture time report."""
        durations = config.getoption("--pytest-durations")
        durations_min = config.getoption("--pytest-durations-min")
        for category, name in Category.report_items():
            report_measurements(
                reporter=terminalreporter,
                section_name=f"{name} duration top",
                measurements=self.measurements[category],
                duration_min=durations_min,
                durations=durations,
            )

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
