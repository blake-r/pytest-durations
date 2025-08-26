"""Plugin command line arguments parsing module."""
from typing import TYPE_CHECKING

from pytest_durations.types import GroupBy

if TYPE_CHECKING:
    from _pytest.config import Config, PytestPluginManager
    from _pytest.config.argparsing import Parser

DEFAULT_DURATIONS = 30
DEFAULT_DURATIONS_MIN = 0.005
DEFAULT_RESULT_LOG = "-"


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
        default=GroupBy.FUNCTION,
        choices=[*GroupBy],
        help=f'Group test durations by module, class, or function.'
             f' Use legacy grouping for backward compatibility.'
             f' Default: "{GroupBy.FUNCTION}"',
    )


def pytest_configure(config: "Config") -> None:
    """Configure plugin options using command line arguments."""
    if not config.getoption("--pytest-durations"):
        return

    from pytest_durations.plugin import PytestDurationPlugin

    pluginmanager = config.pluginmanager

    if pluginmanager.hasplugin("xdist"):
        from pytest_durations.xdist import PytestDurationXdistMixin

        PytestDurationPlugin = type("PytestDurationPlugin", (PytestDurationPlugin, PytestDurationXdistMixin), {})  # noqa: N806

    pluginmanager.register(PytestDurationPlugin())
