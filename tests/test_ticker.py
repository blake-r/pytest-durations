import sys
from datetime import datetime
from importlib import import_module
from typing import Callable, NamedTuple
from unittest.mock import patch

import pytest
from _pytest.python_api import approx
from freezegun import freeze_time
from pytz import UTC
from time_machine import travel

from pytest_durations.ticker import get_current_ticks


class TimeHack(NamedTuple):
    module: str
    context: Callable


@pytest.fixture(
    params=[TimeHack("freezegun", freeze_time), TimeHack("time_machine", travel)],
    ids=["freezegun", "time_machine"],
)
def time_hack(request: "pytest.FixtureRequest") -> TimeHack:
    return request.param


def test_freezegun_import_error(time_hack):
    """Import when freezegun is not installed should be successful."""
    sys.modules.pop("pytest_durations.ticker", None)  # remove already imported ticker
    with patch.dict(sys.modules, values={time_hack.module: None}, clear=False):
        module = import_module("pytest_durations.ticker")
    assert time_hack.module not in module.__dict__


def test_get_current_ticks_frozen(time_hack):
    """Time freezing should not affect tick counter."""
    ticks = get_current_ticks()
    with time_hack.context(datetime(1, 1, 1, tzinfo=UTC)):
        frozen_ticks = get_current_ticks()
    assert frozen_ticks == approx(ticks, 0.1)
