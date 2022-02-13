from typing import List, Iterable

import pytest

_EXPECTED_OUTPUT_LINES = [
    "fixture duration top",
    "grand total   7",
    "test call duration top",
    "grand total   2",
    "test setup duration top",
    "grand total   2",
    "test teardown duration top",
    "grand total   2",
]


@pytest.fixture(autouse=True)
def sample_testfile(pytester):
    code = """
        import pytest

        @pytest.fixture
        def fixture_default():
            return None
            
        @pytest.fixture(autouse=True)
        def fixture_autouse():
            return None

        @pytest.fixture(scope="session")
        def fixture_session():
            return None

        @pytest.fixture(scope="module")
        def fixture_module():
            return None

        @pytest.fixture(scope="class")
        def fixture_class():
            return None

        @pytest.fixture(scope="function")
        def fixture_function():
            return None

        def test_function1(fixture_default):
            assert True

        def test_function2(fixture_session, fixture_module, fixture_class, fixture_function):
            assert True
    """
    pytester.makepyfile(code)


def test_basic(pytester, sample_testfile):
    result = pytester.runpytest()
    result.assert_outcomes(passed=2)
    _assert_output_lines(result.outlines, _EXPECTED_OUTPUT_LINES)


def test_durations_min_option(pytester, sample_testfile):
    result = pytester.runpytest("--pytest-durations-min", "0")
    result.assert_outcomes(passed=2)
    _assert_output_lines(result.outlines, _EXPECTED_OUTPUT_LINES)


def test_xdist(pytester, sample_testfile):
    result = pytester.runpytest("-n", "2")
    result.assert_outcomes(passed=2)
    _assert_output_lines(result.outlines, _EXPECTED_OUTPUT_LINES)


def _assert_output_lines(outlines: Iterable[str], expected_lines: List[str]):
    outlines_iter = iter(outlines)
    for expected_line in expected_lines:
        found = False
        lines = []
        for outline in outlines_iter:
            if expected_line in outline:
                found = True
                break
            lines.append(outline)
        if not found:
            raise AssertionError(f"Line `{expected_line}` is not found in output", lines)
