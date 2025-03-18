import pathlib

import pytest
from _pytest.pytester import LineMatcher

SAMPLE_RESULT_LOG_NAME = "result.log"
SAMPLE_RESULT_LOG_FIRST_LINE = "thefirstline\n"


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


@pytest.fixture
def sample_result_log():
    result_log = pathlib.Path(SAMPLE_RESULT_LOG_NAME)
    with result_log.open("wt") as fp:
        fp.write(SAMPLE_RESULT_LOG_FIRST_LINE)
    yield result_log
    result_log.unlink(missing_ok=False)


@pytest.fixture
def expected_output_lines():
    return [
        "*fixture duration top*",
        "*grand total   7*",
        "*test call duration top*",
        "*grand total   2*",
        "*test setup duration top*",
        "*grand total   2*",
        "*test teardown duration top*",
        "*grand total   2*",
    ]


@pytest.mark.parametrize(
    "options",
    (
        (),
        ("--pytest-durations", "1"),
        ("--pytest-durations-min", "0"),
    ),
)
def test_plugin_with_options(pytester, sample_testfile, options, expected_output_lines):
    """Plugin should show the same grand total lines for provided options."""
    result = pytester.runpytest(*options)
    result.assert_outcomes(passed=2)
    result.stdout.fnmatch_lines(expected_output_lines)


def test_plugin_with_resultlog(pytester, sample_testfile, sample_result_log, expected_output_lines):
    """Plugin should append summary to a file if the result log option is provided."""
    expected_output_lines = [SAMPLE_RESULT_LOG_FIRST_LINE, *expected_output_lines]
    result = pytester.runpytest(*("--pytest-resultlog", SAMPLE_RESULT_LOG_NAME))
    result.assert_outcomes(passed=2)
    with sample_result_log.open("rt") as fp:
        lines = LineMatcher(fp.readlines())
    lines.fnmatch_lines(expected_output_lines)


def test_plugin_disable(pytester, sample_testfile):
    """Zero durations value should disable plugin completely."""
    result = pytester.runpytest("--pytest-durations", "0")
    result.assert_outcomes(passed=2)
    result.stdout.no_fnmatch_line("*duration top*")


def test_plugin_xdist_disabled(pytester, sample_testfile):
    """Run when pytest-xdist is absent or disabled should be successful (#3)."""
    result = pytester.runpytest("-p", "no:xdist")
    result.assert_outcomes(passed=2)


def test_plugin_xdist_enabled(pytester, sample_testfile):
    """Run when pytest-xdist is enabled should be successful (#3)."""
    result = pytester.runpytest("--numprocesses", "2")
    result.assert_outcomes(passed=2)
