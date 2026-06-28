import pytest

pytest_plugins = ["pytester"]


@pytest.fixture(scope="session")
def package_level():
    ...
