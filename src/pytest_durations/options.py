"""Plugin command line arguments parsing module."""
from typing import TYPE_CHECKING

from pytest_durations.types import (
    ALL_CATEGORIES,
    DEFAULT_COLUMNS,
    GroupBy,
    TimeFormat,
    parse_categories,
    parse_columns,
)

if TYPE_CHECKING:
    from _pytest.config import Config, PytestPluginManager
    from _pytest.config.argparsing import Parser

DEFAULT_DURATIONS = 30
DEFAULT_DURATIONS_MIN = 0.005
DEFAULT_RESULT_LOG = "-"
DEFAULT_GROUP_BY = GroupBy.FUNCTION
DEFAULT_TIME_FORMAT = TimeFormat.CLOCK
DEFAULT_SHOW_SECTIONS = ALL_CATEGORIES


def pytest_addoption(parser: "Parser", pluginmanager: "PytestPluginManager") -> None:
    """Add command line arguments parsing."""
    group = parser.getgroup("pytest-durations")
    group.addoption(
        "--pytest-durations",
        metavar="N",
        type=int,
        default=DEFAULT_DURATIONS,
        help=f"Show N slowest setup/test durations (N=0 to disable plugin)."
             f" Default {DEFAULT_DURATIONS}",
    )
    group.addoption(
        "--pytest-durations-min",
        metavar="N",
        type=float,
        default=DEFAULT_DURATIONS_MIN,
        help=f"Minimal duration in seconds for inclusion in slowest list."
             f" Default {DEFAULT_DURATIONS_MIN}",
    )
    group.addoption(
        "--pytest-durations-log",
        "--pytest-resultlog",  # deprecated
        metavar="FILE",
        type=str,
        default=DEFAULT_RESULT_LOG,
        help=f'Result log filename or dash for terminal output.'
             f' Default "{DEFAULT_RESULT_LOG}"',
    )
    group.addoption(
        "--pytest-durations-group-by",
        type=GroupBy,
        default=DEFAULT_GROUP_BY,
        choices=[*GroupBy],
        help=f'Group test durations by module, class, or function.'
             f' Use legacy grouping for backward compatibility.'
             f' Default: "{DEFAULT_GROUP_BY}"',
    )
    group.addoption(
        "--pytest-durations-time-format",
        type=TimeFormat,
        default=DEFAULT_TIME_FORMAT,
        choices=[*TimeFormat],
        help=f'How to format durations in the report.'
             f' "clock" shows the full datetime-style value, "short" a compact H:MM:SS,'
             f' and "auto" picks one readable form based on the report magnitude.'
             f' Default: "{DEFAULT_TIME_FORMAT}"',
    )
    group.addoption(
        "--pytest-durations-show",
        metavar="SECTIONS",
        type=parse_categories,
        default=DEFAULT_SHOW_SECTIONS,
        help='Comma-separated list of report sections to show: "fixture", "call",'
             ' "setup", "teardown". Default: show all sections.',
    )
    group.addoption(
        "--pytest-durations-columns",
        metavar="COLUMNS",
        type=parse_columns,
        default=DEFAULT_COLUMNS,
        help='Comma-separated list of stat columns to show: "total", "num", "min",'
             ' "med", "max". The test/fixture name is always shown second, and the'
             ' first listed column is used to sort the report.'
             f' Default: {",".join(DEFAULT_COLUMNS)}.',
    )


def pytest_configure(config: "Config") -> None:
    """Configure plugin options using command line arguments."""
    if not config.getoption("--pytest-durations"):
        return

    from pytest_durations.plugin import PytestDurationPlugin  # noqa: PLC0415

    pluginmanager = config.pluginmanager

    if pluginmanager.hasplugin("xdist"):
        from pytest_durations.xdist import PytestDurationXdistMixin  # noqa: PLC0415

        PytestDurationPlugin = type("PytestDurationPlugin", (PytestDurationPlugin, PytestDurationXdistMixin), {})  # noqa: N806

    pluginmanager.register(PytestDurationPlugin())
