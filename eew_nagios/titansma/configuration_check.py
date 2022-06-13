from io import FileIO
from eew_nagios.nagios import nagios_api
from typing import List, Tuple, Union
from eew_nagios.titansma import digitizer_interface
# import pathlib


def get_titansma_list(
    nagios_ip: str,
    api_key: str
) -> List:
    titansma_list = nagios_api.fetch_hostgroup_members(
        hostgroup_name='titan-sma',
        nagios_ip=nagios_ip,
        api_key=api_key
    )
    return titansma_list


def get_running_config(
    host_name: str,
    nagios_ip: str,
    api_key: str
):
    titansma_ip = nagios_api.fetch_host_ip(
        host_name=host_name,
        nagios_ip=nagios_ip,
        api_key=api_key
    )

    username, password = fetch_credentials(host_name)

    cookieJar = digitizer_interface.GlobalCookieJar().addCookieToAllRequests()

    digitizerInterface = digitizer_interface.DigitizerInterface(
        address=titansma_ip,
        username=username,
        password=password)

    digitizerInterface.login(cookieJar)

    config = digitizerInterface.getConfiguration()

    # To be continued
    return config


def load_golden_image(
    goldenimg_dir: str,
    host_name: str
) -> Union[FileIO, None]:
    # network, station = host_name.split('-')[:2]

    # goldenimg_path = pathlib.Path(f"{goldenimg_dir}/{network}/{station}")

    return None


def fetch_credentials(
    host_name: str
) -> Tuple[str, str]:

    # What is the safest way to store these so they can be retrieved without
    # user intervention!?!?!?!?
    # TO BE CONTINUED
    return '', ''
