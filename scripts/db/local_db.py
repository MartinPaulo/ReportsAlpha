import logging
import sqlite3

from scripts.config import Configuration


class DB(object):
    _db_connection = None
    _db_cur = None

    def __init__(self):
        self._db_connection = sqlite3.connect(Configuration.get_uom_db())
        self._db_cur = self._db_connection.cursor()

    def query(self, query, params):
        return self._db_cur.execute(query, params)

    def __del__(self):
        self._db_connection.close()

    def save_active(self, user_counts):
        columns = ', '.join(user_counts.keys())
        value_placeholder = ', '.join(
            [':%s' % k for k in user_counts.keys()])
        update = "INSERT OR REPLACE INTO cloud_active_users (%s) " \
                 "VALUES (%s);" % (columns, value_placeholder)
        self._db_cur.execute(update, user_counts)
        self._db_connection.commit()

    def save_faculty_allocated(self, day_date, faculty_totals):
        faculty_totals['date'] = day_date.strftime("%Y-%m-%d")
        columns = ', '.join(faculty_totals.keys())
        value_placeholder = ', '.join(
            [':%s' % k for k in faculty_totals.keys()])
        update = "INSERT OR REPLACE INTO cloud_allocated (%s) VALUES (%s);" % (
            columns, value_placeholder)
        self._db_cur.execute(update, faculty_totals)
        self._db_connection.commit()

    def save_top_twenty_data(self, user_counts):
        columns = ', '.join(user_counts.keys())
        value_placeholder = ', '.join(
            [':%s' % k for k in user_counts.keys()])
        update = "INSERT OR REPLACE INTO cloud_top_twenty (%s) " \
                 "VALUES (%s);" % (
                     columns, value_placeholder)
        self._db_cur.execute(update, user_counts)
        self._db_connection.commit()

    def save_used_data(self, faculty_totals):
        columns = ', '.join(faculty_totals.keys())
        value_placeholder = ', '.join(
            [':%s' % k for k in faculty_totals.keys()])
        update = "INSERT OR REPLACE INTO cloud_used (%s) VALUES (%s);" % (
            columns, value_placeholder)
        self._db_cur.execute(update, faculty_totals)
        self._db_connection.commit()

    def save_faculty_data(self, faculties, contact_email,
                          project_id, project_name):
        for faculty in faculties:
            # TODO: This does not support multiple faculties for a project
            # It will just overwrite the last entry :(
            update = "INSERT OR REPLACE INTO cloud_project_faculty " \
                     "       (project_id, contact_email, " \
                     "        name, faculty_abbreviation) " \
                     "VALUES (:project_id, :contact_email, " \
                     "        :project_name, :faculty);"
            self._db_cur.execute(update, {'project_id':project_id,
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
