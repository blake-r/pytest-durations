from typing import NoReturn, TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.config import PytestPluginManager, Config
    from _pytest.config.argparsing import Parser

DEFAULT_DURATIONS = 30
DEFAULT_DURATIONS_MIN = 0.005


def pytest_addoption(parser: "Parser", pluginmanager: "PytestPluginManager") -> NoReturn:
    group = parser.getgroup("pytest-durations")
    group.addoption(
        "--pytest-durations",
        metavar="N",
        type=int,
        default=DEFAULT_DURATIONS,
        help=f"Show N slowest setup/test durations (N=0 to disable plugin). Default {DEFAULT_DURATIONS}",
    )
    group.addoption(
        "--pytest-durations-min",
        metavar="N",
        type=float,
        default=DEFAULT_DURATIONS_MIN,
        help=f"Minimal duration in seconds for inclusion in slowest list. Default {DEFAULT_DURATIONS_MIN}",
    )


def pytest_configure(config: "Config") -> NoReturn:
    if not config.getoption("--pytest-durations"):
        return

    from pytest_durations.plugin import PytestDurationPlugin

    pluginmanager = config.pluginmanager

    if pluginmanager.hasplugin("xdist"):
        from pytest_durations.xdist import PytestDurationXdistMixin

        PytestDurationPlugin = type("PytestDurationPlugin", (PytestDurationPlugin, PytestDurationXdistMixin), {})

    pluginmanager.register(PytestDurationPlugin())
