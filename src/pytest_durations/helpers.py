"""Internal helper functions module."""
from collections.abc import Mapping
from contextlib import suppress
from functools import partial
from itertools import chain, groupby
from operator import itemgetter
from typing import TYPE_CHECKING, Callable, Literal

from pytest_durations.types import GroupBy

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureDef
    from _pytest.nodes import Item

    from pytest_durations.typing import DurationListT, FunctionKeyT, FunctionMeasurementsT

    MeasurementItemT = tuple[FunctionKeyT, DurationListT]
    GroupingCbT = Callable[[MeasurementItemT], FunctionKeyT]
    GroupingKindT = Literal["test", "fixture"]


def is_shared_fixture(fixturedef: "FixtureDef") -> bool:
    """Return true if a fixture is shared."""
    return fixturedef.scope != "function"


def get_fixture_key(fixturedef: "FixtureDef", item: "Item") -> "FunctionKeyT":
    """Return fixture measurements dict key."""
    baseid = fixturedef.baseid if fixturedef.baseid else get_test_key(item=item)
    return "::".join(filter(None, (baseid, fixturedef.argname)))


def get_test_key(item: "Item") -> "FunctionKeyT":
    """Return test item measurements dict key."""
    return item.nodeid.split("[", 1)[0]


def _get_grouping_func(kind: "GroupingKindT", group_by: "GroupBy") -> "GroupingCbT":
    """Get fixture key grouping function based on a GroupBy enumeration value."""
    with suppress(KeyError):
        return _GROUPING_FUNC_MAP[kind][group_by]
    msg = f'{kind.capitalize()} grouping function for "{group_by}" not implemented'
    raise NotImplementedError(msg)


get_test_grouping_func = partial(_get_grouping_func, kind="test")
get_fixture_grouping_func = partial(_get_grouping_func, kind="fixture")


def get_grouped_measurements(
    measurements: "FunctionMeasurementsT",
    grouping_func: "GroupingCbT",
) -> "FunctionMeasurementsT":
    """Group test measurements using a provided function to get grouping keys."""
    return {
        k: list(chain(*map(itemgetter(1), v)))
        for k, v in groupby(sorted(measurements.items(), key=grouping_func), key=grouping_func)
    }


def _test_group_by_legacy(item: "MeasurementItemT") -> "FunctionKeyT":
    # keep class and test name only (old behaviour before grouping)
    return item[0].split("::", 1)[-1]


def _fixture_group_by_legacy(item: "MeasurementItemT") -> "FunctionKeyT":
    # keep fixture name only (old behaviour before grouping)
    return item[0].rsplit("::", 1)[-1]


def _group_by_module(item: "MeasurementItemT") -> "FunctionKeyT":
    # remove class and test name (keep file name)
    with suppress(IndexError):
        return item[0].split("::", 1)[-2]
    return "uncertain"


def _group_by_class(item: "MeasurementItemT") -> "FunctionKeyT":
    # remove test name (keep file and class name)
    with suppress(IndexError):
        mod = item[0].split("::", 1)[-2]
        cls = item[0].rsplit("::", 1)[-2]
        return cls if cls != mod else f"{mod}::"
    return f"uncertain::{item[0]}"


def _group_by_function(item: "MeasurementItemT") -> "FunctionKeyT":
    # keep name as is
    return item[0]


_GROUPING_FUNC_MAP: Mapping["GroupingKindT", Mapping["GroupBy", "GroupingCbT"]] = {
    "test": {
        GroupBy.LEGACY: _test_group_by_legacy,
        GroupBy.MODULE: _group_by_module,
        GroupBy.CLASS: _group_by_class,
        GroupBy.FUNCTION: _group_by_function,
    },
    "fixture": {
        GroupBy.LEGACY: _fixture_group_by_legacy,
        GroupBy.MODULE: _group_by_module,
        GroupBy.CLASS: _group_by_class,
        GroupBy.FUNCTION: _group_by_function,
    },
}
