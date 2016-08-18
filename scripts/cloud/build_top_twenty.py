import sqlite3
from datetime import date

from scripts.cloud.utility import date_range


def build_top_twenty(cursor_in, cursor_out, start_day,
                     end_day=date.today()):
    for day_date in date_range(start_day, end_day):
        cursor_in.execute("""
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
        result_set = cursor_in.fetchall()
        for row in result_set:
            user_counts = {
                'date': row["date"],
                'project_id': row["project_id"],
                'vcpus': int(row["vcpus"]),
                'tenant_name': row["tenant_name"]
            }
            columns = ', '.join(user_counts.keys())
            value_placeholder = ', '.join(
                [':%s' % k for k in user_counts.keys()])
            update = "INSERT OR REPLACE INTO cloud_top_twenty (%s) VALUES (%s);" % (
                columns, value_placeholder)
            cursor_out.execute(update, user_counts)
            cursor_out.commit()
        print(".", end="", flush=True)
