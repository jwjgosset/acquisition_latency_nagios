from eew_nagios.acquisition_availability import get_state
from eew_nagios.nagios.models import NagiosOutputCode


def test_get_state():
    assert get_state(
        percentage=90,
        warn_threshold="80:",
        crit_threshold="70:"
    ) == NagiosOutputCode.ok

    assert get_state(
        percentage=75,
        warn_threshold="80:",
        crit_threshold="70:"
    ) == NagiosOutputCode.warning

    assert get_state(
        percentage=65,
        warn_threshold="80:",
        crit_threshold="70:"
    ) == NagiosOutputCode.critical
