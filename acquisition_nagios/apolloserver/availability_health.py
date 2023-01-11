'''
Module with functions for interacting with and parsing the output of the
ApolloServer Availability API
'''
from dataclasses import dataclass
import requests
import logging
from typing import Dict, List
from datetime import datetime, timedelta
from acquisition_nagios.nagios.models import NagiosOutputCode, NagiosRange
from acquisition_nagios.acquisition_availability import LatencyCheckResults


@dataclass
class ChannelLatency:
    channel: str
    timestamp: datetime
    latency: float

    def __str__(self):
        latency = self.latency
        age = round((datetime.now() - self.timestamp).total_seconds(), 2)
        return (f"{self.channel}, arrived {age}s ago arrived with" +
                f" {round(latency, 2)}s latency")


@dataclass
class AcquisionStatistics:
    channel_latency: List[ChannelLatency]
    unavailable_channels: List[str]


def get_latency(
    end_time: datetime,
    server_url: str,
    sncl: str
) -> float:
    '''
    Determine a latency value based on the two provided timestamps

    Parameter
    ---------
    current_time: datetime
        The current time when acquision statistics were acquired

    last_time: datetime
        The timestamp of the last data timestamp to use to determine latency

    Returns
    -------
    float: The latency in seconds
    '''
    start_time = end_time - timedelta(minutes=5)

    api_url = assemble_arrival_url(
        server_url=server_url,
        start_time=start_time,
        end_time=end_time,
        sncl=sncl
    )

    latency_json = get_api_json(
        query_url=api_url
    )

    latency = float(
        latency_json['availability'][0]['intervals'][0]['latency']['average'])

    return latency


def assemble_availability_url(
    server_url: str,
    start_time: datetime,
    end_time: datetime,
    port: str = '8787'
) -> str:
    '''
    Constucts the URL used to retrieve data from the Availability API

    Parameters
    ----------
    server_url: str
        The IP address or hostname for the ApolloServer to query

    start_time: datetime
        The start time for the query

    end_time: datetime
        The end time for the query

    Returns
    -------
    Str: The full URL to use with a GET request to retrieve availability
    information.
    '''

    start_string = f"startTime={start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')}"

    end_string = f"endTime={end_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')}"

    api_url = "/api/v1/channels/availability.json"

    option_url = f"?type=timeseries&{start_string}&{end_string}"

    full_url = "http://" + server_url + ':' + port + api_url + option_url
    return full_url


def assemble_arrival_url(
    server_url: str,
    start_time: datetime,
    end_time: datetime,
    sncl: str,
    port: str = '8787'
):
    start_string = f"startTime={start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')}"

    end_string = f"endTime={end_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')}"

    api_url = "/api/v1/channels/availability/summary/intervals"

    option_url = (f"?channels={sncl}&{start_string}&{end_string}" +
                  "&timeFormat=iso8601&intervals=1&arrivalMetrics")

    full_url = "http://" + server_url + ':' + port + api_url + option_url
    return full_url


def get_api_json(
    query_url: str
) -> Dict:
    '''
    Get Availability information from the ApolloServer

    Parameters
    ----------
    query_url: str
        The url to query for Availability information

    Returns
    -------
    Dict: A json-formatted Dictionary object containing availability informaion

    Raises
    ------
    HTTPError: If the request to the ApolloServer's API fails for any reason

    ValueError: If the response from the ApolloServer is not a valid json
    '''
    logging.debug(f"Api query: {query_url}")
    availability_response = requests.get(query_url)

    availability_response.raise_for_status()

    availability = availability_response.json()

    logging.debug(f"Api query: {query_url}")

    return availability


def get_channel_availability(
    availability: Dict,
    end_time: datetime,
    server_url: str
) -> AcquisionStatistics:
    '''
    Parameters
    ----------
    apollo_ip: str
        The address of the apollo server to query for availability statistics

    end_time: datetime
        The time to use to determine the time range to query for, as well as
         compare timestamps to to calculate latency

    Returns
    -------
    AquisitionStatistics
        Object containing list of ChannelLatency objects, and a list of
        channels with no availability information

    Raises
    ------
    KeyError: If the json-formatted data does not contain the expected keys

    '''
    channel_latency: List[ChannelLatency] = []
    unavailable_channels: List[str] = []

    try:
        for channel in availability["availability"]:
            if len(channel["ranges"]) <= 0:
                unavailable_channels.extend([channel["id"]])
            else:
                last_entry_index = len(channel["ranges"]) - 1
                last_timestamp = channel["ranges"][last_entry_index]['endTime']
                last_time = datetime.strptime(last_timestamp,
                                              '%Y-%m-%dT%H:%M:%S.%f000Z')

                latency = get_latency(
                    end_time=end_time,
                    server_url=server_url,
                    sncl=channel["id"]
                )

                if latency < 0:
                    latency = 0

                channel_latency.append(ChannelLatency(channel["id"],
                                       last_time, latency))

        return AcquisionStatistics(channel_latency, unavailable_channels)

    except KeyError as e:
        raise e


