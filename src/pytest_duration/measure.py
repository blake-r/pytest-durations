from types import TracebackType
from typing import Type, Union, NoReturn

from pytest_duration.ticker import get_current_ticks


class MeasureDuration:
    """Context manager measuring duration of block execution."""

    start: float  # monotonic clock value of block entrace
    end: float  # monotonic clock value of block exit
    duration: float  # duration of block execution in seconds

    def __enter__(self) -> "MeasureDuration":
        """Store block entrace time."""
        self.start = get_current_ticks()
        return self

    def __exit__(self, exc_type: Type[Exception], exc_val: Exception, exc_tb: TracebackType) -> None:
        """Store block exit time and calculate its duration."""
        self.end = get_current_ticks()
        self.duration = self.end - self.start
        return None
