import logging
import argparse
# from eew_nagios.data import NRDP_CONFIG
from eew_nagios.guralpdatacenter import guralp_availability  # type: ignore
from eew_nagios.nagios import aquision_availability
# from eew_nagios.nagios import nrdp
# import configparser
from datetime import datetime


def main():
    argsparser = argparse.ArgumentParser()
    argsparser.add_argument(
        '-v',
        '--verbose',
        action='count',
        default=0,
        help="Log more information about the program's execution"
    )
    argsparser.add_argument(
        '-L',
        '--logfile',
        default=None,
        help='To log to a file instead of stdout, specify the filename.',
        type=str
    )
    # argsparser.add_argument(
    #     '-c',
    #     '--config',
    #     default=NRDP_CONFIG,
    #     help="Config file"
    # )
    argsparser.add_argument(
        '-k',
        '--cachefolder',
        help=('The folder where the Guralp Datacenter stores cached data. ' +
              'Default: /var/cache/guralp'),
        default='/var/cache/guralp/'
    )
    argsparser.add_argument(
        '-n',
        '--hostname',
        help='The hostname of the guralp datacenter as it appears in Nagios',
        required=True
    )
    argsparser.add_argument(
        '-e',
        '--expectedchannels',
        required=True,
        help='The expected number of channels.',
        type=int
    )
    argsparser.add_argument(
        '-w',
        '--warning',
        help='The warning range for the check. See Nagios documentation',
        required=True
    )
    argsparser.add_argument(
        '-c',
        '--critical',
        help='The critical range for the check. See Nagios documentation',
        required=True
    )

    args = argsparser.parse_args()

    if args.verbose >= 3:
        logging_level = logging.DEBUG
    elif args.verbose == 2:
        logging_level = logging.INFO
    elif args.verbose == 1:
        logging_level = logging.WARNING
    else:
        logging_level = logging.ERROR

    if args.logfile is not None:
        logging.basicConfig(
            format='%(asctime)s:%(levelname)s:%(message)s',
            datefmt="%Y-%m-%d %H:%M:%S",
            level=logging_level,
            filename=args.logfile, filemode='W')
    else:
        logging.basicConfig(
            format='%(asctime)s:%(levelname)s:%(message)s',
            datefmt="%Y-%m-%d %H:%M:%S",
            level=logging_level)

    cache_folder = args.cachefolder

    id = args.hostname

    # configfile = args.config

    # config = configparser.ConfigParser()
    # config.read(configfile)

    # logging.debug(config.sections())
    # logging.debug(config['nagios'])

    # nagios_ip = config['nagios']['nagios']

    # api_key = config['nagios']['api_key']

    # token = config['nagios']['token']

    # fortimus_list = guralp_availability.get_fortimus(
    #     nagios_ip=nagios_ip,
    #     api_key=api_key
    # )

    expectedchannels = args.expectedchannels

    percent_available = guralp_availability.check_availability(
        expected_channels=expectedchannels,
        cache_folder=cache_folder,
        time=datetime.now()
    )

    state, statetxt = aquision_availability.get_state(
        percentage=percent_available,
        warn_threshold=args.warning,
        crit_threshold=args.critical)

    message = aquision_availability.assemble_message(
        statetxt=statetxt,
        id=id,
        percentage=percent_available
    )

    print(message)

    # check_results = nrdp.NagiosCheckResults()

    # check_results.append(aquision_availability.prepare_check_results(
    #     host_name=id,
    #     state=state,
    #     output=message
    # ))

    # nrdp.submit(
    #         check_results,
    #         nagios_ip,
    #         token=token
    #     )

    return state


if __name__ == '__main__':
    main()
