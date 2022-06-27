from acquisition_nagios.guralpdatacenter.guralp_availability import \
    AcquisitionStatistics, ChannelLatency, get_latency_threshold_state, \
    LatencyCheckResults
from acquisition_nagios.nagios.models import NagiosOutputCode
from datetime import datetime


def test_get_latency_threshold_state():
    test_channel_latency = [
        ChannelLatency(
            channel='QW.ZEROLAT.00.HNZ',
            timestamp=datetime(2022, 6, 1, 1, 0, 0),
            latency=0
        ),
        ChannelLatency(
            channel='QW.ONESEC.00.HNZ',
            timestamp=datetime(2022, 6, 1, 0, 59, 59),
            latency=1
        ),
        ChannelLatency(
            channel='QW.TWOSEC.00.HNZ',
            timestamp=datetime(2022, 6, 1, 0, 59, 58),
            latency=2
        ),
        ChannelLatency(
            channel='QW.FIVESEC.00.HNZ',
            timestamp=datetime(2022, 6, 1, 0, 59, 55),
            latency=5
        ),
        ChannelLatency(
            channel='QW.TENSEC.00.HNZ',
            timestamp=datetime(2022, 6, 1, 0, 59, 50),
            latency=10
        )
    ]
    test_statistics = AcquisitionStatistics(
        channel_latency=test_channel_latency,
    )
    resulting_state = get_latency_threshold_state(
        acquisition_stats=test_statistics,
        warn_time='10',
        crit_time='20',
        warn_threshold='1',
        crit_threshold='2'
    )
    assert resulting_state == LatencyCheckResults(
        crit_count=0,
        warn_count=0,
        state=NagiosOutputCode.ok
    )
    resulting_state = get_latency_threshold_state(
        acquisition_stats=test_statistics,
        warn_time='3',
        crit_time='6',
        warn_threshold='1',
        crit_threshold='2'
    )
    assert resulting_state == LatencyCheckResults(
        crit_count=1,
        warn_count=1,
        state=NagiosOutputCode.warning
    )
    resulting_state = get_latency_threshold_state(
        acquisition_stats=test_statistics,
        warn_time='0',
        crit_time='1',
        warn_threshold='1',
        crit_threshold='2'
    )
    assert resulting_state == LatencyCheckResults(
        crit_count=3,
        warn_count=1,
        state=NagiosOutputCode.critical
    )
