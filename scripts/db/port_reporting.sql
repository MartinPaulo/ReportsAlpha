/**
 * http://stackoverflow.com/questions/19946526/how-pass-dynamic-parameter-in-mysql-view
 * http://stackoverflow.com/questions/2281890/can-i-create-view-with-parameter-in-mysql
 */

/**
 * Cloud allocated (can't do on a cumulative per day basis, as date created/modified isn't tracked).
 * so we need to copy the data across from the allocation table.
 */


-- The allocations that were awarded
CREATE TABLE IF NOT EXISTS allocation (
  project_id    VARCHAR(36) COMMENT 'Of the project that was spawned by this allocation',
  contact_email VARCHAR(75) COMMENT 'Who is the contact person for this allocation',
  modified_time DATETIME COMMENT 'The last time the allocation was modified',
  PRIMARY KEY (project_id)
)
  COMMENT 'The allocations that were awarded';

/* to get the first cut of the data we want the rows with the max modified time */
SELECT
  tenant_uuid AS project_id,
  /* This isn't unique*/
  contact_email,
  modified_time
FROM dashboard.rcallocation_allocationrequest t1
WHERE
  tenant_uuid > ''
  AND modified_time = (
    SELECT MAX(modified_time)
    FROM dashboard.rcallocation_allocationrequest t2
    WHERE t2.tenant_uuid = t1.tenant_uuid)
ORDER BY modified_time;


/* following returns the allocations that were approved or modified on the given day */
SELECT
  tenant_uuid AS project_id,
  modified_time,
  contact_email
FROM rcallocation_allocationrequest t1
WHERE
  tenant_uuid > ''
  AND modified_time = (
    SELECT MAX(modified_time)
    FROM rcallocation_allocationrequest t2
    WHERE t2.tenant_uuid = t1.tenant_uuid
          /* If using a days granularity, risk that we can miss the last few of the previous day */
          /* So should probly be where modified_time >= last_update */
          AND modified_time BETWEEN '2016-06-23' AND DATE_ADD('2016-06-23',
                                                              INTERVAL 1 DAY));
/* so these results can be used to update or insert into the original table*/

/*
INSERT INTO table (id, name, age)
VALUES(1, "A", 19)
ON DUPLICATE KEY UPDATE name="A", age=19 */

SELECT
  id /* used for the join */,
  quota_vcpus /* cores from allocation? */,
  display_name /* just because */,
  organization /* so we can refine by organisation */,
  modified_time /* and get the value on a given day*/,
  end_date /* is it finished? */,
  enabled /* is the project still active */
    contact_email /* used to get the faculty at UoM */
FROM project p
  LEFT JOIN (
              SELECT
                project_id,
                contact_email
              FROM allocation) a
    ON p.id = a.project_id
       AND personal = 0
ORDER BY id;

/* also: data between user and project seems somewhat garbage :( */

SELECT count(*)
FROM user;
/* 8520 */

SELECT count(*)
FROM user
WHERE email IS NULL;
/* 0 */

SELECT count(*)
FROM project;
/* 10484 */

SELECT count(*)
FROM project
WHERE organisation IS NULL;
/* 282 */

SELECT COUNT(DISTINCT (id))
FROM project
WHERE NOT EXISTS(
    SELECT NULL
    FROM user
    WHERE user.default_project = project.id
);
/* 1964 projects without users? */

SELECT COUNT(id)
FROM project
WHERE project.id IN (
  SELECT default_project
  FROM user
  WHERE user.default_project = project.id
);
/* 8520 projects with users, as expected...*/

SELECT
  p.id,
  a.contact_email,
  a.submit_date
FROM project p
  LEFT JOIN (SELECT DISTINCT
               (tenant_uuid),
               contact_email,
               submit_date
             FROM dashboard.rcallocation_allocationrequest) a
    ON p.id = a.tenant_uuid
WHERE NOT EXISTS(SELECT NULL
                 FROM user
                 WHERE user.default_project = p.id);
