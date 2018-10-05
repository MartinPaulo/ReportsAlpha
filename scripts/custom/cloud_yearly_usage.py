#!/usr/bin/env python
from datetime import date

import MySQLdb

from scripts.cloud.utility import LDAP
from scripts.custom.credentials import Credentials


class ReportingDB:
    _db_connection = None
    _db_cur = None

    def __init__(self):
        self._db_connection = MySQLdb.connect(**Credentials.reporting_db)
        self._db_cur = self._db_connection.cursor(MySQLdb.cursors.DictCursor)

    def query(self, query, params):
        return self._db_cur.execute(query, params)

    def __del__(self):
        if self._db_connection is not None:
            self._db_connection.close()

    # https://www.periscopedata.com/blog/rolling-average.html ?
    def get_year_totals(self, year):
        day_date = date(year, 1, 1)
        query = """
        SELECT
          project_name           AS project,
          chief_investigator     AS ci,
          contact_email          AS owner,
          IFNULL(i.vcpucount, 0) AS vcpucount
        FROM allocation
          LEFT JOIN project ON allocation.project_id = project.id
          LEFT JOIN (
                      SELECT
                        project_id,
                        SUM(vcpus) AS vcpucount
                      FROM instance
                      WHERE
                        # deleted during the year
                        ((%(day_date)s <= deleted AND
                          deleted < %(day_date)s + INTERVAL 1 YEAR)
                         OR
                         # started during the year
                         (%(day_date)s <= created AND
                          created < %(day_date)s + INTERVAL 1 YEAR)
                         OR
                         # running during the year
                         ((created < %(day_date)s)
                          AND (deleted IS NULL OR
                               %(day_date)s + INTERVAL 1 YEAR <= deleted)))
                      GROUP BY project_id
                    ) i ON i.project_id = allocation.project_id
        WHERE project.organisation LIKE '%%melb%%'
              AND vcpucount > 0
        ORDER BY vcpucount ASC;
        """
        self._db_cur.execute(query,
                             {'day_date': day_date.strftime("%Y-%m-%d")})
        return self._db_cur.fetchall()


def connect_to_ldap():
    return False


if __name__ == "__main__":
    db = ReportingDB()
    ldap = LDAP()
    o = '{project!s}, {ci!s}, {owner!s}, {name!s}, {faculty!s}, {vcpucount!s}'
    for year in [2013, 2014, 2015, 2016, 2017, 2018]:
        print('=' * 80)
        print('Year: %s' % year)
        print('=' * 80)
        print()
        headings = o.format(
            **{'project': 'Project', 'ci': 'Chief investigator',
               'owner': 'Project owner', 'name': 'Attributed to',
               'faculty': 'Faculty',
               'vcpucount': 'VCPU count'})
        print(headings)
        # print('-' * len(headings))
        years_data = db.get_year_totals(year)
        none_count = 0
        for project in years_data:
            project['faculty'], project['name'] = ldap.find_faculty(
                project['ci'])
            if project['faculty'] is None:
                project['faculty'], project['name'] = ldap.find_faculty(
                    project['owner'])
            if project['faculty'] is None:
                none_count += 1
            print(o.format(**project))
        print()
        print('Of %s entries %s not allocated to a faculty' % (
            len(years_data), none_count))
        print()
