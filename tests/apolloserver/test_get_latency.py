from datetime import datetime
from acquisition_nagios.apolloserver.availability_health import get_latency


def test_get_latency():

    current_time = datetime(2022, 6, 1, 0, 1, 0)

    last_time = datetime(2022, 6, 1, 0, 0, 0)
    assert get_latency(
        current_time=current_time,
        last_time=last_time
    ) == 60