/* 365 null entries but the rest match. and the empty ones are possibly caused by the either being
before the allocation system, or after the snapshot was taken */

/**
 * Top twenty from unimelb on a given date (2016-07-10)
 */
SELECT
  '2016-03-10' AS 'date',
  i.project_id,
  SUM(i.vcpus)    vcpus,
  a.display_name
FROM reporting.instance i
  LEFT JOIN
  (SELECT
     id,
     organisation,
     display_name
   FROM reporting.project t1) a
    ON i.project_id = a.id
WHERE
  /* (started on the day OR ended on the day OR running through the day)
      AND not started and stopped on the day AND a unimelb project
   */
  ((i.deleted BETWEEN '2016-03-10' AND DATE_ADD('2016-03-10', INTERVAL 1 DAY))
   OR
   (i.created BETWEEN '2016-03-10' AND DATE_ADD('2016-03-10', INTERVAL 1 DAY))
   OR (i.created < '2016-03-10' AND (i.deleted IS NULL OR i.deleted > DATE_ADD(
      '2016-03-10', INTERVAL 1 DAY))))
  AND NOT (
    (i.deleted BETWEEN '2016-03-10' AND DATE_ADD('2016-03-10', INTERVAL 1 DAY))
    AND (i.created BETWEEN '2016-03-10' AND DATE_ADD('2016-03-10', INTERVAL 1
                                                     DAY)))
  AND a.organisation LIKE '%melb%' /* OR a.organisation LIKE '%mac%'*/
GROUP BY i.project_id
ORDER BY vcpus DESC
LIMIT 20;

SELECT
  '2016-03-10' AS 'date',
  i.project_id,
  SUM(i.vcpus)    vcpus,
  a.display_name
FROM reporting.instance i
  LEFT JOIN
  (SELECT
     id,
     organisation,
     display_name
   FROM reporting.project t1) a
    ON i.project_id = a.id
WHERE
  /* (started on the day OR ended on the day OR running through the day)
      AND not started and stopped on the day AND a unimelb project
   */
  ((i.deleted BETWEEN '2016-03-10' AND DATE_ADD('2016-03-10', INTERVAL 1 DAY))
   OR
   (i.created BETWEEN '2016-03-10' AND DATE_ADD('2016-03-10', INTERVAL 1 DAY))
   OR (i.created < '2016-03-10' AND i.deleted IS NULL))
  AND NOT (
    (i.deleted BETWEEN '2016-03-10' AND DATE_ADD('2016-03-10', INTERVAL 1 DAY))
    AND (i.created BETWEEN '2016-03-10' AND DATE_ADD('2016-03-10', INTERVAL 1
                                                     DAY)))
  AND a.organisation LIKE '%melb%' /* OR a.organisation LIKE '%mac%'*/
GROUP BY i.project_id
ORDER BY vcpus DESC
LIMIT 20;

/*
I'm not sure why your where clause in that example select is so complex - can't you just say
 "created_at <= date('2016-07-10') and deleted_at > date('2016-07-10')"?

 Present sub selects as views...
*/

/**
 * Cloud used by unimelb on a given date (2016-07-10): same as top 20, but
 * without limit and with private projects removed.
 * (as we don't yet know the faculty of personal projects)
 * This also banks on us doing post matching of a project to a faculty
 */
SELECT
  '2016-07-10' AS 'date',
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
  ((i.deleted BETWEEN '2016-07-10' AND DATE_ADD('2016-07-10', INTERVAL 1 DAY))
   OR
   (i.created BETWEEN '2016-07-10' AND DATE_ADD('2016-07-10', INTERVAL 1 DAY))
   OR (i.deleted IS NULL AND i.created < '2016-07-10'))
  AND NOT (
    (i.deleted BETWEEN '2016-07-10' AND DATE_ADD('2016-07-10', INTERVAL 1 DAY))
    AND (i.created BETWEEN '2016-07-10' AND DATE_ADD('2016-07-10', INTERVAL 1
                                                     DAY)))
  AND a.organisation LIKE '%melb%' AND a.personal = 0
