import argparse
import importlib
import sys
from unittest.mock import create_autospec

import pytest

from pytest_durations.options import pytest_addoption, pytest_configure
from pytest_durations.types import (
    ALL_CATEGORIES,
    DEFAULT_COLUMNS,
    Category,
    parse_categories,
    parse_columns,
)


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
    assert fake_parser.getgroup.return_value.addoption.call_count == 7


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("", ALL_CATEGORIES),
        ("fixture", (Category.FIXTURE_SETUP,)),
        ("fixture,call", (Category.FIXTURE_SETUP, Category.TEST_CALL)),
        ("fixture, call", (Category.FIXTURE_SETUP, Category.TEST_CALL)),
        ("teardown,setup", (Category.TEST_TEARDOWN, Category.TEST_SETUP)),
    ],
)
def test_parse_categories(value: str, expected: tuple[Category, ...]) -> None:
    assert parse_categories(value) == expected


def test_parse_categories_unknown() -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        parse_categories("bogus")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("", DEFAULT_COLUMNS),
        ("total", ("total",)),
        ("max,min", ("max", "min")),
        ("num, med", ("num", "med")),
        ("med,min,max", ("med", "min", "max")),
    ],
)
def test_parse_columns(value: str, expected: tuple[str, ...]) -> None:
    assert parse_columns(value) == expected


def test_parse_columns_unknown() -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        parse_columns("name")


def test_pytest_configure(fake_config, fake_pluginmanager):
    pytest_configure(fake_config)
    assert fake_pluginmanager.register.called is True


def test_pytest_configure_disabled(fake_config, fake_pluginmanager):
    fake_config.getoption.return_value = None
    pytest_configure(fake_config)
    assert fake_pluginmanager.register.called is False
