import importlib
import sys
from unittest.mock import create_autospec

import pytest

from pytest_durations.options import pytest_addoption, pytest_configure


@pytest.fixture(autouse=True, scope="module")
def reload_module():
    # Reloading is required for proper code coverage detection
    importlib.reload(sys.modules["pytest_durations.options"])


@pytest.fixture
def fake_parser():
    return create_autospec(pytest.Parser, instance=True)


@pytest.fixture
def fake_pluginmanager():
    return create_autospec(pytest.PytestPluginManager, instance=True)


@pytest.fixture
def fake_config(fake_pluginmanager):
    return create_autospec(pytest.Config, instance=True, pluginmanager=fake_pluginmanager)


def test_pytest_addoption(fake_parser, fake_pluginmanager):
    pytest_addoption(fake_parser, fake_pluginmanager)
    assert fake_parser.getgroup.called is True
    assert fake_parser.getgroup.return_value.addoption.call_count == 4


def test_pytest_configure(fake_config, fake_pluginmanager):
    pytest_configure(fake_config)
    assert fake_pluginmanager.register.called is True


def test_pytest_configure_disabled(fake_config, fake_pluginmanager):
    fake_config.getoption.return_value = None
    pytest_configure(fake_config)
    assert fake_pluginmanager.register.called is False