GROUP BY i.project_id
ORDER BY vcpus DESC;

/**
 * Find out which user email is associated with each project
 */


SELECT
  id,
  /* the project id*/
  email /* used to get the faculty */
FROM project p
  LEFT JOIN (SELECT
               default_project,
               email
             FROM user) u
    ON p.id = u.default_project
WHERE organisation LIKE '%melb%'
      AND personal = 0
ORDER BY id;
/* returns 427 rows, of which 426 have null email address */
/* so anything that comes through the allocation system does not give the user a default project */
/* so default project is a euphemism for personal tenancy */



SELECT
  p.id,
  a.contact_email
FROM reporting.project p
  LEFT JOIN (SELECT
               project_id,
               contact_email
             FROM allocation) a
    ON p.id = a.project_id
WHERE p.organisation LIKE '%melb%'
      AND p.personal = 0
      AND a.contact_email IS NOT NULL;
/* returns 435 of which 48 are null. So just over 10% is not known */

/**
 * Calculate the cloud active count
 */
SELECT COUNT(DISTINCT created_by) AS others_at_uom
FROM instance
WHERE
  ((deleted BETWEEN '2016-06-27' AND DATE_ADD('2016-06-27', INTERVAL 1 DAY))
   /* stopped on the day */
   OR (created BETWEEN '2016-06-27' AND DATE_ADD('2016-06-27', INTERVAL 1 DAY))
   /* started on the day */
   OR (deleted IS NULL AND created < '2016-06-27'))
  /* running through the day */
  AND cell_name IN
      ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2')
  AND project_id NOT IN (SELECT id
                         FROM project
                         WHERE organisation LIKE '%melb%');
/* 76 vs 564*/

SELECT COUNT(DISTINCT created_by) AS UoM_only
FROM instance
WHERE
  ((deleted BETWEEN '2016-06-27' AND DATE_ADD('2016-06-27', INTERVAL 1 DAY))
   OR (created BETWEEN '2016-06-27' AND DATE_ADD('2016-06-27', INTERVAL 1 DAY))
   OR (deleted IS NULL AND created < '2016-06-27'))
  AND cell_name IN
      ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2')
  /* and not running any instances in any other zone on the day */
  AND created_by NOT IN (SELECT DISTINCT created_by
                         FROM instance
                         WHERE
                           ((deleted BETWEEN '2016-06-27' AND DATE_ADD(
                               '2016-06-27', INTERVAL 1 DAY))
                            OR (created BETWEEN '2016-06-27' AND DATE_ADD(
                               '2016-06-27', INTERVAL 1 DAY))
                            OR (deleted IS NULL AND created < '2016-06-27'))
                           AND cell_name NOT IN
                               ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2')
                           AND project_id IN (SELECT DISTINCT id
                                              FROM project
                                              WHERE
                                                organisation LIKE '%melb%'))
  AND project_id IN (SELECT DISTINCT id
                     FROM project
                     WHERE organisation LIKE '%melb%');

/* 124 vs 330*/

SELECT COUNT(DISTINCT created_by) AS elsewhere_only
FROM instance
WHERE
  ((deleted BETWEEN '2016-06-28' AND DATE_ADD('2016-06-28', INTERVAL 1 DAY))
   OR (created BETWEEN '2016-06-28' AND DATE_ADD('2016-06-28', INTERVAL 1 DAY))
   OR (deleted IS NULL AND created < '2016-06-28'))
  AND cell_name NOT IN
      ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2')
  /* and not running any instances in melbourne on the day */
  AND created_by NOT IN (SELECT DISTINCT created_by
                         FROM instance
                         WHERE
                           ((deleted BETWEEN '2016-06-28' AND DATE_ADD(
                               '2016-06-28', INTERVAL 1 DAY))
                            OR (created BETWEEN '2016-06-28' AND DATE_ADD(
                               '2016-06-28', INTERVAL 1 DAY))
                            OR (deleted IS NULL AND created < '2016-06-28'))
                           AND cell_name IN
                               ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2')
                           AND project_id IN (SELECT DISTINCT id
                                              FROM project
                                              WHERE
                                                organisation LIKE '%melb%'))
  AND project_id IN (SELECT DISTINCT id
                     FROM project
                     WHERE organisation LIKE '%melb%');

