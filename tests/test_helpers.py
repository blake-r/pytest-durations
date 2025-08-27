from unittest.mock import create_autospec

import pytest
from _pytest.nodes import Item

from pytest_durations.helpers import _get_test_key


class TestScope:
    @pytest.fixture
    def sample(self):
        return ""


    @pytest.mark.parametrize("param", [None, "param", "param1-param2"])
    @pytest.mark.parametrize(
        ("nodeid", "expected"),
        [
            ("func", "func"),
            ("filename.py::func", "func"),
            ("filename.py::scope::func", "scope::func"),
        ],
    )
    def test_get_test_key(self, nodeid, param, expected, sample):
        """Filename and parameters should be removed from test key."""
        if param:
            nodeid = f"{nodeid}[{param}]"
        item = create_autospec(Item, instance=True, nodeid=nodeid)
        result = _get_test_key(item)
        assert result == expected
