import time

from shop.pricing import total


def test_checkout_end_to_end(cart):
    # Decoy: slow, but it is the only end-to-end test, so it must never be proposed for removal.
    time.sleep(0.3)
    assert total(cart) > 0