/* 93 vs 272 */

SELECT COUNT(DISTINCT r.created_by) AS in_both
FROM instance l
  LEFT JOIN instance r
    ON l.created_by = r.created_by
WHERE
  (((l.deleted BETWEEN '2016-06-28' AND DATE_ADD('2016-06-28', INTERVAL 1 DAY))
    OR
    (l.created BETWEEN '2016-06-28' AND DATE_ADD('2016-06-28', INTERVAL 1 DAY))
    OR (l.deleted IS NULL AND l.created < '2016-06-27'))
   AND l.cell_name IN
       ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2')
   AND l.project_id IN (SELECT DISTINCT id
                        FROM project
                        WHERE organisation LIKE '%melb%'))
  AND
  (((r.deleted BETWEEN '2016-06-27' AND DATE_ADD('2016-06-27', INTERVAL 1 DAY))
    OR
    (r.created BETWEEN '2016-06-27' AND DATE_ADD('2016-06-27', INTERVAL 1 DAY))
    OR (r.deleted IS NULL AND r.created < '2016-06-27'))
   AND r.cell_name NOT IN
       ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2')
   AND r.project_id IN (SELECT DISTINCT id
                        FROM project
                        WHERE organisation LIKE '%melb%'));

/* 28 vs 108*/
/* depressing: 2016-06-27	330	272	109	564 */

SELECT count(*)
FROM instance
WHERE created BETWEEN '2016-06-27' AND DATE_ADD('2016-06-27', INTERVAL 1 DAY);
/* 728 */
SELECT count(*)
FROM nova.instances
WHERE
  created_at BETWEEN '2016-06-27' AND DATE_ADD('2016-06-27', INTERVAL 1 DAY);
/* 728 */


SELECT count(*) AS in_uom
FROM instance
WHERE
  ((deleted BETWEEN '2016-06-27' AND DATE_ADD('2016-06-27', INTERVAL 1 DAY)) OR
   (created BETWEEN '2016-06-27' AND DATE_ADD('2016-06-27', INTERVAL 1 DAY)) OR
   (deleted IS NULL AND created < '2016-06-27'))
  AND availability_zone LIKE '%melb%';
/*  1197 */

SELECT COUNT(*) AS in_uom
FROM nova.instances
WHERE
  ((deleted_at BETWEEN '2016-06-27' AND DATE_ADD('2016-06-27', INTERVAL 1 DAY))
   /* stopped on the day */
   OR
   (created_at BETWEEN '2016-06-27' AND DATE_ADD('2016-06-27', INTERVAL 1 DAY))
   /* started on the day */
   OR (deleted_at IS NULL AND created_at < '2016-06-27'))
  /* running through the day */
  AND availability_zone LIKE '%melb%';
/* 994: so availability zone isn't the same between the two tables? */

SELECT COUNT(*) AS in_uom
FROM nova.instances
WHERE ((deleted_at BETWEEN '2016-06-27' AND DATE_ADD('2016-06-27', INTERVAL 1
                                                     DAY)) OR
       (created_at BETWEEN '2016-06-27' AND DATE_ADD('2016-06-27', INTERVAL 1
                                                     DAY)) OR
       (deleted_at IS NULL AND created_at < '2016-06-27')) AND
      cell_name IN
      ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2');
/* 2335 which is close as I can make out to being correct... */

SELECT COUNT(*) AS in_uom
FROM nova.instances
WHERE ((deleted_at BETWEEN '2016-06-27' AND DATE_ADD('2016-06-27', INTERVAL 1
                                                     DAY)) OR
       (created_at BETWEEN '2016-06-27' AND DATE_ADD('2016-06-27', INTERVAL 1
                                                     DAY)) OR
       (deleted_at IS NULL AND created_at < '2016-06-27')) AND
      cell_name IN
      ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2') AND
      availability_zone IS NULL;