def check_availability_percentage(
    available_channels: int,
    expected_channel_count: int
) -> float:
    '''
    Check what percentage of expected channels are actually arriving at the
    ApolloServer

    Parameters
    ----------
    unavailable_channels: list
        List of unavailable channels

    expected_channel_count: int
        Number of channels expected to arrive

    Returns
    -------
    Float: The percentage of channels expected that are availabile

    Raises
    ------
    ZeroDivisionError: If for some reason there are no channels in the
    availability json returned from the ApolloServer
    '''

    try:
        percent_channels_available = (available_channels * 100 /
                                      expected_channel_count)
    except ZeroDivisionError as e:
        raise e

    logging.debug("ApolloCheck: Percent of channels available: " +
                  f"{percent_channels_available}%")

    return percent_channels_available


def get_latency_threshold_state(
    acquisition_stats: AcquisionStatistics,
    warn_time: str,
    crit_time: str,
    warn_threshold: str,
    crit_threshold: str
) -> LatencyCheckResults:
    '''
    Get a set of Nagios check results based on the provided latency thresholds

    Parameters
    ----------
    acquisition_stats: AcquisitionStatistics
        Object containing a list of station latency statistics

    warn_time: str
        The latency threshold used to count channels that contribute to the
        warning threshold

    crit_time: str
        The latency threshold used to count channels that contribute to the
        critical threshold

    warn_threshold: str
        The number of channels that need to fail the warn_time threshold to
        create a warning state

    crit_threshold: str
        The number of channels that need to fail the crit_time threshold to
        create a critical state

    Returns
    -------
    LatencyCheckResults:
        Object containing the count of channels within the warning threshold,
        critical threshold, and the Nagios state

    '''
    crit_count = 0
    warn_count = 0

    # Count the channels within the critical and warning thresholds

    for channel in acquisition_stats.channel_latency:
        if NagiosRange(crit_time).in_range(channel.latency):
            crit_count += 1
        elif NagiosRange(warn_time).in_range(channel.latency):
            warn_count += 1

    # Channels that don't have latency statistics for the past hour should
    # also count as critical
    # Removing this because of all the channels that have been tested
    # pre-deplpoyment but are not deployed. Maybe re-add later
    # crit_count += len(acquisition_stats.unavailable_channels)

    if NagiosRange(crit_threshold).in_range(crit_count):
        state = NagiosOutputCode.critical
    # Critical channels should also count towards the warning threshold
    elif NagiosRange(warn_threshold).in_range((warn_count+crit_count)):
        state = NagiosOutputCode.warning
    else:
        state = NagiosOutputCode.ok

    return LatencyCheckResults(crit_count, warn_count, state)


def assemble_details(
    acquisition_statistics: AcquisionStatistics,
    warning_time: str,
    critical_time: str
) -> str:

    stale_details = "Stale channels:\n"

    crit_details = f"\nChannels above with latency above {critical_time}s:\n"

    warn_details = f"\nChannels above with latency above {warning_time}s:\n"

    ok_details = "\nChannels with good latency:\n"

    for channel in acquisition_statistics.unavailable_channels:
        stale_details += f"{channel} "

    acquisition_statistics.channel_latency.sort(
        key=lambda x: x.latency,
        reverse=True)

    # Sort latency statistics by threshold for display
    for stats in acquisition_statistics.channel_latency:
        if NagiosRange(critical_time).in_range(stats.latency):
            crit_details += (f"{str(stats)}\n")
        elif NagiosRange(warning_time).in_range(stats.latency):
            warn_details += (f"{str(stats)}\n")
        else:
            ok_details += (f"{str(stats)}\n")

    details = stale_details + "\n" + crit_details + warn_details + ok_details

    return details
