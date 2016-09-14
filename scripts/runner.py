import argparse
import logging
from datetime import date, timedelta

from scripts.cloud.build_active import build_active
from scripts.cloud.build_allocated import build_faculty_allocated
from scripts.cloud.build_project_faculty import build_project_faculty
from scripts.cloud.build_top_twenty import build_top_twenty
from scripts.cloud.build_used import build_used
# from scripts.cloud.uptime import read_national
from scripts.db import local_db
from scripts.db import reporting_db


def parse_args():
    parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS)
    parser.add_argument('--loglevel', action='store', required=False,
                        choices=['critical', 'error', 'debug',
                                 'info', 'warning'], default='debug',
                        help='Specify the log level')
    parser.add_argument('-d', '--days', action='store',
                        required=False, default=0,
                        help='Rebuild the last n days of data')
    return parser.parse_args()


def main():
    args = parse_args()
    log_config = {
        'format': "%(asctime)s %(levelname)s: %(message)s",
        'datefmt': '%Y-%m-%d %X',
        'level': (getattr(logging, args.loglevel.upper())),
    }
    logging.basicConfig(**log_config)

    start_day = None
    days_past = int(args.days)
    if days_past:
        start_day = date.today() - timedelta(days=days_past)
    logging.info("Start date chosen is %s", start_day)

    load_db = local_db.DB()
    extract_db = reporting_db.DB()
    build_project_faculty(extract_db, load_db)
    build_active(extract_db, load_db, start_day)
    build_faculty_allocated(extract_db, load_db, start_day)
    build_top_twenty(extract_db, load_db, start_day)
    build_used(extract_db, load_db, start_day)
    # read_national(load_db)


if __name__ == '__main__':
    main()