/* 1343 lost due to nullity of availability_zone. BTW: 2335 - 994 = 1341 so 2 out? */
/* difference is that cells don't return the instance running in the 'melbourne' az */
/* there are two, with no cell name: b493e089-c9fa-4b86-a7e1-92338772f19e and cda961d2-71f8-433b-84ae-b99c1dab2b81 */
/* Under both my sql and the reporting sql these two instances are reported as running: even though they never launched */

SELECT
  value,
  count(*)
FROM nova.instance_system_metadata
WHERE `key` = 'availability_zone'
GROUP BY value;

SELECT COUNT(vcpus) AS vcpu_count
FROM instance
WHERE
  ((deleted BETWEEN '2016-06-28' AND DATE_ADD('2016-06-28', INTERVAL 1 DAY))
   /* stopped on the day */
   OR (created BETWEEN '2016-06-28' AND DATE_ADD('2016-06-28', INTERVAL 1 DAY))
   /* started on the day */
   OR (deleted IS NULL AND created < '2016-06-28'))
  /* running through the day */
  AND cell_name IN
      ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2')
  AND project_id NOT IN (SELECT id
                         FROM project
                         WHERE organisation LIKE '%melb%');

/*
+------------+
| vcpu_count |
+------------+
|        980 |
+------------+
*/

SELECT COUNT(DISTINCT r.created_by) AS in_both
FROM instance l
  LEFT JOIN instance r
    ON l.created_by = r.created_by
WHERE
  (((l.deleted BETWEEN '2016-03-10' AND DATE_ADD('2016-03-10', INTERVAL 1 DAY))
    OR
    (l.created BETWEEN '2016-03-10' AND DATE_ADD('2016-03-10', INTERVAL 1 DAY))
    OR (l.created < '2016-03-10' AND (l.deleted IS NULL OR l.deleted >
                                                           DATE_ADD(
                                                               '2016-03-10',
                                                               INTERVAL 1
                                                               DAY))))
   AND l.cell_name IN
       ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2')
   AND l.project_id IN (SELECT DISTINCT id
                        FROM project
                        WHERE organisation LIKE '%melb%'))
  AND
  (((r.deleted BETWEEN '2016-03-10' AND DATE_ADD('2016-03-10', INTERVAL 1 DAY))
    OR
    (r.created BETWEEN '2016-03-10' AND DATE_ADD('2016-03-10', INTERVAL 1 DAY))
    OR (r.created < '2016-03-10' AND (r.deleted IS NULL OR r.deleted >
                                                           DATE_ADD(
                                                               '2016-03-10',
                                                               INTERVAL 1
                                                               DAY))))
   AND r.cell_name NOT IN
       ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2')
   AND r.project_id IN (SELECT DISTINCT id
                        FROM project
                        WHERE organisation LIKE '%melb%'));

SELECT COUNT(DISTINCT r.created_by) AS in_both
FROM instance l
  LEFT JOIN instance r
    ON l.created_by = r.created_by
WHERE
  ((
     (l.created < '2016-03-10' AND (l.deleted IS NULL OR l.deleted >
                                                         DATE_ADD('2016-03-10',
                                                                  INTERVAL 1
                                                                  DAY)))
     OR
     (l.created BETWEEN '2016-03-10' AND DATE_ADD('2016-03-10', INTERVAL 1 DAY)
      AND (l.deleted IS NULL OR
           l.deleted > DATE_ADD('2016-03-10', INTERVAL 1 DAY)))
     OR
     (l.created < '2016-03-10' AND
      (l.deleted BETWEEN '2016-03-10' AND DATE_ADD('2016-03-10', INTERVAL 1
                                                   DAY))))
   AND l.cell_name IN
       ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2')
   AND l.project_id IN (SELECT DISTINCT id
                        FROM project
                        WHERE organisation LIKE '%melb%'))
  AND
  ((
     (r.created < '2016-03-10' AND (r.deleted IS NULL OR r.deleted >
                                                         DATE_ADD('2016-03-10',
                                                                  INTERVAL 1
                                                                  DAY)))
     OR
     (r.created BETWEEN '2016-03-10' AND DATE_ADD('2016-03-10', INTERVAL 1 DAY)
      AND (r.deleted IS NULL OR
           r.deleted > DATE_ADD('2016-03-10', INTERVAL 1 DAY)))
     OR
     (r.created < '2016-03-10' AND
      (r.deleted BETWEEN '2016-03-10' AND DATE_ADD('2016-03-10', INTERVAL 1
                                                   DAY))))
   AND r.cell_name NOT IN
       ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2')
   AND r.project_id IN (SELECT DISTINCT id
                        FROM project
                        WHERE organisation LIKE '%melb%'));

