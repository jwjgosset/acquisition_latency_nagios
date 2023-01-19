from typing import List
from datetime import datetime, timedelta
import pathlib
import logging
from dataclasses import dataclass
from acquisition_nagios.nagios.models import NagiosRange, NagiosOutputCode
from acquisition_nagios.acquisition_availability import LatencyCheckResults
from subprocess import Popen, PIPE


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
class AcquisitionStatistics:
    channel_latency: List[ChannelLatency]
    unavailable_channels: List[str]


def get_expected_channels(
    gdc_address: str = "localhost",
    seedlink_port: str = "18000"
) -> List[str]:
    '''
    Returns a list of channels that the acquisition server is expecting using
    slinktool

    Parameters
    ----------
    gdc_address: str
        The IP address or hostname of the acqusition server. Because this
        nagios plugin is expected to run on the Guralp Datacenter, the default
        is localhost

    seedlink_port: str
        The port that the seedlink server is hosted on. Default: 18000

    Returns: List[str]
        List of expected channels, in the format NN.SSSSS.LL.CCC
    '''

    # Use -Q option with slinktool to get a list of each individual channel
    cmd = ['slinktool', '-Q', f"{gdc_address}:{seedlink_port}"]
    process = Popen(cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()

    # Log any error using slinktool
    if stderr != b'':
        logging.error(f"Slinktool error: {stderr.decode('utf-8')}")

    # Decode and split the stdout lines
    outlines = stdout.decode('utf-8').split('\n')

    expected_channels: List = []

    for line in outlines:
        line_parts = line.split(' ')

        # Less than 3 parts means that an entire SNCL is not present
        if len(line_parts) > 3:
            # Only record channel names for seismic data
            if line_parts[3] in ['HNZ', 'HNN', 'HNE', 'HHZ', 'HHN', 'HHE']:
                channel = (f"{line_parts[0]}.{line_parts[1]}.{line_parts[2]}" +
                           f".{line_parts[3]}")
                expected_channels.append(channel)
    return expected_channels


def get_channel_latency(
    cache_folder: str,
    archive_folder: str,
    time: datetime,
    expected_channels: List[str]
) -> AcquisitionStatistics:
    '''
    Parameters
    ----------
    cache_folder: str
        The folder where the Guralp Datacenter stores cached miniseed, soh and
        latency files

    archive_folder: str
        The folder where the long-term archive is stored

    time: datetime
        Datetime object representing the current time

    expected_channels: List
        List of channels expected to be available

    Returns
    -------
    AcquisitionStatistics
        Object containing arrival times and latencies for channels
    '''

    # Use year and jday from current time to ensure that old files aren't read
    year = time.year
    jday = time.strftime('%-j')

    channel_latency: List[ChannelLatency] = []

    # Determine the path to the latency subdirectory in the cache and archive
    cache_path = pathlib.Path(cache_folder).joinpath('latency')

    archive_path = pathlib.Path(archive_folder).joinpath('latency')

    missing_channels: List[str] = []

    for channel in expected_channels:

        channel_parts = channel.split('.')

        net = channel_parts[0]
        sta = channel_parts[1]
        loc = channel_parts[2]
        cha = channel_parts[3]

        # Search for a latency file for the channel in the cache
        latency_files = list(cache_path.glob(
            f"{net}_{sta}_{loc}_{cha}_{year}_{jday}.csv"))

        if len(latency_files) < 1:

            # Loop through the last 7 days of the long-term archive
            working_date = time - timedelta(days=1)

            end_date = time - timedelta(days=7)

            while working_date > end_date:
                latency_files = list(archive_path.glob(
                    (working_date.strftime('%Y/%m/%d') +
                     f"/{net}_{sta}_{loc}_{cha}_*_*.csv")))

                # Stop looping if a latency file is found
                if len(latency_files) > 0:
                    break
                else:
                    working_date = working_date - timedelta(days=1)

        if len(latency_files) > 0:
            channel_latency.append(
                get_latencystatistics_of_last_row(
                    csv_file=latency_files[0]))
        # If no latency file was found for the last 7 days, flag the channel
        # as misisng/unavailable
        else:
            missing_channels.append(channel)

    return AcquisitionStatistics(
        channel_latency=channel_latency,
        unavailable_channels=missing_channels)


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
    csv_file: pathlib.Path
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
    # Get the last line from the file
    f = open(csv_file, "r", encoding="utf-8", errors="ignore")
    last_line = f.readlines()[-1]

    # Break the line up
    line = last_line.split(',')

    time_string = line[0]

    channel_name = line[1]

    data_latency = line[3]

    # Convert data latency into real number
    # =100/100+0.3

    datlatparts = data_latency.split('+')

    net_lat = float(datlatparts[1])

    filltimeparts = ((datlatparts[0]).lstrip('=')).split('/')

    dat_lat = net_lat + (float(filltimeparts[0]) / float(filltimeparts[1]))

    # Assemble ChannelLatency object
    timestamp = (datetime.strptime(time_string, "%Y/%m/%d %H:%M:%S.%f") +
                 timedelta(seconds=dat_lat))

    latency = dat_lat

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


def assemble_details(
    acquisition_statistics: AcquisitionStatistics,
    warning_time: str,
    critical_time: str
) -> str:

    acquisition_statistics.channel_latency.sort(
        key=lambda x: x.latency,
        reverse=True)

    missing_channels = "Channels stale for more than a week:\n"

    for missing_channel in acquisition_statistics.unavailable_channels:
        missing_channels += (missing_channel + '\n')

    stale_channels = "Stale channels:\n"

    critical_channels = f"Channels with latency above {critical_time}s:\n"

    warning_channels = f"Channels with latency above {warning_time}s:\n"

    good_channels = "Channels with good latency:\n"

    for channel in acquisition_statistics.channel_latency:
        if channel.timestamp < (datetime.now() - timedelta(hours=1)):
            stale_channels += (str(channel) + '\n')

        elif channel.latency > float(critical_time):
            critical_channels += (str(channel) + '\n')

        elif channel.latency > float(warning_time):
            warning_channels += (str(channel) + '\n')

        else:
            good_channels += (str(channel) + '\n')

    details = (missing_channels + '\n' + stale_channels + '\n' +
               critical_channels + '\n' + warning_channels + '\n'
               + good_channels)

    return details
