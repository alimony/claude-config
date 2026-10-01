STATE = {"ready": False}


def test_prepare():
    STATE["ready"] = True
    assert STATE["ready"]


def test_uses_prepared_state():
    # Planted: passes only when test_prepare ran first in the same process.
    assert STATE["ready"]
