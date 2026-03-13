"""Helper to generate formatted measurement report rows from timing data."""
from collections.abc import Collection
from datetime import timedelta
from operator import attrgetter
from statistics import median
from typing import NamedTuple

# Default sort field for report ordering
_SORT_BY_DEFAULT = "sum"


def get_report_rows(
    measurements: dict[str, list[float]],
    duration_min: float = -1.0,
    max_rows: int = 0,
    sort_by: str = _SORT_BY_DEFAULT,
) -> list["ReportRowT"]:
    """Generate a formatted performance report from timing measurements.

    :param measurements: Mapping of operation names to lists of execution times (seconds).
    :param duration_min: If specified, filter out entries with total time < this value.
                         Use None (default) to disable filtering.
    :param max_rows: Limit number of entries in report (excluding header and grand total).
                     Use 0 (default) for no limit.
    :param sort_by: Field to sort by — one of: 'name', 'calls', 'min', 'max', 'med', 'sum'.
                    Default: 'sum' (descending).
    :return: List of formatted rows including header, filtered/sorted entries, and grand total.
    """
    time_values: list[TimeValuesT] = []
    time_values_grand = TimeValueGrandT(name=[], calls=[], min=[], max=[], med=[], sum=[])

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
    result.extend(ReportRowT.from_time_value(time_value) for time_value in time_values)
    result.append(ReportRowT.from_time_value(time_value_grand))

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


class TimeValuesT(NamedTuple):
    """Aggregated timing statistics for a single operation."""

    name: str   # Operation name
    calls: int  # Number of calls (invocations)
    min: float  # Minimum execution time in seconds
    max: float  # Maximum execution time in seconds
    med: float  # Median execution time in seconds
    sum: float  # Total (cumulative) execution time in seconds

    @classmethod
    def from_times(cls, name: str, times: Collection[float]) -> "TimeValuesT":
        """Create aggregated timing stats from a list of individual timings."""
        # It is not possible to get an empty times collection here

        sorted_times = sorted(times)  # To avoid multiple passes for min/max/median

        return cls(
            name=name,
            calls=len(times),
            min=sorted_times[0],
            max=sorted_times[-1],
            med=median(sorted_times),  # Efficient on sorted data
            sum=sum(sorted_times),
        )

    @classmethod
    def get_grand_total(cls, time_values_grand: "TimeValueGrandT") -> "TimeValuesT":
        """Return grand total aggregated timing stats."""
        label = "grand total"

        if not time_values_grand.name:
            return cls(name=label, calls=0, min=0.0, max=0.0, med=0.0, sum=0.0)

        return cls(
            name=label,
            calls=sum(time_values_grand.calls),
            min=min(time_values_grand.min),
            max=max(time_values_grand.max),
            med=median(time_values_grand.med),
            sum=sum(time_values_grand.sum),
        )


class TimeValueGrandT(NamedTuple):
    """Aggregated timing statistics across all operations (per-field lists)."""

    # Keep field order and types in sync with TimeValuesT, but use lists.
    name: list[str]
    calls: list[int]
    min: list[float]
    max: list[float]
    med: list[float]
    sum: list[float]


class ReportRowT(NamedTuple):
    """Formatted row for display in a human-readable time report."""

    total: str  # Formatted total time column (HH:MM:SS)
    name: str   # Operation name column
    num: str    # Number of calls column
    med: str    # Formatted median column
    min: str    # Formatted minimum column
    max: str    # Formatted maximum column

    @classmethod
    def get_header(cls) -> "ReportRowT":
        """Generate header row using field names as labels."""
        return cls(*cls._fields)

    @classmethod
    def from_time_value(cls, time_value: TimeValuesT) -> "ReportRowT":
        """Format a TimeValuesT into display-ready strings for reporting."""

        def format_seconds(seconds: float) -> str:
            """Format seconds as HH:MM:SS."""
            return str(timedelta(seconds=seconds))

        return cls(
            total=format_seconds(seconds=time_value.sum),
            name=time_value.name,
            num=str(time_value.calls),
            min=format_seconds(seconds=time_value.min),
            max=format_seconds(seconds=time_value.max),
            med=format_seconds(seconds=time_value.med),
        )
