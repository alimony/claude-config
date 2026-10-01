import datetime
import os
import urllib.request


def test_writes_environment():
    # Planted: writes os.environ directly, which leaks into later tests.
    os.environ["SHOP_MODE"] = "test"
    assert os.environ["SHOP_MODE"] == "test"


def test_uses_real_clock():
    # Planted: depends on the real clock.
    assert datetime.datetime.now().year >= 2024


def test_network_guarded():
    # Planted: a real network call in a test body (not reached unless SHOP_ONLINE is set).
    if os.environ.get("SHOP_ONLINE"):
        urllib.request.urlopen("https://example.com")
    assert os.environ.get("SHOP_ONLINE") in (None, "", "1")
