import MySQLdb

from scripts.config import Configuration


class DB(object):
    _db_connection = None
    _db_cur = None

    def __init__(self):
        self._db_connection = MySQLdb.connect(
            **Configuration.get_reporting_db())
        self._db_cur = self._db_connection.cursor(MySQLdb.cursors.DictCursor)

    def query(self, query, params):
        return self._db_cur.execute(query, params)

    def __del__(self):
        self._db_connection.close()

    def get_in_both(self, day_date):
        self._db_cur.execute("""SELECT COUNT(DISTINCT r.user_id) AS in_both
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
        return self._db_cur.fetchone()["in_both"]

    def get_elsewhere_only(self, day_date):
        self._db_cur.execute("""SELECT COUNT(DISTINCT user_id) AS elsewhere_only
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
        return self._db_cur.fetchone()["elsewhere_only"]

    def get_uom_only(self, day_date):
        self._db_cur.execute("""SELECT COUNT(DISTINCT user_id) AS UoM_only
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
        return self._db_cur.fetchone()["UoM_only"]

    def get_count_of_others_at_uom(self, day_date):
        self._db_cur.execute("""SELECT COUNT(DISTINCT user_id) AS others_at_uom
                    FROM nova.instances
                    WHERE
                      ((terminated_at BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))  /* stopped on the day */
                      OR (created_at BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))   /* started on the day */
                      OR (terminated_at IS NULL AND created_at < '{0}' ))                 /* running through the day */
                      AND cell_name IN ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2' )
                      AND user_id NOT IN (SELECT DISTINCT user_id FROM rcshib.user WHERE email LIKE '%unimelb.edu.au%');
                    """.format(day_date.strftime("%Y-%m-%d")))
        return self._db_cur.fetchone()["others_at_uom"]

    def get_allocated_totals(self, day_date):
        """
        project id b97d4ecd7f554796b5f59fadfb10a087 has null cores?
        :param day_date:
        :return:
        """
        self._db_cur.execute("""
            SELECT
              p.id as tenant_uuid /* used for the join */,
              a.contact_email /* used to get the faculty at UoM */,
              IFNULL(p.quota_vcpus, 0) as cores /* cores from allocation? */,
              a.modified_time /* and get the value on a given day*/,
              p.display_name as tenant_name/* just because */,
              p.organisation /* so we can refine by organisation */
            FROM project p
              LEFT JOIN (
                          SELECT
                            project_id,
                            contact_email,
                            modified_time
                          FROM allocation) a
                ON p.id = a.project_id
            WHERE p.personal = 0
                AND p.organisation LIKE '%melb%'
                AND modified_time <= DATE_ADD('{0}', INTERVAL 1 DAY)
            ORDER BY id;""".format(day_date.strftime("%Y-%m-%d")))
        return self._db_cur.fetchall()

    def get_used_data(self, day_date):
        """

        :param day_date:
        :return:
        """
        self._db_cur.execute("""
            SELECT
              i.project_id,
              SUM(i.vcpus)    vcpus,
              a.display_name
            FROM reporting.instance i
              LEFT JOIN
              (SELECT
                 id,
                 organisation,
                 display_name,
                 personal
               FROM reporting.project t1) a
                ON i.project_id = a.id
            WHERE
              /* (started on the day OR ended on the day OR running through the day)
                  AND not started and stopped on the day AND a unimelb project
               */
              ((i.deleted BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
               OR (i.created BETWEEN '2016-07-10' AND DATE_ADD('{0}', INTERVAL 1 DAY))
               OR (i.deleted IS NULL AND i.created < '{0}'))
              AND NOT ((i.deleted BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
                       AND (i.created BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY)))
              AND a.organisation LIKE '%melb%' AND a.personal = 0
            GROUP BY i.project_id
            ORDER BY vcpus DESC;
                    """.format(day_date.strftime("%Y-%m-%d")))
        return self._db_cur.fetchall()

    def get_top_twenty_data(self, day_date):
        self._db_cur.execute("""
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
        return self._db_cur.fetchall()

    def get_faculty_data(self):
        self._db_cur.execute("""
                    SELECT
                      tenant_uuid,
                      contact_email,
                      tenant_name
                    FROM dashboard.rcallocation_allocationrequest t1
                    WHERE contact_email LIKE '%unimelb.edu.au%'
                          AND tenant_uuid > ''
                          /* we want the last modified row */
                          AND modified_time = (SELECT MAX(modified_time)
                                               FROM
                                                 dashboard.rcallocation_allocationrequest t2
                                               WHERE
                                                 t2.tenant_uuid = t1.tenant_uuid)
                    ORDER BY t1.modified_time;
                    """)
        return self._db_cur.fetchall()
