from contextlib import contextmanager
from typing import Dict, List, Iterable

from pytest_duration.measure import MeasureDuration


class Session:
    """Session object storing runtime parameters."""

    measurements: Dict[str, Dict[str, List[float]]]
    shared_fixture_duration: float
    last_fixture_teardown_start: float

    def __init__(self):
        super().__init__()
        self.shared_fixture_duration = 0.0
        self.last_fixture_teardown_start = 0.0
        self.measurements = {}

    @contextmanager
    def measure(self, source: str, key: str) -> Iterable["MeasureDuration"]:
        """Measure wrapping block exeution time and put it into a dict."""
        try:
            measurements = self.measurements[source]
        except KeyError:
            measurements = self.measurements[source] = {}

        with MeasureDuration() as measurement:
            yield measurement

        try:
            measurements[key].append(measurement.duration)
        except KeyError:
            measurements[key] = [measurement.duration]


session = Session()  # Session singleton.
