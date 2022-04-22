from unittest.mock import Mock, create_autospec

import pytest
import xdist.workermanage

from pytest_durations.plugin import Category
from pytest_durations.xdist import PytestDurationXdistMixin


@pytest.fixture
def fake_session():
    return create_autospec(pytest.Session, instance=True)


@pytest.fixture
def fake_node():
    return create_autospec(xdist.workermanage.WorkerController, instance=True)


@pytest.fixture
def instance(measurements):
    instance = PytestDurationXdistMixin()
    instance.measurements = {Category.TEST_CALL: {}}
    return instance


@pytest.fixture
def measurements():
    return {Category.TEST_CALL: {"fixture1": [0.1, 0.2, 0.3]}}


def test_pytest_sessionfinish(fake_session, instance, measurements):
    instance.measurements = measurements
    fake_session.config.workeroutput = {}
    instance.pytest_sessionfinish(fake_session, 0)
    assert fake_session.config.workeroutput == {"pytest_durations": measurements}


def test_pytest_sessionfinish_noxdist(fake_session, instance, measurements):
    instance.pytest_sessionfinish(fake_session, 0)
    assert isinstance(fake_session.config.workeroutput["pytest_durations"], Mock)


def test_pytest_testnodedown(fake_node, instance, measurements):
    fake_node.workeroutput = {"pytest_durations": measurements}
    instance.pytest_testnodedown(fake_node, None)
    assert instance.measurements == measurements


def test_pytest_testnodedown_noxdist(fake_node, instance, measurements):
    instance.pytest_testnodedown(fake_node, None)
    assert instance.measurements == {"test": {}}
