"""Helper to generate formatted measurement report rows from timing data."""
from collections.abc import Callable, Collection
from datetime import timedelta
from operator import attrgetter
from statistics import median
from typing import NamedTuple

from pytest_durations.types import TimeFormat

# Default sort field for report ordering
_SORT_BY_DEFAULT = "sum"
_SECONDS_PER_MINUTE = 60
_SECONDS_PER_HOUR = 3600
_SECONDS_PER_DAY = 86400


def format_seconds_clock(seconds: float) -> str:
    """Format seconds exactly as ``str(timedelta(seconds=...))`` (default behavior)."""
    return str(timedelta(seconds=seconds))


def format_seconds_short(seconds: float) -> str:
    """Format seconds as compact ``H:MM:SS`` (days folded into hours), no microseconds."""
    total = int(seconds)
    hours, rem = divmod(total, _SECONDS_PER_HOUR)
    minutes, secs = divmod(rem, _SECONDS_PER_MINUTE)
    return f"{hours}:{minutes:02d}:{secs:02d}"


def _format_seconds_sub_second(seconds: float) -> str:
    """Format sub-second durations in milliseconds."""
    return f"{seconds * 1000:.0f}ms"


def _format_seconds_millis(seconds: float) -> str:
    """Format durations as ``SS.fff`` seconds."""
    return f"{seconds:.3f}s"


def _format_seconds_time(seconds: float) -> str:
    """Format durations as ``M:SS`` minutes and seconds."""
    total = int(seconds)
    minutes, secs = divmod(total, _SECONDS_PER_MINUTE)
    return f"{minutes}:{secs:02d}"


def _format_seconds_hms(seconds: float) -> str:
    """Format durations as ``H:MM:SS`` hours, minutes and seconds."""
    total = int(seconds)
    hours, rem = divmod(total, _SECONDS_PER_HOUR)
    minutes, secs = divmod(rem, _SECONDS_PER_MINUTE)
    return f"{hours}:{minutes:02d}:{secs:02d}"


def _format_seconds_days(seconds: float) -> str:
    """Format durations as ``Xd H:MM:SS`` days, hours, minutes and seconds."""
    total = int(seconds)
    days, rem = divmod(total, _SECONDS_PER_DAY)
    hours, rem = divmod(rem, _SECONDS_PER_HOUR)
    minutes, secs = divmod(rem, _SECONDS_PER_MINUTE)
    return f"{days}d {hours}:{minutes:02d}:{secs:02d}"


def resolve_time_format(time_format: TimeFormat, max_seconds: float) -> Callable[[float], str]:
    """Resolve a :class:`TimeFormat` into a single concrete formatter for a whole report.

    :param time_format: The requested formatting mode.
    :param max_seconds: Global maximum duration (seconds) across all measurements, used to
                        pick the *auto* form once for the whole report.
    :return: A formatter callable mapping a duration (seconds) to a display string.
    """
    if time_format is TimeFormat.SHORT:
        return format_seconds_short
    if time_format is TimeFormat.CLOCK:
        return format_seconds_clock
    if max_seconds >= _SECONDS_PER_DAY:
        formatter = _format_seconds_days
    elif max_seconds >= _SECONDS_PER_HOUR:
        formatter = _format_seconds_hms
    elif max_seconds >= _SECONDS_PER_MINUTE:
        formatter = _format_seconds_time
    elif max_seconds >= 1:
        formatter = _format_seconds_millis
    else:
        formatter = _format_seconds_sub_second
    return formatter


def get_report_rows(
    measurements: dict[str, list[float]],
    duration_min: float = -1.0,
    max_rows: int = 0,
    sort_by: str = _SORT_BY_DEFAULT,
    format_seconds: Callable[[float], str] = format_seconds_clock,
) -> list["ReportRowT"]:
    """Generate a formatted performance report from timing measurements.

    :param measurements: Mapping of operation names to lists of execution times (seconds).
    :param duration_min: If specified, filter out entries with total time < this value.
                         Use None (default) to disable filtering.
    :param max_rows: Limit number of entries in report (excluding header and grand total).
                     Use 0 (default) for no limit.
    :param sort_by: Field to sort by — one of: 'name', 'calls', 'min', 'max', 'med', 'sum'.
                    Default: 'sum' (descending).
    :param format_seconds: Callable formatting a duration (seconds) into a display string.
                           Defaults to the clock format.
    :return: List of formatted rows including header, filtered/sorted entries, and grand total.
    """
    time_values: list[TimeValuesT] = []
    time_values_grand = TimeValueGrandT(name=[], calls=[], min=[], med=[], p90=[], p95=[], p99=[], max=[], sum=[])

    for name, times in measurements.items():
        time_value = TimeValuesT.from_times(name=name, times=times)
        for idx in range(len(TimeValuesT._fields)):
            time_values_grand[idx].append(time_value[idx])
        if time_value.sum >= duration_min:
            time_values.append(time_value)

    time_value_grand = TimeValuesT.get_grand_total(time_values_grand=time_values_grand)

    # Sort by requested field (descending)
    time_values.sort(key=attrgetter(sort_by), reverse=True)
    # Limit number of rows if requested
    if max_rows > 0:
        time_values = time_values[:max_rows]

    # Build final report: header + filtered entries + grand total
    result: list[ReportRowT] = [ReportRowT.get_header()]
    result.extend(ReportRowT.from_time_value(time_value, format_seconds=format_seconds) for time_value in time_values)
    result.append(ReportRowT.from_time_value(time_value_grand, format_seconds=format_seconds))

    return result


