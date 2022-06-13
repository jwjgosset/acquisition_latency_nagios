from eew_nagios.nagios import nagios_api
from typing import List
from datetime import datetime, timedelta
import pathlib
import logging


def get_fortimus(
    nagios_ip: str,
    api_key: str
) -> List:
    '''
    ######DEPRECATED#######
    Function to get a list of all members of the digitizer-fortimus hostgroup
    from Nagios

    Parameters
    ----------
    nagios_ip: str
        The IP address of the Nagios XI server

    api_key: str
        The api key to use to query the Nagios XI server

    Returns
    -------
    List: List of dictionaries containing each fortimus's host name and unique
    ID in Nagios
    '''
    fortimus_list = nagios_api.fetch_hostgroup_members(
        hostgroup_name='digitizer-fortimus',
        nagios_ip=nagios_ip,
        api_key=api_key
    )
    return fortimus_list


def check_availability(
    expected_channels: int,
    cache_folder: str,
    time: datetime
) -> float:
    '''
    Determines the percentage of expected channels that have actually arrived
    in the last hour

    Parameters
    ----------
    expectedchannels: int
        The number of expected channels

    cache_folder: str
        The folder where the Guralp Datacenter stores cached miniseed, soh and
        latency files

    time: datetime
        Datetime object representing the current time

    Returns
    -------
    float: The percentage of expected channels that have actually arrived in
    the last hour
    '''
    available_channels = 0

    cache_path = pathlib.Path(f"{cache_folder}/latency/")

    latency_files = list(cache_path.glob("*_*_00_HN?_*.csv"))

    logging.debug(f"Latency files found: {latency_files}")

    logging.debug(f"Current time: {time}")

    for lat_file in latency_files:
        timestamp = get_timestamp_of_last_row(lat_file)

        logging.debug(f"Last timetamp of {lat_file}: {timestamp}")

        if timestamp > time - timedelta(hours=1):
            available_channels += 1

    percent_available = (available_channels / expected_channels) * 100

    return percent_available


def get_timestamp_of_last_row(
    csv_file: pathlib.Path
) -> datetime:
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

    time_string = last_line.split(',')[0]

    timestamp = datetime.strptime(time_string, "%Y/%m/%d %H:%M:%S.%f")

    return timestamp
