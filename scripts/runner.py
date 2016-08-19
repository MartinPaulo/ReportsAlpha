import argparse
import logging
from datetime import date, timedelta

from scripts.cloud.build_active import build_active
from scripts.cloud.build_allocated import build_allocated
from scripts.cloud.build_project_faculty import build_project_faculty
from scripts.cloud.build_top_twenty import build_top_twenty
from scripts.cloud.build_used import build_used
from scripts.config import Configuration
from scripts.db import local_db
from scripts.db import production_db
from scripts.db import reporting_db


def parse_args():
    parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS)
    parser.add_argument('-c', '--config-file', action='store',
                        required=False, help='Specify the config file')
    return parser.parse_args()


def main():
    args = parse_args()
    log_config = {
        'format': "%(asctime)s %(levelname)s: %(message)s",
        'datefmt': '%Y-%m-%d %X',
        'level': logging.DEBUG,
    }
    logging.basicConfig(**log_config)

    if 'config_file' in args:
        Configuration.load_from(args.config_file)

    start_day = date.today() - timedelta(days=480)
    load_db = local_db.DB()
    # extract_db = production_db.DB()
    extract_db = reporting_db.DB()
    # build_project_faculty(extract_db, load_db, start_day)
    # build_active(extract_db, load_db, start_day)
    # -> build_allocated(extract_db, load_db, start_day)
    # build_top_twenty(extract_db, load_db, start_day)
    # -> build_used(extract_db, load_db, start_day)


if __name__ == '__main__':
    main()
