[![Downloads](https://pepy.tech/badge/pytest-durations/month)](https://pepy.tech/project/pytest-durations)

## Introduction

A pytest plugin to measure fixture and test durations.

In order to get the pure test setup/teardown durations, plugin subtracts time taken by fixtures which scope is larger than "function".

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
```

Note: please don't be mistaken by `--duration` options which comes from pytest itself.

## Example of report

```text
============================== fixture duration top ==============================
total          name                              num avg            min
0:00:00.115193                fake_pluginmanager   3 0:00:00.034275 0:00:00.034190
0:00:00.060736                       fake_config   2 0:00:00.030368 0:00:00.030047
0:00:00.048220                      fake_session   2 0:00:00.024110 0:00:00.023326
0:00:00.015640                         fake_node   2 0:00:00.007820 0:00:00.007083
0:00:00.011255                          pytester   6 0:00:00.001447 0:00:00.001332
0:00:00.008079                       fake_parser   1 0:00:00.008079 0:00:00.008079
0:00:00.263918                       grand total  78 0:00:00.000031 0:00:00.000017
============================= test call duration top =============================
total          name                              num avg            min
0:00:00.720817         test_plugin_xdist_enabled   1 0:00:00.720817 0:00:00.720817
0:00:00.252951          test_plugin_with_options   3 0:00:00.084313 0:00:00.084112
0:00:00.158072                 test_get_test_key   9 0:00:00.017230 0:00:00.016828
0:00:00.083768               test_plugin_disable   1 0:00:00.083768 0:00:00.083768
0:00:00.079307        test_plugin_xdist_disabled   1 0:00:00.079307 0:00:00.079307
0:00:00.053477     test_get_current_ticks_frozen   1 0:00:00.053477 0:00:00.053477
0:00:01.355299                       grand total  31 0:00:00.000713 0:00:00.000157
============================ test setup duration top =============================
total          name                              num avg            min
0:00:00.065258    test_pytest_configure_disabled   1 0:00:00.065258 0:00:00.065258
0:00:00.064810             test_pytest_configure   1 0:00:00.064810 0:00:00.064810
0:00:00.055380             test_pytest_addoption   1 0:00:00.055380 0:00:00.055380
0:00:00.025389         test_pytest_sessionfinish   1 0:00:00.025389 0:00:00.025389
0:00:00.023777 test_pytest_sessionfinish_noxdist   1 0:00:00.023777 0:00:00.023777
0:00:00.010331          test_plugin_with_options   3 0:00:00.002551 0:00:00.002534
0:00:00.008948  test_pytest_testnodedown_noxdist   1 0:00:00.008948 0:00:00.008948
0:00:00.007471          test_pytest_testnodedown   1 0:00:00.007471 0:00:00.007471
0:00:00.273505                       grand total  31 0:00:00.002209 0:00:00.000143
=========================== test teardown duration top ===========================
total          name                              num avg            min
0:00:00.007211                       grand total  31 0:00:00.000177 0:00:00.000123
======================== 31 passed, 2 warnings in 1.72s ========================
```

## Development

Project uses [poetry](https://python-poetry.org/) for dependencies management, [pytest](https://pytest.org/) for testing and [pre-commit](https://pre-commit.com/) for coding standard checks.

```shell
$ pip install poetry
$ poetry install
$ pre-commit install
$ pytest tests
```

## Change Log

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
