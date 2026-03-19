"""Helper class to measure function call durations."""
from types import TracebackType

from pytest_durations.ticker import get_current_ticks


class MeasureDuration:
    """Context manager measuring duration of block execution."""

    start: float  # monotonic clock value of block entrance
    end: float  # monotonic clock value of block exit
    duration: float  # duration of block execution in seconds

    def __enter__(self) -> "MeasureDuration":
        """Store block entrance time."""
        self.start = get_current_ticks()
        self.duration = 0.0
        return self

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None,
    ) -> None:
        """Store block exit time and calculate its duration."""
        self.end = get_current_ticks()
        self.duration += self.end - self.start
