"""
This file manages the loading of the data from the production databases
and into the reporting databases.
"""

import argparse
import logging
import random
import sys
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


def get_start_day(args):
    result = None
    days_past = int(args.days)
    if days_past:
        result = date.today() - timedelta(days=days_past)
    logging.info("Start date chosen is %s", result)
    return result


def configure_logging(args):
    log_config = {
        'format': "%(asctime)s %(levelname)s: %(message)s",
        'datefmt': '%Y-%m-%d %X',
        'level': (getattr(logging, args.loglevel.upper())),
    }
    logging.basicConfig(**log_config)
    logging.info("Python version: %s", sys.version)


def main():
    # TODO:
    # Offer up a menu of scripts to run?
    # Add support for an all flag that won't show the menu?
    args = parse_args()
    configure_logging(args)
    start_day = get_start_day(args)

    load_db = local_db.DB()
    # extract_db = reporting_db.DB()
    # A short hand that stops us from having to type out repeated arguments
    # Indicates a smell, methinks.
    _args = {'extract_db': reporting_db.DB(),
             'load_db': load_db, 'start_day': start_day}

    build_project_faculty(**_args)
    nectar.build_active(**_args)
    nectar.build_faculty_allocated(**_args)
    nectar.build_top_twenty(**_args)
    nectar.build_used(**_args)

    if False:
        read_national(load_db)

    unknown_source = FakeCloudCapacityData()
    nectar.build_capacity(unknown_source, load_db, start_day)

    vicnode_source_db = vicnode_db.DB()
    try:
        # _args = {'extract_db': vicnode_source_db,
        #                  'load_db': load_db, 'start_day': start_day}
        _args['extract_db'] = vicnode_source_db
        # # Following is one way to get/call all the methods in the module
        # # allows us to build a menu system?
        # all_functions = inspect.getmembers(vicnode, inspect.isfunction)
        # for name, function in all_functions:
        #     if name.startswith('build'):
        #         function(**args)
        vicnode.build_allocated(**_args)
        vicnode.build_allocated_by_faculty(**_args)
        vicnode.build_used(**_args)
        vicnode.build_used_by_faculty(**_args)
        vicnode.build_headroom_unused(**_args)
        vicnode.build_headroom_unused_by_faculty(**_args)
        vicnode.build_capacity(**_args)
        vicnode.build_headroom_unallocated(**_args)
        # unknown_source = FakeStorageCapacityData()
        # vicnode.build_capacity(unknown_source, load_db)
    finally:
        vicnode_source_db.close_connection()


if __name__ == '__main__':
    main()
