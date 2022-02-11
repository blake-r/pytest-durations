from contextlib import contextmanager
from datetime import timedelta
from time import monotonic
from typing import Any, Dict, Iterable, List, NoReturn, Optional, Tuple

from _pytest.config import Config, ExitCode
from _pytest.fixtures import FixtureDef, SubRequest
from _pytest.nodes import Item
from _pytest.terminal import TerminalReporter
import pytest

from pytest_duration.reporting import report_measurements
from pytest_duration.storage import fixture_time_measurements, test_time_measurements, setup_time_measurements, \
    teardown_time_measurements

try:
    import pytest_duration.freezegun_helper
except ImportError:
    pass

try:
    import pytest_duration.xdist_helper
except ImportError:
    pass


class SessionData:
    shared_fixture_time_measurement: float = 0.0
    last_fixture_teardown_start: float = 0.0


_session_data = SessionData()


@pytest.hookimpl(hookwrapper=True)
def pytest_fixture_setup(fixturedef: FixtureDef, request: SubRequest) -> Optional[Any]:
    """Measure fixture setup execution time."""
    fixture_key = request.fixturename

    with _measure_block_time(fixture_time_measurements, fixture_key):
        yield

    if fixturedef.scope != "function":
        # for shared scope fixture setups, store their last execution time
        _session_data.shared_fixture_time_measurement += fixture_time_measurements[fixture_key][-1]


@pytest.hookimpl(hookwrapper=True)
def pytest_fixture_post_finalizer(fixturedef: FixtureDef, request: SubRequest) -> NoReturn:
    """Calculate fixture teardown execution time."""
    # nothing to measure
    yield

    teardown_end = monotonic()
    if fixturedef.scope != "function":
        # for shared scope fixture teardowns, store their last execution time
        time = teardown_end - _session_data.last_fixture_teardown_start
        _session_data.shared_fixture_time_measurement += time
    # last fixture clock ticks should always be updated
    _session_data.last_fixture_teardown_start = teardown_end


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item: Item) -> NoReturn:
    """Measure test execution time."""
    test_key = _get_test_key(item)

    with _measure_block_time(test_time_measurements, test_key):
        yield


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_setup(item: Item) -> NoReturn:
    """Measure test fixtures preparing time.

    Excludes time taken by setting up of shared fixtures.
    """
    test_key = _get_test_key(item)

    with _measure_block_time(setup_time_measurements, test_key):
        yield

    # subtract time taken by shared fixture initializations (if any)
    setup_time_measurements[test_key][-1] -= _session_data.shared_fixture_time_measurement
    _session_data.shared_fixture_time_measurement = 0.0


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_teardown(item: Item) -> NoReturn:
    """Measure test fixture cleaning up time.

    Excludes time taken by tearing down of shared fixtures.
    """
    test_key = _get_test_key(item)

    with _measure_block_time(teardown_time_measurements, test_key):
        _session_data.last_fixture_teardown_start = monotonic()
        yield

    # subtract time taken by shared fixture finalizing (if any)
    # teardown_time_measurements[test_key][-1] -= _session_data.shared_fixture_time_measurement
    _session_data.shared_fixture_time_measurement = 0.0


def pytest_terminal_summary(terminalreporter: TerminalReporter, exitstatus: ExitCode, config: Config) -> NoReturn:
    """Add the fixture time report."""
    report_measurements(terminalreporter, "fixture top by execution time", fixture_time_measurements, 0, 30)
    report_measurements(terminalreporter, "test top by execution time", test_time_measurements, 0, 30)
    report_measurements(terminalreporter, "setup top by execution time", setup_time_measurements, 0, 30)
    report_measurements(terminalreporter, "teardown top by execution time", teardown_time_measurements, 0, 30)


def _get_test_key(item: Item) -> str:
    """Return test item name without filename part (class and function names only)."""
    key = item.nodeid
    try:
        # remove filename
        key = key.split("::", 1)[1]
    except IndexError:
        pass
    # remove parameters
    key = key.split("[", 1)[0]
    return key


@contextmanager
def _measure_block_time(measurements: Dict[str, List[float]], key: str) -> Iterable[None]:
    """Measure wrapping block exeution time and put it into a dict."""
    start = monotonic()
    yield
    time = monotonic() - start

    if key not in measurements:
        measurements[key] = [time]
    else:
        measurements[key].append(time)
