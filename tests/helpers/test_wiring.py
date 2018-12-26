import pytest

from antidote import wire


def test_invalid_value():
    with pytest.raises(ValueError):
        wire(object())

    with pytest.raises(ValueError):
        wire(1)

    with pytest.raises(ValueError):
        wire(lambda: None)
