from datetime import date

from scripts.cloud.utility import date_range, get_new_faculty_totals


def build_used(cursor_in, cursor_out, start_day, end_day=date.today()):
    for day_date in date_range(start_day, end_day):
        faculty_totals = get_new_faculty_totals()
        result_set = get_used_data(cursor_in, day_date)
        for row in result_set:
            project_id = row["project_id"]
            fetchone = get_faculty_abbreviation(cursor_out, project_id)
            if not fetchone:
                print("Not found: %s" % project_id)
                continue
            faculty = fetchone[0]
            faculty_totals[faculty] += int(row["vcpus"])
        faculty_totals['date'] = day_date.strftime("%Y-%m-%d")
        columns = ', '.join(faculty_totals.keys())
        value_placeholder = ', '.join(
            [':%s' % k for k in faculty_totals.keys()])
        update = "INSERT OR REPLACE INTO cloud_used (%s) VALUES (%s);" % (
            columns, value_placeholder)
        cursor_out.execute(update, faculty_totals)
        cursor_out.commit()
        print(".", end="", flush=True)


def get_faculty_abbreviation(cursor_out, project_id):
    sqlite3_query = "SELECT faculty_abbreviation FROM cloud_project_faculty WHERE project_id = ?"
    cursor_out.execute(sqlite3_query, (project_id,))
    fetchone = cursor_out.fetchone()
    return fetchone


def get_used_data(cursor_in, day_date):
    cursor_in.execute("""SELECT
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
    return cursor_in.fetchall()
