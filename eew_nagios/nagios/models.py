'''
Model information is based on structure defined under:

https://nagios-plugins.org/doc/guidelines.html

..  codeauthor:: Charles Blais
'''
from dataclasses import dataclass, field

from typing import Optional, List

from enum import IntEnum


class NagiosVerbose(IntEnum):
    minimal: int = 0
    singleline: int = 1
    multiline: int = 2
    debug: int = 3


class NagiosOutputCode(IntEnum):
    ok: int = 0
    warning: int = 1
    critical: int = 2
    unknown: int = 3


@dataclass
class NagiosRange:
    range: str

    def in_range(self, value: float) -> bool:
        '''
        Determine if the value is in range.

        :param float value: value to check
        :rtype: bool

        :raises ValueError: range format invalid
        '''
        parts = self.range.strip().split(':')
        if len(parts) > 2:
            raise ValueError(f'range format invalid: {self.range}')

        reverse = False
        if parts[0].startswith('@'):
            reverse = True
            parts[0] = parts[0][1:]

        cond = False
        if len(parts) == 1:
            if parts[0] == '~':
                raise ValueError(f'range format invalid: {self.range}')
            cond = value < 0 or value > float(parts[0])
        else:
            if parts[0] == '~':
                cond = value > float(parts[1])
            elif len(parts[1]) == 0:
                cond = value < float(parts[0])
            else:
                cond = value < float(parts[0]) or value > float(parts[1])
        return not cond if reverse else cond


@dataclass
class NagiosPerformance:
    label: str
    value: float
    uom: str = ''
    warning: Optional[float] = None
    critical: Optional[float] = None
    minimum: Optional[float] = None
    maximum: Optional[float] = None

    def __str__(self) -> str:
        '''
        Convert nagios performance to plugin compliant string

        As per guideline, it is formulated as:

        'label'=value[UOM];[warn];[crit];[min];[max]

        :rtype: str
        '''
        warning = '' if self.warning is None else "%.5f" % self.warning
        critical = '' if self.critical is None else "%.5f" % self.critical
        minimum = '' if self.minimum is None else "%.5f" % self.minimum
        maximum = '' if self.maximum is None else "%.5f" % self.maximum

        return f'\'{self.label}\'={self.value}{self.uom};{warning}\
;{critical};{minimum};{maximum}'


@dataclass
class NagiosResult:
    summary: str = ''
    verbose: NagiosVerbose = NagiosVerbose.minimal
    status: NagiosOutputCode = NagiosOutputCode.unknown
    performances: List[NagiosPerformance] = field(default_factory=list)
    details: str = ''

    def __str__(self) -> str:
        '''
        Convert the nagios result to a plugin conforming
        output used by nagios.  See plugin guidelines.

        :rtype: str
        '''

        if self.verbose == NagiosVerbose.minimal:
            return self.summary

        perf = ' |'
        for performance in self.performances:
            perf += ' ' + str(performance)

        if self.verbose == NagiosVerbose.singleline:
            return f'{self.summary}{perf}'

        return f'{self.summary}{perf}\n{self.details}'


@dataclass
class NagiosResultExtended:
    '''
    NagiosResults works fine for NRPE,NCPA checks following the standard
    Nagios plugin format however NRDP (passive check) can submit results
    to Nagios XI but do so it needs the hostname and service that it
    needs to update.
    '''
    hostname: str
    servicename: str
    check: NagiosResult


@dataclass
class NRDPCheckResult:
    type: str


@dataclass
class NRDPCheckResults:
    checkresult: NRDPCheckResult
    hostname: str
    servicename: str
    state: str
    output: str


@dataclass
class NRDP:
    checkresults: List[NRDPCheckResults] = field(default_factory=list)
