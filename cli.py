import argparse
import logging

import sys
import time

from services.data_services import DataServices

logger = logging.getLogger('cli')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('cli.log')
fh.setLevel(logging.DEBUG)
sh = logging.StreamHandler(sys.stdout)
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '[%(asctime)s] [%(threadName)s] %(levelname)s [%(filename)s.%(funcName)s:%(lineno)d] %(message)s',
    datefmt='%a, %d %b %Y %H:%M:%S')
fh.setFormatter(formatter)
sh.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(sh)


def get_arg_parser():
    parser = argparse.ArgumentParser(prog="n38701-cli", description="Utils for N38701 data analysis",
                                     epilog="Created by James P. Sefton (james.sefton@9bit-tech.com)")

    general = parser.add_argument_group("General Options", "Arguments used in general across several features")
    # GENERAL
    general.add_argument("--load-directory", help="Load using csv format")
    general.add_argument("--load-file", help="Load using csv format")

    return parser


def run():
    parser = get_arg_parser()
    args = parser.parse_args()
    data = DataServices()

    if args.load_directory:
        data.load_csvs(path=args.load_directory)
        return

    if args.load_file:
        data.load_csv(path=args.load_file)
        return


def execute():
    try:
        start_time = time.perf_counter()
        run()
        elapsed_time = time.perf_counter() - start_time

        logger.info(f'Finished. Execution time: {time.strftime("%H:%M:%S", time.gmtime(elapsed_time))}')
    except RuntimeError as e:
        logger.error(e, stack_info=False, exc_info=True)


execute()
