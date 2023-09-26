"""Test validation functions."""

import pytest

from aineko.models.validations import check_power_of_2, check_semver


def test_check_power_of_2():
    """Tests for check_power_of_2."""
    for i in range(5):
        assert check_power_of_2(2**i) == 2**i

    for i in [0, 5]:
        with pytest.raises(ValueError):
            check_power_of_2(i)


def test_check_semver():
    """Tests for check_semver."""
    assert check_semver("1.2.3")
    assert check_semver("1.2.3-rc.1")
    assert check_semver("1.2.3+build.1")
    assert check_semver("1.2.3-rc.1+build.1")

    with pytest.raises(ValueError):
        check_semver("1.2.3.4")

    with pytest.raises(ValueError):
        check_semver("v1.2.3")

    with pytest.raises(ValueError):
        check_semver("version1")
