import argparse
import logging
from datetime import date, timedelta

from scripts.cloud import builder as nectar
from scripts.cloud.build_project_faculty import build_project_faculty
from scripts.cloud.uptime import read_national
from scripts.db import local_db
from scripts.db import reporting_db
from scripts.db import vicnode_db
from scripts.vicnode import builder as vicnode


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
    # start_day = date.today() - timedelta(days=360)
    logging.info("Start date chosen is %s", start_day)

    load_db = local_db.DB()
    extract_db = reporting_db.DB()

    # This builds fake data...
    nectar.build_capacity(load_db, start_day)

    build_project_faculty(extract_db, load_db)

    nectar.build_active(extract_db, load_db, start_day)
    nectar.build_faculty_allocated(extract_db, load_db, start_day)
    nectar.build_top_twenty(extract_db, load_db, start_day)
    nectar.build_used(extract_db, load_db, start_day)

    if False:
        read_national(load_db)

    vicnode_source_db = vicnode_db.DB()
    vicnode.build_allocated(vicnode_source_db, load_db, start_day)
    vicnode.build_allocated_by_faculty(vicnode_source_db, load_db,
                                       start_day)
    vicnode.build_allocated_by_faculty_compute(vicnode_source_db, load_db,
                                               start_day)
    vicnode.build_allocated_by_faculty_market(vicnode_source_db, load_db,
                                              start_day)
    vicnode.build_allocated_by_faculty_vault(vicnode_source_db, load_db,
                                             start_day)
    vicnode.build_used(vicnode_source_db, load_db, start_day)
    vicnode.build_used_by_faculty(vicnode_source_db, load_db, start_day)
    vicnode.build_used_by_faculty_compute(vicnode_source_db, load_db,
                                          start_day)
    vicnode.build_used_by_faculty_market(vicnode_source_db, load_db,
                                         start_day)
    vicnode.build_used_by_faculty_vault(vicnode_source_db, load_db,
                                        start_day)
    vicnode.build_headroom_unused(vicnode_source_db, load_db, start_day)
    vicnode.build_headroom_unused_by_faculty(vicnode_source_db, load_db,
                                             start_day)
    vicnode.build_headroom_unused_by_faculty_compute(vicnode_source_db,
                                                     load_db,
                                                     start_day)
    vicnode.build_headroom_unused_by_faculty_market(vicnode_source_db,
                                                    load_db,
                                                    start_day)
    vicnode.build_headroom_unused_by_faculty_vault(vicnode_source_db,
                                                   load_db,
                                                   start_day)


if __name__ == '__main__':
    main()
