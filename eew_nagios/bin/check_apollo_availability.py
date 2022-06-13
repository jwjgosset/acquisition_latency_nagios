from eew_nagios.apolloserver import availability_health  # type: ignore
from datetime import datetime
from eew_nagios.nagios import aquision_availability
from eew_nagios.config import LogLevels
import logging
import click


@click.command()
@click.option(
    '--expected-channels',
    help=('The number or channels expected to arrive at the aquisition ' +
          'server')
)
@click.option(
    '--warning',
    help=('The warning range for the percentage of channels available. ' +
          'See Nagios documentation')
)
@click.option(
    '--critical',
    help=('The critical range for the percentage of channels available. ' +
          'See Nagios documentation'),
    required=True
)
@click.option(
    '--warning-time',
    help=("The latency in seconds for a channel that should be " +
          "considered for a warning state")
    )
@click.option(
    '--critical-time',
    help=("The latency in seconds for a channel that should be " +
          "considered for a critical state")
    )
@click.option(
    '--warning-count',
    help=("The number of channels required exceeding the waring-time to " +
          "qualify for a warning state")
    )
@click.option(
    '--critical-count',
    help=("The number of channels required exceeding the critical-time " +
          "to qualify for a critical state"),
    )
@click.option(
    '--logfile',
    default=None,
    help='To log to a file instead of stdout, specify the filename.',
)
@click.option(
    '--log-level',
    type=click.Choice([v.value for v in LogLevels]),
    help="Log more information about the program's execution",
    default=LogLevels.WARNING

)
def main(
    expected_channels: int,
    warning: float,
    critical: float,
    warning_time: float,
    critical_time: float,
    warning_count: int,
    critical_count: int,
    logfile: str,
    log_level: str
):

    # Configure logging
    if logfile is not None:
        logging.basicConfig(
            format='%(asctime)s:%(levelname)s:%(message)s',
            datefmt="%Y-%m-%d %H:%M:%S",
            level=log_level,
            filename=logfile, filemode='W')
    else:
        logging.basicConfig(
            format='%(asctime)s:%(levelname)s:%(message)s',
            datefmt="%Y-%m-%d %H:%M:%S",
            level=log_level)

    # Get the current time to use as the end_time of the availability query
    # and to compare timestamps to for latency values
    end_time = datetime.now()

    # Get the channel_latency objects and list of unavailable channels
    channel_latency, unavailable_channels = \
        availability_health.get_channel_availability(
            apollo_ip="localhost",
            end_time=end_time)

    # Calculate percentage of channels that are available
    percent = availability_health.check_availability_percentage(
        available_channels=len(channel_latency),
        expected_channel_count=expected_channels)

    logging.debug(f"Available channels: {percent}%")
    logging.debug("Unvailable Channels: " +
                  ', '.join(unavailable_channels))

    # Determine the state according to the percentage of available channels
    state, statetxt = aquision_availability.get_state(
        percentage=percent,
        warn_threshold=warning,
        crit_threshold=critical)

    # Determine the state accoding to the latency thresholds
    lat_state, lat_statetxt = availability_health.get_latency_threshold_state(
        channel_latency,
        warn_time=warning_time,
        crit_time=critical_time,
        warn_threshold=warning_count,
        crit_threshold=critical_count
        )

    # If the latency threshold state is higher than the available channel
    # state, overwrite it
    if lat_state > state:
        state = lat_state
        statetxt = lat_statetxt

    message = aquision_availability.assemble_message(
        statetxt=statetxt,
        percentage=percent)

    print(message)

    print(f"Channels in binder but not present: {len(unavailable_channels)}")
    for channel in unavailable_channels:
        print(channel)

    print("Channels sorted by latency: ")

    channel_latency.sort(key=lambda x: x.latency)
    for channel_lat in channel_latency:
        print(f"{channel_lat.channel} {channel_lat.timestamp}")

    return state


if __name__ == '__main__':
    main()
