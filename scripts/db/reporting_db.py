import MySQLdb

from scripts.config import Configuration
from scripts.db.source_db import BaseDB


class DB(BaseDB):
    """
    Contains queries specific to the reporting database.
    """

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
        self._db_cur.execute("""
            SELECT COUNT(DISTINCT r.created_by) AS in_both
            FROM instance l
              LEFT JOIN instance r
                ON l.created_by = r.created_by
            WHERE (((l.deleted BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
                  OR (l.created BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
                  OR (l.created < '{0}' AND (l.deleted IS NULL OR l.deleted > DATE_ADD('{0}', INTERVAL 1 DAY))))
              AND l.cell_name IN ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2')
              AND l.project_id IN (SELECT DISTINCT id
                                    FROM project
                                    WHERE organisation LIKE '%melb%'))
              AND (((r.deleted BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
                  OR (r.created BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
                  OR (r.created < '{0}' AND (r.deleted IS NULL OR r.deleted > DATE_ADD('{0}', INTERVAL 1 DAY))))
                AND r.cell_name NOT IN ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2')
                AND r.project_id IN (SELECT DISTINCT id
                                     FROM project
                                     WHERE organisation LIKE '%melb%'));
        """.format(day_date.strftime("%Y-%m-%d")))
        return self._db_cur.fetchone()["in_both"]

    def get_all_outside(self, day_date):
        self._db_cur.execute("""
            SELECT COUNT(DISTINCT created_by) AS uom_users_outside_uom
            FROM instance
            WHERE
              (((deleted BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
                OR
                (created BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
                OR (created < '{0}'
                    AND
                    (deleted IS NULL OR deleted > DATE_ADD('{0}', INTERVAL 1 DAY))))
               AND cell_name NOT IN
                   ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2')
               AND project_id IN (SELECT DISTINCT id
                                  FROM project
                                  WHERE organisation LIKE '%melb%'));
        """.format(day_date.strftime("%Y-%m-%d")))
        return self._db_cur.fetchone()["uom_users_outside_uom"]

    def get_elsewhere_only(self, day_date):
        self._db_cur.execute("""
            SELECT COUNT(DISTINCT created_by) AS elsewhere_only
            FROM instance
            WHERE
              ((deleted BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
                  OR (created BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
                  OR (created < '{0}' AND (deleted IS NULL OR deleted > DATE_ADD('{0}', INTERVAL 1 DAY))))
              AND cell_name NOT IN ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2')
              AND project_id IN (SELECT DISTINCT id
                                 FROM project
                                 WHERE organisation LIKE '%melb%')
              /* and not running any instances in melbourne on the day */
              AND created_by NOT IN (
                 SELECT DISTINCT created_by
                 FROM instance
                 WHERE
                   ((deleted BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
                        OR (created BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
                        OR (created < '{0}' AND (deleted IS NULL OR deleted > DATE_ADD('{0}', INTERVAL 1 DAY))))
                   AND cell_name IN ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2')
                   AND project_id IN (SELECT DISTINCT id
                                      FROM project
                                      WHERE organisation LIKE '%melb%'));
        """.format(day_date.strftime("%Y-%m-%d")))
        return self._db_cur.fetchone()["elsewhere_only"]

    def get_uom_only(self, day_date):
        self._db_cur.execute("""
            SELECT COUNT(DISTINCT created_by) AS UoM_only
            FROM instance
            WHERE
              ((deleted BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
                OR (created BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
                OR (created < '{0}' AND (deleted IS NULL OR deleted > DATE_ADD('{0}', INTERVAL 1 DAY))))
              AND cell_name IN ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2')
              AND project_id IN (SELECT DISTINCT id
                                 FROM project
                                 WHERE organisation LIKE '%melb%')
              /* and not running any instances in any other zone on the day */
              AND created_by NOT IN (
                SELECT DISTINCT created_by
                FROM instance
                WHERE
                    ((deleted BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
                    OR (created BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
                    OR (created < '{0}' AND (deleted IS NULL OR deleted > DATE_ADD('{0}', INTERVAL 1 DAY))))
                    AND cell_name NOT IN ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2')
                    AND project_id IN (SELECT DISTINCT id
                                      FROM project
                                      WHERE organisation LIKE '%melb%'));
        """.format(day_date.strftime("%Y-%m-%d")))
        return self._db_cur.fetchone()["UoM_only"]

    def get_count_of_others_at_uom(self, day_date):
        self._db_cur.execute("""
            SELECT COUNT(DISTINCT created_by) AS others_at_uom
            FROM instance
            WHERE
              /* stopped on the day */
              ((deleted BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
                  /* started on the day */
                  OR (created BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
                  /* running through the day */
                  OR (created < '{0}' AND (deleted IS NULL OR deleted > DATE_ADD('{0}', INTERVAL 1 DAY))))
              AND cell_name IN ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2')
              AND project_id NOT IN (SELECT id
                                     FROM project
                                     WHERE organisation LIKE '%melb%');
        """.format(day_date.strftime("%Y-%m-%d")))
        return self._db_cur.fetchone()["others_at_uom"]

    def get_allocated_totals(self, day_date):
        """
        Notes:
            The allocations table is used simply to filter the results by
            date.

            Any project that was initially provisioned before the requested
            date then subsequently modified afterward will be excluded. Which
            doesn't give a fair reflection of the state on a given day if
            the query is being stepped through past data.

            However, once the historical data has been worked through, it
            will show the changing state of the allocation totals as they are
            made.

            If it weren't for the desire to capture historical data it would
            be possible to simply query only the project table every day
            and save the total - no need to include the allocations table.

            Once crams goes live it should be possible to rather query the
            crams API for a more accurate historical record of the allocations
            made.

            Also, now newly discovered is that the reporting project table
            has projects allocated to UoM that don't actually have allocations
            in the allocation table: further investigation is required...

            Also, there are three projects that have no quota...
        """
        self._db_cur.execute("""
            SELECT
              p.id                     AS project_id,
              IFNULL(p.quota_vcpus, 0) AS quota_vcpus
            FROM project p
              LEFT JOIN allocation a
                ON p.id = a.project_id
            WHERE p.personal = 0
                  AND p.organisation LIKE '%%melb%%'
                  AND (a.modified_time <= DATE_ADD(%(day_date)s, INTERVAL 1 DAY)
                       OR a.modified_time IS NULL) /* never modified */
            ;
        """, {'day_date': day_date.strftime("%Y-%m-%d")})
        return self._db_cur.fetchall()

    def get_used_data(self, day_date):
        self._db_cur.execute("""
            SELECT
              project_id,
              SUM(vcpus) AS vcpus,
              display_name
            FROM instance i
              LEFT JOIN project a
                ON i.project_id = a.id
            WHERE
              (( /* started on or before the day*/
                 created < DATE_ADD(%(day_date)s, INTERVAL 1 DAY)
                 /* and running after the day */
                 AND (deleted > DATE_ADD(%(day_date)s, INTERVAL 1 DAY)
                      OR deleted IS NULL))
               OR (
                 /* started before the day */
                 created < %(day_date)s
                 /* and deleted on the day */
                 AND %(day_date)s < deleted
                 AND deleted < DATE_ADD(%(day_date)s, INTERVAL 1 DAY)))
              /* and a UoM project */
              AND organisation LIKE '%%melb%%'
              /* that is not personal */
              AND personal = 0
            GROUP BY project_id
            ORDER BY project_id, vcpus DESC;
        """, {'day_date': day_date.strftime("%Y-%m-%d")})
        return self._db_cur.fetchall()

    def get_top_twenty_projects(self, day_date):
        self._db_cur.execute("""
            SELECT
              '{0}' AS 'date',
              i.project_id,
              SUM(i.vcpus) AS vcpus,
              a.display_name AS tenant_name
            FROM instance i
              LEFT JOIN
              (SELECT
                 id,
                 organisation,
                 display_name
               FROM project t1) a
                ON i.project_id = a.id
            WHERE
              /* (started on the day OR ended on the day OR running through the day)
                  AND not started and stopped on the day AND a unimelb project
               */
              ((i.deleted BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
               OR (i.created BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
               OR (created < '{0}' AND (deleted IS NULL OR deleted > DATE_ADD('{0}', INTERVAL 1 DAY))))
              AND NOT ((i.deleted BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY))
                       AND (i.created BETWEEN '{0}' AND DATE_ADD('{0}', INTERVAL 1 DAY)))
              AND a.organisation LIKE '%melb%'
            GROUP BY i.project_id
            ORDER BY vcpus DESC
            LIMIT 20;
        """.format(day_date.strftime("%Y-%m-%d")))
        return self._db_cur.fetchall()

    def get_uom_project_contact_email(self):
        """
        :return: A list of projects and the contact email taken from the
        matching allocation record. All projects where the associated contact
        email is known are returned.

        Notes:
            A join between the project and the user tables:

                SELECT count(*)
                FROM project p
                  LEFT JOIN user u
                    ON p.id = u.default_project
                WHERE organisation LIKE '%melb%'
                    AND email IS NULL;

            returns 427 null email addresses. If we remove the
            'email IS NULL' condition we get 2503, so 1/5th
            are missing.

            If we change the join to only include personal tenancies:

                WHERE organisation LIKE '%melb%' AND personal = 1

            it returns 2076 rows, of which only 1 has a null email address

            If we change the join to exclude personal tenancies:

                WHERE organisation LIKE '%melb%' AND personal = 0

            it returns 427 rows, of which 426 have a null email address.
            So anything that comes through the allocation system does not give
            the user a default project. Essentially a default project is a
            euphemism for a personal tenancy.
        """
        self._db_cur.execute("""
            SELECT
              p.id        AS tenant_uuid,
              contact_email,
              description AS tenant_name
            FROM reporting.project p
              LEFT JOIN allocation a
                ON p.id = a.project_id
            WHERE organisation LIKE '%melb%'
                  AND personal = 0
                  AND contact_email IS NOT NULL;
        """)
        return self._db_cur.fetchall()

    def count_instances_since(self, start_day):
        """
        :return:
            The number of instances launched since start day date.
        """
        self._db_cur.execute("""
            SELECT COUNT(*) AS total
            FROM instance
            WHERE created >= '{0}'
            """.format(start_day.strftime("%Y-%m-%d")))
        return self._db_cur.fetchone()["total"]

    def get_cell_names(self):
        """
        :return:
            The set of the cell names in the reporting database
        """
        result = set()
        self._db_cur.execute("""
          SELECT DISTINCT cell_name
          FROM instance;
          """)
        result_set = self._db_cur.fetchall()
        for row in result_set:
            result.add(row['cell_name'] if row['cell_name'] else 'NULL')
        return result

    def get_private_cell_data(self, day_date):
        self._db_cur.execute("""
            SELECT
              count(*)   AS instances,
              SUM(vcpus) AS vcpus,
              project_id,
              organisation,
              display_name
            FROM instance i
              LEFT JOIN
              (SELECT
                 id,
                 organisation,
                 display_name
               FROM reporting.project t1) a
                ON i.project_id = a.id
            WHERE
              cell_name = 'nectar!qh2-uom'
              # and running trough the day
              AND (created < '{0}' AND
                  (deleted IS NULL OR deleted > DATE_ADD('{0}', INTERVAL 1 DAY)))
            GROUP BY project_id
            ORDER BY instances DESC;
        """.format(day_date.strftime("%Y-%m-%d")))
        return self._db_cur.fetchall()
