from datetime import timedelta
from operator import itemgetter
from statistics import median
from typing import Callable, Dict, Iterable, List, NoReturn, TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from _pytest.terminal import TerminalReporter


ReportRowT = Tuple[str, str, str, str, str, str]
TimeValuesT = Tuple[str, int, float, float, float, float]

# columns: 0 - name, 1 - calls, 2 - min, 3 - max, 4 - avg, 5 - sum
_SUM_COLUMN_IDX = 5  # sum
_SORT_COLUMN_IDX = 5  # sum
_COLUMNS_ORDER = (5, 0, 1, 4, 2, 3)  # sum, name, calls, avg, min, max
_GRAND_TOTAL_STR = "grand total"


def report_measurements(
    reporter: "TerminalReporter",
    section_name: str,
    measurements: Dict[str, List[float]],
    duration_min: float = -1.0,
    durations: int = 0,
) -> NoReturn:
    """Add time measurement results to reporter."""
    time_values_all = [
        (name, len(times), min(times), max(times), median(times), sum(times)) for name, times in measurements.items()
    ]
    # verbose values are limited by minimal time and number of rows
    time_values_verbose = [values for values in time_values_all if values[_SUM_COLUMN_IDX] >= duration_min]
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

    def _reduce(idx: int, func: Callable[[Iterable[float]], float]) -> float:
        return func(times[idx] for times in time_values)

    return (
        (
            _GRAND_TOTAL_STR,
            str(_reduce(1, sum)),  # calls
            str(timedelta(seconds=_reduce(2, min))),  # min time
            str(timedelta(seconds=_reduce(3, max))),  # max time
            str(timedelta(seconds=_reduce(4, median))),  # avg time
            str(timedelta(seconds=_reduce(5, sum))),  # sum time
        )
        if time_values
        else tuple(map(str, (_GRAND_TOTAL_STR, 0, *(timedelta(),) * 4)))
    )


def _get_report_timing_rows(time_values: List[TimeValuesT]) -> List[ReportRowT]:
    """Return report time measurement rows."""
    return [
        (
            times[0],
            str(times[1]),
            str(timedelta(seconds=times[2])),
            str(timedelta(seconds=times[3])),
            str(timedelta(seconds=times[4])),
            str(timedelta(seconds=times[5])),
        )
        for times in time_values
    ]
