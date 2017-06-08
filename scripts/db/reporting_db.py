import MySQLdb

from reports_beta.settings import UOM_PRIVATE_CELL, UOM_CELL_NAMES
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
        query = """
            SELECT COUNT(DISTINCT r.created_by) AS in_both
            FROM instance l
              LEFT JOIN instance r
                ON l.created_by = r.created_by
            WHERE (((l.deleted BETWEEN %(day_date)s AND DATE_ADD(%(day_date)s, INTERVAL 1 DAY))
                  OR (l.created BETWEEN %(day_date)s AND DATE_ADD(%(day_date)s, INTERVAL 1 DAY))
                  OR (l.created < %(day_date)s AND (l.active OR l.deleted > DATE_ADD(%(day_date)s, INTERVAL 1 DAY))))
              AND l.cell_name IN %(cell_names)s
              AND l.project_id IN (SELECT DISTINCT id
                                    FROM project
                                    WHERE organisation LIKE '%%melb%%'))
              AND (((r.deleted BETWEEN %(day_date)s AND DATE_ADD(%(day_date)s, INTERVAL 1 DAY))
                  OR (r.created BETWEEN %(day_date)s AND DATE_ADD(%(day_date)s, INTERVAL 1 DAY))
                  OR (r.created < %(day_date)s AND (r.active OR r.deleted > DATE_ADD(%(day_date)s, INTERVAL 1 DAY))))
                AND r.cell_name NOT IN %(cell_names)s
                AND r.project_id IN (SELECT DISTINCT id
                                     FROM project
                                     WHERE organisation LIKE '%%melb%%'));
        """
        self._db_cur.execute(query,
                             {'day_date': day_date.strftime("%Y-%m-%d"),
                              'cell_names': tuple(UOM_CELL_NAMES)})
        return self._db_cur.fetchone()["in_both"]

    def get_all_outside(self, day_date):
        query = """
            SELECT COUNT(DISTINCT created_by) AS uom_users_outside_uom
            FROM instance
            WHERE
              (((deleted BETWEEN %(day_date)s AND DATE_ADD(%(day_date)s, INTERVAL 1 DAY))
                OR
                (created BETWEEN %(day_date)s AND DATE_ADD(%(day_date)s, INTERVAL 1 DAY))
                OR (created < %(day_date)s
                    AND
                    (active OR deleted > DATE_ADD(%(day_date)s, INTERVAL 1 DAY))))
               AND cell_name NOT IN %(cell_names)s
               AND project_id IN (SELECT DISTINCT id
                                  FROM project
                                  WHERE organisation LIKE '%%melb%%'));
        """
        self._db_cur.execute(query,
                             {'day_date': day_date.strftime("%Y-%m-%d"),
                              'cell_names': tuple(UOM_CELL_NAMES)})
        return self._db_cur.fetchone()["uom_users_outside_uom"]

    def get_elsewhere_only(self, day_date):
        query = """
            SELECT COUNT(DISTINCT created_by) AS elsewhere_only
            FROM instance
            WHERE
              ((deleted BETWEEN %(day_date)s AND DATE_ADD(%(day_date)s, INTERVAL 1 DAY))
                  OR (created BETWEEN %(day_date)s AND DATE_ADD(%(day_date)s, INTERVAL 1 DAY))
                  OR (created < %(day_date)s AND (active OR deleted > DATE_ADD(%(day_date)s, INTERVAL 1 DAY))))
              AND cell_name NOT IN %(cell_names)s
              AND project_id IN (SELECT DISTINCT id
                                 FROM project
                                 WHERE organisation LIKE '%%melb%%')
              /* and not running any instances in melbourne on the day */
              AND created_by NOT IN (
                 SELECT DISTINCT created_by
                 FROM instance
                 WHERE
                   ((deleted BETWEEN %(day_date)s AND DATE_ADD(%(day_date)s, INTERVAL 1 DAY))
                        OR (created BETWEEN %(day_date)s AND DATE_ADD(%(day_date)s, INTERVAL 1 DAY))
                        OR (created < %(day_date)s AND (active OR deleted > DATE_ADD(%(day_date)s, INTERVAL 1 DAY))))
                   AND cell_name IN %(cell_names)s
                   AND project_id IN (SELECT DISTINCT id
                                      FROM project
                                      WHERE organisation LIKE '%%melb%%'));
        """
        self._db_cur.execute(query,
                             {'day_date': day_date.strftime("%Y-%m-%d"),
                              'cell_names': tuple(UOM_CELL_NAMES)})
        return self._db_cur.fetchone()["elsewhere_only"]

    def get_uom_only(self, day_date):
        query = """
            SELECT COUNT(DISTINCT created_by) AS UoM_only
            FROM instance
            WHERE
              ((deleted BETWEEN %(day_date)s AND DATE_ADD(%(day_date)s, INTERVAL 1 DAY))
                OR (created BETWEEN %(day_date)s AND DATE_ADD(%(day_date)s, INTERVAL 1 DAY))
                OR (created < %(day_date)s AND (active OR deleted > DATE_ADD(%(day_date)s, INTERVAL 1 DAY))))
              AND cell_name IN %(cell_names)s
              AND project_id IN (SELECT DISTINCT id
                                 FROM project
                                 WHERE organisation LIKE '%%melb%%')
              /* and not running any instances in any other zone on the day */
              AND created_by NOT IN (
                SELECT DISTINCT created_by
                FROM instance
                WHERE
                    ((deleted BETWEEN %(day_date)s AND DATE_ADD(%(day_date)s, INTERVAL 1 DAY))
                    OR (created BETWEEN %(day_date)s AND DATE_ADD(%(day_date)s, INTERVAL 1 DAY))
                    OR (created < %(day_date)s AND (active OR deleted > DATE_ADD(%(day_date)s, INTERVAL 1 DAY))))
                    AND cell_name NOT IN %(cell_names)s
                    AND project_id IN (SELECT DISTINCT id
                                      FROM project
                                      WHERE organisation LIKE '%%melb%%'));
        """
        self._db_cur.execute(query,
                             {'day_date': day_date.strftime("%Y-%m-%d"),
                              'cell_names': tuple(UOM_CELL_NAMES)})
        return self._db_cur.fetchone()["UoM_only"]

    def get_count_of_others_at_uom(self, day_date):
        query = """
            SELECT COUNT(DISTINCT created_by) AS others_at_uom
            FROM instance
            WHERE
              /* stopped on the day */
              ((deleted BETWEEN %(day_date)s AND DATE_ADD(%(day_date)s, INTERVAL 1 DAY))
                  /* started on the day */
                  OR (created BETWEEN %(day_date)s AND DATE_ADD(%(day_date)s, INTERVAL 1 DAY))
                  /* running through the day */
                  OR (created < %(day_date)s AND (active OR deleted > DATE_ADD(%(day_date)s, INTERVAL 1 DAY))))
              AND cell_name IN %(cell_names)s
              AND project_id NOT IN (SELECT id
                                     FROM project
                                     WHERE organisation LIKE '%%melb%%');
        """
        self._db_cur.execute(query,
                             {'day_date': day_date.strftime("%Y-%m-%d"),
                              'cell_names': tuple(UOM_CELL_NAMES)})
        # print(self._db_cur._last_executed)
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
                      OR active))
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
              %(day_date)s AS 'date',
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
              ((i.deleted BETWEEN %(day_date)s AND DATE_ADD(%(day_date)s, INTERVAL 1 DAY))
               OR (i.created BETWEEN %(day_date)s AND DATE_ADD(%(day_date)s, INTERVAL 1 DAY))
               OR (created < %(day_date)s AND (active OR deleted > DATE_ADD(%(day_date)s, INTERVAL 1 DAY))))
              AND NOT ((i.deleted BETWEEN %(day_date)s AND DATE_ADD(%(day_date)s, INTERVAL 1 DAY))
                       AND (i.created BETWEEN %(day_date)s AND DATE_ADD(%(day_date)s, INTERVAL 1 DAY)))
              AND a.organisation LIKE '%%melb%%'
            GROUP BY i.project_id
            ORDER BY vcpus DESC
            LIMIT 20;
        """, {'day_date': day_date.strftime("%Y-%m-%d")})
        return self._db_cur.fetchall()

    def get_uom_project_contact_details(self):
        """
        :return: a list of project and contact details taken from the
            matching allocation record. All projects where the associated
            contact email is known are returned.
        :rtype: list

        :notes:
            A join between the project and the user tables: ::

                SELECT count(*)
                FROM project p
                  LEFT JOIN user u
                    ON p.id = u.default_project
                WHERE organisation LIKE '%melb%'
                    AND email IS NULL;

            returns 427 null email addresses. If we remove the
            ``email IS NULL`` condition we get 2503, so about 1/5th
            are missing.

            If we change the join to only include personal tenancies: ::

                WHERE organisation LIKE '%melb%' AND personal = 1

            it returns 2076 rows, of which only 1 has a null email address

            If we change the join to exclude personal tenancies: ::

                WHERE organisation LIKE '%melb%' AND personal = 0

            it returns 427 rows, of which 426 have a null email address.
            So anything that comes through the allocation system does not give
            the user a default project. Essentially a default project is a
            euphemism for a personal tenancy.
        """
        self._db_cur.execute("""
            SELECT
                  p.id        AS tenant_uuid,
                  chief_investigator,  # can be null
                  contact_email, 
                  (CASE 
                   WHEN for_percentage_2 >= for_percentage_1 AND
                        for_percentage_2 >= for_percentage_3
                     THEN field_of_research_2
                   WHEN for_percentage_3 >= for_percentage_1 AND
                        for_percentage_3 >= for_percentage_2
                     THEN field_of_research_3
                   ELSE field_of_research_1
                   END)       AS field_of_research,
                  end_date,
                  description AS tenant_name,  # TODO This should be kept as description!
                  quota_instances, 
                  quota_vcpus, 
                  quota_memory, 
                  quota_volume_total, 
                  quota_snapshot, 
                  quota_volume_count
            FROM reporting.project p
                LEFT JOIN allocation a
                  ON p.id = a.project_id
            WHERE organisation LIKE '%melb%'
                  AND personal = 0
                  AND contact_email IS NOT NULL
                  AND quota_instances IS NOT NULL
                  AND quota_instances > 0
                  ;
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
        query = """
            SELECT
              count(*)   AS instances,
              SUM(i.vcpus) AS vcpus,
              i.project_id,
              a.organisation,
              a.display_name
            FROM instance i
              LEFT JOIN reporting.project a
                ON i.project_id = a.id
            WHERE
              i.cell_name = %(private_cell)s
              # and running trough the day
              AND (i.created < %(day_date)s
                   AND (i.active
                        OR i.deleted > DATE_ADD(%(day_date)s, INTERVAL 1 DAY)))
            GROUP BY i.project_id
            ORDER BY instances DESC;
        """
        self._db_cur.execute(query, {'day_date': day_date.strftime("%Y-%m-%d"),
                                     'private_cell': UOM_PRIVATE_CELL})
        # print(self._db_cur._last_executed)
        return self._db_cur.fetchall()

    def get_projects_active(self, from_date, to_date):
        query = """
          SELECT count(DISTINCT project_id) AS active
          FROM instance
          WHERE
              (%(start)s <= deleted AND deleted < %(end)s + INTERVAL 1 DAY)
              OR
              (%(start)s <= created AND created <= %(end)s + INTERVAL 1 DAY)
              OR (instance.active
                  AND created <= %(end)s + INTERVAL 1 DAY);
        """
        self._db_cur.execute(query, {'start': from_date.strftime("%Y-%m-%d"),
                                     'end': to_date.strftime("%Y-%m-%d")})
        return self._db_cur.fetchone()['active']

    def get_admins_active(self, from_date, to_date):
        query = """
          SELECT COUNT(DISTINCT (u.email)) AS active
          FROM instance i
            LEFT JOIN user u ON i.created_by = u.id
          WHERE ((%(start)s <= deleted AND deleted < %(end)s + INTERVAL 1 DAY)
           OR (%(start)s <= created AND created < %(end)s + INTERVAL 1 DAY)
           OR ((created < %(start)s) AND
               (active OR %(end)s + INTERVAL 1 DAY <= deleted)));
        """
        self._db_cur.execute(query, {'start': from_date.strftime("%Y-%m-%d"),
                                     'end': to_date.strftime("%Y-%m-%d")})
        return self._db_cur.fetchone()['active']

    def get_uom_projects_active(self, from_date, to_date):
        query = """
          SELECT count(DISTINCT project_id) AS active
          FROM instance
          WHERE
          ((%(start)s <= deleted AND deleted < %(end)s + INTERVAL 1 DAY)
            OR (%(start)s <= created AND created < %(end)s + INTERVAL 1 DAY)
            OR (created < %(start)s) AND 
              (active OR %(end)s + INTERVAL 1 DAY <= deleted))
          AND project_id IN (
              SELECT id
              FROM project
              WHERE organisation LIKE '%%melb%%' AND personal = 0);
        """
        self._db_cur.execute(query, {'start': from_date.strftime("%Y-%m-%d"),
                                     'end': to_date.strftime("%Y-%m-%d")})
        return self._db_cur.fetchone()['active']

    def get_all_uom_projects_active(self, from_date, to_date):
        query = """
          SELECT count(DISTINCT project_id) AS active
          FROM instance i
            LEFT JOIN project p ON i.project_id = p.id
          WHERE p.organisation LIKE '%%melb%%'
            AND
             ((%(start)s <= deleted AND deleted < %(end)s + INTERVAL 1 DAY)
               OR (%(start)s <= created AND created < %(end)s + INTERVAL 1 DAY)
               OR ((created < %(start)s) AND
                   (active OR %(end)s + INTERVAL 1 DAY <= deleted)));
        """
        self._db_cur.execute(query, {'start': from_date.strftime("%Y-%m-%d"),
                                     'end': to_date.strftime("%Y-%m-%d")})
        return self._db_cur.fetchone()['active']

    def get_projects_active_with_uom_participation(self, from_date, to_date):
        query = """
          SELECT count(DISTINCT project_id) AS active
          FROM instance i
            LEFT JOIN user u ON i.created_by = u.id
          WHERE u.email LIKE '%%melb%%'
            AND
            ((%(start)s <= deleted AND deleted < %(end)s + INTERVAL 1 DAY)
              OR (%(start)s <= created AND created < %(end)s + INTERVAL 1 DAY)
              OR ((created < %(start)s) AND
                  (active OR %(end)s + INTERVAL 1 DAY <= deleted)));
        """
        self._db_cur.execute(query, {'start': from_date.strftime("%Y-%m-%d"),
                                     'end': to_date.strftime("%Y-%m-%d")})
        return self._db_cur.fetchone()['active']

    def get_uom_users_active(self, from_date, to_date):
        """
        We could combine the above and this into one: something along the lines
        of:
        SELECT
            count(DISTINCT project_id) AS projects,
            count(DISTINCT created_by) AS creators
        FROM instance i
            LEFT JOIN user u ON i.created_by = u.id
        WHERE u.email LIKE '%%melb%%'
            AND
         ((%(start)s <= deleted AND deleted < %(end)s + INTERVAL 1 DAY)
       OR (%(start)s <= created AND created < %(end)s + INTERVAL 1 DAY)
       OR ((created < %(start)s) AND
           (active OR %(end)s + INTERVAL 1 DAY <= deleted)));
        """
        query = """
          SELECT count(DISTINCT created_by) AS active
          FROM instance i
            LEFT JOIN user u ON i.created_by = u.id
          WHERE u.email LIKE '%%melb%%'
            AND
              ((%(start)s <= deleted AND deleted < %(end)s + INTERVAL 1 DAY)
                OR (%(start)s <=created AND created < %(end)s + INTERVAL 1 DAY)
                OR ((created < %(start)s) AND
                  (active OR %(end)s + INTERVAL 1 DAY <= deleted)));
        """
        self._db_cur.execute(query, {'start': from_date.strftime("%Y-%m-%d"),
                                     'end': to_date.strftime("%Y-%m-%d")})
        return self._db_cur.fetchone()['active']

    def get_email_of_active_uom_users(self, from_date, to_date):
        query = """
            SELECT DISTINCT u.email
            FROM instance i
              LEFT JOIN user u ON i.created_by = u.id
            WHERE u.email LIKE '%%melb%%'
              AND
              ((%(start)s <= deleted AND deleted < %(end)s + INTERVAL 1 DAY)
               OR (%(start)s <= created AND created < %(end)s + INTERVAL 1 DAY)
               OR ((created < %(start)s) AND
                   (active OR %(end)s + INTERVAL 1 DAY <= deleted)));
        """
        self._db_cur.execute(query, {'start': from_date.strftime("%Y-%m-%d"),
                                     'end': to_date.strftime("%Y-%m-%d")})
        return self._db_cur.fetchall()

    def get_core_hours(self, from_date, to_date):
        query = """
            SELECT
              project.id                     AS project_id,
              project_name                   AS project_name,
              IFNULL(chief_investigator, '') AS ci,
              contact_email                  AS owner,
              i.vcpu_hours                   AS vcpu_hours
            FROM allocation
              LEFT JOIN project ON allocation.project_id = project.id
              LEFT JOIN (
                  SELECT
                    project_id,
                    ROUND(IFNULL(
                              SUM(vcpus * TIMESTAMPDIFF(SECOND,
                                        # the start date, if created is < the start date
                                        IF(created < %(start)s, %(start)s, created),
                                        # the deleted date can be be before the end date, after the end date or null
                                        # so if deleted is null, take now else take the end date.
                                        # if that 'deleted' date is greater thant the end date,
                                        #   then take the end date
                                        #   else take the 'deleted' date (works if now < end date)
                                        IF(IF(deleted IS NULL, NOW(), deleted) > %(end)s + INTERVAL 1 DAY,
                                           %(end)s + INTERVAL 1 DAY, IF(deleted IS NULL, NOW(), deleted))))
                              / 3600, 0)) AS vcpu_hours
                  FROM instance
                  WHERE project_id IS NOT NULL
                        # where created before the end date
                        AND created < %(end)s + INTERVAL 1 DAY
                        # and deleted after the start date
                        AND (deleted IS NULL OR deleted > %(start)s)
                        # i.e.: was active at any point during the start and end date
                  GROUP BY project_id
                        ) i ON i.project_id = allocation.project_id
            WHERE project.organisation LIKE '%%melb%%'
                  AND vcpu_hours > 0
            ORDER BY vcpu_hours DESC;
        """
        self._db_cur.execute(query, {'start': from_date.strftime("%Y-%m-%d"),
                                     'end': to_date.strftime("%Y-%m-%d")})
        return self._db_cur.fetchall()
