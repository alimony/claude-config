import pytest

from shop.pricing import discount, format_price, parse_price, total


def test_total(cart):
    assert total(cart) == 6.75


def test_discount():
    assert discount(100, 10) == 90


def test_discount():  # noqa: F811 – planted: shadows the test above, so the first one never runs.
    assert discount(100, 0) == 100


def test_total_is_number(cart):
    assert (total(cart), "total should be a number")  # planted: a non-empty tuple is always true


def test_format_price_runs():
    format_price(3)  # planted: no assertion


def test_discount_rejects_bad_percent():
    try:
        discount(100, 150)
    except ValueError as exc:  # planted: the test passes when nothing is raised
        assert "between" in str(exc)


def test_parse_price_dollars():
    value = parse_price("$3.50")
    assert value == 3.5


def test_parse_price_plain():
    value = parse_price("4.25")
    assert value == 4.25


def test_parse_price_spaces():
    value = parse_price(" 7.00 ")
    assert value == 7.0


@pytest.mark.parametrize("amount", [10, 20, 30, 40])
def test_discount_zero_percent(amount):
    # Decoy: parametrised siblings share one code path by design.
    assert discount(amount, 0) == amount
