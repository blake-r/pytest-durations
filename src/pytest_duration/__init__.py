from typing import NoReturn

from _pytest.config import Config

from pytest_duration.options import pytest_addoption
from pytest_duration.plugin import PytestDurationPlugin

__version__ = '0.1.0'


def pytest_configure(config: "Config") -> NoReturn:
    if not config.getoption("--pytest-durations"):
        return
    config.pluginmanager.register(PytestDurationPlugin())
