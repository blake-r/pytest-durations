"""Type declarations module."""
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
