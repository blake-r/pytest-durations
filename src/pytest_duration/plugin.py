from typing import Any, NoReturn, Optional, TYPE_CHECKING, Iterable, Tuple

import pytest

from pytest_duration.helpers import _get_fixture_key, _get_test_key, _is_shared_fixture
from pytest_duration.reporting import report_measurements
from pytest_duration.session import session
from pytest_duration.ticker import get_current_ticks
from pytest_duration.xdist import xdist_sessionfinish, xdist_testnodedown

if TYPE_CHECKING:
    from _pytest.config import Config, ExitCode, PytestPluginManager
    from _pytest.fixtures import FixtureDef, SubRequest
    from _pytest.nodes import Item
    from _pytest.terminal import TerminalReporter


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


def pytest_addhooks(pluginmanager: "PytestPluginManager") -> NoReturn:
    if pluginmanager.has_plugin("pytest-xdist"):
        pluginmanager.add_hookspecs(xdist_sessionfinish)
        pluginmanager.add_hookspecs(xdist_testnodedown)


@pytest.hookimpl(hookwrapper=True)
def pytest_fixture_setup(fixturedef: "FixtureDef", request: "SubRequest") -> Optional[Any]:
    """Measure fixture setup execution duration."""
    fixture_key = _get_fixture_key(fixturedef)

    with session.measure(Category.FIXTURE_SETUP, fixture_key) as measurement:
        yield

    if _is_shared_fixture(fixturedef):
        # for shared fixtures, store their last setup duration
        session.shared_fixture_duration += measurement.duration


@pytest.hookimpl(hookwrapper=True)
def pytest_fixture_post_finalizer(fixturedef: "FixtureDef", request: "SubRequest") -> NoReturn:
    """Calculate fixture teardown execution duration."""
    # nothing to measure
    yield

    teardown_end = get_current_ticks()
    if _is_shared_fixture(fixturedef):
        # for shared scope fixture teardowns, store their last duration
        duration = teardown_end - session.last_fixture_teardown_start
        session.shared_fixture_duration += duration
    # last fixture duration should always be updated
    session.last_fixture_teardown_start = teardown_end


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item: "Item") -> NoReturn:
    """Measure test execution duration."""
    with session.measure(Category.TEST_CALL, _get_test_key(item)):
        yield


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_setup(item: "Item") -> NoReturn:
    """Measure test fixtures preparing time.

    Excludes time taken by setting up of shared fixtures.
    """
    test_key = _get_test_key(item)

    with session.measure(Category.TEST_SETUP, test_key):
        yield

    # subtract time taken by shared fixture initializations (if any)
    session.measurements["setup"][test_key][-1] -= session.shared_fixture_duration
    session.shared_fixture_duration = 0.0


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_teardown(item: "Item") -> NoReturn:
    """Measure test fixture cleaning up time.

    Excludes time taken by tearing down of shared fixtures.
    """
    test_key = _get_test_key(item)

    with session.measure(Category.TEST_TEARDOWN, test_key):
        session.last_fixture_teardown_start = get_current_ticks()
        yield

    # subtract time taken by shared fixture finalizations (if any)
    session.measurements["teardown"][test_key][-1] -= session.shared_fixture_duration
    session.shared_fixture_duration = 0.0


def pytest_terminal_summary(terminalreporter: "TerminalReporter", exitstatus: "ExitCode", config: "Config") -> NoReturn:
    """Add the fixture time report."""
    for category, name in Category.report_items():
        report_measurements(
            reporter=terminalreporter,
            section_name=f"{name} duration top",
            measurements=session.measurements[category],
            min_duration=config.getoption("--ng-durations-min"),
            durations=config.getoption("--ng-durations"),
        )
