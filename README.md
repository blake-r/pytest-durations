[![Downloads](https://pepy.tech/badge/pytest-durations/month)](https://pepy.tech/project/pytest-durations)

## Introduction

A pytest plugin to measure fixture and test durations.

In order to get the pure test setup/teardown durations, plugin subtracts time taken by fixtures which scope is larger than "function".

## Installation

```shell
$ pip install pytest-durations
```

## Example of report

```
============================= fixture duration top =============================
total          name                                     num avg            min            max           
0:00:00.063821                            fake_reporter   4 0:00:00.015300 0:00:00.014831 0:00:00.018389
0:00:00.068513                              grand total  22 0:00:00.000117 0:00:00.000110 0:00:00.000132
============================ test call duration top ============================
total          name                                     num avg            min            max           
0:00:00.527693                 test_plugin_with_options   4 0:00:00.041085 0:00:00.040256 0:00:00.405267
0:00:00.041535                      test_plugin_disable   1 0:00:00.041535 0:00:00.041535 0:00:00.041535
0:00:00.018607            test_get_current_ticks_frozen   1 0:00:00.018607 0:00:00.018607 0:00:00.018607
0:00:00.590297                              grand total  10 0:00:00.000706 0:00:00.000706 0:00:00.000706
=========================== test setup duration top ============================
total          name                                     num avg            min            max           
0:00:00.018670                 test_report_measurements   1 0:00:00.018670 0:00:00.018670 0:00:00.018670
0:00:00.015979 test_report_measurements_with_rows_limit   1 0:00:00.015979 0:00:00.015979 0:00:00.015979
0:00:00.015100 test_report_measurements_with_time_limit   1 0:00:00.015100 0:00:00.015100 0:00:00.015100
0:00:00.015079   test_report_measurements_empty_results   1 0:00:00.015079 0:00:00.015079 0:00:00.015079
0:00:00.005076                 test_plugin_with_options   4 0:00:00.001138 0:00:00.001030 0:00:00.001770
0:00:00.071377                              grand total  10 0:00:00.015079 0:00:00.015079 0:00:00.015079
========================== test teardown duration top ==========================
total          name                                     num avg            min            max           
0:00:00.001990                              grand total  10 0:00:00.000128 0:00:00.000128 0:00:00.000128
============================== 10 passed in 0.71s ==============================
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

### 1.3.0 (Sep 11, 2024)

* Update supported Python versions
* Upgrade development dependencies

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
