import sqlite3
import sys
from datetime import date

from ldap3 import Server, Connection

from scripts.cloud.utility import date_range, get_faculty, \
    get_new_faculty_totals

ldap_server = Server('centaur.unimelb.edu.au')
ldap_connection = Connection(ldap_server)
if not ldap_connection.bind():
    print("Could not bind to LDAP server")
    sys.exit(1)

found_projects = {}


def build_allocated(cursor_in, cursor_out, start_day,
                    end_day=date.today()):
    for day_date in date_range(start_day, end_day):
        faculty_totals = get_new_faculty_totals()
        cursor_in.execute("""SELECT
                  tenant_uuid,
                  contact_email,
                  cores,
                  modified_time,
                  tenant_name
                FROM rcallocation_allocationrequest t1
                WHERE
                  contact_email LIKE '%unimelb.edu.au%'
                  AND tenant_uuid > ''
                  AND modified_time <= DATE_ADD('{0}', INTERVAL 1 DAY)
                  AND modified_time = (
                    SELECT MAX(modified_time)
                    FROM rcallocation_allocationrequest t2
                    WHERE t2.tenant_uuid = t1.tenant_uuid
                          AND modified_time <= DATE_ADD('{0}', INTERVAL 1 DAY))
                ORDER BY t1.modified_time;""".format(
            day_date.strftime("%Y-%m-%d")))
        result_set = cursor_in.fetchall()
        desc = cursor_in.description
        for row in result_set:
            project_id = row["tenant_uuid"]
            if not found_projects.get(project_id):
                project_leader = row["contact_email"]
                query = '(&(objectclass=person)(mail=%s))' % project_leader
                ldap_connection.search('o=unimelb', query,
                                       attributes=['department',
                                                   'departmentNumber',
                                                   'auEduPersonSubType'])
                if len(ldap_connection.entries) > 0:
                    department_no = []
                    for entry in ldap_connection.entries:
                        if hasattr(entry, 'departmentNumber'):
                            department_no.extend(entry.departmentNumber)
                    faculties = get_faculty(department_no)
                    found_projects[project_id] = faculties
            faculties = found_projects.get(project_id)
            if not faculties:
                faculties = ['Unknown']
            for faculty in faculties:
                # faculty_totals[faculty] += 1 / len(faculties)
                # currently each faculty will be assigned the projects cores...
                faculty_totals[faculty] += row["cores"]
        faculty_totals['date'] = day_date.strftime("%Y-%m-%d")
        columns = ', '.join(faculty_totals.keys())
        value_placeholder = ', '.join(
            [':%s' % k for k in faculty_totals.keys()])
        update = "INSERT OR REPLACE INTO cloud_allocated (%s) VALUES (%s);" % (
            columns, value_placeholder)
        cursor_out.execute(update, faculty_totals)
        cursor_out.commit()
        print(".", end="", flush=True)