-- from simon: By the way, I managed to come up with a query that relates
-- project uuids to allocation ids, using the data in keystone where it lists
-- the allocation_id in the extra field

SELECT
  p.id AS tenant_id,
  p.name,
  a.id
FROM (SELECT
        id,
        name,
        replace(
            replace(substring(extra, locate('allocation_id', extra) + 16, 5),
                    '"', ''), '}', '') AS allocation_id,
        extra
      FROM keystone_k.project) AS p
  LEFT JOIN dashboard.rcallocation_allocationrequest AS a
    ON p.allocation_id = a.id
WHERE
  p.name NOT LIKE 'pt-%' AND a.parent_request_id IS NULL AND a.id IS NOT NULL
ORDER BY a.id;


SELECT COUNT(DISTINCT created_by) AS others_at_uom
FROM instance
WHERE
  /* stopped on the day */
  ((deleted BETWEEN '2016-03-10' AND DATE_ADD('2016-03-10', INTERVAL 1 DAY))
   /* started on the day */
   OR (created BETWEEN '2016-03-10' AND DATE_ADD('2016-03-10', INTERVAL 1 DAY))
   /* running through the day */
   OR (created < '2016-03-10' AND
       (deleted IS NULL OR deleted > DATE_ADD('2016-03-10', INTERVAL 1 DAY))))
  AND cell_name IN
      ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2')
  AND project_id NOT IN (SELECT id
                         FROM project
                         WHERE organisation LIKE '%melb%')


SELECT COUNT(DISTINCT created_by) AS others_at_uom
FROM instance
WHERE ((
         (created < '2016-03-10' AND (deleted IS NULL OR deleted >
                                                         DATE_ADD('2016-03-10',
                                                                  INTERVAL 1
                                                                  DAY)))
         OR
         (created BETWEEN '2016-03-10' AND DATE_ADD('2016-03-10', INTERVAL 1
                                                    DAY) AND
          (deleted IS NULL OR
           deleted > DATE_ADD('2016-03-10', INTERVAL 1 DAY)))
         OR
         (created < '2016-03-10' AND
          (deleted BETWEEN '2016-03-10' AND DATE_ADD('2016-03-10', INTERVAL 1
                                                     DAY))))
       AND cell_name IN
           ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2')
       AND project_id NOT IN (SELECT DISTINCT id
                              FROM project
                              WHERE organisation LIKE '%melb%'))

/* BY the way, I managed TO come up WITH a QUERY that relates project uuids
TO allocation ids, USING the DATA IN keystone WHERE it lists the allocation_id
IN the extra field
 */

SELECT
  p.id AS tenant_id,
  p.name,
  a.id
FROM (SELECT
        id,
        name,
        replace(
            replace(substring(extra, locate('allocation_id', extra) + 16, 5),
                    '"', ''), '}', '') AS allocation_id,
        extra
      FROM keystone_k.project) AS p LEFT JOIN
  dashboard.rcallocation_allocationrequest AS a ON p.allocation_id = a.id
WHERE
  p.name NOT LIKE 'pt-%' AND a.parent_request_id IS NULL AND a.id IS NOT NULL
ORDER BY a.id;

#------------------------------------------------------------------------------
# Allocated
#------------------------------------------------------------------------------

SELECT count(*)
FROM project p
WHERE p.personal = 0 AND p.organisation LIKE '%melb%' AND p.enabled = 1;

