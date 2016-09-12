# This file shows the settings that can be placed in local_settings.py
# local_settings.py is a way for us to have machine specific information
# if (any)


# The reporting database against which the cloud reports are run.
reporting_db = {
    'user': 'root',
    'passwd': 'Password',
    'db': 'reporting',
    'host': '192.168.33.1',
    'port': 3306,
}

# The production databases, probably never going to be used in real life,
# but useful during development.
production_db = {
    'user': 'root',
    'passwd': 'Password',
    'db': 'dashboard',
    'host': '192.168.33.1',
    'port': 3306,
}

# the nagios server
nagios_auth = ("user", "password")
nagios_url = "http://mon.test.nectar.org.au/cgi-bin/nagios3/"


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'g8hkvxw54%k-$ymtp90ig*4ai8c%6ra4p@(&m##6b_#g=@0v)!'