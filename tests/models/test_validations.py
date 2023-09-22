"""Test validation functions."""

import pytest

from aineko.models.validations import check_power_of_2


def test_check_power_of_2():
    """Check that check_power_of_2 works."""
    for i in range(5):
        assert check_power_of_2(2**i) == 2**i

    for i in [0, 5]:
        with pytest.raises(ValueError):
            check_power_of_2(i)
