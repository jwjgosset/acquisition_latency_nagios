from eew_nagios.nagios import nrdp
from eew_nagios.nagios.models import NagiosPerformance, NagiosOutputCode, \
    NagiosRange, NagiosResult, NagiosVerbose
from typing import List


def assemble_message(
    state: NagiosOutputCode,
    percentage: float,
    performances: List[NagiosPerformance],
    details: str
) -> NagiosResult:
    '''
    Assembles the message to feet to Nagios to display in Nagios for this
    service

    Parameters
    ----------
    statetxt: str
        The display text for the state the service is in. Either OK, WARNING,
        CRITICAL or UNKNOWN

    percentage: float
        The percentage of channels that have successfully streamed to the
        aquisition server during the time period

    Returns
    -------
    str: The assembled status message with performance data to display in
    Nagios
    '''
    percent = '%.2f' % percentage
    info = f'{percent}% of expected channels available'

    result = NagiosResult(
        summary=info,
        verbose=NagiosVerbose.multiline,
        status=state,
        performances=performances,
        details=details
    )

    return result


def prepare_check_results(
    host_name: str,
    state: int,
    output: str
) -> nrdp.NagiosCheckResult:
    '''
    Assemble check results into a format that the NRDP API for Nagios can
    ingest

    Parameters
    ----------
    host_name: str
        The host name for the aquision server as it is configured in Nagios

    state: int
        The integer representation of the service's state. 0=OK, 1=WARNING,
        2=CRITICAL, 3=UNKNOWN

    output: str
        The message to display in Nagios beside the service, including
        performance data

    Returns
    -------
    NagiosCheckResult: Object used to package check results in a way that the
    Nagios NRDP API can ingest
    '''
    check_result = nrdp.NagiosCheckResult(
        hostname=host_name,
        servicename="Channels available in last hour",
        state=state,
        output=output
    )
    return check_result


def get_state(
    percentage: float,
    warn_threshold: str,
    crit_threshold: str
) -> NagiosOutputCode:
    '''
    Determine the state of the service check according the the thresholds

    Parameters
    ----------

    percentage: float
        The percentage of the channels that are available in the ApolloServer

    Returns
    -------
    int: The integer representing the state. 0=OK, 1=WARNING, 2=CRITICAL,
    3=UNKNOWN

    str: The state text for the current state
    '''

    if NagiosRange(crit_threshold).in_range(percentage):
        state = NagiosOutputCode.critical
    elif NagiosRange(warn_threshold).in_range(percentage):
        state = NagiosOutputCode.warning
    else:
        state = NagiosOutputCode.ok

    return state
