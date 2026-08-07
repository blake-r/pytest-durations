import pytest

from pytest_durations.reporting import (
    ReportRowT,
    TimeFormat,
    format_seconds_clock,
    format_seconds_short,
    get_report_max_widths,
    get_report_rows,
    get_selected_max_widths,
    report_column_fields,
    resolve_time_format,
)


@pytest.fixture
def sample_measurements() -> dict[str, list[float]]:
    return {
        "fixture1": [0.1, 0.2, 0.4],
        "fixture2": [1.1, 1.2, 1.4],
    }


@pytest.fixture
def expected_report_rows() -> list[ReportRowT]:
    return [
        ReportRowT("total", "name", "num", "med", "max", "min"),
        ReportRowT("0:00:03.700000", "fixture2", "3", "0:00:01.200000", "0:00:01.400000", "0:00:01.100000"),
        ReportRowT("0:00:00.700000", "fixture1", "3", "0:00:00.200000", "0:00:00.400000", "0:00:00.100000"),
        ReportRowT("0:00:04.400000", "grand total", "6", "0:00:00.700000", "0:00:01.400000", "0:00:00.100000"),
    ]


def test_get_report_rows(sample_measurements, expected_report_rows):
    """Show all fixture in the reverse order of their total time."""
    result = get_report_rows(measurements=sample_measurements)
    assert result == expected_report_rows


def test_get_report_rows_empty_result():
    """Show header and zeroed footer rows only (empty report)."""
    result = get_report_rows(measurements={})
    assert result == [
        ("total", "name", "num", "med", "max", "min"),
        ("0:00:00", "grand total", "0", "0:00:00", "0:00:00", "0:00:00"),
    ]


def test_get_report_rows_with_time_limit(sample_measurements, expected_report_rows):
    """Show fixtures with total time more than a limit (1 second)."""
    result = get_report_rows(measurements=sample_measurements, duration_min=1.0)
    del expected_report_rows[2]
    assert result == expected_report_rows


def test_get_report_rows_with_rows_limit(sample_measurements, expected_report_rows):
    """Report a single line of fixture with the top total time."""
    result = get_report_rows(measurements=sample_measurements, max_rows=1)
    del expected_report_rows[2]
    assert result == expected_report_rows


def test_get_report_max_widths(expected_report_rows):
    result = get_report_max_widths(expected_report_rows)
    assert result == (14, 11, 3, 14, 14, 14)


@pytest.mark.parametrize(
    ("selected", "expected"),
    [
        (("total", "num", "med", "max"), ("total", "name", "num", "med", "max")),
        (("max",), ("max", "name")),
        (("min", "max"), ("min", "name", "max")),
        (("med", "min", "max"), ("med", "name", "min", "max")),
    ],
)
def test_report_column_fields(selected, expected):
    """name is always the second rendered column; first selected leads."""
    assert report_column_fields(selected) == expected


@pytest.mark.parametrize(
    ("selected", "expected"),
    [
        (("total", "num", "med", "max"), (14, 11, 3, 14, 14)),
        (("max",), (14, 11)),
        (("min", "max"), (14, 11, 14)),
    ],
)
def test_get_selected_max_widths(expected_report_rows, selected, expected):
    """Widths are computed only over the actually-rendered columns."""
    assert get_selected_max_widths(expected_report_rows, selected) == expected


def test_time_format_clock():
    """clock matches the default str(timedelta(...)) output exactly."""
    assert format_seconds_clock(3.7) == "0:00:03.700000"
    assert format_seconds_clock(0.0) == "0:00:00"


def test_time_format_short():
    """short uses a compact H:MM:SS with no microseconds, days folded into hours."""
    assert format_seconds_short(3.7) == "0:00:03"
    assert format_seconds_short(0.05) == "0:00:00"
    assert format_seconds_short(90000.0) == "25:00:00"
    assert format_seconds_short(3723.5) == "1:02:03"


def test_resolve_time_format_auto_by_magnitude():
    """auto picks one form per report based on the global max duration."""
    assert resolve_time_format(TimeFormat.AUTO, max_seconds=0.5)(0.05) == "50ms"
    assert resolve_time_format(TimeFormat.AUTO, max_seconds=30.0)(3.7) == "3.700s"
    assert resolve_time_format(TimeFormat.AUTO, max_seconds=300.0)(185.0) == "3:05"
    assert resolve_time_format(TimeFormat.AUTO, max_seconds=7200.0)(3723.0) == "1:02:03"
    assert resolve_time_format(TimeFormat.AUTO, max_seconds=200000.0)(90000.0) == "1d 1:00:00"


def test_resolve_time_format_clock_and_short():
    """clock and short are resolved directly without magnitude selection."""
    assert resolve_time_format(TimeFormat.CLOCK, max_seconds=100000.0) is format_seconds_clock
    assert resolve_time_format(TimeFormat.SHORT, max_seconds=100000.0) is format_seconds_short


def test_get_report_rows_time_format_short(sample_measurements):
    """The chosen format threads through every row uniformly."""
    result = get_report_rows(
        measurements=sample_measurements,
        format_seconds=format_seconds_short,
    )
    assert result[1:] == [
        ReportRowT("0:00:03", "fixture2", "3", "0:00:01", "0:00:01", "0:00:01"),
        ReportRowT("0:00:00", "fixture1", "3", "0:00:00", "0:00:00", "0:00:00"),
        ReportRowT("0:00:04", "grand total", "6", "0:00:00", "0:00:01", "0:00:00"),
    ]
