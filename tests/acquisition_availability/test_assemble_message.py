from eew_nagios.acquisition_availability import assemble_message
from eew_nagios.nagios.models import NagiosOutputCode, NagiosPerformance


def test_assemble_message_ok():
    state = NagiosOutputCode.ok
    percentage = 95
    performances = [NagiosPerformance(
        label="Percentage",
        value=95,
        uom='%'
    )]
    details = "Some Details"
    results = assemble_message(
        state=state,
        percentage=percentage,
        performances=performances,
        details=details
    )
    assert results.summary == "OK: 95.00% of expected channels available"


def test_assemble_message_warning():
    state = NagiosOutputCode.warning
    percentage = 70
    performances = [NagiosPerformance(
        label="Percentage",
        value=70,
        uom='%'
    )]
    details = "Some Details"
    results = assemble_message(
        state=state,
        percentage=percentage,
        performances=performances,
        details=details
    )
    assert results.summary == "WARNING: 70.00% of expected channels available"


def test_assemble_message_critical():
    state = NagiosOutputCode.critical
    percentage = 65
    performances = [NagiosPerformance(
        label="Percentage",
        value=65,
        uom='%'
    )]
    details = "Some Details"
    results = assemble_message(
        state=state,
        percentage=percentage,
        performances=performances,
        details=details
    )
    assert results.summary == "CRITICAL: 65.00% of expected channels available"


def test_assemble_message_unknown():
    state = NagiosOutputCode.unknown
    percentage = 65
    performances = [NagiosPerformance(
        label="Percentage",
        value=65,
        uom='%'
    )]
    details = "Some Details"
    results = assemble_message(
        state=state,
        percentage=percentage,
        performances=performances,
        details=details
    )
    assert results.summary == "UNKNOWN: 65.00% of expected channels available"
