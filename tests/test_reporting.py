import pytest

from pytest_durations.reporting import get_report_max_widths, get_report_rows


@pytest.fixture
def sample_measurements() -> dict[str, list[float]]:
    return {
        "fixture1": [0.1, 0.2, 0.4],
        "fixture2": [1.1, 1.2, 1.4],
    }


@pytest.fixture
def expected_report_rows() -> list[tuple[str, str, str, str, str, str]]:
    return [
        ("total", "name", "num", "avg", "min", "max"),
        ("0:00:03.700000", "fixture2", "3", "0:00:01.200000", "0:00:01.100000", "0:00:01.400000"),
        ("0:00:00.700000", "fixture1", "3", "0:00:00.200000", "0:00:00.100000", "0:00:00.400000"),
        ("0:00:04.400000", "grand total", "6", "0:00:00.700000", "0:00:00.100000", "0:00:01.400000"),
    ]


def test_get_report_rows(sample_measurements, expected_report_rows):
    """Show all fixture in the reverse order of their total time."""
    result = get_report_rows(measurements=sample_measurements)
    assert result == expected_report_rows


def test_get_report_rows_empty_result():
    """Show header and zeroed footer rows only (empty report)."""
    result = get_report_rows(measurements={})
    assert result == [
        ("total", "name", "num", "avg", "min", "max"),
        ("0:00:00", "grand total", "0", "0:00:00", "0:00:00", "0:00:00"),
    ]


def test_get_report_rows_with_time_limit(sample_measurements, expected_report_rows):
    """Show fixtures with total time more than a limit (1 second)."""
    result = get_report_rows(measurements=sample_measurements, duration_min=1.0)
    del expected_report_rows[2]
    assert result == expected_report_rows


def test_get_report_rows_with_rows_limit(sample_measurements, expected_report_rows):
    """Report a single line of fixture with the top total time."""
    result = get_report_rows(measurements=sample_measurements, durations=1)
    del expected_report_rows[2]
    assert result == expected_report_rows


def test_get_report_max_widths(expected_report_rows):
    result = get_report_max_widths(expected_report_rows)
    assert result == (14, 11, 3, 14, 14, 14)
