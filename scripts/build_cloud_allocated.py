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


found_projects = {}


def date_range(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


end_day = date.today()  # date(2016,3,11)
start_day = end_day - timedelta(days=380)

password = input("Please enter the db password: ")

mysql_connection = MySQLdb.connect(host='192.168.33.1',
                                   user='root',
                                   passwd=password,
                                   db='dashboard')
try:
    cursor = mysql_connection.cursor(MySQLdb.cursors.DictCursor)
    for day_date in date_range(start_day, end_day):
        faculty_totals = {'FoA': 0, 'VAS': 0, 'FBE': 0, 'MSE': 0, 'MGSE': 0, 'MDHS': 0, 'FoS': 0, 'ABP': 0, 'MLS': 0,
                          'VCAMCM': 0, 'Unknown': 0, 'Other': 0}
        # I can't port this to the reporting database, as it doesn't have date modified or date created
        # It also doesn't have properly linked users and projects.
        # This is cumulative: the sum of all cores allocated till day_date. So 12756 yesterday, 12768 the day before,
        # etc..
        # So it is likely to double count projects that have been amended. However its not too far out...
        cursor.execute("""SELECT
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
            ORDER BY t1.modified_time;""".format(day_date.strftime("%Y-%m-%d")))
        result_set = cursor.fetchall()
        desc = cursor.description
        for row in result_set:
            project_id = row["tenant_uuid"]
            if not found_projects.get(project_id):
                project_leader = row["contact_email"]
                query = '(&(objectclass=person)(mail=%s))' % project_leader
                ldap_connection.search('o=unimelb', query,
                                       attributes=['department', 'departmentNumber', 'auEduPersonSubType'])
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
        sqlite3_cursor = sqlite3_connection.cursor()
        faculty_totals['date'] = day_date.strftime("%Y-%m-%d")
        columns = ', '.join(faculty_totals.keys())
        value_placeholder = ', '.join([':%s' % k for k in faculty_totals.keys()])
        update = "INSERT OR REPLACE INTO cloud_allocated (%s) VALUES (%s);" % (columns, value_placeholder)
        sqlite3_cursor.execute(update, faculty_totals)
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
