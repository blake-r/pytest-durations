from typing import Union, Optional, Any, TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from _pytest.config import ExitCode
    from _pytest.main import Session
    from xdist.workermanage import WorkerController
    from pytest_durations.types import MeasurementsT

_WORKEROUTPUT_KEY = "pytest_durations"


class PytestDurationXdistMixin:
    measurements: "MeasurementsT"

    @pytest.hookimpl(tryfirst=True)
    def pytest_sessionfinish(self, session: "Session", exitstatus: Union[int, "ExitCode"]) -> None:
        """Send measurements to the master process if the current session runs under pytest-xdist."""
        # for xdist, results should be added to worker output
        workeroutput = getattr(session.config, "workeroutput", None)
        if workeroutput is not None:
            workeroutput[_WORKEROUTPUT_KEY] = self.measurements

    def pytest_testnodedown(self, node: "WorkerController", error: Optional[Any]) -> None:
        """Merge measurements from slave processes if the current sesions runs under pytest-xdist."""
        # for xdist, results should be accumulated from workers
        workeroutput = getattr(node, "workeroutput", None)
        if workeroutput is not None:
            node_measurements = node.workeroutput[_WORKEROUTPUT_KEY]
            self._extend_measurements(node_measurements)

    def _extend_measurements(self, src: "MeasurementsT") -> None:
        """Merge measured durations by appending new value series to the end of existing ones."""
        for category, src_series in src.items():
            dst_series = self.measurements[category]
            for key, values in src_series.items():
                try:
                    dst_series[key].extend(values)
                except KeyError:
                    dst_series[key] = values
