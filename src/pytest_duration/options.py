from typing import NoReturn, TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.config import PytestPluginManager
    from _pytest.config.argparsing import Parser

DEFAULT_DURATIONS = 30
DEFAULT_DURATIONS_MIN = 0.005


def pytest_addoption(parser: "Parser", pluginmanager: "PytestPluginManager") -> NoReturn:
    group = parser.getgroup("pytest-duration")
    group.addoption(
        "--pytest-durations",
        metavar="N",
        type=int,
        default=DEFAULT_DURATIONS,
        help=f"Show N slowest setup/test durations (N=0 to disable report). Default {DEFAULT_DURATIONS}"
    )
    group.addoption(
        "--pytest-durations-min",
        metavar="N",
        type=float,
        default=DEFAULT_DURATIONS_MIN,
        help=f"Minimal duration in seconds for inclusion in slowest list. Default {DEFAULT_DURATIONS_MIN}"
    )
