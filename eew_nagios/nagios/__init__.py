"""
..  codeauthor:: Charles Blais <charles.blais@canada.ca>
"""
import copy
from typing import Optional, Union, Dict

import requests

# Constants
STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2
STATE_UNKNOWN = 3


def _range_check(
    dataval: float,
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
        return dataval > float(threshold)

    try:
        # its a string so lets try to convert it
        return dataval > float(threshold)
    except ValueError:
        values = threshold.strip().split(':')
        # Check that the split resulted in 2 values
        if len(values) != 2:
            raise ValueError(f'Invalid threshold {threshold}')
        # Values[0] doesn't exist so compare if > critical threshold
        if len(values[0]) and not len(values[1]):
            if dataval > float(values[0]):
                return True
        # Values[1] doesn't exist so compare if < critical threshold
        elif len(values[1]) and not len(values[0]):
            if dataval < float(values[1]):
                return True
        # Otherwise is a range so check between min and max critical thresholds
        else:
            minthreshold = float(values[0])
            maxthreshold = float(values[1])
            if dataval >= minthreshold and dataval < maxthreshold:
                return True
    return False


def range_check(
    dataval: float,
    threshold: Union[float, str],
) -> bool:
    """
    According to the logic specified under:

    http://nagios-plugins.org/doc/guidelines.html#THRESHOLDFORMAT

    We check if values fall within/outside a range.

    The following is a wrapper funciton for _nrpe_range_check but
    handles the option of @ by reverting the response returned.

    :return: True
    """
    reverse_logic = False
    if isinstance(threshold, str):
        if threshold.startswith('@'):
            reverse_logic = True
            threshold = threshold[1:]
    status = _range_check(dataval, threshold)
    return not status if reverse_logic else status


class NagiosError(Exception):
    """Nagios Object Exception"""


class NagiosHost(dict):
    """
    Host definition object
    """
    def to_query_dict(self) -> dict:
        """
        Return data as dictionary (used by requests)
        """
        # set check periods if they are not defined (defaults)
        check_periods = [
            'check_period',
            'notification_period'
        ]
        for key in check_periods:
            if key not in self:
                self[key] = '24x7'

        required = [
            'host_name',
            'address',
            'max_check_attempts',
            'check_period',
            'notification_interval',
            'notification_period'
        ]
        for key in required:
            if key not in self:
                raise NagiosError(
                    f'{key} must be defined under host object')

        # remove empty fields
        return dict((k, v) for k, v in self.items() if v != '')


class NagiosService(dict):
    '''
    Service definition object
    '''
    def to_query_dict(self) -> dict:
        '''
        Return data as dictionary (used by requests)
        '''
        # set check periods if they are not defined (defaults)
        check_periods = [
            'check_period',
            'notification_period'
        ]
        for key in check_periods:
            if key not in self:
                self[key] = '24x7'

        required = [
            'host_name',
            'service_description',
            'check_command',
            'max_check_attempts',
            'check_interval',
            'retry_interval',
            'check_period',
            'notification_interval',
            'notification_period'
        ]
        for key in required:
            if key not in self:
                raise NagiosError(
                    f'{key} must be defined under service object')

        # remove empty fields
        return dict((k, v) for k, v in self.items() if v != '')


class NagiosQuery(dict):
    """
    Nagios Limited Query builder for object query

    We assume the programmer is sending correct format variables to the
    functions.
    No validation.
    """
    @property
    def starttime(self) -> Optional[float]:
        return self.get('starttime')

    @starttime.setter
    def starttime(self, value: float):
        self['starttime'] = value

    @property
    def endtime(self) -> Optional[float]:
        return self.get('endtime')

    @endtime.setter
    def endtime(self, value: float):
        self['endtime'] = value

    @property
    def records(self) -> Optional[str]:
        return self.get('records')

    @records.setter
    def records(self, value: Union[int, str]):
        self['records'] = str(value)

    def set_records(
        self,
        amount: int,
        starting_at: Optional[int] = None
    ):
        """
        Set the records option

        Arguments:
        amount - Integer, amount of records to return
            (or string as amount:starting_at)
        starting_at - Integer, starting at record
        """
        self['records'] = f'{amount}:{starting_at}' \
            if starting_at is not None else str(amount)

    @property
    def orderby(self) -> Optional[str]:
        return self.get('orderby')

    @orderby.setter
    def orderby(self, value: Union[int, str]):
        self['orderby'] = str(value)

    def set_orderby(
        self,
        column: str,
        order: Optional[str] = None
    ):
        """
        Set the orderbyoption

        Arguments:
        column - string, column to order
        order - string, ordering type
        """
        self['orderby'] = f'{column}:{order}' \
            if order is not None else column

    @property
    def columns(self) -> Dict[str, str]:
        return self.get('columns', {})

    @columns.setter
    def columns(self, value: Dict[str, str]):
        """
        Set column limitation with key value pair (kwargs)

        Note that the key must the column name and the value is the
        limitation field
        Format:
            key: value (find exact field match)
            key: lk:value (find field with value in name)
            key: in:value1,value2 (find field with list of matching value)
        """
        self['columns'] = value

    def to_query_dict(self):
        """
        Return nagios dictionary
        """
        query = copy.deepcopy(self)
        if 'columns' in self:
            query.update(query.pop('columns'))
        return query


class NagiosAPI(object):
    """
    The following is an wrapper to the API documented under Nagios XI
    """
    def __init__(
        self,
        apikey: str,
        baseurl: str = 'http://nagios-e1.seismo.nrcan.gc.ca/nagiosxi/api/v1/'
    ):
        """
        Build essential arguments to API calls

        Arguments:
        apikey - string, api key

        Keywords;
        baseurl - Nagios XI base URL (up to version number)
        """
        self.baseurl = baseurl
        self.apikey = apikey

    def _get(
        self,
        url: str,
        params: dict
    ) -> dict:
        """
        Get object definition from Nagios (json)

        Exception:
        Throws request.exceptions
        """
        # add apikey to query
        params['apikey'] = self.apikey
        # query nagios xi
        req = requests.get(url, params=params)
        # throw error if not 200
        req.raise_for_status()
        # return response
        return req.json()

    def _set(
        self,
        url: str,
        params: Optional[dict] = None
    ) -> dict:
        """
        Set object definition too Nagios (json)

        Exception:
        Throws request.exceptions
        """
        # query nagios xi
        req = requests.post(url, params={'apikey': self.apikey}, data=params)
        # throw error if not 200
        req.raise_for_status()
        # return response
        return req.json()

    def apply(self) -> dict:
        '''
        Apply configuration
        '''
        return self._set(f'{self.baseurl}system/applyconfig')

    def get_host(
        self,
        nagiosquery: NagiosQuery
    ) -> dict:
        """
        Get host

        Arguments:
        nagiosobjquery -

        Return:
        JSON (see api doc)
        """
        return self._get(
            f'{self.baseurl}objects/host',
            nagiosquery.to_query_dict())

    def get_service(
        self,
        nagiosquery: NagiosQuery
    ) -> dict:
        """
        Get service

        Arguments:
        nagiosobjquery -

        Return:
        JSON (see api doc)
        """
        return self._get(
            f'{self.baseurl}objects/service',
            nagiosquery.to_query_dict())

    def set_host(
        self,
        nagioshost: NagiosHost,
    ) -> dict:
        """
        Set host

        Arguments:
        nagioshost -

        Return:
        JSON (see api doc)
        """
        return self._set(
            f'{self.baseurl}config/host',
            nagioshost.to_query_dict())

    def set_service(
        self,
        nagiosservice: NagiosService,
    ) -> dict:
        """
        Set Service

        Arguments:
        nagiosservice -

        Return:
        JSON (see api doc)
        """
        return self._set(
            f'{self.baseurl}config/service',
            nagiosservice.to_query_dict())
