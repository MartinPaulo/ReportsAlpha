import logging
import os

import sys
from configparser import ConfigParser

reporting_db = {
    'user': 'root',
    'password': 'Testing out the system',
    'database': 'reporting',
    'host': '192.168.33.1',
    'port': 3306,
}


class Configuration(object):

    reporting_db = None

    @classmethod
    def load_from(cls, config_file):
        if not os.path.isfile(config_file):
            logging.critical("Configuration file %s not found", config_file)
            sys.exit(1)
        logging.info("Loading configuration from %s", config_file)
        parser = ConfigParser()
        parser.read(config_file)
        if not parser.has_section('reporting_db'):
            logging.critical("No reporting database configuration in config")
            sys.exit(1)
        cls.reporting_db = {}
        for (name, value) in parser.items('reporting_db'):
            cls.reporting_db[name] = value
        if reporting_db.keys() != cls.reporting_db.keys():
            logging.critical("Reporting database mapping doesn't match")
            sys.exit(1)

    @classmethod
    def get_reporting_db(cls):
        if not cls.reporting_db:
            cls.reporting_db = reporting_db
        return cls.reporting_db

    @classmethod
    def get_uom_db(cls):
        return '/Users/mpaulo/PycharmProjects/ReportsBeta/db/db.sqlite3'
