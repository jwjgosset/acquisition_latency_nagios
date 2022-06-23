from eew_nagios.guralpdatacenter.guralp_availability import \
    get_latencystatistics_of_last_row
from tests import TESTDATA
from pathlib import Path
from datetime import datetime


def test_get_latencystatistics_of_last_row():
    csv_file = Path(f"{TESTDATA}/latency/QW_BCH09_00_HNE_2022_152.csv")
    time = datetime(2022, 6, 2, 0, 0, 1)

    result_latency = get_latencystatistics_of_last_row(
        csv_file=csv_file,
        time=time
    )
    assert result_latency.channel == "QW.BCH09.00.HNE"
    assert result_latency.latency == 2.6
    assert result_latency.timestamp == datetime(2022, 6, 1, 23, 59, 58, 400000)
