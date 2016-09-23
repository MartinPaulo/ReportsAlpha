import codecs
import logging
import sqlite3
from datetime import datetime, date, timedelta
from decimal import Decimal

from scripts.config import Configuration


def decimal2float(val):
    return float(str(val))


sqlite3.register_adapter(Decimal, decimal2float)


def float2decimal(val):
    return Decimal(str(val))


sqlite3.register_converter("decimal", float2decimal)


class DB(object):
    _db_connection = None
    _db_cur = None

    # see http://stackoverflow.com/questions/6514274/
    # how-do-you-escape-strings-for-sqlite-table-column-names-in-python
    @staticmethod
    def quote_identifier(s, errors="strict"):
        encodable = s.encode("utf-8", errors).decode("utf-8")
        nul_index = encodable.find("\x00")
        if nul_index >= 0:
            error = UnicodeEncodeError("NUL-terminated utf-8", encodable,
                                       nul_index, nul_index + 1,
                                       "NUL not allowed")
            error_handler = codecs.lookup_error(errors)
            replacement, _ = error_handler(error)
            encodable = encodable.replace("\x00", replacement)
        return "\"" + encodable.replace("\"", "\"\"") + "\""

    def __init__(self):
        self._db_connection = sqlite3.connect(
            Configuration.get_uom_db(),
            detect_types=sqlite3.PARSE_DECLTYPES)
        self._db_cur = self._db_connection.cursor()

    def __del__(self):
        self._db_connection.close()

    def query(self, query, params):
        return self._db_cur.execute(query, params)

    def get_max_date(self, table_name):
        # default is a year ago...
        last_date = date.today() - timedelta(days=365)
        query = "SELECT MAX(date) AS max_date FROM %s;" % \
                self.quote_identifier(table_name)
        self._db_cur.execute(query)
        row = self._db_cur.fetchone()
        if row is None or row[0] is None:
            logging.warning("No last date found for table %s", table_name)
        else:
            last_date = datetime.strptime(row[0], "%Y-%m-%d").date()
        return last_date

    def get_active_last_run_date(self):
        return self.get_max_date('cloud_active_users')

    def save_active(self, user_counts):
        columns = ', '.join(user_counts.keys())
        value_placeholder = ', '.join(
            [':%s' % k for k in user_counts.keys()])
        # TODO: escape
        update = "INSERT OR REPLACE INTO cloud_active_users (%s) " \
                 "VALUES (%s);" % (columns, value_placeholder)
        self._db_cur.execute(update, user_counts)
        self._db_connection.commit()

    def get_faculty_allocated_last_run_date(self):
        return self.get_max_date('cloud_allocated')

    def save_faculty_allocated(self, day_date, faculty_totals):
        faculty_totals['date'] = day_date.strftime("%Y-%m-%d")
        columns = ', '.join(faculty_totals.keys())
        value_placeholder = ', '.join(
            [':%s' % k for k in faculty_totals.keys()])
        # TODO: escape
        update = "INSERT OR REPLACE INTO cloud_allocated (%s) " \
                 "VALUES (%s);" % \
                 (columns, value_placeholder)
        self._db_cur.execute(update, faculty_totals)
        self._db_connection.commit()

    def get_top_twenty_last_run_date(self):
        return self.get_max_date('cloud_top_twenty')

    def save_top_twenty_data(self, user_counts):
        columns = ', '.join(user_counts.keys())
        value_placeholder = ', '.join(
            [':%s' % k for k in user_counts.keys()])
        # TODO: escape
        update = "INSERT OR REPLACE INTO cloud_top_twenty (%s) " \
                 "VALUES (%s);" % (
                     columns, value_placeholder)
        self._db_cur.execute(update, user_counts)
        self._db_connection.commit()

    def get_used_last_run_date(self):
        return self.get_max_date('cloud_used')

    def save_used_data(self, faculty_totals):
        columns = ', '.join(faculty_totals.keys())
        value_placeholder = ', '.join(
            [':%s' % k for k in faculty_totals.keys()])
        # TODO: escape
        update = "INSERT OR REPLACE INTO cloud_used (%s) " \
                 "VALUES (%s);" % (columns, value_placeholder)
        self._db_cur.execute(update, faculty_totals)
        self._db_connection.commit()

    def save_faculty_data(self, faculties, contact_email,
                          project_id, project_name):
        for faculty in faculties:
            # This should not overwrite existing assigned projects
            query = "SELECT faculty_abbreviation FROM cloud_project_faculty " \
                    "WHERE project_id=:project_id;"
            self._db_cur.execute(query, {'project_id': project_id})
            row = self._db_cur.fetchone()
            if row is not None:
                if row[0] != 'Unknown':
                    logging.info("Found faculty %s for project %s", row[0],
                                 project_id)
                    continue
            # TODO: This does not support multiple faculties for a project
            # It will just overwrite the last entry :(
            update = "INSERT OR REPLACE INTO cloud_project_faculty " \
                     "       (project_id, contact_email, " \
                     "        name, faculty_abbreviation) " \
                     "VALUES (:project_id, :contact_email, " \
                     "        :project_name, :faculty);"
            self._db_cur.execute(update, {'project_id': project_id,
                                          'contact_email': contact_email,
                                          'project_name': project_name,
                                          'faculty': faculty})
        self._db_connection.commit()

    def get_faculty_abbreviations(self, project_id):
        sqlite3_query = "SELECT faculty_abbreviation " \
                        "FROM cloud_project_faculty " \
                        "WHERE project_id = ?"
        self._db_cur.execute(sqlite3_query, (project_id,))
        # unpack the tuples into a list
        faculties = [item[0] for item in self._db_cur.fetchall()]
        if not faculties:
            faculties = ['Unknown']
        return faculties

    def _save_storage(self, day_date, totals,
                      query):
        totals['date'] = day_date.strftime("%Y-%m-%d")
        columns = ', '.join(totals.keys())
        value_placeholder = ', '.join([':%s' % k for k in totals.keys()])
        # TODO: escape columns?
        update = query % (columns, value_placeholder)
        self._db_cur.execute(update, totals)
        self._db_connection.commit()

    def get_storage_allocated_last_run_date(self):
        return self.get_max_date('storage_allocated')

    def save_storage_allocated(self, day_date, totals):
        query = "INSERT OR REPLACE INTO storage_allocated (%s) " \
                "VALUES (%s);"
        self._save_storage(day_date, totals, query)

    def get_storage_used_last_run_date(self):
        return self.get_max_date('storage_used')

    def save_storage_used(self, day_date, totals):
        query = "INSERT OR REPLACE INTO storage_used (%s) " \
                "VALUES (%s);"
        self._save_storage(day_date, totals, query)

    def get_storage_allocated_by_faculty_last_run_date(self):
        return self.get_max_date('storage_allocated_by_faculty')

    def save_storage_allocated_by_faculty(self, day_date, faculty_totals):
        query = "INSERT OR REPLACE INTO storage_allocated_by_faculty (%s) " \
                "VALUES (%s);"
        self._save_storage(day_date, faculty_totals, query)

    def get_storage_allocated_by_faculty_compute_last_run_date(self):
        return self.get_max_date('storage_allocated_by_faculty_compute')

    def save_storage_allocated_by_faculty_compute(self, day_date,
                                                  faculty_totals):
        query = "INSERT OR REPLACE INTO " \
                "storage_allocated_by_faculty_compute (%s) " \
                "VALUES (%s);"
        self._save_storage(day_date, faculty_totals, query)

    def get_storage_allocated_by_faculty_market_last_run_date(self):
        return self.get_max_date('storage_allocated_by_faculty_market')

    def save_storage_allocated_by_faculty_market(self, day_date,
                                                 faculty_totals):
        query = "INSERT OR REPLACE INTO " \
                "storage_allocated_by_faculty_market (%s) " \
                "VALUES (%s);"
        self._save_storage(day_date, faculty_totals, query)

    def get_storage_allocated_by_faculty_vault_last_run_date(self):
        return self.get_max_date('storage_allocated_by_faculty_vault')

    def save_storage_allocated_by_faculty_vault(self, day_date,
                                                faculty_totals):
        query = "INSERT OR REPLACE INTO " \
                "storage_allocated_by_faculty_vault (%s) " \
                "VALUES (%s);"
        self._save_storage(day_date, faculty_totals, query)

    def get_storage_used_by_faculty_last_run_date(self):
        return self.get_max_date('storage_used_by_faculty')

    def save_storage_used_by_faculty(self, day_date, faculty_totals):
        query = "INSERT OR REPLACE INTO storage_used_by_faculty (%s) " \
                "VALUES (%s);"
        self._save_storage(day_date, faculty_totals, query)

    def get_storage_used_by_faculty_compute_last_run_date(self):
        return self.get_max_date('storage_used_by_faculty_compute')

    def save_storage_used_by_faculty_compute(self, day_date, faculty_totals):
        query = "INSERT OR REPLACE INTO " \
                "storage_used_by_faculty_compute (%s) " \
                "VALUES (%s);"
        self._save_storage(day_date, faculty_totals, query)

    def get_storage_used_by_faculty_market_last_run_date(self):
        return self.get_max_date('storage_used_by_faculty_market')

    def save_storage_used_by_faculty_market(self, day_date, faculty_totals):
        query = "INSERT OR REPLACE INTO storage_used_by_faculty_market (%s) " \
                "VALUES (%s);"
        self._save_storage(day_date, faculty_totals, query)

    def get_storage_used_by_faculty_vault_last_run_date(self):
        return self.get_max_date('storage_used_by_faculty_vault')

    def save_storage_used_by_faculty_vault(self, day_date, faculty_totals):
        query = "INSERT OR REPLACE INTO storage_used_by_faculty_vault (%s) " \
                "VALUES (%s);"
        self._save_storage(day_date, faculty_totals, query)

    def get_headroom_unused_last_run_date(self):
        return self.get_max_date('storage_headroom_unused')

    def save_headroom_unused(self, day_date, totals):
        query = "INSERT OR REPLACE INTO storage_headroom_unused (%s) " \
                "VALUES (%s);"
        self._save_storage(day_date, totals, query)

    def get_headroom_unused_by_faculty_last_run_date(self):
        return self.get_max_date('storage_headroom_unused_by_faculty')

    def save_storage_headroom_unused_by_faculty(self, day_date,
                                                faculty_totals):
        query = "INSERT OR REPLACE INTO " \
                "  storage_headroom_unused_by_faculty (%s) " \
                "VALUES (%s);"
        self._save_storage(day_date, faculty_totals, query)

    def get_headroom_unused_by_faculty_compute_last_run_date(self):
        return self.get_max_date('storage_headroom_unused_by_faculty_compute')

    def save_storage_headroom_unused_by_faculty_compute(self, day_date,
                                                        faculty_totals):
        query = "INSERT OR REPLACE INTO " \
                "  storage_headroom_unused_by_faculty_compute (%s) " \
                "VALUES (%s);"
        self._save_storage(day_date, faculty_totals, query)

    def get_headroom_unused_by_faculty_market_last_run_date(self):
        return self.get_max_date('storage_headroom_unused_by_faculty_market')

    def save_storage_headroom_unused_by_faculty_market(self, day_date,
                                                       faculty_totals):
        query = "INSERT OR REPLACE INTO " \
                "  storage_headroom_unused_by_faculty_market (%s) " \
                "VALUES (%s);"
        self._save_storage(day_date, faculty_totals, query)

    def get_headroom_unused_by_faculty_vault_last_run_date(self):
        return self.get_max_date('storage_headroom_unused_by_faculty_vault')

    def save_storage_headroom_unused_by_faculty_vault(self, day_date,
                                                      faculty_totals):
        query = "INSERT OR REPLACE INTO " \
                "  storage_headroom_unused_by_faculty_vault (%s) " \
                "VALUES (%s);"
        self._save_storage(day_date, faculty_totals, query)
