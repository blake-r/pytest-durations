from typing import Optional, Any, NoReturn, Union

import pytest
from _pytest.config import ExitCode
from _pytest.main import Session
from xdist.workermanage import WorkerController

from pytest_duration.storage import MEASUREMENT_STORAGES

_XDIST_DATA_KEY = "pytest_duration"


@pytest.hookimpl(tryfirst=True)
def pytest_sessionfinish(session: Session, exitstatus: Union[int, ExitCode]) -> NoReturn:
    """Send measurements to the master process if the current session runs under pytest-xdist."""
    yield
    # for xdist, results should be added to worker output
    workeroutput = getattr(session.config, "workeroutput", None)
    if workeroutput is not None:
        workeroutput[_XDIST_DATA_KEY] = MEASUREMENT_STORAGES


def pytest_testnodedown(node: WorkerController, error: Optional[Any]) -> NoReturn:
    """Merge measurements from slave processes if the current sesions runs under pytest-xdist."""
    # for xdist, results should be accumulated from workers
    workeroutput = getattr(node, "workeroutput", None)
    if workeroutput is not None:
        slave_data = node.workeroutput[_XDIST_DATA_KEY]
        for idx, measurements in enumerate(MEASUREMENT_STORAGES):
            for key, values in slave_data[idx].items():
                if key not in measurements:
                    measurements[key] = values
                else:
                    measurements[key].extend(values)
