# import configparser
# from eew_nagios.bin import NRDP_CONFIG
from eew_nagios.apolloserver import availability_health  # type: ignore
# from eew_nagios.nagios import nagios_api  # type: ignore
# from eew_nagios.nagios import nrdp
from datetime import datetime
from eew_nagios.nagios import aquision_availability
import logging
import argparse


def main():
    argsparser = argparse.ArgumentParser()
    argsparser.add_argument(
        '-v',
        '--verbose',
        action='count',
        default=0,
        help="Log more information about the program's execution"
    )
    argsparser.add_argument(
        '-L',
        '--logfile',
        default=None,
        help='To log to a file instead of stdout, specify the filename.',
        type=str
    )
    argsparser.add_argument(
        '-e',
        '--expected_channels',
        help=('The number or channels expected to arrive at the aquisition ' +
              'server'),
        required=True,
        type=int
    )
    argsparser.add_argument(
        '-w',
        '--warning',
        help=('The warning range for the percentage of channels available. ' +
              'See Nagios documentation'),
        required=True
    )
    argsparser.add_argument(
        '-c',
        '--critical',
        help=('The critical range for the percentage of channels available. ' +
              'See Nagios documentation'),
        required=True
    )
    argsparser.add_argument(
        '--warning_time',
        help=("The latency in seconds for a channel that should be " +
              "considered for a warning state"),
        required=True,
        type=int
    )
    argsparser.add_argument(
        '--critical_time',
        help=("The latency in seconds for a channel that should be " +
              "considered for a critical state"),
        required=True,
        type=int
    )
    argsparser.add_argument(
        '--warning_count',
        help=("The number of channels required exceeding the waring-time to " +
              "qualify for a warning state"),
        required=True,
        type=int
    )
    argsparser.add_argument(
        '--critical_count',
        help=("The number of channels required exceeding the critical-time " +
              "to qualify for a critical state"),
        required=True,
        type=int
    )

    args = argsparser.parse_args()

    if args.verbose >= 3:
        logging_level = logging.DEBUG
    elif args.verbose == 2:
        logging_level = logging.INFO
    elif args.verbose == 1:
        logging_level = logging.WARNING
    else:
        logging_level = logging.ERROR

    if args.logfile is not None:
        logging.basicConfig(
            format='%(asctime)s:%(levelname)s:%(message)s',
            datefmt="%Y-%m-%d %H:%M:%S",
            level=logging_level,
            filename=args.logfile, filemode='W')
    else:
        logging.basicConfig(
            format='%(asctime)s:%(levelname)s:%(message)s',
            datefmt="%Y-%m-%d %H:%M:%S",
            level=logging_level)

    end_time = datetime.now()

    channel_latency, unavailable_channels = \
        availability_health.get_channel_availability(
            apollo_ip="localhost",
            end_time=end_time)

    expected_channel_count = str(args.expected_channels)

    percent = availability_health.check_availability_percentage(
        unavailable_channels=unavailable_channels,
        expected_channel_count=expected_channel_count)

    logging.debug(f"Available channels: {percent}%")
    logging.debug("Unvailable Channels: " +
                  ', '.join(unavailable_channels))

    state, statetxt = aquision_availability.get_state(
        percentage=percent,
        warn_threshold=args.warning,
        crit_threshold=args.critical)

    lat_state, lat_statetxt = availability_health.get_latency_threshold_state(
        channel_latency,
        warn_time=args.warning_time,
        crit_time=args.critical_time,
        )

    if lat_state > state:
        state = lat_state
        statetxt = lat_statetxt

    message = aquision_availability.assemble_message(
        statetxt=statetxt,
        percentage=percent)

    print(message)

    print("Channels in binder but not present: ")
    for channel in unavailable_channels:
        print(channel)

    print("Channel latency: ")
    for channel in channel_latency:
        print(f"{channel.channel} {channel.timestamp}")

    return state


if __name__ == '__main__':
    main()
