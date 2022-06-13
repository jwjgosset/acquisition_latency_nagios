'''
Module with functions for interacting with and parsing the output of the
ApolloServer Availability API
'''
from attr import dataclass
import requests
import logging
from typing import Tuple, Dict, List
from datetime import datetime, timedelta
# from eew_nagios import nagios
# from eew_nagios.nagios import nrdp
from requests import HTTPError

from eew_nagios.nagios.models import NagiosOutputCode, NagiosRange


@dataclass
class ChannelLatency:
    channel: str
    timestamp: datetime
    latency: float


def get_latency(
    current_time: datetime,
    last_time: datetime,
) -> float:

    latencydelta = current_time - last_time

    return latencydelta.total_seconds()


def assemble_url(
    server_url: str,
    start_time: datetime,
    end_time: datetime
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

    full_url = "http://" + server_url + ':8787' + api_url + option_url

    return full_url


def get_availability_json(
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
    availability_response = requests.get(query_url)

    availability_response.raise_for_status()

    availability = availability_response.json()

    return availability


def get_channel_availability(
    apollo_ip: str,
    end_time: datetime
) -> Tuple[List[ChannelLatency], List[str]]:
    '''
    Return a list of available channels for the time range. Available
    channels are those which appear in the Availability json and are not empty

    Parameters
    ----------
    availability: Dict
    Json-formatted dictionary object containing availability information

    Returns
    -------
    List: A list of the IDs of unavailable channels

    Raises
    ------
    KeyError: If the json-formatted data does not contain the expected keys

    '''
    start_time = end_time - timedelta(hours=1)
    url = assemble_url(apollo_ip, start_time, end_time)

    try:
        availability = get_availability_json(url)
    except HTTPError as e:
        raise e
    except ValueError as e:
        raise e

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

                latency = get_latency(end_time, last_time)

                channel_latency.extend([ChannelLatency(channel["id"],
                                        last_time, latency)])

        return channel_latency, unavailable_channels

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


@dataclass
class LatencyCheckResults:
    crit_count: int
    warn_count: int
    state: NagiosOutputCode


def get_latency_threshold_state(
    channel_latencies: List[ChannelLatency],
    warn_time: str,
    crit_time: str,
    warn_threshold: str,
    crit_threshold: str
) -> LatencyCheckResults:

    crit_count = 0
    warn_count = 0

    for channel in channel_latencies:
        if NagiosRange(crit_time).in_range(channel.latency):
            crit_count += 1
        elif NagiosRange(warn_time).in_range(channel.latency):
            warn_count += 1

    if NagiosRange(crit_threshold).in_range(crit_count):
        state = NagiosOutputCode.critical
    elif NagiosRange(warn_threshold).in_range(warn_count):
        state = NagiosOutputCode.warning
    else:
        state = NagiosOutputCode.ok

    return LatencyCheckResults(crit_count, warn_count, state)