# +----------+
# | count(*) |
# +----------+
# |      450 |
# +----------+

SELECT sum(quota_vcpus)
FROM project p
WHERE p.personal = 0 AND p.organisation LIKE '%melb%' AND p.enabled = 1;

# +------------------+
# | sum(quota_vcpus) |
# +------------------+
# |            14316 |
# +------------------+

SELECT count(*)
FROM project p
WHERE p.personal = 0 AND p.organisation LIKE '%melb%' AND p.enabled = 1 AND
      p.quota_vcpus IS NULL;

# +----------+
# | count(*) |
# +----------+
# |       10 |
# +----------+

-- Ok: there are projects that are not referenced by the allocation table, so
-- we have to modify the query to deal with null modified times

SELECT
  p.id                     AS tenant_uuid /* used for the join */,
  a.contact_email /* used to get the faculty at UoM */,
  IFNULL(p.quota_vcpus, 2) AS cores /* cores from allocation? */,
  IFNULL(a.modified_time, '2013-12-04') /* and get the value on a given day*/,
  p.display_name           AS tenant_name/* just because */,
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
      AND p.enabled = 1
      AND p.organisation LIKE '%melb%'
      AND (modified_time <= DATE_ADD('2016-09-14', INTERVAL 1 DAY) OR
           modified_time IS NULL)
ORDER BY id;

#------------------------------------------------------------------------------
# Used
#------------------------------------------------------------------------------

SELECT SUM(i.vcpus) AS vcpus
FROM instance i
  LEFT JOIN
  (SELECT
     id,
     organisation,
     display_name,
     personal
   FROM project t1) a
    ON i.project_id = a.id
WHERE
  /* (started on the day OR ended on the day OR running through the day)
      AND not started and stopped on the day AND a unimelb project
   */
  ((i.deleted BETWEEN '2016-09-13' AND DATE_ADD('2016-09-13', INTERVAL 1 DAY))
   OR
   (i.created BETWEEN '2016-07-10' AND DATE_ADD('2016-09-13', INTERVAL 1 DAY))
   OR (created < '2016-09-13' AND
       (deleted IS NULL OR deleted > DATE_ADD('2016-09-13', INTERVAL 1 DAY))))
  AND NOT (
    (i.deleted BETWEEN '2016-09-13' AND DATE_ADD('2016-09-13', INTERVAL 1 DAY))
    AND (i.created BETWEEN '2016-09-13' AND DATE_ADD('2016-09-13', INTERVAL 1
                                                     DAY)))
  AND a.organisation LIKE '%melb%'
  AND a.personal = 0;

# +-------+
# | vcpus |
# +-------+
# | 12858 |
# +-------+

SELECT SUM(i.vcpus) AS vcpus
FROM instance i
  LEFT JOIN
  (SELECT
     id,
     organisation,
     display_name,
     personal
   FROM project t1) a
    ON i.project_id = a.id
WHERE
  /* (started on the day OR ended on the day OR running through the day)
      AND not started and stopped on the day AND a unimelb project
   */
  ((i.deleted BETWEEN '2016-09-14' AND DATE_ADD('2016-09-14', INTERVAL 1 DAY))
   OR
   (i.created BETWEEN '2016-07-10' AND DATE_ADD('2016-09-14', INTERVAL 1 DAY))
   OR (created < '2016-09-14' AND
       (deleted IS NULL OR deleted > DATE_ADD('2016-09-14', INTERVAL 1 DAY))))
  AND NOT (
    (i.deleted BETWEEN '2016-09-14' AND DATE_ADD('2016-09-14', INTERVAL 1 DAY))
    AND (i.created BETWEEN '2016-09-14' AND DATE_ADD('2016-09-14', INTERVAL 1
                                                     DAY)))
  AND cell_name IN
      ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2')
  AND a.organisation LIKE '%melb%'
  AND a.personal = 0;

# +-------+
# | vcpus |
# +-------+
# |  8841 | Graphana reports 7578
# +-------+

