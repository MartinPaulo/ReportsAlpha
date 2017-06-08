#!/usr/bin/env python

"""
This application manages the loading of the data from the production databases
into the reporting database.

Usage:
    ./runner.py [options] (cloud | storage | all)

Commands:
    cloud       Load the data from the cloud database
    storage     Load the data from the storage database
    all         Load the data from all the production databases

Options:
    -h, --help          Show this screen
    -v, --version       Show the version
    -d <n>, --days=<n>  Rebuild the last n days of data. If no value is
                        specified, the runner will start at the highest day
                        loaded so far for each table [default: None]

"""
import logging
import os
import random
import sys
from datetime import date, timedelta
from operator import add, sub

import django
from docopt import docopt

from scripts import __version__ as VERSION
from scripts.cloud.uptime import read_national
from scripts.db import local_db
from scripts.db import reporting_db
from scripts.db import vicnode_db
from scripts.vicnode import builder as vicnode


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


def get_start_day(days):
    result = None
    if days != 'None':
        result = date.today() - timedelta(days=int(days))
    logging.info("Start date chosen is %s", result)
    return result


def main():
    # see:
    # http://stackoverflow.com/questions/15048963/alternative-to-the-deprecated-setup-environ-for-one-off-django-scripts
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reports_beta.settings")
    django.setup()

    logging.info("Python version: %s", sys.version)

    options = docopt(__doc__, version=VERSION)
    start_day = get_start_day(options['--days'])

    load_db = local_db.DB()
    # A short hand that stops us from having to type out repeated arguments
    # Indicates a smell, methinks.
    _args = {'load_db': load_db, 'start_day': start_day}
    if options['all'] or options['cloud']:
        _args['extract_db'] = reporting_db.DB()
        # these imports are done here as the django setup has to be performed
        # first as the builders reference django based models
        from scripts.cloud import builder as nectar
        from scripts.cloud.build_project_faculty import build_project_faculty
        nectar.test_db(**_args)
        build_project_faculty(**_args)
        nectar.build_active(**_args)
        nectar.build_top_twenty(**_args)
        nectar.build_faculty_allocated(**_args)
        nectar.build_used(**_args)
        nectar.build_private_cell_data(**_args)
        nectar.build_buyers_committee(**_args)
        nectar.build_quarterly_usage(**_args)
        if False:
            read_national(load_db)

        unknown_source = FakeCloudCapacityData()
        nectar.build_capacity(unknown_source, load_db, start_day)

    if options['all'] or options['storage']:
        vicnode_source_db = vicnode_db.DB()
        # replace the extract database with vicnodes, but otherwise keep the
        # arguments the same.
        _args['extract_db'] = vicnode_source_db
        try:
            vicnode.test_db(**_args)
            vicnode.build_allocated(**_args)
            vicnode.build_allocated_by_faculty(**_args)
            vicnode.build_used(**_args)
            vicnode.build_used_by_faculty(**_args)
            vicnode.build_headroom_unused(**_args)
            vicnode.build_headroom_unused_by_faculty(**_args)
            vicnode.build_capacity(**_args)
            vicnode.build_headroom_unallocated(**_args)
        finally:
            vicnode_source_db.close_connection()

    logging.warning("Completed ETL run, arguments %s ", options)


if __name__ == '__main__':
    main()
