from typing import TYPE_CHECKING, cast

import pytest

from pytest_durations.helpers import (
    _GROUPING_FUNC_MAP,
    _get_grouping_func,
    get_fixture_key,
    get_grouped_measurements,
    get_test_key,
    is_shared_fixture,
)
from pytest_durations.types import GroupBy

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest, SubRequest

    from pytest_durations.helpers import MeasurementItemT
    from pytest_durations.typing import FunctionKeyT, FunctionMeasurementsT


@pytest.fixture
def module_level():
    ...


class TestIsSharedFixture:
    @pytest.fixture
    def scoped(self):
        ...

    @pytest.fixture(scope="class")
    def shared(self):
        ...

    @pytest.mark.parametrize(
        "rule",
        [
            (module_level.__name__, False),
            (scoped.__name__, False),
            (shared.__name__, True),
        ],
    )
    @pytest.mark.usefixtures("module_level", "scoped", "shared")
    def test_is_shared_fixture(self, request: "FixtureRequest", rule):
        fixture, expected = rule
        fixturedef = request._fixture_defs[fixture]
        assert is_shared_fixture(fixturedef) is expected


class TestGetFixtureKey:
    @pytest.fixture(scope="class")
    def class_level(self):
        ...

    @pytest.mark.parametrize(
        "rule",
        [
            (module_level.__name__, "tests/test_helpers.py::module_level"),
            (class_level.__name__, "tests/test_helpers.py::TestGetFixtureKey::class_level"),
            ("rule", "tests/test_helpers.py::TestGetFixtureKey::test_get_fixture_key[rule2]::rule"),
        ],
    )
    @pytest.mark.usefixtures("module_level", "class_level")
    def test_get_fixture_key(self, request: "FixtureRequest",  rule):
        fixture, expected = rule
        fixturedef = request._fixture_defs[fixture]
        result = get_fixture_key(fixturedef=fixturedef, item=request.node)
        assert result == expected


class TestGetTestKey:
    def test_get_test_key(self, request: "FixtureRequest"):
        result = get_test_key(item=request.node)
        assert result == "tests/test_helpers.py::TestGetTestKey::test_get_test_key"

    @pytest.mark.parametrize("param", [None])
    def test_get_test_key_parametrized(self, request: "FixtureRequest", param):
        result = get_test_key(item=request.node)
        assert result == "tests/test_helpers.py::TestGetTestKey::test_get_test_key_parametrized[None]"


class TestGetGroupingFunc:
    @pytest.fixture(params=[*GroupBy])
    def group_by(self, request: "SubRequest"):
        return request.param

    @pytest.fixture(params=["test", "fixture"])
    def kind(self, request: "SubRequest"):
        return request.param

    def test_get_grouping_func(self, group_by, kind):
        result = _get_grouping_func(kind=kind, group_by=group_by)
        assert callable(result) is True

    def test_get_grouping_func_invalid(self):
        with pytest.raises(NotImplementedError) as exc:
            _get_grouping_func(kind="test", group_by=cast("GroupBy", "invalid"))
        assert exc.match('Test grouping function for "invalid" not implemented')


class TestGetGroupedMeasurements:
    @pytest.fixture(scope="class")
    def measurements(self) -> "FunctionMeasurementsT":
        return {
            "module.py::scope::function": [1.0],
            "module.py::scope": [2.0],
            "module.py": [3.0],
        }

    @pytest.mark.parametrize(
        "rule",
        [
            (1, {"module.py::scope::function": [1.0], "module.py::scope": [2.0], "module.py": [3.0]}),
            (2, {"module.py::scope": [1.0, 2.0], "module.py": [3.0]}),
            (3, {"module.py": [1.0, 2.0, 3.0]}),
        ],
    )
    def test_get_grouped_measurements(self, measurements, rule):
        def grouping_func(item: "MeasurementItemT") -> "FunctionKeyT":
            return item[0].rsplit("::", depth)[0]

        depth, expected = rule
        get_grouped_measurements(measurements=measurements, grouping_func=grouping_func)


