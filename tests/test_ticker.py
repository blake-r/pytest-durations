from datetime import datetime

from _pytest.python_api import approx
from freezegun import freeze_time

from pytest_durations.ticker import get_current_ticks


def test_get_current_ticks_frozen():
    """Time freezing should not affect tick counter."""
    ticks = get_current_ticks()
    with freeze_time(datetime(1, 1, 1)):
        frozen_ticks = get_current_ticks()
    assert frozen_ticks == approx(ticks, 0.1)