def get_report_max_widths(report_rows: Collection["ReportRowT"]) -> tuple[int, ...]:
    """Return maximum width for each column in the report.

    :param report_rows: Collection of report rows.
    :return: Tuple of maximum widths per column.
    """
    return tuple(
        max(len(row[idx]) for row in report_rows)
        for idx in range(len(ReportRowT._fields))
    )


def report_column_fields(selected_columns: Collection[str]) -> tuple[str, ...]:
    """Resolve selected stat columns into the display fields actually rendered.

    The first selected column is rendered first (it is the report sort key), then
    ``name``, then the remaining selected columns. ``name`` is therefore always the
    second rendered column and can never be first.
    """
    ordered = tuple(selected_columns)
    return (ordered[0], "name", *ordered[1:])


def get_selected_max_widths(
    report_rows: Collection["ReportRowT"],
    selected_columns: Collection[str],
) -> tuple[int, ...]:
    """Return the maximum width for each actually-rendered column."""
    fields = report_column_fields(selected_columns)
    return tuple(max(len(getattr(row, field)) for row in report_rows) for field in fields)


def _pct(sorted_times: list[float], p: float) -> float:
    """Calculate the p-th percentile using linear interpolation."""
    n = len(sorted_times)
    if n == 1:
        return sorted_times[0]
    k = n - 1
    idx = p / 100 * k
    lower = int(idx)
    upper = min(lower + 1, k)
    frac = idx - lower
    return sorted_times[lower] + frac * (sorted_times[upper] - sorted_times[lower])


class TimeValuesT(NamedTuple):
    """Aggregated timing statistics for a single operation."""

    name: str   # Operation name
    calls: int  # Number of calls (invocations)
    min: float  # Minimum execution time in seconds
    med: float  # Median execution time in seconds
    p90: float  # 90th percentile execution time in seconds
    p95: float  # 95th percentile execution time in seconds
    p99: float  # 99th percentile execution time in seconds
    max: float  # Maximum execution time in seconds
    sum: float  # Total (cumulative) execution time in seconds

    @classmethod
    def from_times(cls, name: str, times: Collection[float]) -> "TimeValuesT":
        """Create aggregated timing stats from a list of individual timings."""
        sorted_times = sorted(times)

        return cls(
            name=name,
            calls=len(sorted_times),
            min=sorted_times[0],
            med=_pct(sorted_times, 50.0),
            p90=_pct(sorted_times, 90.0),
            p95=_pct(sorted_times, 95.0),
            p99=_pct(sorted_times, 99.0),
            max=sorted_times[-1],
            sum=sum(sorted_times),
        )

    @classmethod
    def get_grand_total(cls, time_values_grand: "TimeValueGrandT") -> "TimeValuesT":
        """Return grand total aggregated timing stats."""
        label = "grand total"

        if not time_values_grand.name:
            return cls(name=label, calls=0, min=0.0, med=0.0, p90=0.0, p95=0.0, p99=0.0, max=0.0, sum=0.0)

        return cls(
            name=label,
            calls=sum(time_values_grand.calls),
            min=min(time_values_grand.min),
            med=median(time_values_grand.med),
            p90=_pct(sorted(time_values_grand.p90), 90.0),
            p95=_pct(sorted(time_values_grand.p95), 95.0),
            p99=_pct(sorted(time_values_grand.p99), 99.0),
            max=max(time_values_grand.max),
            sum=sum(time_values_grand.sum),
        )


class TimeValueGrandT(NamedTuple):
    """Aggregated timing statistics across all operations (per-field lists)."""

    # Keep field order and types in sync with TimeValuesT, but use lists.
    name: list[str]
    calls: list[int]
    min: list[float]
    med: list[float]
    p90: list[float]
    p95: list[float]
    p99: list[float]
    max: list[float]
    sum: list[float]


class ReportRowT(NamedTuple):
    """Formatted row for display in a human-readable time report."""

    total: str  # Formatted total time column (HH:MM:SS)
    name: str   # Operation name column
    num: str    # Number of calls column
    min: str    # Formatted minimum column
    med: str    # Formatted median column
    p90: str    # Formatted 90th percentile column
    p95: str    # Formatted 95th percentile column
    p99: str    # Formatted 99th percentile column
    max: str    # Formatted maximum column

    @classmethod
    def get_header(cls) -> "ReportRowT":
        """Generate header row using field names as labels."""
        return cls(*cls._fields)

    @classmethod
    def from_time_value(
        cls,
        time_value: TimeValuesT,
        format_seconds: Callable[[float], str] = format_seconds_clock,
    ) -> "ReportRowT":
        """Format a TimeValuesT into display-ready strings for reporting."""
        return cls(
            total=format_seconds(seconds=time_value.sum),
            name=time_value.name,
            num=str(time_value.calls),
            min=format_seconds(seconds=time_value.min),
            med=format_seconds(seconds=time_value.med),
            p90=format_seconds(seconds=time_value.p90),
            p95=format_seconds(seconds=time_value.p95),
            p99=format_seconds(seconds=time_value.p99),
            max=format_seconds(seconds=time_value.max),
        )
