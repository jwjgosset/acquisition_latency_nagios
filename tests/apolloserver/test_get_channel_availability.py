from datetime import datetime
from eew_nagios.apolloserver.availability_health import \
    get_channel_availability
import pytest


def test_get_channel_availability():
    test_availability = {
        "availability": [
            {
                "id": "QW.BCV13.00.HNZ",
                "ranges": [
                    {
                        "startTime": "2022-06-19T23:59:59.950000000Z",
                        "endTime": "2022-06-20T01:00:00.430000000Z",
                        "firstSequence": 852772,
                        "lastSequence": 859695
                    }
                ]
            },
            {
                "id": "QW.BCV13.00.HNN",
                "ranges": [
                    {
                        "startTime": "2022-06-19T23:59:59.820000000Z",
                        "endTime": "2022-06-20T01:00:00.300000000Z",
                        "firstSequence": 852785,
                        "lastSequence": 859708
                    }
                ]
            },
            {
                "id": "QW.BCV13.00.HNE",
                "ranges": [
                    {
                        "startTime": "2022-06-19T23:59:59.780000000Z",
                        "endTime": "2022-06-20T01:00:00.260000000Z",
                        "firstSequence": 852771,
                        "lastSequence": 859694
                    }
                ]
            },
            {
                "id": "QW.QCC01.00.HNZ",
                "ranges": [
                    {
                        "startTime": "2022-06-19T23:59:59.720000000Z",
                        "endTime": "2022-06-20T01:00:01.400000000Z",
                        "firstSequence": 954904,
                        "lastSequence": 956997
                    }
                ]
            },
            {
                "id": "QW.QCC01.00.HNN",
                "ranges": [
                    {
                        "startTime": "2022-06-20T00:00:00.000000000Z",
                        "endTime": "2022-06-20T00:59:59.000000000Z",
                        "firstSequence": 955349,
                        "lastSequence": 957442
                    }
                ]
            },
            {
                "id": "QW.QCC01.00.HNE",
                "ranges": [
                    {
                        "startTime": "2022-06-19T23:59:58.800000000Z",
                        "endTime": "2022-06-20T01:00:00.000000000Z",
                        "firstSequence": 955131,
                        "lastSequence": 957224
                    }
                ]
            },
            {
                "id": "QW.QCC07.00.HNZ",
                "ranges": []
            }
        ]
    }
    bad_data = {
        "availability": [
            {
                "not_id": "wrong.name",
                "out_of_range": [

                ]
            }
        ]
    }
    end_time = datetime(2022, 6, 20, 1, 0, 0)

    acquisition_statistics = get_channel_availability(
        availability=test_availability,
        end_time=end_time
    )

    assert acquisition_statistics.channel_latency[4].latency == 1
    assert "QW.QCC07.00.HNZ" in acquisition_statistics.unavailable_channels
    with pytest.raises(KeyError):
        get_channel_availability(
            availability=bad_data,
            end_time=end_time
        )
