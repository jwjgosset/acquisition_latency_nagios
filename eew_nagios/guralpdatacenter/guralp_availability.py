from typing import List
from datetime import datetime, timedelta
import pathlib
import logging
from dataclasses import dataclass
from eew_nagios.nagios.models import NagiosRange, NagiosOutputCode
from eew_nagios.nagios.acquision_availability import LatencyCheckResults


@dataclass
class ChannelLatency:
    channel: str
    timestamp: datetime
    latency: float


@dataclass
class AcquisitionStatistics:
    channel_latency: List[ChannelLatency]


def get_channel_latency(
    cache_folder: str,
    time: datetime
) -> AcquisitionStatistics:
    '''
    cache_folder: str
        The folder where the Guralp Datacenter stores cached miniseed, soh and
        latency files

    time: datetime
        Datetime object representing the current time
    '''

    channel_latency: List[ChannelLatency] = []

    cache_path = pathlib.Path(f"{cache_folder}/latency/")

    latency_files = list(cache_path.glob("*_*_00_HN?_*.csv"))

    logging.debug(f"Latency files found: {latency_files}")

    logging.debug(f"Current time: {time}")

    for lat_file in latency_files:

        channel_latency.append(
            get_latencystatistics_of_last_row(lat_file, time))

    return AcquisitionStatistics(channel_latency)


def check_availability(
    expected_channels: int,
    found_channels: int
) -> float:
    '''
    Determines the percentage of expected channels that have actually arrived
    in the last hour

    Parameters
    ----------
    expectedchannels: int
        The number of expected channels

    Returns
    -------
    float: The percentage of expected channels that have actually arrived in
    the last hour
    '''
    percent_available = (found_channels / expected_channels) * 100

    return percent_available


def get_latencystatistics_of_last_row(
    csv_file: pathlib.Path,
    time: datetime
) -> ChannelLatency:
    '''
    Reads a CSV file of latency information and returns the timestamp for the
    last entry

    Parameter
    ---------
    csv_file: Path
        A Path object containing the location of the csv file to check

    Returns
    -------
    datetime: A datetime object representing the timestamp of the most recent
    entry in the csv file
    '''
    f = open(csv_file, "r", encoding="utf-8", errors="ignore")
    last_line = f.readlines()[-1]

    line = last_line.split(',')

    time_string = line[0]

    channel_name = line[1]

    network_latency = float(line[2])

    timestamp = (datetime.strptime(time_string, "%Y/%m/%d %H:%M:%S.%f") -
                 timedelta(seconds=network_latency))

    latency = (time - timestamp).total_seconds()

    if latency < 0:
        latency = 0

    return ChannelLatency(channel_name, timestamp, latency)


def get_latency_threshold_state(
    acquisition_stats: AcquisitionStatistics,
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

    if NagiosRange(crit_threshold).in_range(crit_count):
        state = NagiosOutputCode.critical
    # Critical channels should also count towards the warning threshold
    elif NagiosRange(warn_threshold).in_range((warn_count+crit_count)):
        state = NagiosOutputCode.warning
    else:
        state = NagiosOutputCode.ok

    return LatencyCheckResults(crit_count, warn_count, state)
