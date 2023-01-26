import logging
from pathlib import Path
from acquisition_nagios.guralpdatacenter.guralp_availability import \
    assemble_details, get_masked_channels
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
@click.option(
    '--archive-folder',
    help="Location of the long term archive",
    default='/data/archive'
)
@click.option(
    '--mask-file',
    help="File containing list of channels to ignore",
    default=None
)
def main(
    warning: str,
    critical: str,
    warning_time: str,
    critical_time: str,
    warning_count: str,
    critical_count: str,
    logfile: str,
    log_level: Optional[str],
    cache_folder: str,
    archive_folder: str,
    mask_file: Optional[str]
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

    expected_channels = guralp_availability.get_expected_channels()

    logging.debug(f"Expected channels: {expected_channels}")

    if mask_file is not None:
        masked_channels = get_masked_channels(mask_file=Path(mask_file))
        logging.debug(f"Masked channels: {masked_channels}")
        # Remove masked channels from expected channels
        for item in expected_channels:
            if item in masked_channels:
                expected_channels.remove(item)
        logging.debug(
            f"Expected channels without masked channels: {expected_channels}")

    # Get the last timestamp and latency values for all the channels available
    # in the cache folder
    acquisition_statistics = guralp_availability.get_channel_latency(
        cache_folder=cache_folder,
        archive_folder=archive_folder,
        time=end_time,
        expected_channels=expected_channels
    )

    # Determine the percentage expected channels that have latency files in
    # the cache
    percent_available = guralp_availability.check_availability(
        expected_channels=len(expected_channels),
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

    details = assemble_details(
        acquisition_statistics=acquisition_statistics,
        warning_time=warning_time,
        critical_time=critical_time
    )

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
