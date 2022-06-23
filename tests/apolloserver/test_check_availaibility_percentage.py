from eew_nagios.apolloserver.availability_health import \
    check_availability_percentage
import pytest


def test_check_availability_percentage():
    assert check_availability_percentage(
        available_channels=10,
        expected_channel_count=10
    ) == 100
    assert check_availability_percentage(
        available_channels=5,
        expected_channel_count=10
    ) == 50
    with pytest.raises(ZeroDivisionError):
        check_availability_percentage(
            available_channels=10,
            expected_channel_count=0)
