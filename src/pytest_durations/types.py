"""Type declarations module."""
from enum import Enum


class StrEnum(str, Enum):
    """Enum for string values that proxies their behavior."""

    def __str__(self) -> str:
        """Return the current value (expected to be a string)."""
        return self.value

    def save(self) -> str:
        """Serialize StrEnum to a plain string."""
        return self.name

    @classmethod
    def load(cls, name: str) -> "StrEnum":
        """Deserialize StrEnum from a plain string."""
        return cls[name]


class Category(StrEnum):
    """Measurement category constants."""

    FIXTURE_SETUP = "fixture"
    TEST_CALL = "test call"
    TEST_SETUP = "test setup"
    TEST_TEARDOWN = "test teardown"


class GroupBy(StrEnum):
    """Possible test grouping enumeration."""

    LEGACY = "legacy"
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
