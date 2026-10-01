class TestWithInit:
    # Planted: pytest skips classes that define __init__, so these tests never run.
    def __init__(self):
        self.value = 1

    def test_value(self):
        assert self.value == 1


class TestPlain:
    def test_ok(self):
        assert "ok".upper() == "OK"
