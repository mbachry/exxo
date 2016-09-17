import pytest


@pytest.mark.xfail(reason='broken for now')
def test_numpy_importable():
    from numpy.core.multiarray import zeros
    zeros(5)
