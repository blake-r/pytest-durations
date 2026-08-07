"""Type declarations module."""
from argparse import ArgumentTypeError
from collections.abc import Iterator
from enum import Enum


class CategoryMeta(type):
    """Category should be a plain string, but compatible with Enum class iterator."""

    def __iter__(cls) -> Iterator[str]:
        """Return enumeration of class field values."""
        return (v for k, v in cls.__dict__.items() if not k.startswith("__"))


class Category(metaclass=CategoryMeta):
    """Measurement category constants."""

    FIXTURE_SETUP = "fixture"
    TEST_CALL = "test call"
    TEST_SETUP = "test setup"
    TEST_TEARDOWN = "test teardown"


class StrEnum(str, Enum):
    """Enum for string values that proxies their behavior."""

    def __str__(self) -> str:
        """Return the current value (expected to be a string)."""
        return self.value


class GroupBy(StrEnum):
    """Possible test grouping enumeration."""

    LEGACY = "legacy"
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    NONE = "none"


class TimeFormat(StrEnum):
    """Possible duration formatting modes for the report."""

    CLOCK = "clock"
    SHORT = "short"
    AUTO = "auto"


ALL_CATEGORIES: tuple[Category, ...] = tuple(Category)

# Selectable stat columns for --pytest-durations-columns. Each key is a selectable
# column name (also a ReportRowT field); its value is the TimeValuesT field used for
# sorting. The row key ("name") is always shown separately and can never be selected
# or used as a sort field.
COLUMN_NAMES: dict[str, str] = {
    "num": "calls",
    "min": "min",
    "max": "max",
    "med": "med",
    "total": "sum",
}

DEFAULT_COLUMNS: tuple[str, ...] = ("total", "num", "med", "max")

CATEGORY_NAMES: dict[str, Category] = {
    "fixture": Category.FIXTURE_SETUP,
    "call": Category.TEST_CALL,
    "setup": Category.TEST_SETUP,
    "teardown": Category.TEST_TEARDOWN,
}


def parse_categories(value: str) -> tuple[Category, ...]:
    """Parse a comma-separated list of section names into an ordered tuple of categories.

    An empty value selects every category.
    """
    if not value:
        return ALL_CATEGORIES
    parsed: list[Category] = []
    for raw_name in value.split(","):
        name = raw_name.strip()
        try:
            parsed.append(CATEGORY_NAMES[name])
        except KeyError:
            choices = ", ".join(CATEGORY_NAMES)
            message = f"unknown section {name!r}; choose from: {choices}"
            raise ArgumentTypeError(message) from None
    return tuple(parsed)


def parse_columns(value: str) -> tuple[str, ...]:
    """Parse a comma-separated list of stat column names into an ordered tuple.

    An empty value selects the default column set.
    """
    if not value:
        return DEFAULT_COLUMNS
    parsed: list[str] = []
    for raw_name in value.split(","):
        name = raw_name.strip()
        if name not in COLUMN_NAMES:
            choices = ", ".join(COLUMN_NAMES)
            message = f"unknown column {name!r}; choose from: {choices}"
            raise ArgumentTypeError(message)
        parsed.append(name)
    return tuple(parsed)
