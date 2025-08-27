[![Downloads](https://pepy.tech/badge/pytest-durations/month)](https://pepy.tech/project/pytest-durations)

## Introduction

Pytest plugin to measure fixture and test durations.

In order to get the pure test setup/teardown durations, the plugin subtracts time taken by fixtures whose scope
is larger than "function".

In comparison to the built-in pytest "--durations", this plugin shows fixture durations separately from test function
durations and supports xdist and time-traveling packages.

## Installation

```shell
$ pip install pytest-durations
```

## Plugin options

```text
pytest-durations:
  --pytest-durations=N  Show N slowest setup/test durations (N=0 to disable
                        plugin). Default 30
  --pytest-durations-min=N
                        Minimal duration in seconds for inclusion in slowest
                        list. Default 0.005
  --pytest-durations-log=FILE
                        Result log filename or dash for terminal output. Default
                        "-"
  --pytest-durations-group-by={legacy,module,class,function}
                        Group test durations by module, class, or function. Use
                        legacy grouping for backward compatibility. Default:
                        "function"
```

Note: Please don't confuse these options with the --durations options that come from pytest itself.

## Example of report

```text
========================================= fixture duration top ==========================================
total          name                                                     num med            min
0:00:00.031589 tests/test_options.py::fake_pluginmanager                  3 0:00:00.008776 0:00:00.008076
0:00:00.015807 tests/test_xdist.py::fake_session                          2 0:00:00.007904 0:00:00.007442
0:00:00.014311 tests/test_options.py::fake_config                         2 0:00:00.007155 0:00:00.007126
0:00:00.009118 tests/test_plugin.py::test_plugin_with_options::pytester   3 0:00:00.002232 0:00:00.002049
0:00:00.005009 tests/test_options.py::reload_module                       1 0:00:00.005009 0:00:00.005009
0:00:00.096780 grand total                                              164 0:00:00.000016 0:00:00.000010
======================================== test call duration top =========================================
total          name                                                     num med            min
0:00:00.483961 tests/test_plugin.py::test_plugin_xdist_enabled            1 0:00:00.483961 0:00:00.483961
0:00:00.177326 tests/test_plugin.py::test_plugin_with_options             3 0:00:00.057389 0:00:00.057286
0:00:00.067949 tests/test_plugin.py::test_plugin_with_resultlog           1 0:00:00.067949 0:00:00.067949
0:00:00.066597 tests/test_plugin.py::test_plugin_disable                  1 0:00:00.066597 0:00:00.066597
0:00:00.059509 tests/test_plugin.py::test_plugin_xdist_disabled           1 0:00:00.059509 0:00:00.059509
0:00:00.025053 tests/test_ticker.py::test_freezegun_import_none           1 0:00:00.025053 0:00:00.025053
0:00:00.023706 tests/test_ticker.py::test_get_current_ticks_frozen        2 0:00:00.011853 0:00:00.000215
0:00:00.912538 grand total                                               78 0:00:00.000083 0:00:00.000050
======================================== test setup duration top ========================================
total          name                                                     num med            min
0:00:00.019535 tests/test_options.py::test_pytest_addoption               1 0:00:00.019535 0:00:00.019535
0:00:00.016147 tests/test_options.py::test_pytest_configure_disabled      1 0:00:00.016147 0:00:00.016147
0:00:00.015358 tests/test_options.py::test_pytest_configure               1 0:00:00.015358 0:00:00.015358
0:00:00.010575 tests/test_plugin.py::test_plugin_with_options             3 0:00:00.002773 0:00:00.002462
0:00:00.008763 tests/test_xdist.py::test_pytest_sessionfinish_noxdist     1 0:00:00.008763 0:00:00.008763
0:00:00.007749 tests/test_xdist.py::test_pytest_sessionfinish             1 0:00:00.007749 0:00:00.007749
0:00:00.100089 grand total                                               78 0:00:00.000113 0:00:00.000052
====================================== test teardown duration top =======================================
total          name                                                     num med            min
0:00:00.006716 grand total                                               78 0:00:00.000062 0:00:00.000044
```

## Development

The project uses [poetry](https://python-poetry.org/) for dependency management, [pytest](https://pytest.org/) for
testing, and [pre-commit](https://pre-commit.com/) for coding standard checks.

```shell
$ pip install poetry
$ poetry install
$ pre-commit install
$ pytest
```

## Change Log

### 1.6.0 (Aug 27, 2025)

* Added support for grouping test durations by module, class, or function (#26)
* Improved column alignment in duration reports, ensuring test names are left-aligned
* Renamed the avg column to med in reports, as it correctly represents median durations, not average durations (#24)
* Refactoring
  * Added a Python script (check_versions.py) to automate checking that the package version is synchronized
  * Renamed the pytest-resultlog option to pytest-durations-log for consistency.
    The pytest-resultlog option will be deprecated in a future release
  * Converted the internal Category class to inherit from StrEnum for improved type safety and better serialization

To revert to the old behavior for test and fixture names in reports, set the `--pytest-durations-group-by` option to "legacy".

### 1.5.2 (Apr 29, 2025)

* Fix a time-machine time.monotonic() unpatching glitch by using time.time() instead (#19)

### 1.5.1 (Apr 27, 2025)

* Add Python 3.13 to supported versions
* Drop Python 3.8 from supported versions, because of poetry and time_machine dependencies
* Add time_machine package compatibility (#19)
* Add README commentary on the difference from pytest builtin "--duration" function (#18)
* Replace separated code style packages with ruff
* Upgrade poetry and package dependencies versions

### 1.4.0 (Mar 18, 2025)

* Add command line option to write the measure report to a file instead of terminal (#16)

### 1.3.1 (Sep 11, 2024)

* Upgrade development dependencies

### 1.3.0 (Sep 11, 2024)

* Update supported Python versions

### 1.2.0 (Apr 22, 2022)

* Use same width for all reports (#6)
* Improve test coverage (#7)
* Continuous delivery GitHub workflow

### 1.1.0 (Mar 7, 2022)

* Do not interoperate with xdist if it is disabled or absent

### 1.0.1 (Feb 14, 2022)

* Grand total row shows real min/max values instead of averages

### 1.0.0 (Feb 14, 2022)
 
* First Release
