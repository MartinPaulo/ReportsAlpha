import argparse
import logging
import sys

import MySQLdb
from datetime import date, timedelta

import sqlite3

from scripts.cloud.build_active import build_active
from scripts.cloud.build_allocated import build_allocated
from scripts.cloud.build_project_faculty import build_project_faculty
from scripts.cloud.build_top_twenty import build_top_twenty
from scripts.cloud.build_used import build_used
from scripts.config import Configuration


def parse_args():
    parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS)
    parser.add_argument('-c', '--config-file', action='store',
                        required=False, help='Specify the config file')
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    if 'config_file' in args:
        Configuration.load_from(args.config_file)
    mysql_connection = None
    connection_out = None
    try:
        start_day = date.today() - timedelta(days=380)
        mysql_connection = MySQLdb.connect(**Configuration.get_reporting_db())
        cursor_in = mysql_connection.cursor(MySQLdb.cursors.DictCursor)
        cursor_out = sqlite3.connect(Configuration.get_uom_db())
        with cursor_in, cursor_out:
            build_active(cursor_in, cursor_out, start_day)
            build_allocated(cursor_in, cursor_out, start_day)
            build_project_faculty(cursor_in, cursor_out, start_day)
            build_top_twenty(cursor_in, cursor_out, start_day)
            build_used(cursor_in, cursor_out, start_day)
    except MySQLdb.Error as e:
        logging.exception("MySql experienced a problem")
        sys.exit(1)
    finally:
        if mysql_connection:
            mysql_connection.close()
        if connection_out:
            connection_out.close()

if __name__ == '__main__':
    main()
