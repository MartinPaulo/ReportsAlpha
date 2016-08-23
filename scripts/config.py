import logging

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
    def load(cls):
        try:
            from reports_beta.local_settings import reporting_db as ls_rep
            cls.reporting_db = ls_rep
            from reports_beta.local_settings import reporting_db as ls_prod
            cls.reporting_db = ls_prod
            logging.info('Settings loaded from local_settings.py')
        except ImportError as e:
            logging.warning('Local settings not found, using defaults...')
            cls.reporting_db = reporting_db
            cls.production_db = production_db

    @classmethod
    def get_production_db(cls):
        if not cls.production_db:
            cls.load()
        return cls.production_db

    @classmethod
    def get_reporting_db(cls):
        if not cls.reporting_db:
            cls.load()
        return cls.reporting_db

    @classmethod
    def get_uom_db(cls):
        return '/Users/mpaulo/PycharmProjects/ReportsBeta/db/db.sqlite3'
