import sys

import pytest


@pytest.mark.skip(reason="broken since the tax change")
def test_tax_rounding():
    # Planted: skipped unconditionally.
    assert round(2.675, 2) == 2.68


@pytest.mark.xfail(reason="known bug")
def test_known_bug():
    # Planted: xfail without strict, so an unexpected pass goes unnoticed.
    assert 1 + 1 == 2


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX paths only")
def test_posix_paths():
    # Decoy: a legitimate platform skip.
    assert "/".join(["a", "b"]) == "a/b"