class TestTestGroupBy:
    @pytest.fixture
    def assertion(self, rule):
        def assertion(group_by: "GroupBy") -> bool:
            (sample, expected), grouping_func = rule, _GROUPING_FUNC_MAP["test"][group_by]
            result = grouping_func((sample, [1.0]))
            return result == expected

        return assertion

    @pytest.mark.parametrize(
        "rule",
        [
            ("module.py::scope::function", "scope::function"),
            ("module.py::function", "function"),
            ("function", "function"),
        ],
    )
    def test_group_by_legacy(self, assertion, rule):
        assert assertion(group_by=GroupBy.LEGACY) is True

    @pytest.mark.parametrize(
        "rule",
        [
            ("module.py::scope::function", "module.py"),
            ("module.py::function", "module.py"),
            ("function", "uncertain"),
        ],
    )
    def test_group_by_module(self, assertion, rule):
        assert assertion(group_by=GroupBy.MODULE) is True

    @pytest.mark.parametrize(
        "rule",
        [
            ("module.py::scope::function", "module.py::scope"),
            ("module.py::function", "module.py::"),
            ("function", "uncertain::function"),
        ],
    )
    def test_group_by_class(self, assertion, rule):
        assert assertion(group_by=GroupBy.CLASS) is True

    @pytest.mark.parametrize(
        "rule",
        [
            ("module.py::scope::function", "module.py::scope::function"),
            ("module.py::function", "module.py::function"),
            ("function", "function"),
        ],
    )
    def test_group_by_function(self, assertion, rule):
        assert assertion(group_by=GroupBy.FUNCTION) is True


class TestFixtureGroupBy:
    @pytest.fixture
    def assertion(self, rule):
        def assertion(group_by: "GroupBy") -> bool:
            (sample, expected), grouping_func = rule, _GROUPING_FUNC_MAP["fixture"][group_by]
            result = grouping_func((sample, []))
            return result == expected

        return assertion

    @pytest.mark.parametrize(
        "rule",
        [
            ("module.py::scope::function::fixture", "fixture"),
            ("module.py::scope::fixture", "fixture"),
            ("module.py::function::fixture", "fixture"),
            ("module.py::fixture", "fixture"),
            ("fixture", "fixture"),
        ],
    )
    def test_group_by_legacy(self, assertion, rule):
        assert assertion(group_by=GroupBy.LEGACY) is True

    @pytest.mark.parametrize(
        "rule",
        [
            ("module.py::scope::function::fixture", "module.py"),
            ("module.py::scope::fixture", "module.py"),
            ("module.py::function::fixture", "module.py"),
            ("module.py::fixture", "module.py"),
            ("fixture", "uncertain"),
        ],
    )
    def test_group_by_module(self, assertion, rule):
        assert assertion(group_by=GroupBy.MODULE) is True

    @pytest.mark.parametrize(
        "rule",
        [
            ("module.py::scope::function::fixture", "module.py::scope::function"),
            ("module.py::scope::fixture", "module.py::scope"),
            ("module.py::function::fixture", "module.py::function"),
            ("module.py::fixture", "module.py::"),
            ("fixture", "uncertain::fixture"),
        ],
    )
    def test_group_by_class(self, assertion, rule):
        assert assertion(group_by=GroupBy.CLASS) is True

    @pytest.mark.parametrize(
        "rule",
        [
            ("module.py::scope::function::fixture", "module.py::scope::function::fixture"),
            ("module.py::scope::fixture", "module.py::scope::fixture"),
            ("module.py::function::fixture", "module.py::function::fixture"),
            ("module.py::fixture", "module.py::fixture"),
            ("fixture", "fixture"),
        ],
    )
    def test_group_by_function(self, assertion, rule):
        assert assertion(group_by=GroupBy.FUNCTION) is True
