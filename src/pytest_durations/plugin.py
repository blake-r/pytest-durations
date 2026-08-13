"""Plugin main implementation logic."""
from collections.abc import Iterable
from contextlib import ExitStack, contextmanager
from itertools import count
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from pytest_durations.helpers import (
    get_fixture_grouping_func,
    get_fixture_key,
    get_grouped_measurements,
    get_test_grouping_func,
    get_test_key,
    is_shared_fixture,
)
from pytest_durations.json_exporter import export_json
from pytest_durations.measure import MeasureDuration
from pytest_durations.options import DEFAULT_RESULT_LOG
from pytest_durations.reporting import (
    get_report_rows,
    get_selected_max_widths,
    report_column_fields,
    resolve_time_format,
)
from pytest_durations.ticker import get_current_ticks
from pytest_durations.types import COLUMN_NAMES, Category

if TYPE_CHECKING:
    from _pytest.config import Config, ExitCode
    from _pytest.fixtures import FixtureDef, SubRequest
    from _pytest.nodes import Item
    from _pytest.terminal import TerminalReporter

    from pytest_durations.typing import CategoryMeasurementsT, FunctionKeyT


class PytestDurationPlugin:
    """Main plugin implementation to measure test and fixture function durations."""

    measurements: "CategoryMeasurementsT"
    shared_fixture_duration: float
    last_fixture_teardown_start: float

    def __init__(self):
        super().__init__()
        self.measurements = {category: {} for category in Category}
        self.shared_fixture_duration = 0.0
        self.last_fixture_teardown_start = 0.0

    @pytest.hookimpl(hookwrapper=True)
    def pytest_fixture_setup(self, fixturedef: "FixtureDef", request: "SubRequest") -> Any | None:
        """Measure fixture setup execution duration."""
        fixture_key = get_fixture_key(fixturedef=fixturedef, item=request.node)

        with self._measure(Category.FIXTURE_SETUP, fixture_key) as measurement:
            yield

        if is_shared_fixture(fixturedef):
            # for shared fixtures, store their last setup duration
            self.shared_fixture_duration += measurement.duration

    def pytest_fixture_post_finalizer(self, fixturedef: "FixtureDef", request: "SubRequest") -> None:
        """Calculate fixture teardown execution duration."""
        teardown_end = get_current_ticks()
        if is_shared_fixture(fixturedef):
            # for shared scope fixture teardowns, store their last duration
            duration = teardown_end - self.last_fixture_teardown_start
            self.shared_fixture_duration += duration
        # last fixture duration should always be updated
        self.last_fixture_teardown_start = teardown_end

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_call(self, item: "Item") -> None:
        """Measure test execution duration."""
        with self._measure(Category.TEST_CALL, get_test_key(item)):
            yield

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_setup(self, item: "Item") -> None:
        """Measure test fixtures preparing time.

        Excludes time taken by setting up of shared fixtures.
        """
        with self._measure(Category.TEST_SETUP, get_test_key(item)) as measurement:
            yield
            # subtract time taken by shared fixture initializations (if any)
            measurement.duration -= self.shared_fixture_duration
        self.shared_fixture_duration = 0.0

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_teardown(self, item: "Item") -> None:
        """Measure test fixture cleaning up time.

        Excludes time taken by tearing down of shared fixtures.
        """
        with self._measure(Category.TEST_TEARDOWN, get_test_key(item)) as measurement:
            self.last_fixture_teardown_start = get_current_ticks()
            yield
            # subtract time taken by shared fixture finalizations (if any)
            measurement.duration -= self.shared_fixture_duration
        self.shared_fixture_duration = 0.0

    def pytest_terminal_summary(
        self,
        terminalreporter: "TerminalReporter",
        exitstatus: "ExitCode",
        config: "Config",
    ) -> None:
        """Write the measured time to a terminal reporter or to a file."""
        durations = config.getoption("--pytest-durations")
        result_log = config.getoption("--pytest-durations-log")
        json_output = config.getoption("--pytest-durations-json")
        if json_output:
            export_json(measurements=self.measurements, filename=json_output)
        if not durations:
            return
        with ExitStack() as stack:
            if result_log != DEFAULT_RESULT_LOG:
                result_log_fp = stack.enter_context(Path(result_log).open(mode="a"))
                terminalreporter = type(terminalreporter)(config=config, file=result_log_fp)
            self._report_summary(terminalreporter=terminalreporter, config=config)

    def _report_summary(self, terminalreporter: "TerminalReporter", config: "Config") -> None:
        """Write time report to the specified terminal reporter."""
        fullwidth = terminalreporter._tw.fullwidth  # noqa: SLF001
        durations = config.getoption("--pytest-durations")
        durations_min = config.getoption("--pytest-durations-min")
        reports = []
        group_by = config.getoption("--pytest-durations-group-by")
        time_format = config.getoption("--pytest-durations-time-format")
        test_grouping_func = get_test_grouping_func(group_by=group_by)
        fixture_grouping_func = get_fixture_grouping_func(group_by=group_by)
        selected_columns = config.getoption("--pytest-durations-columns")
        sort_by = COLUMN_NAMES[selected_columns[0]]
        max_duration = max(
            (
                max(times)
                for measurements in self.measurements.values()
                for times in measurements.values()
                if times
            ),
            default=0.0,
        )
        format_seconds = resolve_time_format(time_format=time_format, max_seconds=max_duration)
        selected_categories = config.getoption("--pytest-durations-show")
        for category in selected_categories:
            grouping_func = test_grouping_func if category is not Category.FIXTURE_SETUP else fixture_grouping_func
            category_measurements = get_grouped_measurements(
                grouping_func=grouping_func,
                measurements=self.measurements[category],
            )
            category_report_rows = get_report_rows(
                measurements=category_measurements,
                duration_min=durations_min,
                max_rows=durations,
                sort_by=sort_by,
                format_seconds=format_seconds,
            )
            reports.append((f"{category} duration top", category_report_rows))
        rendered_columns = report_column_fields(selected_columns)
        all_rows = [row for _, rows in reports for row in rows]
        widths = get_selected_max_widths(all_rows, selected_columns)
        fullwidth = max(fullwidth, sum(widths) + len(widths) - 1)
        for section_name, category_report_rows in reports:
            terminalreporter.write_sep(sep="=", title=section_name, fullwidth=fullwidth)
            for idx, row in enumerate(category_report_rows):
                # align columns right except test name column
                content = " ".join(
                    f"{getattr(row, col):{'>' if idx and c else '<'}{width}}"
                    for col, width, c in zip(rendered_columns, widths, count(-1))
                )
                terminalreporter.line(content)

    @contextmanager
    def _measure(self, category: "Category", key: "FunctionKeyT") -> Iterable["MeasureDuration"]:
        """Measure wrapping block execution time and put it into a dict."""
        measurements = self.measurements[category]

        with MeasureDuration() as measurement:
            yield measurement

        try:
            measurements[key].append(measurement.duration)
        except KeyError:
            measurements[key] = [measurement.duration]
