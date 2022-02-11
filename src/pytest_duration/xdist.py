from typing import Optional, Any, NoReturn, Union, TYPE_CHECKING, Dict, List

import pytest

from pytest_duration.session import session as plugin_session

if TYPE_CHECKING:
    from _pytest.config import ExitCode
    from _pytest.main import Session
    from xdist.workermanage import WorkerController

_WORKEROUTPUT_KEY = "pytest_duration"


@pytest.hookimpl(tryfirst=True)
def xdist_sessionfinish(session: "Session", exitstatus: Union[int, "ExitCode"]) -> NoReturn:
    """Send measurements to the master process if the current session runs under pytest-xdist."""
    yield
    # for xdist, results should be added to worker output
    workeroutput = getattr(session.config, "workeroutput", None)
    if workeroutput is not None:
        workeroutput[_WORKEROUTPUT_KEY] = plugin_session.measurements


def xdist_testnodedown(node: "WorkerController", error: Optional[Any]) -> NoReturn:
    """Merge measurements from slave processes if the current sesions runs under pytest-xdist."""
    # for xdist, results should be accumulated from workers
    workeroutput = getattr(node, "workeroutput", None)
    if workeroutput is not None:
        node_measurements = node.workeroutput[_WORKEROUTPUT_KEY]
        _merge_measurements(src=node_measurements, dst=plugin_session.measurements)


def _merge_measurements(src: Dict[str, Dict[str, List[float]]], dst: Dict[str, Dict[str, List[float]]]) -> NoReturn:
    """Merge measured durations by appending new value series to the end of existing ones."""
    for category, src_series in src.items():
        try:
            dst_series = dst[category]
        except KeyError:
            dst_series = dst[category] = {}
        for key, values in src_series.items():
            try:
                dst_series[key].extend(values)
            except KeyError:
                dst_series[key] = values
