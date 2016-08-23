import logging
import os

import sys
from configparser import ConfigParser

# default for local development
reporting_db = {
    'user': 'root',
    'passwd': 'Password',
    'db': 'menagerie',
    'host': '192.168.33.1',
    'port': 3306,
}

# default for local development
production_db = {
    'user': 'root',
    'passwd': 'Password',
    'db': 'dashboard',
    'host': '192.168.33.1',
    'port': 3306,
}


class Configuration(object):
    reporting_db = None
    production_db = None

    @classmethod
    def load_from(cls, config_file):
        if not os.path.isfile(config_file):
            logging.critical("Configuration file %s not found", config_file)
            sys.exit(1)
        logging.info("Loading configuration from %s", config_file)
        parser = ConfigParser()
        parser.read(config_file)
        cls.read_db_section(parser, 'production_db', cls.production_db)
        cls.read_db_section(parser, 'reporting_db', cls.reporting_db)

    @classmethod
    def read_db_section(cls, parser, section_name, target):
        if parser.has_section(section_name):
            logging.info("Reading %s configuration", section_name)
            target = {}
            for (name, value) in parser.items(section_name):
                target[name] = value
            # we assume that bot the reporting and the production have the
            # same number of values
            if target.keys() != cls.reporting_db.keys():
                logging.critical("Database %s mapping doesn't match",
                                 section_name)
                sys.exit(1)

    @classmethod
    def get_production_db(cls):
        if not cls.production_db:
            cls.production_db = production_db
        return cls.production_db

    @classmethod
    def get_reporting_db(cls):
        if not cls.reporting_db:
            cls.reporting_db = reporting_db
        return cls.reporting_db

    @classmethod
    def get_uom_db(cls):
        return '/Users/mpaulo/PycharmProjects/ReportsBeta/db/db.sqlite3'
