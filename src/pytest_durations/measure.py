"""Helper class to measure function call durations."""
from types import TracebackType
from typing import Optional

from pytest_durations.ticker import get_current_ticks


class MeasureDuration:
    """Context manager measuring duration of block execution."""

    start: float  # monotonic clock value of block entrace
    end: float  # monotonic clock value of block exit
    duration: float  # duration of block execution in seconds

    def __enter__(self) -> "MeasureDuration":
        """Store block entrace time."""
        self.start = get_current_ticks()
        self.duration = 0.0
        return self

    def __exit__(
            self,
            exc_type: Optional[type[BaseException]],
            exc_val: Optional[BaseException],
            exc_tb: Optional[TracebackType],
    ) -> None:
        """Store block exit time and calculate its duration."""
        self.end = get_current_ticks()
        self.duration += self.end - self.start
