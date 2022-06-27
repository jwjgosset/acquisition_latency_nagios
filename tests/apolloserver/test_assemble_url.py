from acquisition_nagios.apolloserver.availability_health import assemble_url
from datetime import datetime


def test_assemble_url():
    server_url = 'localhost'
    start_time = datetime(2022, 6, 1, 0, 0, 0)
    end_time = datetime(2022, 6, 1, 1, 0, 0)

    expected_url = ("http://localhost:8787/api/v1/channels/availability" +
                    ".json?type=timeseries&startTime=2022-06-01T00:00:00." +
                    "000Z&endTime=2022-06-01T01:00:00.000Z")
    assert assemble_url(
        server_url=server_url,
        start_time=start_time,
        end_time=end_time
    ) == expected_url
