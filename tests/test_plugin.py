import pytest

_EXPECTED_OUTPUT_LINES = [
    "*fixture duration top*",
    "*grand total   7*",
    "*test call duration top*",
    "*grand total   2*",
    "*test setup duration top*",
    "*grand total   2*",
    "*test teardown duration top*",
    "*grand total   2*",
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


@pytest.mark.parametrize(
    "options",
    (
        (),
        ("--pytest-durations", "1"),
        ("--pytest-durations-min", "0"),
    ),
)
def test_plugin_with_options(pytester, sample_testfile, options):
    """Plugin should show the same grand total lines for provided options."""
    result = pytester.runpytest(*options)
    result.assert_outcomes(passed=2)
    result.stdout.fnmatch_lines(_EXPECTED_OUTPUT_LINES)


def test_plugin_disable(pytester, sample_testfile):
    """Zero durations should disable plugin completely."""
    result = pytester.runpytest("--pytest-durations", "0")
    result.assert_outcomes(passed=2)
    result.stdout.no_fnmatch_line("*duration top*")


def test_plugin_xdist_disabled(pytester, sample_testfile):
    """Run when pytest-xdist is absent or disabled should be successful (#3)."""
    result = pytester.runpytest("-p", "no:xdist")
    result.assert_outcomes(passed=2)


def test_plugin_xdist_enabled(pytester, sample_testfile):
    """Run when pytest-xdist is absent or disabled should be successful (#3)."""
    result = pytester.runpytest("--numprocesses", "2")
    result.assert_outcomes(passed=2)
