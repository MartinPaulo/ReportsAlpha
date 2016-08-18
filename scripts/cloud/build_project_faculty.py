import sqlite3
import sys
from datetime import date

from ldap3 import Server, Connection

from scripts.cloud.utility import get_faculty

ldap_server = Server('centaur.unimelb.edu.au')
ldap_connection = Connection(ldap_server)
if not ldap_connection.bind():
    print("Could not bind to LDAP server")
    sys.exit(1)


def build_project_faculty(cursor_in, cursor_out, start_day,
                          end_day=date.today()):
    cursor_in.execute("""
                SELECT
                  tenant_uuid,
                  contact_email,
                  tenant_name
                FROM rcallocation_allocationrequest t1
                WHERE contact_email LIKE '%unimelb.edu.au%'
                      AND tenant_uuid > ''
                      /* we want the last modified row */
                      AND modified_time = (SELECT MAX(modified_time)
                                           FROM
                                             rcallocation_allocationrequest t2
                                           WHERE
                                             t2.tenant_uuid = t1.tenant_uuid)
                ORDER BY t1.modified_time;
                """)
    result_set = cursor_in.fetchall()
    for row in result_set:
        project_id = row["tenant_uuid"]
        project_leader = row["contact_email"]
        project_name = row["tenant_name"]
        query = '(&(objectclass=person)(mail=%s))' % project_leader
        ldap_connection.search('o=unimelb', query,
                               attributes=['department',
                                           'departmentNumber',
                                           'auEduPersonSubType'])
        faculties = None
        if len(ldap_connection.entries) > 0:
            department_no = []
            for entry in ldap_connection.entries:
                if hasattr(entry, 'departmentNumber'):
                    department_no.extend(entry.departmentNumber)
            faculties = get_faculty(department_no)
        if not faculties:
            faculties = ['Unknown']
        update = "INSERT OR REPLACE INTO cloud_project_faculty " \
                 "(project_id, contact_email, name, faculty_abbreviation) VALUES ('%s', '%s', '%s', '%s');" % \
                 (
                     project_id, project_leader, project_name,
                     faculties.pop())
        # print(update)
        cursor_out.execute(update)
        cursor_out.commit()
        print(".", end="", flush=True)
