from contextlib import contextmanager
from datetime import timedelta
from operator import itemgetter
from statistics import median
from time import monotonic
from typing import Any, Dict, Iterable, List, NoReturn, Optional, Tuple, Union, cast

from _pytest.config import Config, ExitCode
from _pytest.fixtures import FixtureDef, SubRequest
from _pytest.main import Session
from _pytest.nodes import Item
from _pytest.terminal import TerminalReporter
import freezegun
import pytest
from xdist.workermanage import WorkerController

# Exclude the current module from time freezes.
freezegun.configure(extend_ignore_list=[__name__])

ReportRowT = Tuple[str, str, str, str, str, str]
TimeValuesT = Tuple[str, int, timedelta, timedelta, timedelta, timedelta]


# columns: 0 - name, 1 - calls, 2 - min, 3 - max, 4 - avg, 5 - sum
_SUM_COLUMN_IDX = 5  # sum
_SORT_COLUMN_IDX = 5  # sum
_COLUMNS_ORDER = (5, 0, 1, 4, 2, 3)  # sum, name, calls, avg, min, max
_XDIST_DATA_KEY = "fixture_time_measurements"

_fixture_time_measurements = {}
_test_time_measurements = {}
_setup_time_measurements = {}
_teardown_time_measurements = {}


class SessionData:
    shared_fixture_time_measurement: float = 0.0
    last_fixture_teardown_start: float = 0.0


_session_data = SessionData()


@pytest.hookimpl(hookwrapper=True)
def pytest_fixture_setup(fixturedef: FixtureDef[Any], request: SubRequest) -> Optional[Any]:
    """Measure fixture setup execution time."""
    fixture_key = request.fixturename

    with _measure_block_time(_fixture_time_measurements, fixture_key):
        yield

    if fixturedef.scope != "function":
        # for shared scope fixture setups, store their last execution time
        _session_data.shared_fixture_time_measurement += _fixture_time_measurements[fixture_key][-1]


@pytest.hookimpl(hookwrapper=True)
def pytest_fixture_post_finalizer(fixturedef: FixtureDef[Any], request: SubRequest) -> NoReturn:
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

    with _measure_block_time(_test_time_measurements, test_key):
        yield


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_setup(item: Item) -> NoReturn:
    """Measure test fixtures preparing time.

    Excludes time taken by setting up of shared fixtures.
    """
    test_key = _get_test_key(item)

    with _measure_block_time(_setup_time_measurements, test_key):
        yield

    # subtract time taken by shared fixture initializations (if any)
    _setup_time_measurements[test_key][-1] -= _session_data.shared_fixture_time_measurement
    _session_data.shared_fixture_time_measurement = 0.0


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_teardown(item: Item) -> NoReturn:
    """Measure test fixture cleaning up time.

    Excludes time taken by tearing down of shared fixtures.
    """
    test_key = _get_test_key(item)

    with _measure_block_time(_teardown_time_measurements, test_key):
        _session_data.last_fixture_teardown_start = monotonic()
        yield

    # subtract time taken by shared fixture finalizing (if any)
    # _teardown_time_measurements[test_key][-1] -= _session_data.shared_fixture_time_measurement
    _session_data.shared_fixture_time_measurement = 0.0


@pytest.hookimpl(hookwrapper=True, trylast=True)
def pytest_sessionfinish(session: Session, exitstatus: Union[int, ExitCode]) -> NoReturn:
    """Send measurements to the master process if the current session runs under pytest-xdist."""
    yield
    # for xdist, results should be added to worker output
    workeroutput = getattr(session.config, "workeroutput", None)
    if workeroutput is not None:
        workeroutput[_XDIST_DATA_KEY] = (
            _fixture_time_measurements,
            _test_time_measurements,
            _setup_time_measurements,
            _teardown_time_measurements,
        )


def pytest_testnodedown(node: WorkerController, error: Optional[Any]) -> NoReturn:
    """Merge measurements from slave processes if the current sesions runs under pytest-xdist."""
    # for xdist, results should be accumulated from workers
    workeroutput = getattr(node, "workeroutput", None)
    if workeroutput is not None:
        slave_data = node.workeroutput[_XDIST_DATA_KEY]
        for idx, measurements in enumerate(
            (
                _fixture_time_measurements,
                _test_time_measurements,
                _setup_time_measurements,
                _teardown_time_measurements,
            )
        ):
            for key, values in slave_data[idx].items():
                if key not in measurements:
                    measurements[key] = values
                else:
                    measurements[key].extend(values)


def pytest_terminal_summary(terminalreporter: TerminalReporter, exitstatus: ExitCode, config: Config) -> NoReturn:
    """Add the fixture time report."""
    _report_measurements(terminalreporter, "fixture top by execution time", _fixture_time_measurements, 1, 30)
    _report_measurements(terminalreporter, "test top by execution time", _test_time_measurements, 1, 30)
    _report_measurements(terminalreporter, "setup top by execution time", _setup_time_measurements, 1, 30)
    _report_measurements(terminalreporter, "teardown top by execution time", _teardown_time_measurements, 1, 30)


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


def _report_measurements(
    reporter: TerminalReporter,
    section_name: str,
    measurements: Dict[str, List[float]],
    min_time: float = -1.0,
    max_rows: int = None,
) -> NoReturn:
    """Add time measurement results to reporter."""
    time_values_all = [
        (
            name,
            len(times),
            timedelta(seconds=min(times)),
            timedelta(seconds=max(times)),
            timedelta(seconds=median(times)),
            timedelta(seconds=sum(times)),
        )
        for name, times in measurements.items()
    ]
    # verbose values are limited by minimal time and number of rows
    time_values_verbose = [values for values in time_values_all if values[_SUM_COLUMN_IDX].total_seconds() >= min_time]
    time_values_verbose.sort(key=itemgetter(_SORT_COLUMN_IDX), reverse=True)
    time_values_verbose = time_values_verbose[:max_rows]

    report_rows = [
        _get_report_header_row(),
        *_get_report_timing_rows(time_values=time_values_verbose),
        _get_report_footer_row(time_values=time_values_all),
    ]
    widths = tuple(max(map(len, map(itemgetter(x), report_rows))) for x in range(len(report_rows[0])))
    reporter.ensure_newline()
    reporter.section(section_name, sep="=")
    for idx, row in enumerate(report_rows):
        content = " ".join(f"{row[i]: {'>' if idx else '<'}{widths[i]}}" for i in _COLUMNS_ORDER)
        reporter.line(content)


def _get_report_header_row() -> ReportRowT:
    """Return report header row."""
    return "name", "num", "min", "max", "avg", "total"


def _get_report_footer_row(time_values: List[TimeValuesT]) -> ReportRowT:
    """Return grand total report row."""
    # calculate average values for min, max and avg columns
    average_values = (
        tuple(timedelta(seconds=median(times[idx].total_seconds() for times in time_values)) for idx in range(2, 5))
        if time_values
        else (timedelta(),) * 3
    )
    return (
        "grand total",
        str(sum(times[1] for times in time_values)),  # total calls
        str(average_values[0]),  # average min time
        str(average_values[1]),  # average max time
        str(average_values[2]),  # average time
        str(timedelta(seconds=sum(times[_SUM_COLUMN_IDX].total_seconds() for times in time_values))),  # total time
    )


def _get_report_timing_rows(time_values: List[TimeValuesT]) -> List[ReportRowT]:
    """Return report time measurement rows."""
    return [cast(ReportRowT, tuple(map(str, x))) for x in time_values]
