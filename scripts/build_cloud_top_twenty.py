import sqlite3
import sys
from datetime import timedelta, date

import MySQLdb

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
        cursor.execute("""
            SELECT  '{0}' AS 'date', i.project_id, SUM(i.vcpus) vcpus, a.tenant_name
            FROM nova.instances i
            LEFT JOIN
            (SELECT DISTINCT tenant_uuid, tenant_name, contact_email
                 FROM dashboard.rcallocation_allocationrequest t1
                 WHERE tenant_uuid > ''
                    AND modified_time = (
                      SELECT MAX(modified_time)
                      FROM dashboard.rcallocation_allocationrequest t2
                      WHERE t1.tenant_uuid = t2.tenant_uuid)) a
            ON i.project_id = a.tenant_uuid
            WHERE
              /* (started on the day OR ended on the day OR running through the day)
                  AND not started and stopped on the day AND a unimelb project
               */
              ((i.terminated_at BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
               OR (i.created_at BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
               OR (i.terminated_at IS NULL AND i.created_at < '{0}'))
              AND NOT ((i.terminated_at BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
                       AND (i.created_at BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY)))
              AND a.contact_email LIKE '%unimelb.edu.au%'
            GROUP BY i.project_id
            ORDER BY vcpus DESC
            LIMIT 20;
          """.format(day_date.strftime("%Y-%m-%d")))
        result_set = cursor.fetchall()
        for row in result_set:
            user_counts = {
                'date': row["date"],
                'project_id': row["project_id"],
                'vcpus': int(row["vcpus"]),
                'tenant_name': row["tenant_name"]
            }
            sqlite3_cursor = sqlite3_connection.cursor()
            columns = ', '.join(user_counts.keys())
            value_placeholder = ', '.join([':%s' % k for k in user_counts.keys()])
            update = "INSERT OR REPLACE INTO cloud_top_twenty (%s) VALUES (%s);" % (columns, value_placeholder)
            sqlite3_cursor.execute(update, user_counts)
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
