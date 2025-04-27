"""Internal helper functions module."""
import contextlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureDef
    from _pytest.nodes import Item


def _get_fixture_key(fixturedef: "FixtureDef") -> str:
    """Return fixture name."""
    return fixturedef.argname


def _get_test_key(item: "Item") -> str:
    """Return test item name without filename part (class and function names only)."""
    key = item.nodeid
    with contextlib.suppress(IndexError):
        # remove filename
        key = key.split("::", 1)[1]
    # remove parameters
    return key.split("[", 1)[0]


def _is_shared_fixture(fixturedef: "FixtureDef") -> bool:
    """Return true if a fixture is shared."""
    return fixturedef.scope != "function"
