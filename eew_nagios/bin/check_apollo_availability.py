from eew_nagios.apolloserver import availability_health  # type: ignore
from datetime import datetime
from eew_nagios.nagios import acquision_availability
from eew_nagios.config import LogLevels
from eew_nagios.nagios.models import NagiosPerformance
from typing import List, Optional
import logging
import click
import sys


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
    expected_channels: str,
    warning: str,
    critical: str,
    warning_time: str,
    critical_time: str,
    warning_count: str,
    critical_count: str,
    logfile: str,
    log_level: Optional[str]
) -> int:

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
    acquisition_statistics = \
        availability_health.get_channel_availability(
            apollo_ip="localhost",
            end_time=end_time)

    # Calculate percentage of channels that are available
    percent = availability_health.check_availability_percentage(
        available_channels=len(acquisition_statistics.channel_latency),
        expected_channel_count=int(expected_channels))

    logging.debug(f"Available channels: {percent}%")
    logging.debug("Unvailable Channels: " +
                  ', '.join(acquisition_statistics.unavailable_channels))

    # Determine the state according to the percentage of available channels
    state = acquision_availability.get_state(
        percentage=percent,
        warn_threshold=warning,
        crit_threshold=critical)

    # Determine the state accoding to the latency thresholds
    latency_results = availability_health.get_latency_threshold_state(
        acquisition_statistics,
        warn_time=warning_time,
        crit_time=critical_time,
        warn_threshold=warning_count,
        crit_threshold=critical_count
        )

    # If the latency threshold state is higher than the available channel
    # state, overwrite it
    if latency_results.state > state:
        state = latency_results.state

    performances: List[NagiosPerformance] = []

    performances.append(NagiosPerformance(
        label='available',
        value=percent,
        uom='%',
        warning=float(warning.strip(':')),
        critical=float(critical.strip(':'))
    ))
    performances.append(NagiosPerformance(
        label='critical_count',
        value=latency_results.crit_count,
        critical=float(critical_count)
    ))
    performances.append(NagiosPerformance(
        label='warning_count',
        value=latency_results.warn_count,
        warning=float(warning_count)
    ))

    details = ("Channels more than 1 hour old: " +
               f"{len(acquisition_statistics.unavailable_channels)}\n")

    for channel in acquisition_statistics.unavailable_channels:
        details += f"{channel} "

    details += "\n\nChannels sorted by latency: \n"

    acquisition_statistics.channel_latency.sort(
        key=lambda x: x.latency,
        reverse=True)

    for channel_lat in acquisition_statistics.channel_latency:
        details += (f"{channel_lat.channel} {channel_lat.timestamp} " +
                    f"({channel_lat.latency}s)\n")

    message = acquision_availability.assemble_message(
        state=state,
        percentage=percent,
        performances=performances,
        details=details
        )

    print(message)

    return state.value


if __name__ == '__main__':
    sys.exit(main())
