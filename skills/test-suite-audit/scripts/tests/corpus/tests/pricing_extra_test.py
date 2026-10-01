from shop.pricing import total


def test_total_empty():
    # Planted: pytest never collects this file, because python_files is test_*.py.
    assert total([]) == 0
