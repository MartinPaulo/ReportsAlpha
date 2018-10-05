#!/usr/bin/env python
import time
from datetime import date

import MySQLdb
from ldap3 import Server, Connection

from scripts.cloud.utility import Faculties
from scripts.custom.credentials import Credentials


class ReportingDB:
    """
    
    SELECT
      project_name                   AS project,
      IFNULL(chief_investigator, '') AS ci,
      contact_email                  AS owner,
      (CASE
       WHEN for_percentage_2 >= for_percentage_1 AND
            for_percentage_2 >= for_percentage_3
         THEN field_of_research_2
       WHEN for_percentage_3 >= for_percentage_1 AND
            for_percentage_3 >= for_percentage_2
         THEN field_of_research_3
       ELSE field_of_research_1
       END)                          AS field_of_research,
      i.vcpu_hours                   AS vcpu_hours,
      i.cell_name                    AS cell
    FROM allocation
      LEFT JOIN project ON allocation.project_id = project.id
      LEFT JOIN (
            SELECT
                project_id,
                ROUND(IFNULL(SUM(vcpus * TIMESTAMPDIFF(SECOND,
                                IF(created < '2017-1-1', '2017-1-1', created),
                                IF(IF(deleted IS NULL, NOW(), deleted) > DATE_ADD('2017-1-1', INTERVAL 1 YEAR),
                                   DATE_ADD('2017-1-1', INTERVAL 1 YEAR), IF(deleted IS NULL, NOW(), deleted))))
                  / 3600, 0)) AS vcpu_hours,
                cell_name
            FROM instance
            WHERE project_id IS NOT NULL
                AND created < DATE_ADD('2017-1-1', INTERVAL 1 YEAR)
                AND (deleted IS NULL OR deleted > '2017-1-1')
            GROUP BY project_id, cell_name
                ) i ON i.project_id = allocation.project_id
    WHERE project.organisation LIKE '%melb%'
          AND vcpu_hours > 0
    ORDER BY project, cell, vcpu_hours DESC;
    
    
    SELECT
        project_id,
        ROUND(IFNULL(SUM(vcpus * TIMESTAMPDIFF(SECOND,
                        IF(created < '2017-1-1', '2017-1-1', created),
                        IF(IF(deleted IS NULL, NOW(), deleted) > DATE_ADD('2017-1-1', INTERVAL 1 YEAR),
                           DATE_ADD('2017-1-1', INTERVAL 1 YEAR), IF(deleted IS NULL, NOW(), deleted))))
          / 3600, 0)) AS vcpu_hours,
        cell_name
    FROM instance
    WHERE project_id IS NOT NULL
        AND created < DATE_ADD('2017-1-1', INTERVAL 1 YEAR)
        AND (deleted IS NULL OR deleted > '2017-1-1')
    GROUP BY project_id, cell_name;
    
    
    SELECT
        project_id,
        SUM(vcpus),
        cell_name
    FROM instance
    WHERE project_id IS NOT NULL
        AND created < DATE_ADD('2017-1-1', INTERVAL 1 YEAR)
        AND (deleted IS NULL OR deleted > '2017-1-1')
    GROUP BY project_id, cell_name;
    """
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

    def get_year_totals(self, year):
        day_date = date(year, 1, 1)
        query = """
            SELECT
              project_name                   AS project,
              IFNULL(chief_investigator, '') AS ci,
              contact_email                  AS owner,
              (CASE
               WHEN for_percentage_2 >= for_percentage_1 AND
                    for_percentage_2 >= for_percentage_3
                 THEN field_of_research_2
               WHEN for_percentage_3 >= for_percentage_1 AND
                    for_percentage_3 >= for_percentage_2
                 THEN field_of_research_3
               ELSE field_of_research_1
               END)                          AS field_of_research,
              i.vcpu_hours                   AS vcpu_hours,
              i.cell_name                    AS cell
            FROM allocation
              LEFT JOIN project ON allocation.project_id = project.id
              LEFT JOIN (
                          SELECT
                            project_id,
                            ROUND(IFNULL(SUM(vcpus * TIMESTAMPDIFF(SECOND,
                                                    IF(created < %(day_date)s, %(day_date)s, created),
                                                    IF(IF(deleted IS NULL, NOW(), deleted) > DATE_ADD(%(day_date)s, INTERVAL 1 YEAR),
                                                       DATE_ADD(%(day_date)s, INTERVAL 1 YEAR), IF(deleted IS NULL, NOW(), deleted))))
                                      / 3600, 0)) AS vcpu_hours,
                            cell_name
                          FROM instance
                          WHERE project_id IS NOT NULL
                                AND created < DATE_ADD(%(day_date)s, INTERVAL 1 YEAR)
                                AND (deleted IS NULL OR deleted > %(day_date)s)
                          GROUP BY project_id, cell_name
                        ) i ON i.project_id = allocation.project_id
            WHERE project.organisation LIKE '%%melb%%'
                  AND vcpu_hours > 0
            ORDER BY project, cell, vcpu_hours DESC;
        """
        self._db_cur.execute(query,
                             {'day_date': day_date.strftime("%Y-%m-%d")})
        return self._db_cur.fetchall()


