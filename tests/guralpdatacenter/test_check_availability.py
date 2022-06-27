from eew_nagios.guralpdatacenter.guralp_availability import check_availability
import pytest


def test_check_availability():
    assert check_availability(
        expected_channels=10,
        found_channels=9
    ) == 90
    with pytest.raises(ZeroDivisionError):
        check_availability(
            expected_channels=0,
            found_channels=9
        )
