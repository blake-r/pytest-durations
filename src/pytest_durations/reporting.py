from datetime import timedelta
from operator import itemgetter
from statistics import median
from typing import Dict, List, NoReturn, cast, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.terminal import TerminalReporter


ReportRowT = Tuple[str, str, str, str, str, str]
TimeValuesT = Tuple[str, int, timedelta, timedelta, timedelta, timedelta]

# columns: 0 - name, 1 - calls, 2 - min, 3 - max, 4 - avg, 5 - sum
_SUM_COLUMN_IDX = 5  # sum
_SORT_COLUMN_IDX = 5  # sum
_COLUMNS_ORDER = (5, 0, 1, 4, 2, 3)  # sum, name, calls, avg, min, max


def report_measurements(
    reporter: "TerminalReporter",
    section_name: str,
    measurements: Dict[str, List[float]],
    duration_min: float = -1.0,
    durations: int = 0,
) -> NoReturn:
    """Add time measurement results to reporter."""
    time_values_all = [
        (
            name,
            len(times),
            timedelta(seconds=min(times)),
            timedelta(seconds=max(times)),
            timedelta(seconds=median(times)),
            timedelta(seconds=sum(times)),
        )
        for name, times in measurements.items()
    ]
    # verbose values are limited by minimal time and number of rows
    time_values_verbose = [
        values for values in time_values_all if values[_SUM_COLUMN_IDX].total_seconds() >= duration_min
    ]
    time_values_verbose.sort(key=itemgetter(_SORT_COLUMN_IDX), reverse=True)
    time_values_verbose = time_values_verbose[:durations] if durations else time_values_verbose

    report_rows = [
        _get_report_header_row(),
        *_get_report_timing_rows(time_values=time_values_verbose),
        _get_report_footer_row(time_values=time_values_all),
    ]
    widths = tuple(max(map(len, map(itemgetter(x), report_rows))) for x in range(len(report_rows[0])))
    reporter.ensure_newline()
    reporter.section(section_name, sep="=")
    for idx, row in enumerate(report_rows):
        content = " ".join(f"{row[i]: {'>' if idx else '<'}{widths[i]}}" for i in _COLUMNS_ORDER)
        reporter.line(content)


def _get_report_header_row() -> ReportRowT:
    """Return report header row."""
    return "name", "num", "min", "max", "avg", "total"


def _get_report_footer_row(time_values: List[TimeValuesT]) -> ReportRowT:
    """Return grand total report row."""
    # calculate average values for min, max and avg columns
    average_values = (
        tuple(timedelta(seconds=median(times[idx].total_seconds() for times in time_values)) for idx in range(2, 5))
        if time_values
        else (timedelta(),) * 3
    )
    return (
        "grand total",
        str(sum(times[1] for times in time_values)),  # total calls
        str(average_values[0]),  # average min time
        str(average_values[1]),  # average max time
        str(average_values[2]),  # average time
        str(timedelta(seconds=sum(times[_SUM_COLUMN_IDX].total_seconds() for times in time_values))),  # total time
    )


def _get_report_timing_rows(time_values: List[TimeValuesT]) -> List[ReportRowT]:
    """Return report time measurement rows."""
    return [cast(ReportRowT, tuple(map(str, x))) for x in time_values]
