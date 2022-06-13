from eew_nagios.nagios import nrdp
from eew_nagios import nagios
from typing import Tuple, Union


def assemble_message(
    statetxt: str,
    percentage: float
) -> str:
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
    performance = '%.2f' % percentage
    info = f'{performance}% of expected channels'

    message = f"{statetxt} - {info} | channels={performance}%"

    return message


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
    warn_threshold: Union[str, float],
    crit_threshold: Union[str, float]
) -> Tuple[int, str]:
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

    if range_check(percentage, crit_threshold):
        state = nagios.STATE_CRITICAL
        statetxt = "CRITICAL"
    elif range_check(percentage, warn_threshold):
        state = nagios.STATE_WARNING
        statetxt = "WARNING"
    else:
        state = nagios.STATE_OK
        statetxt = "OK"

    return state, statetxt


def range_check(
    value: float,
    threshold: Union[float, str]
) -> bool:
    """
    Compare average to critical/warning based on a given warning/critical
    integer value or string value (typically includes a colon to
    represent >= and <=)

    Threshold can be:
    - float
    - float:float (min to max)
    - float: (min)
    - :float (max)

    :raises ValueError: Invalid NRDP range check
    """
    # Check if the threshold is numeric then use threshold comparison
    if isinstance(threshold, float):
        return value > float(threshold)

    try:
        # its a string so lets try to convert it
        return value > float(threshold)
    except ValueError:
        values = threshold.strip().split(':')
        # Check that the split resulted in 2 values
        if len(values) != 2:
            raise ValueError(f'Invalid threshold {threshold}')
        # Values[0] doesn't exist so compare if > critical threshold
        if len(values[0]) and not len(values[1]):
            if value > float(values[0]):
                return True
        # Values[1] doesn't exist so compare if < critical threshold
        elif len(values[1]) and not len(values[0]):
            if value < float(values[1]):
                return True
        # Otherwise is a range so check between min and max critical thresholds
        else:
            minthreshold = float(values[0])
            maxthreshold = float(values[1])
            if value >= minthreshold and value < maxthreshold:
                return True
    return False
