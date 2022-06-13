"""
..  codeauthor:: Gloria Son <gloria.son@canada.ca>
..  codeauthor:: Charles Blais <charles.blais@canada.ca>

..  history:: 2017-11-24 - Gloria Son
    Created NRDP Centaur SOH check

..  history:: 2018-10-23 - Charles Blais
    Clean up code and configuration

Use nrdp to query fdsn and get trace data into Nagios

Author: Gloria Son 2017-11-24
"""

import xml.etree.ElementTree as ET
import requests
import logging


class NagiosCheckResult(dict):
    """
    Dictionary with keys hostname, servicename, state, output

    If the servicename is not set, it is assume to be a host check
    """
    def __init__(self, *args, **kwargs):
        super(NagiosCheckResult, self).__init__(*args, **kwargs)
        self.setdefault('hostname', '')
        self.setdefault('servicename', '')
        self.setdefault('state', 3)  # unknown
        self.setdefault('output', '')


class NagiosCheckResults(list):
    """
    Create Nagios check results response with a list of CheckResult
    """
    def to_xml(
        self
    ) -> bytes:
        """
        Convert list of check results to XML response (NRDP format)
        """
        xml = ET.Element('checkresults')
        for result in self:
            logging.debug(f"Trying: {result}")
            # define if the type of check result is host or service
            new = ET.SubElement(
                xml,
                'checkresult',
                type='service' if result['servicename'] else 'host')
            ET.SubElement(new, 'hostname').text = result['hostname']
            if result['servicename']:
                ET.SubElement(new, 'servicename').text = result['servicename']
            ET.SubElement(new, 'state').text = str(result['state'])
            ET.SubElement(new, 'output').text = result['output']
        return ET.tostring(xml)


def submit(
    nrdp: NagiosCheckResults,
    nagios: str,
    token: str,
    **kwargs
) -> None:
    """
    Submit NRDP Check results to Nagios

    :type nrdp: :class:`NagiosCheckResults`
    :param str nagios: nagios URL
    :param str token: nagios access token
    """
    data = {
        'token': token,
        'cmd': 'submitcheck',
        'XMLDATA': nrdp.to_xml()
    }

    logging.debug(data)
    request = requests.post(
        f"{nagios}/nrdp/",
        data=data, **kwargs)

    logging.debug(request.status_code)
    request.raise_for_status()