def connect_to_ldap():
    return False


class LDAP:
    _server = None
    _conn = None

    @staticmethod
    def append_if_not_in(target, faculty):
        if not faculty in target:
            target.append(faculty)

    def __init__(self):
        self._server = Server('centaur.unimelb.edu.au')
        self._conn = Connection(self._server)
        if not self._conn.bind():
            raise Exception('Could not bind to ldap server')

    def find_department(self, email):
        if email is None:
            return None, None
        if 'unimelb' not in email:
            return 'External', None
        query = '(&(objectclass=person)(mail=%s))' % email
        self._conn.search('o=unimelb', query,
                          attributes=['department', 'departmentNumber',
                                      'auEduPersonSubType', 'displayName'])
        if len(self._conn.entries) == 0:
            return None, None
        department_no = []
        for entry in self._conn.entries:
            if hasattr(entry, 'departmentNumber'):
                department_no.extend(entry.departmentNumber)
        return Faculties.get_from_departments(department_no)

    def __del__(self):
        self._conn.unbind()


if __name__ == "__main__":
    db = ReportingDB()
    ldap = LDAP()
    out_file = "output/cyvbc_%s.txt" % time.strftime("%Y%m%d-%H%M%S")
    o = '{project!s}, {ci!s}, {owner!s}, {faculty!s}, {cell!s}, {vcpu_hours!s}'
    with open(out_file, "w") as output:
        for year in [2012, 2013, 2014, 2015, 2016, 2017]:
            total = 0
            output.write('=' * 80 + '\n')
            output.write('Year: %s\n' % year)
            output.write('=' * 80 + '\n')
            output.write('\n')
            headings = o.format(
                **{'project': 'Project',
                   'ci': 'Chief investigator',
                   'owner': 'Project owner',
                   'faculty': 'Faculty',
                   'cell': 'Cell',
                   'vcpu_hours': 'VCPU hours'})
            output.write(headings + '\n')
            # output.write('-' * len(headings))
            years_data = db.get_year_totals(year)
            none_count = 0
            for project in years_data:
                faculties = ldap.find_department(project['ci'])
                if not len(faculties):
                    faculties = ldap.find_department(project['owner'])
                if not len(faculties):
                    faculties = Faculties.get_from_for_code(
                        project['field_of_research'])
                if not len(faculties):
                    none_count += 1
                if Faculties.MDHS in faculties:
                    project['faculty'] = 'MDHS'
                    output.write(o.format(**project) + '\n')
                    total += int(project['vcpu_hours'])
            output.write('\n')
            output.write('Year\'s total: %s\n' % total)
            output.write('\n')
            print('%s: Of %s entries %s not allocated to a faculty\n' % (
                year, len(years_data), none_count))
