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
    # on the 2016-03-11 we have 452 UoM users in total, with
    # 309 running elsewhere,
    # 233 running at UoM and 92 users are running in both UoM and elsewhere.
    # so we have set A = 309, set B = 233, A ∪ B = 452 and A ∩ B = 92
    cursor = mysql_connection.cursor(MySQLdb.cursors.DictCursor)
    for day_date in date_range(start_day, end_day):
        cursor.execute("""SELECT COUNT(DISTINCT user_id) AS others_at_uom
            FROM nova.instances
            WHERE
              ((terminated_at BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
              OR (created_at BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
              OR (terminated_at IS NULL AND created_at < '{0}' ))
              AND cell_name IN ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2' )
              AND user_id NOT IN (SELECT DISTINCT user_id FROM rcshib.user WHERE email LIKE '%unimelb.edu.au%');
            """.format(day_date.strftime("%Y-%m-%d")))
        row = cursor.fetchone()
        others_at_uom = row["others_at_uom"]

        cursor.execute("""SELECT COUNT(DISTINCT user_id) AS UoM_only
            FROM nova.instances
            WHERE
              ((terminated_at BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
              OR  (created_at BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
              OR  (terminated_at IS NULL AND created_at < '{0}' ))
              AND cell_name IN ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2' )
              AND user_id NOT IN (SELECT DISTINCT user_id AS user_id
                FROM nova.instances
                WHERE
                ((terminated_at BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
                OR  (created_at BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
                OR  (terminated_at IS NULL AND created_at < '{0}' ))
                AND cell_name NOT IN ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2' )
                AND user_id IN (SELECT DISTINCT user_id FROM rcshib.user WHERE email like '%unimelb.edu.au%'))
              AND user_id IN (SELECT DISTINCT user_id FROM rcshib.user WHERE email like '%unimelb.edu.au%');
        """.format(day_date.strftime("%Y-%m-%d")))
        row = cursor.fetchone()
        uom_only = row["UoM_only"]

        cursor.execute("""SELECT COUNT(DISTINCT user_id) AS elsewhere_only
            FROM nova.instances
            WHERE
              ((terminated_at  BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
              OR  (created_at  BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
              OR  (terminated_at IS NULL AND created_at < '{0}' ))
              AND cell_name NOT IN ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2' )
              AND user_id NOT IN (SELECT DISTINCT user_id AS user_id
                FROM nova.instances
                WHERE
                ((terminated_at  BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
                OR  (created_at  BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
                OR  (terminated_at IS NULL AND created_at < '{0}' ))
                AND cell_name IN ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2' )
                AND user_id IN (SELECT DISTINCT user_id FROM rcshib.user WHERE email LIKE '%unimelb.edu.au%'))
              AND user_id IN (SELECT DISTINCT user_id FROM rcshib.user WHERE email LIKE '%unimelb.edu.au%');
        """.format(day_date.strftime("%Y-%m-%d")))
        row = cursor.fetchone()
        elsewhere_only = row["elsewhere_only"]

        cursor.execute("""SELECT COUNT(DISTINCT r.user_id) AS in_both
            FROM nova.instances l
            LEFT JOIN nova.instances r
            ON l.user_id = r.user_id
            WHERE
              (((l.terminated_at BETWEEN  '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
              OR (l.created_at BETWEEN  '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
              OR (l.terminated_at IS NULL AND l.created_at < '{0}' ))
              AND l.cell_name IN ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2' )
              AND l.user_id IN (SELECT DISTINCT user_id FROM rcshib.user WHERE email LIKE '%unimelb.edu.au%'))
              AND
              (((r.terminated_at BETWEEN  '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
              OR (r.created_at BETWEEN  '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
              OR (r.terminated_at IS NULL AND r.created_at < '{0}' ))
              AND r.cell_name NOT IN ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2' )
              AND r.user_id IN (SELECT DISTINCT user_id FROM rcshib.user WHERE email LIKE '%unimelb.edu.au%'));
        """.format(day_date.strftime("%Y-%m-%d")))
        row = cursor.fetchone()
        in_both = row["in_both"]

        user_counts = {
            'date': day_date.strftime("%Y-%m-%d"),
            'others_at_uom': others_at_uom,
            'in_both': in_both,
            'elsewhere_only': elsewhere_only,
            'at_uom_only': uom_only
        }
        sqlite3_cursor = sqlite3_connection.cursor()
        columns = ', '.join(user_counts.keys())
        value_placeholder = ', '.join([':%s' % k for k in user_counts.keys()])
        update = "INSERT OR REPLACE INTO cloud_active_users (%s) VALUES (%s);" % (columns, value_placeholder)
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
