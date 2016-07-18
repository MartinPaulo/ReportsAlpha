import sys
from datetime import timedelta, date

import MySQLdb
from ldap3 import Server, Connection
import sqlite3

sqlite3_connection = sqlite3.connect('/Users/mpaulo/PycharmProjects/ReportsBeta/db/db.sqlite3')


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
        cursor.execute("""SELECT
              i.project_id,
              sum(i.vcpus) vcpus,
              u.contact_email
            FROM nova.instances i
              LEFT JOIN
              (/* runs the risk that we will pick up an older email */
                SELECT
                  tenant_uuid,
                  contact_email
                FROM dashboard.rcallocation_allocationrequest
                WHERE contact_email LIKE '%unimelb.edu.au%'
                GROUP BY tenant_uuid) u
                ON i.project_id = u.tenant_uuid
            WHERE
              /* (started on the day OR ended on the day OR running through the day)
                  AND not started and stopped on the day AND a unimelb project
               */
              ((i.terminated_at BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
               OR (i.created_at BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
               OR (i.terminated_at IS NULL AND i.created_at < '{0}'))
              AND NOT ((i.terminated_at BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
                       AND (i.created_at BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY)))
              AND i.project_id IN (SELECT DISTINCT tenant_uuid AS project_id
                                   FROM rcallocation_allocationrequest t1
                                   WHERE contact_email LIKE '%unimelb.edu.au%'
                                         AND tenant_uuid > ''
                                         /* we want the last modified row
                                         this misses projects that once had a unimelb contact,
                                         but now have someone else */
                                         AND modified_time = (SELECT MAX(modified_time)
                                                              FROM
                                                                rcallocation_allocationrequest t2
                                                              WHERE
                                                                t2.tenant_uuid = t1.tenant_uuid))
            GROUP BY i.project_id
            ORDER BY vcpus;
            """.format(day_date.strftime("%Y-%m-%d")))
        result_set = cursor.fetchall()
        for row in result_set:
            project_id = row["project_id"]
            sqlite3_cursor = sqlite3_connection.cursor()
            sqlite3_query = "SELECT faculty_abbreviation FROM cloud_project_faculty WHERE project_id = ?"
            sqlite3_cursor.execute(sqlite3_query, (project_id,))
            fetchone = sqlite3_cursor.fetchone()
            if not fetchone:
                print("Not found: %s" % project_id)
                continue
            faculty = fetchone[0]
            faculty_totals[faculty] += int(row["vcpus"])
        sqlite3_cursor = sqlite3_connection.cursor()
        faculty_totals['date'] = day_date.strftime("%Y-%m-%d")
        columns = ', '.join(faculty_totals.keys())
        value_placeholder = ', '.join([':%s' % k for k in faculty_totals.keys()])
        update = "INSERT OR REPLACE INTO cloud_used (%s) VALUES (%s);" % (columns, value_placeholder)
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
