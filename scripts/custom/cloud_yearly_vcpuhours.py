#!/usr/bin/env python
from datetime import date

import MySQLdb
from ldap3 import Server, Connection

from scripts.custom.credentials import Credentials


class ReportingDB:
    """

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
              i.vcpu_hours                   AS vcpu_hours
            FROM allocation
              LEFT JOIN project ON allocation.project_id = project.id
              LEFT JOIN (
                          SELECT
                            project_id,
                            ROUND(IFNULL(
                                      SUM(vcpus * TIMESTAMPDIFF(SECOND,
                                                                IF(created < %(day_date)s, %(day_date)s, created),
                                                                IF(IF(deleted IS NULL, NOW(), deleted) > DATE_ADD(%(day_date)s, INTERVAL 1 YEAR),
                                                                   DATE_ADD(%(day_date)s, INTERVAL 1 YEAR), IF(deleted IS NULL, NOW(), deleted))))
                                      / 3600, 0)) AS vcpu_hours
                          FROM instance
                          WHERE project_id IS NOT NULL
                                AND created < DATE_ADD(%(day_date)s, INTERVAL 1 YEAR)
                                AND (deleted IS NULL OR deleted > %(day_date)s)
                          GROUP BY project_id
                        ) i ON i.project_id = allocation.project_id
            WHERE project.organisation LIKE '%%melb%%'
                  AND vcpu_hours > 0
            ORDER BY vcpu_hours DESC;
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

    @staticmethod
    def get_faculty(department_numbers):
        result = list()
        for departmentNumber in department_numbers:
            dep_no = int(departmentNumber[:3])
            if 100 <= dep_no < 250:
                # Faculty of Arts
                LDAP.append_if_not_in(result, 'FoA')
            elif 250 <= dep_no < 300:
                # VAS? Veterinary and Agricultural Sciences
                LDAP.append_if_not_in(result, 'VAS')
            elif 300 <= dep_no < 400:
                # Faculty of Business and Economics
                LDAP.append_if_not_in(result, 'FBE')
            elif 400 <= dep_no < 460:
                # Melbourne School Of Engineering
                LDAP.append_if_not_in(result, 'MSE')
            elif 460 <= dep_no < 500:
                # Melbourne Graduate School of Education
                LDAP.append_if_not_in(result, 'MGSE')
            elif 500 <= dep_no < 600:
                # Medicine, Dentistry and Health Science
                LDAP.append_if_not_in(result, 'MDHS')
            elif 600 <= dep_no < 700:
                # FoS? Faculty of Science: SCI in spreadsheet
                LDAP.append_if_not_in(result, 'FoS')
            elif 700 <= dep_no < 730:
                # Architecture, Building and Planning
                LDAP.append_if_not_in(result, 'ABP')
            elif 730 <= dep_no < 750:
                # Melbourne Law School
                LDAP.append_if_not_in(result, 'MLS')
            elif 750 <= dep_no < 780:
                # Victorian College of the Arts and
                # Melbourne Conservatorium of Music
                LDAP.append_if_not_in(result, 'VCAMCM')
            elif 780 <= dep_no < 900:
                LDAP.append_if_not_in(result, 'Bio 21')
            else:
                LDAP.append_if_not_in(result, 'Staff')
        return result

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
        display_names = []
        department_no = []
        for entry in self._conn.entries:
            if hasattr(entry, 'departmentNumber'):
                department_no.extend(entry.departmentNumber)
            if hasattr(entry, 'displayName'):
                display_names.extend(entry.displayName)
        display_name = None
        if len(display_names) > 0:
            display_name = display_names[0]
        faculties = self.get_faculty(department_no)
        if len(faculties) == 0:
            return None, display_name
        return ' '.join(map(str, faculties)), display_name

    def __del__(self):
        self._conn.unbind()


if __name__ == "__main__":
    db = ReportingDB()
    ldap = LDAP()
    years = [2012, 2013, 2014, 2015, 2016, 2017, 2018]
    vcpu_total_hours = {}
    o = '{project!s}, {ci!s}, {owner!s}, {name!s}, {faculty!s}, {vcpu_hours!s}'
    with open("output/ps_cloud_yearly_vcpu_hours.txt", "w") as output:
        for year in years:
            output.write('=' * 80 + '\n')
            output.write('Year: %s\n' % year)
            output.write('=' * 80 + '\n')
            output.write('\n')
            headings = o.format(
                **{'project': 'Project', 'ci': 'Chief investigator',
                   'owner': 'Project owner', 'name': 'Attributed to',
                   'faculty': 'Faculty',
                   'vcpu_hours': 'VCPU hours'})
            output.write(headings + '\n')
            # output.write('-' * len(headings))
            years_data = db.get_year_totals(year)
            none_count = 0
            total_vcpu_hours = 0
            for project in years_data:
                project['faculty'], project['name'] = ldap.find_department(
                    project['ci'])
                if project['faculty'] is None:
                    project['faculty'], project['name'] = ldap.find_department(
                        project['owner'])
                if project['faculty'] is None:
                    none_count += 1
                output.write(o.format(**project) + '\n')
                total_vcpu_hours += project['vcpu_hours']
            vcpu_total_hours[year] = total_vcpu_hours
            output.write('\n')
            output.write('Total vcpu hours for year %s\n' % total_vcpu_hours)
            output.write('\n')
            output.write('Of %s entries %s not allocated to a faculty\n' % (
                len(years_data), none_count))
            output.write('\n')
        output.write('VCPU hours over the years\n')
        output.write('=========================\n')
        for key, value in vcpu_total_hours.items():
            output.write(f'{key}: {int(value):12,}\n')