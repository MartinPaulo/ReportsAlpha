import sys
from datetime import timedelta, date

import MySQLdb
from ldap3 import Server, Connection
import sqlite3

sqlite3_connection = sqlite3.connect('/Users/mpaulo/PycharmProjects/ReportsBeta/db/db.sqlite3')

ldap_server = Server('centaur.unimelb.edu.au')
ldap_connection = Connection(ldap_server)
if not ldap_connection.bind():
    print("Could not bind to LDAP server")
    sys.exit(1)


def get_faculty(department_numbers):
    result = set()
    for departmentNumber in department_numbers:
        depNo = int(departmentNumber[:3])
        if 100 <= depNo < 250:
            result.add('FoA')  # Faculty of Arts: ARTS in spreadsheet
        elif 250 <= depNo < 300:
            result.add('VAS')  # VAS? Veterinary and Agricultural Sciences: VET SC in spreadsheet
        elif 300 <= depNo < 400:
            result.add('FBE')  # Faculty of Business and Economics
        elif 400 <= depNo < 460:
            result.add('MSE')  # Melbourne School Of Engineering
        elif 460 <= depNo < 500:
            result.add('MGSE')  # Melbourne Graduate School of Education
        elif 500 <= depNo < 600:
            result.add('MDHS')  # Medicine, Dentistry and Health Science
        elif 600 <= depNo < 700:
            result.add('FoS')  # FoS? Faculty of Science: SCI in spreadsheet
        elif 700 <= depNo < 730:
            result.add('ABP')  # Architecture, Building and Planning
        elif 730 <= depNo < 750:
            result.add('MLS')  # Melbourne Law School
        elif 750 <= depNo < 780:
            result.add('VCAMCM')  # Victorian College of the Arts and Melbourne Conservatorium of Music
        elif 780 <= depNo < 900:
            result.add('MDHS')  # Medicine, Dentistry and Health Science
            # result.add('Bio 21') # Bio 21 goes to MDHS
        else:
            result.add('Other')
    return result


password = input("Please enter the db password: ")

mysql_connection = MySQLdb.connect(host='192.168.33.1',
                                   user='root',
                                   passwd=password,
                                   db='dashboard')
try:
    cursor = mysql_connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
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
    result_set = cursor.fetchall()
    for row in result_set:
        project_id = row["tenant_uuid"]
        project_leader = row["contact_email"]
        project_name = row["tenant_name"]
        query = '(&(objectclass=person)(mail=%s))' % project_leader
        ldap_connection.search('o=unimelb', query,
                               attributes=['department', 'departmentNumber', 'auEduPersonSubType'])
        faculties = None
        if len(ldap_connection.entries) > 0:
            department_no = []
            for entry in ldap_connection.entries:
                if hasattr(entry, 'departmentNumber'):
                    department_no.extend(entry.departmentNumber)
            faculties = get_faculty(department_no)
        if not faculties:
            faculties = ['Unknown']
        sqlite3_cursor = sqlite3_connection.cursor()
        update = "INSERT OR REPLACE INTO cloud_project_faculty " \
                 "(project_id, contact_email, name, faculty_abbreviation) VALUES ('%s', '%s', '%s', '%s');" % \
                 (project_id, project_leader, project_name, faculties.pop())
        #print(update)
        sqlite3_cursor.execute(update)
        sqlite3_connection.commit()
        print(".", end="", flush=True)
except MySQLdb.Error as e:
    print("Error %d: %s" % (e.args[0], e.args[1]))
    sys.exit(1)
finally:
    if mysql_connection:
        mysql_connection.close()
    if sqlite3_connection:
        sqlite3_connection.close()
print()
print("All done!")
