"""Pytest plugin mixin to be used when xdist package is used."""
from typing import TYPE_CHECKING, Any, Optional, Union

import pytest

from pytest_durations.types import Category

if TYPE_CHECKING:
    from _pytest.config import ExitCode
    from _pytest.main import Session
    from xdist.workermanage import WorkerController

    from pytest_durations.typing import CategoryMeasurementsT, FunctionMeasurementsT


_WORKEROUTPUT_ATTR = "workeroutput"
_PLUGIN_KEY = "pytest_durations"


class PytestDurationXdistMixin:
    """Mixin to combine measurements from xdist workers."""

    measurements: "CategoryMeasurementsT"

    @pytest.hookimpl(tryfirst=True)
    def pytest_sessionfinish(self, session: "Session", exitstatus: Union[int, "ExitCode"]) -> None:
        """Send measurements to the master process if the current session runs under pytest-xdist."""
        # for xdist, results should be added to worker output
        workeroutput: Optional[dict[str, Any]] = getattr(session.config, _WORKEROUTPUT_ATTR, None)
        if workeroutput is not None:
            workeroutput[_PLUGIN_KEY] = dump_measurements(self.measurements)

    def pytest_testnodedown(self, node: "WorkerController", error: Optional[Any]) -> None:
        """Merge measurements from slave processes if the current sesions runs under pytest-xdist."""
        # for xdist, results should be accumulated from workers
        workeroutput: Optional[dict[str, Any]] = getattr(node, _WORKEROUTPUT_ATTR, None)
        if workeroutput is not None:
            node_measurements = node.workeroutput[_PLUGIN_KEY]
            load_measurements(node_measurements, self.measurements)


def dump_measurements(measurements: "CategoryMeasurementsT") -> dict[str, "FunctionMeasurementsT"]:
    """Serialize category measurement mapping with simple types only."""
    return {
        category.save(): measurements
        for category, measurements in measurements.items()
    }


def load_measurements(measurements: dict[str, "FunctionMeasurementsT"], destination: "CategoryMeasurementsT") -> None:
    """Deserialize category measurement mapping into an existing object."""
    for category, src_series in measurements.items():
        dst_series = destination[Category.load(category)]
        for key, values in src_series.items():
            dst_series.setdefault(key, []).extend(values)
