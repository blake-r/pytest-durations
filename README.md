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
  --pytest-resultlog=FILE
                        Result log filename or dash for terminal output.
                        Default "-"
```

Note: please don't be mistaken by `--durations` options which comes from pytest itself.

## Example of report

```text
============================== fixture duration top ==============================
total          name                              num avg            min
0:00:00.115563                fake_pluginmanager   3 0:00:00.034653 0:00:00.033694
0:00:00.060115                       fake_config   2 0:00:00.030057 0:00:00.029842
0:00:00.048612                      fake_session   2 0:00:00.024306 0:00:00.023556
0:00:00.016073                         fake_node   2 0:00:00.008037 0:00:00.008029
0:00:00.012089                          pytester   6 0:00:00.001444 0:00:00.001330
0:00:00.008237                       fake_parser   1 0:00:00.008237 0:00:00.008237
0:00:00.265457                       grand total  78 0:00:00.000031 0:00:00.000018
============================= test call duration top =============================
total          name                              num avg            min
0:00:00.755826         test_plugin_xdist_enabled   1 0:00:00.755826 0:00:00.755826
0:00:00.246548          test_plugin_with_options   3 0:00:00.081849 0:00:00.081029
0:00:00.158057                 test_get_test_key   9 0:00:00.017376 0:00:00.016729
0:00:00.121555               test_plugin_disable   1 0:00:00.121555 0:00:00.121555
0:00:00.078009        test_plugin_xdist_disabled   1 0:00:00.078009 0:00:00.078009
0:00:00.037713     test_get_current_ticks_frozen   1 0:00:00.037713 0:00:00.037713
0:00:01.405064                       grand total  31 0:00:00.000708 0:00:00.000162
============================= test setup duration top ============================
total          name                              num avg            min
0:00:00.065316    test_pytest_configure_disabled   1 0:00:00.065316 0:00:00.065316
0:00:00.063908             test_pytest_configure   1 0:00:00.063908 0:00:00.063908
0:00:00.055924             test_pytest_addoption   1 0:00:00.055924 0:00:00.055924
0:00:00.025543 test_pytest_sessionfinish_noxdist   1 0:00:00.025543 0:00:00.025543
0:00:00.024043         test_pytest_sessionfinish   1 0:00:00.024043 0:00:00.024043
0:00:00.011220          test_plugin_with_options   3 0:00:00.002642 0:00:00.002580
0:00:00.008443  test_pytest_testnodedown_noxdist   1 0:00:00.008443 0:00:00.008443
0:00:00.008431          test_pytest_testnodedown   1 0:00:00.008431 0:00:00.008431
0:00:00.274801                       grand total  31 0:00:00.002182 0:00:00.000149
=========================== test teardown duration top ===========================
total          name                              num avg            min
0:00:00.007093                       grand total  31 0:00:00.000178 0:00:00.000126
=============================== 31 passed in 1.77s ===============================
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

### 1.4.0 (Mar 18, 2025)

* Add command line option to write the measure report to a file instead of terminal

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
