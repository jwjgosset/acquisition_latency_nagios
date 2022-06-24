from eew_nagios.guralpdatacenter.guralp_availability import get_channel_latency
from tests import TESTDATA
from datetime import datetime


def test_get_channel_latency():
    cache_folder: str = TESTDATA
    time = datetime(2022, 6, 2, 0, 0, 0)
    test_statistics = get_channel_latency(
        cache_folder=cache_folder,
        time=time
    )

    print(test_statistics)

    assert len(test_statistics.channel_latency) == 3

    assert test_statistics.channel_latency[0].channel == 'QW.BCH09.00.HNE'

    assert test_statistics.channel_latency[0].latency == 1.6
