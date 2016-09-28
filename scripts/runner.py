import argparse
import logging
import random
from datetime import date, timedelta
from operator import add, sub

from scripts.cloud import builder as nectar
from scripts.cloud.build_project_faculty import build_project_faculty
from scripts.cloud.uptime import read_national
from scripts.db import local_db
from scripts.db import reporting_db
from scripts.db import vicnode_db
from scripts.vicnode import builder as vicnode


class FakeStorageCapacityData:
    """Fake data provider for storage capacity"""

    def get_storage_capacity(self):
        return [{
            'product': 'computational',
            'capacity': 288000.00,
        }, {
            'product': 'market',
            'capacity': 1482000.00,
        }, {
            'product': 'vault',
            'capacity': 1263150.00
        }]


class FakeCloudCapacityData:
    """Fake data provider for cloud capacity"""
    _ops = (add, sub)

    def get_cloud_capacity(self, day_date):
        nectar_contribution = random.randrange(100)
        uom_contribution = random.randrange(100)
        co_contribution = random.randrange(100)
        op = random.choice(self._ops)
        nectar_contribution = op(nectar_contribution, random.randrange(10))
        op = random.choice(self._ops)
        uom_contribution = op(uom_contribution, random.randrange(10))
        op = random.choice(self._ops)
        co_contribution = op(co_contribution, random.randrange(10))
        return {
            'date': day_date,
            'nectar_contribution': nectar_contribution,
            'uom_contribution': uom_contribution,
            'co_contribution': co_contribution
        }


def parse_args():
    parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS)
    parser.add_argument('--loglevel', action='store', required=False,
                        choices=['critical', 'error', 'debug',
                                 'info', 'warning'], default='debug',
                        help='Specify the log level')
    parser.add_argument('-d', '--days', action='store',
                        required=False, default=0,
                        help='Rebuild the last n days of data for all reports')
    return parser.parse_args()


def main():
    # TODO:
    # Offer up a menu of reports to run?
    # Add support for an all flag that won't show the menu
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

    unknown_source = FakeCloudCapacityData()
    nectar.build_capacity(unknown_source, load_db, start_day)

    build_project_faculty(extract_db, load_db)

    nectar.build_active(extract_db, load_db, start_day)
    nectar.build_faculty_allocated(extract_db, load_db, start_day)
    nectar.build_top_twenty(extract_db, load_db, start_day)
    nectar.build_used(extract_db, load_db, start_day)

    if False:
        read_national(load_db)

    vicnode_source_db = vicnode_db.DB()
    try:
        args = {'extract_db': vicnode_source_db,
                'load_db': load_db, 'start_day': start_day}
        vicnode.build_allocated(**args)
        vicnode.build_allocated_by_faculty(**args)
        vicnode.build_allocated_by_faculty_compute(**args)
        vicnode.build_allocated_by_faculty_market(**args)
        vicnode.build_allocated_by_faculty_vault(**args)
        vicnode.build_used(**args)
        vicnode.build_used_by_faculty(**args)
        vicnode.build_used_by_faculty_compute(**args)
        vicnode.build_used_by_faculty_market(**args)
        vicnode.build_used_by_faculty_vault(**args)
        vicnode.build_headroom_unused(**args)
        vicnode.build_headroom_unused_by_faculty(**args)
        vicnode.build_headroom_unused_by_faculty_compute(**args)
        vicnode.build_headroom_unused_by_faculty_market(**args)
        vicnode.build_headroom_unused_by_faculty_vault(**args)
        unknown_source = FakeStorageCapacityData()
        # vicnode.build_capacity(unknown_source, load_db)
        vicnode.build_capacity(**args)
        vicnode.build_headroom_unallocated(**args)
    finally:
        vicnode_source_db.close_connection()

if __name__ == '__main__':
    main()
