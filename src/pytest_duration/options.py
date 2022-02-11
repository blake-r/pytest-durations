from typing import NoReturn, TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.config import PytestPluginManager
    from _pytest.config.argparsing import Parser


def pytest_addoption(parser: "Parser", pluginmanager: "PytestPluginManager") -> NoReturn:
    group = parser.getgroup("pytest-duration")
    group.addoption(
        "--ng-durations",
        metavar="N",
        type=int,
        default=0,
        help="Show N slowest setup/test durations (N=0 for all)"
    )
    group.addoption(
        "--ng-durations-min",
        metavar="N",
        type=float,
        default=0.005,
        help="Minimal duration in seconds for inclusion in slowest list. Default 0.005"
    )
