import logging
from acquisition_nagios.guralpdatacenter import guralp_availability
from acquisition_nagios import acquisition_availability
import sys
from datetime import datetime
import click
from acquisition_nagios.config import LogLevels
from typing import Optional, List
from acquisition_nagios.nagios.models import NagiosPerformance


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
@click.option(
    '--cache-folder',
    help="Guralp cache folder",
    default='/var/cache/guralp'
)
def main(
    expected_channels: int,
    warning: str,
    critical: str,
    warning_time: str,
    critical_time: str,
    warning_count: str,
    critical_count: str,
    logfile: str,
    log_level: Optional[str],
    cache_folder: str
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

    # Use the current time to compare to channel timestamps
    end_time = datetime.now()

    # Get the last timestamp and latency values for all the channels available
    # in the cache folder
    acquisition_statistics = guralp_availability.get_channel_latency(
        cache_folder=cache_folder,
        time=end_time
    )

    # Determine the percentage expected channels that have latency files in
    # the cache
    percent_available = guralp_availability.check_availability(
        expected_channels=int(expected_channels),
        found_channels=len(acquisition_statistics.channel_latency)
    )

    # Determine the state based on this percentage
    state = acquisition_availability.get_state(
        percentage=percent_available,
        warn_threshold=warning,
        crit_threshold=critical)

    latency_results = guralp_availability.get_latency_threshold_state(
        acquisition_stats=acquisition_statistics,
        warn_time=warning_time,
        crit_time=critical_time,
        warn_threshold=warning_count,
        crit_threshold=critical_count
    )

    if latency_results.state > state:
        state = latency_results.state

    performances: List[NagiosPerformance] = []

    performances.append(NagiosPerformance(
        label='available',
        value=percent_available,
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

    missing_channels = int(expected_channels) - len(
        acquisition_statistics.channel_latency)

    details = (f"Stale channels: {missing_channels}, ")

    details += (f"Channels with latency over {warning_time}s: ")

    details += (f"{latency_results.warn_count}, ")

    details += (f"Channels with latency over {critical_time}s: ")

    details += (f"{latency_results.crit_count}")

    details += "\n\nChannels sorted by latency: \n"

    acquisition_statistics.channel_latency.sort(
        key=lambda x: x.latency,
        reverse=True)

    for channel_lat in acquisition_statistics.channel_latency:
        details += (f"{channel_lat.channel} {channel_lat.timestamp} " +
                    f"({channel_lat.latency}s)\n")

    message = acquisition_availability.assemble_message(
        state=state,
        percentage=percent_available,
        performances=performances,
        details=details
    )

    print(message)

    sys.exit(state.value)


if __name__ == '__main__':
    sys.exit(main())
