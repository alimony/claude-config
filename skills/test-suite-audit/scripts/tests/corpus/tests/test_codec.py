from shop.codec import dumps, loads


def test_round_trip():
    # Planted: a round trip written as one example, a property-based testing candidate.
    order = {"id": 1, "items": [1, 2]}
    assert loads(dumps(order)) == order


def test_dumps_sorted():
    text = dumps({"b": 1, "a": 2})
    assert text.index('"a"') < text.index('"b"')


def test_dumps_sorted_copy():
    # Planted: an exact copy of the test above.
    text = dumps({"b": 1, "a": 2})
    assert text.index('"a"') < text.index('"b"')
