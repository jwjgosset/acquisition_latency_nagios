from typing import List
import requests
from requests import HTTPError


def get_object_query(
    nagios_ip: str,
    object_query: str,
    api_key: str
) -> requests.Response:
    '''
    Query Nagios XI to get information about an object or many objects

    Parameters
    ----------
    nagios: str
        The IP address or hostname of the Nagios XI server

    object_query: str
        The query to perform on the objects api of Nagios XI.
        Some examples include:
            hostgroupmembers?hostgroup_name=apolloserver\n
            host?host_name=apollo-1
        For full list of available queries see the Nagios XI help menu

    api_key: str
        The api_key to be used to access the nagios API. Can be found in a
        Nagios User's profile

    Returns
    -------
    Response: The http GET response resulting from the query

    Raises
    ------
    HTTPError: If the GET request fails in any way
    '''
    query = (f"{nagios_ip}/nagiosxi/api/v1/objects/{object_query}" +
             f"&apikey={api_key}&pretty=1")
    query_response = requests.get(query)
    query_response.raise_for_status()

    return query_response


def fetch_hostgroup_members(
    hostgroup_name: str,
    nagios_ip: str,
    api_key: str
) -> List:
    '''
    Get information about all hosts that are members of a specific hostgroup

    Parameters
    ----------
    hostgroup_name: str
        The hostgroup to get the numbers of

    nagios: str
        The IP address or hostname of the Nagios XI server

    api_key: str
        The api_key to be used to access the nagios API. Can be found in a
        Nagios User's profile

    Returns
    -------
    List: List of Dictionary objects containing host names and IDs

    Raises
    ------
    HTTPError: If the GET request fails for any reason

    ValueError: If the response from the get request isn't a valid json format

    IndexError: If the json returned from Nagios doesn't contain the expected
    keys
    '''
    try:
        query_response = get_object_query(
            nagios_ip=nagios_ip,
            api_key=api_key,
            object_query=f"hostgroupmembers?hostgroup_name={hostgroup_name}")
    except HTTPError as e:
        raise e

    try:
        response_json = query_response.json()
    except ValueError as e:
        raise e

    try:
        host_json = response_json['hostgroup'][0]['members']['host']
    except KeyError as e:
        raise e

    return host_json


def fetch_host_ip(
    host_name: str,
    nagios_ip: str,
    api_key: str
) -> str:
    '''
    Get the IP address associated with a host from Nagios XI

    Parameters
    ----------
    host_name: str
        The name associated with the host in Nagios

    nagios_ip: str
        The IP address or hostname of the Nagios XI server

    api_key: str
        The api_key to be used to access the nagios API. Can be found in a
        Nagios User's profile

    Returns
    -------
    str: The IP address associated with the specified host name

    Raises
    ------
    HTTPError: If the GET request fails for any reason

    ValueError: If the response from the get request isn't a valid json format

    IndexError: If the json returned from Nagios doesn't contain the expected
    keys
    '''
    try:
        query_response = get_object_query(
            nagios_ip=nagios_ip,
            api_key=api_key,
            object_query=f"host?host_name={host_name}")
    except HTTPError as e:
        raise e

    try:
        response_json = query_response.json()
    except ValueError as e:
        raise e

    try:
        host_ip = response_json['host'][0]['address']
    except IndexError as e:
        raise e

    return host_ip
