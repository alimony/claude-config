import time

import pytest


@pytest.fixture(autouse=True)
def slow_setup():
    # Planted: an autouse function-scoped fixture that costs time in every test.
    time.sleep(0.01)
    yield


@pytest.fixture
def cart():
    return [1.5, 2.25, 3.0]


@pytest.fixture
def never_used():
    # Planted: no test requests this fixture.
    return 42
