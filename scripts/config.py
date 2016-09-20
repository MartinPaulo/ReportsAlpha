import logging

import sys


class Configuration(object):
    reporting_db = None
    production_db = None
    vicnode_db = None
    nagios_auth = None
    nagios_url = None
    sqlite3_location = None
    ssh_tunnel = None

    # noinspection PyBroadException
    @classmethod
    def load(cls):
        try:
            import reports_beta.settings as settings
            cls.reporting_db = settings.reporting_db
            cls.vicnode_db = settings.vicnode_db
            cls.nagios_auth = settings.nagios_auth
            cls.nagios_url = settings.NECTAR_NAGIOS_URL
            cls.sqlite3_location = settings.DATABASES['default']['NAME']
            cls.ssh_tunnel = settings.ssh_tunnel
            logging.info('Settings loaded from settings.py')
        except ImportError as e:
            logging.error('Settings not found, exiting...')
            sys.exit(1)
        except:
            logging.error("Unexpected error, exiting...", sys.exc_info()[0])
            sys.exit(2)

    @classmethod
    def get_attribute_value(cls, attribute_name):
        """
        :param attribute_name: String giving name of attribute value to return
        :return: The value of the named attribute. If the initial value is None
        loads the configuration from settings.py first.
        """
        if not getattr(cls, attribute_name):
            cls.load()
        return getattr(cls, attribute_name)

    @classmethod
    def get_production_db(cls):
        return cls.get_attribute_value('production_db')

    @classmethod
    def get_vicnode_db(cls):
        return cls.get_attribute_value('vicnode_db')

    @classmethod
    def get_reporting_db(cls):
        return cls.get_attribute_value('reporting_db')

    @classmethod
    def get_nagios_auth(cls):
        return cls.get_attribute_value('nagios_auth')

    @classmethod
    def get_nagios_url(cls):
        return cls.get_attribute_value('nagios_url').strip("/")

    @classmethod
    def get_uom_db(cls):
        return cls.get_attribute_value('sqlite3_location')

    @classmethod
    def get_ssh_tunnel_info(cls):
        return cls.get_attribute_value('ssh_tunnel')
