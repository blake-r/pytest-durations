# Architecture

This document provides a high-level overview of how `pytest-durations` measures,
aggregates, and reports test and fixture execution times.

## Overview

`pytest-durations` is a pytest plugin that instruments four distinct phases of
test execution:

1. **Fixture setup** — time spent initializing fixtures
2. **Test call** — time spent executing the test function itself
3. **Test setup** — time spent preparing test resources (fixtures excluding shared ones)
4. **Test teardown** — time spent cleaning up test resources (fixtures excluding shared ones)

## Core Components

### Plugin (`plugin.py`)

`PytestDurationPlugin` is the main plugin class that hooks into pytest's lifecycle:

- `pytest_fixture_setup` / `pytest_fixture_post_finalizer` — measure fixture setup/teardown
- `pytest_runtest_call` — measure test execution
- `pytest_runtest_setup` / `pytest_runtest_teardown` — measure test preparation/cleanup
- `pytest_terminal_summary` — emit the final report

### Measurement (`measure.py`)

`MeasureDuration` is a context manager that records elapsed time:

```python
with MeasureDuration() as measurement:
    yield  # wrapped code runs here
# measurement.duration is now available
```

### Time Source (`ticker.py`)

Durations are captured using `time.time()` (not `time.monotonic()`). This is
intentional: `time.time()` respects time-travel mocking libraries like
`freezegun` and `time-machine`, so tests that freeze time do not produce
absurd duration values.

### Shared Fixture Handling

Shared fixtures (session/module/class scope) are set up once and reused across
multiple tests. Their duration must **not** be attributed to every individual
test that uses them.

The plugin tracks `shared_fixture_duration` as a running offset:

1. When a shared fixture is set up, its duration is added to the offset
2. During `test setup`, this offset is subtracted from the measurement
3. The offset is reset to 0 after each test

This ensures shared fixture time appears only in the **fixture setup** category,
not in **test setup** or **test teardown**.

### Aggregation Pipeline

Raw measurements flow through a three-stage pipeline:

```
raw timings (dict[key → list[float]])
    ↓
grouping function (e.g., by module, class, function)
    ↓
grouped measurements (dict[group_key → list[float]])
    ↓
report rows (list[ReportRowT])
    ↓
terminal / file output
```

### Report Formatting (`reporting.py`)

The report uses two core data structures:

- `TimeValuesT` — aggregated stats for a single operation (name, calls, min, max, med, sum)
- `ReportRowT` — formatted display row (total, name, num, med, max, min)

Note: `ReportRowT` field order determines terminal column visibility. The first
5 columns are shown by default; `min` is the 6th and is hidden unless explicitly
selected via `--pytest-durations-columns`.

Time formatting supports three modes:

- `clock` — `HH:MM:SS.microseconds` (default)
- `short` — compact `H:MM:SS`
- `auto` — picks the most appropriate format based on the maximum duration

### xdist Support (`xdist.py`)

When `pytest-xdist` is active, measurements are collected on each worker and
merged on the master node:

1. `pytest_sessionfinish` serializes measurements into `workeroutput`
2. `pytest_testnodedown` deserializes and merges worker measurements

Serialization uses plain Python dicts with string keys, so no custom
serialization logic is required.

### Baseline Comparison (`baseline.py`)

The baseline module enables performance regression detection across test runs:

1. `save_baseline()` — serializes aggregated measurements to a JSON file
2. `load_baseline()` — reads a previously saved baseline
3. `compare_to_baseline()` — computes relative slowdowns and returns regressions above a threshold
4. `format_github_annotation()` — formats regressions as GitHub Actions workflow commands

The baseline file stores per-test `total` time by category. Comparison happens
after aggregation (including xdist merge), so baseline data is always
representative of the full test suite.

### Types (`types.py`)

Domain enums use a consistent `StrEnum` pattern:

- `Category` — measurement categories (fixture, test call, test setup, test teardown)
- `GroupBy` — grouping strategy (legacy, module, class, function, none)
- `TimeFormat` — time display format (clock, short, auto)

## Data Flow

```
pytest_runtest_setup (hookwrapper)
    ├─ MeasureDuration() context
    ├─ yield (test setup runs)
    ├─ subtract shared_fixture_duration
    └─ store in measurements[TEST_SETUP][test_key]

pytest_runtest_call (hookwrapper)
    ├─ MeasureDuration() context
    ├─ yield (test runs)
    └─ store in measurements[TEST_CALL][test_key]

pytest_runtest_teardown (hookwrapper)
    ├─ MeasureDuration() context
    ├─ yield (test teardown runs)
    ├─ subtract shared_fixture_duration
    └─ store in measurements[TEST_TEARDOWN][test_key]

pytest_fixture_setup (hookwrapper)
    ├─ MeasureDuration() context
    ├─ yield (fixture setup runs)
    └─ store in measurements[FIXTURE_SETUP][fixture_key]

pytest_terminal_summary
    ├─ group measurements by category
    ├─ apply grouping function (module/class/function)
    ├─ compute TimeValuesT (min, max, med, sum)
    ├─ format as ReportRowT
    └─ write to terminal or file
```

## Design Decisions

### Why `time.time()` over `time.monotonic()`?

`time.monotonic()` is more robust against system clock changes, but it does not
respect time-travel mocking. Since this plugin is used in test suites that
frequently freeze time, `time.time()` is the pragmatic choice.

### Why separate fixture setup from test setup?

Fixtures can have different scopes (function, class, module, session). A
session-scoped fixture is set up once but used by hundreds of tests. Attributing
its full cost to every test would be misleading. Separating fixture durations
into their own category gives an accurate view of where time is actually spent.

### Why NamedTuple over dataclass for ReportRowT?

`NamedTuple` provides immutability, unpacking, and minimal memory overhead.
The report rows are purely data carriers with no behavior, making NamedTuple
a natural fit.
