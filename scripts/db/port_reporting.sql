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


# We want to know how many instances have been launched since the start date
SELECT count(*)
FROM instance
WHERE created >= '2016-09-09'

# we want to know the cell names that are in use
SELECT DISTINCT cell_name
FROM instance;

# calculate the core hours for each project in a given date range (e.g.:
# '2017-01-01' - '2017-03-31')
SELECT
  project.id                     AS project_id,
  project_name                   AS project_name,
  IFNULL(chief_investigator, '') AS chief_investigator,
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
                                                    IF(created < '2017-01-01',
                                                       '2017-01-01', created),
                                                    # the deleted date can be be before the end date, after the end date or null
                                                    # so if deleted is null, take now else take the end date.
                                                    # if that 'deleted' date is greater thant the end date,
                                                    #   then take the end date
                                                    #   else take the 'deleted' date (works if now < end date)
                                                    IF(IF(deleted IS NULL,
                                                          NOW(), deleted) >
                                                       '2017-03-31' +
                                                       INTERVAL 1 DAY,
                                                       '2017-03-31' +
                                                       INTERVAL 1 DAY,
                                                       IF(deleted IS NULL,
                                                          NOW(), deleted))))
                          / 3600, 0)) AS vcpu_hours
              FROM instance
              WHERE project_id IS NOT NULL
                    # where created before the end date
                    AND created < '2017-03-31' + INTERVAL 1 DAY
                    # and deleted after the start date
                    AND (deleted IS NULL OR deleted > '2017-01-01')
              # i.e.: was active at any point during the start and end date
              GROUP BY project_id
            ) i ON i.project_id = allocation.project_id
WHERE project.organisation LIKE '%melb%'
      AND vcpu_hours > 0
ORDER BY vcpu_hours DESC;

# Return details for meg/aurin projects in a given date range (e.g.:
# '2017-01-01' - '2017-03-31')
SELECT
  instance.project_id,
  display_name,
  description,
  COUNT(*)              AS instances,
  IFNULL(SUM(vcpus), 0) AS vcpus,
  ROUND(IFNULL(
            SUM(vcpus * TIMESTAMPDIFF(SECOND,
                                      # the start date, if created is < the start date
                                      IF(created < '2017-01-01', '2017-01-01',
                                         created),
                                      # the deleted date can be be before the end date, after the end date or null
                                      # so if deleted is null, take now else take the end date.
                                      # if that 'deleted' date is greater thant the end date,
                                      #   then take the end date
                                      #   else take the 'deleted' date (works if now < end date)
                                      IF(IF(deleted IS NULL, NOW(), deleted) >
                                         '2017-03-31' + INTERVAL 1 DAY,
                                         '2017-03-31' + INTERVAL 1 DAY,
                                         IF(deleted IS NULL, NOW(), deleted))))
            / 3600, 0)) AS vcpu_hours,
  quota_instances,
  quota_vcpus,
  quota_memory,
  quota_volume_total,
  contact_email,
  chief_investigator
FROM instance
  LEFT JOIN project ON instance.project_id = project.id
  LEFT JOIN allocation ON allocation.project_id = instance.project_id
WHERE
  (display_name REGEXP '^meg(-|_|PN)'
   OR (display_name LIKE '%aurin%' AND organisation LIKE '%melb%'))
  # where created before the end date
  AND created < '2017-03-31' + INTERVAL 1 DAY
  # and deleted after the start date
  AND (deleted IS NULL OR deleted > '2017-01-01')
# i.e.: was active at any point during the start and end date
GROUP BY instance.project_id
ORDER BY display_name;

# Return details for meg/aurin projects in a given date range (e.g.:
# '2017-01-01' - '2017-03-31')
SELECT
  instance.project_id,
  display_name,
  description,
  COUNT(*)              AS instances,
  IFNULL(SUM(vcpus), 0) AS vcpus,
  ROUND(IFNULL(
            SUM(vcpus * TIMESTAMPDIFF(SECOND,
                                      # the start date, if created is < the start date
                                      IF(created < '2017-01-01', '2017-01-01',
                                         created),
                                      # the deleted date can be be before the end date, after the end date or null
                                      # so if deleted is null, take now else take the end date.
                                      # if that 'deleted' date is greater thant the end date,
                                      #   then take the end date
                                      #   else take the 'deleted' date (works if now < end date)
                                      IF(IF(deleted IS NULL, NOW(), deleted) >
                                         '2017-03-31' + INTERVAL 1 DAY,
                                         '2017-03-31' + INTERVAL 1 DAY,
                                         IF(deleted IS NULL, NOW(), deleted))))
            / 3600, 0)) AS vcpu_hours,
  quota_instances,
  quota_vcpus,
  quota_memory,
  quota_volume_total,
  contact_email,
  chief_investigator
FROM instance
  LEFT JOIN project ON instance.project_id = project.id
  LEFT JOIN allocation ON allocation.project_id = instance.project_id
WHERE
  instance.project_id IN (
    '374', 'b6d58e1bd1d046048e9d4a8a742a07a8', 'ed15a17952044ee4b2a260af81daa3f5',
           '6af9f1967d324e9eab070b257aa93211', '8bdb4ede59c8454b908c14c0f3317f14', '7bd8f74b80244c17b490b2abae5949ef', 'eb888a3f907f4e539235aebcac1403dd', '54a8e4b4e14f4dd7a522561164d9912a', '171d98b6455b403b8d8677f6c9d1eacc',
           'be87d3ad8d8a4c3ca51d2f8d2ee208b2', '90c4b6a570bd42a6ae4bb0c4b7afb037', '5a03658077874643a1f8e6ba9098b791', '68453f262a5b4937af04ff3f261e295e', '2cce8eb5036b47bba134eb63b290457f', '6c66411e774747e8a47f3b49e649084a',
                                                                                   'adcfdeec0b044744a2fd5ffbc5ce786c', 'f4fff40d98984cea9e39af597456001b', '66ce37eae8c94c0d90ac458b5d8eb486', 'e5e794b8d1444a07b7d07ce67014bda9', '525de0ba52c342e88bb5a56eb758b306', 'd2b393a80a32489ab4172276396434ec',
    '2ce320a64abe42a1b1f40d7b75f20e29', '637db1544ded4b7f9245c33403e4b96b', '26c55bc83ea248628be73ba3d98bd947', 'b18e9b19d9914c7ca121dce1a2daa65f', '57cc370dffd44900aee04ce9bc89af13', '57ac9d27519e4f88a04776c0d9430fe0',
    '29825fd608f5441e8aa9e7738a609c92', '564a6ee5b9e34b82aee7105cc3448f5c', '8c8e49dd0df142b7ac76620e7feb56fa', '3e02a1d38c254f51803a081306967598', 'ff613d6d5c034d2d90678d8e8473efcd', '00b00b50fcab4ef18ae93b8e737e8282',
                                                                                                                                                    '0a9af5295d6749459657c41c47d9399f', '32415c02f99b44ed934dc2c92e4e62f2', 'c541a8f52f9948169efab8f310b0eb1b', 'b64ec060bc6d4d04a44f6c1ccefaa3dc', '4bf0bf96da5544e8a957d6a509d295e9', '8ea0ee71c5154ba7b6996a5029111f48',
                                                                                                                                                    '9865281125944ee2b5d192bbd010fb45', 'dbff7bfcf4924c9fb971362486df36ca', 'd7aea77c8db64bae97b81513fdd1a594', '7f61fc0b763b43a3b6ced98211e8c20e', '66fa26242a894349963e7e221b01971e', 'dcd0f07de6114362898081e323385649',
                                                                                                                                                                                                                            '3d29bd1b73d14f5abc3bc01d8de0aa31', '41e32fe031e7414f80414f1bbe0c155f', '5faaad8c3dba439da11b433f576629b4', 'd553156150194013ab74f3cd50161f0f', '75dfabaad7cd45c4be5e65ee9518a80a', '970e669c4d234cd995b311becfa4dd1f',
    'd84f44c76d5a4d21a8d79bd6d09985f0', '7fcf7c15a7c44a75abc3bc6384f18287', 'f3b76a84740f45a992f55ca5fb5c5745', '5510ca2e855f47c8b86a70b483d4032e', '34982f5ba7aa4c35a1d2bd4b24725448', 'aad35bfd8c6f4797b10e0e88e3d1b029',
    '5816f8d63899417287465b398823524c', '482b9beb01924b67a24a0fa585abf7f2', '77072cc4663940c19f6d4861ce792461', 'cbef19365c264123a4f00b8901b4dacc', 'c61ef4a9d3104f42b33d9500ae62985c', '1a0e3fdc4b524126b9db95aa8ded0667',
                                                                                                                                                    '21e8e0f6f9c2403785be97e3222783f2', '5515da4d78874519aa5bf7424f3a9038', 'fe1645cbb9154356976921b5a9c821e7', '39dcf26837ae48b39ffdb693de1fc185', '42df19711e7547a5bb7de4f9fb7b3297', 'a82054fa26414cddaeb17e95fa606414',
                                                                                                                                                    'e73d5798d25441c3b66ef019589844f8', '5c43fa2592964ea396543b12071d978d', 'c46fc903e5ba4321b562f52e3143da87', '939e02ede349461eab7b9160199f3bcc', '756c13bde07d49eab9ab5693b75beaa9', '3576075d53004d08aeecc4c564f41961',
                                                                                                                                                                                                                            '12a054505d69439487d9476af0a26dd1', 'da49b84bb4c14eee99e3913772553491', '51b51c7946f7497386bf9629a499800e', '28e0bad74bf04dc5a4d8d91c3bc346b7', '685471438aca45189814bdfe3b34b7d6', '3b0c24aff3cf4b678ae6bc6c5029cfb2',
    'f5c0924eb3d14d49a60250b9c0ec2f09', '1b348ea16942443fb7305b99882a844c', 'f46e59a0f2134266b0904c6ef455e9df', '8bf0716623fa468cb11acd88a6d36037', '16332aab15294d9ba287e584cc7cfb0b', '75771d1e73af439dbe48b9f224a46117',
    '7ba4c2ae9970464683191a5e2ab3fd78', 'fdee23d2faeb4dae9a158ce7c31985e3', '29c343a2f28244a78adccc2a9184233c', '6988090880bb4ff0a3e84e8470cf5555', 'a9212653354c4f729902926b6151f4f1', 'bef09fa8086841b688e8c11b457d04cf',
                                                                                                                                                    'eafe95ec3f93429ba098678d3c2aa7f9', '3863d7d295db41229cd4479dcc66568f', 'fa083d16b0474b718fa9f01b07e72193', '75d1e8d380294e4a8205219e4648696a', '655459357f5c415fac589ca01b3e8b3c', '3000d429a577498a97d89f4ce7464f0d',
                                                                                                                                                    '9b6644e43bd94fa2b8a4ae59cc97ee52', '4637c5334bf145fd9413c6c721cac7e5', '3e70f71e4f914c75a93224c88d43343b', '4282e2bc301a44e98e9884d0738a2789', 'e415d08589c24e449059e1df5029bb80', '8f18dfb26d6e41daa0f54f58aa78f53b',
                                                                                                                                                                                                                            'a9e282f38add4947a002bc541fe20ed6', '1238c96996de4390b1674ca39210d6b2', 'daa0acaa4c464a81a99e60eec581f248', '78d23ce7c44940188adeca1108613b75', '0913197112cc4fe2817ab94ef1a68464', '782d2eec36cd492a81a165280976fe1d',
    '8a96cc7283b849fb8cd6fcdc42fd67ef', '4bc2c465e51d4d3ab3bf26af76157768', '7f2a7c1d7fec4b88b3cfa6ee65f13941', '1bcfeae26e964e03a1044c425986602d', '5edb41086d054d9486e054d053f4a53e', 'e57f01279e0c4ad8be600ec415cdc432',
    '561ce2be9d904d998b29d3211f2e623e', '510d818378ea4793867fda5edc7d90fb', '08ec19eb9e4d490b9a88e059508b96a4', 'c346c71029d8426d80a789a96be783e7', 'f326ea627c5346a6847c4056827edeef', 'be9c0afbad0c46de9047fb2c964b33f1',
                                                                                                                                                    '69a65cb205074e169a4061ab5fddaab4', 'fbde9ffc4e4946598ffdb28b496e39ea', '554a7c10bdbf4fffa0897c36d0be94eb', 'c49c26fa132348f9bc8d04a1c47223ba', '3898fef85ea34e4089dc99f6583cca84', '2cfc442233f74138b6c6cf2441c9ff13',
                                                                                                                                                    '53d8d89864e94392ae4e28a6e15387c6', 'e64e6fa2842a49b9a335374b6fa4391c', 'a2ea875f81b64571a8d1c1f71fe0b331', '7a40ba0538814b509aa911a383571f78', '0fd3199ffe524833837608e4796c9f63', '35f3f6de0f2140c4ad4a98d2e984cd19',
                                                                                                                                                                                                                            '594a7305e81c42ec9d4a2a42891d75de', '374049f3e09d46788148d5ad2a2ce642', '16db87371d364651984767303ebf5248', '7e4b78bca4984d37815433e5d88ae670', 'b690a3a74be64661b7f7f42e7efa266d', '52d4b4ecdab2463e97d40f4d3de48c4c',
    '67e64bf11ac04bf29b44544ebb395e6d', '6fe03410282a461ebb9b12bdb88ca924', 'e84855d9cddc44f99546fc694b1bc637', 'fc2cdbe022ff425199faa3ae8cd04c87', '9ef67f139f654eacb5d7d4cb3439755a', 'b44f80a0b9574456b457fe97f029b1c9',
    '7c2da41d97044e58b15b570f542533ee', '59f7db4847fc4538bf515260f3565c20', '5b4728581e92492b82ef6b55e3cacf28', 'c1c6b1139a854998a331ba08c109b91e', 'c73d55655c114c858f3a2891f78e8976', '8b16fbf9070b4c57ae78e41ae3945e2b',
                                                                                                                                                    '00ac16dd47fe4443bce3a749fdf3fd3f', '997051ea78a94d4d999a98dd38a867af', '4573d95739d4448ca668609c3b6fa1ba', '6a16b4729a474d1d9d973fd4911e6038', '55f4565483b643c7a49dc5081fd4db4c', 'c715411c900b463981ca58133b15b4ea',
                                                                                                                                                    '780e482a732a49eeb923abb802e5e15a', 'eab8cc39e44d40d4a3f4cbd8ba83250c', '544ddd92f4fd4c5fb4447be77c58bcba', '76a0d5f5ae0646bdb23d63787946e5c9', '97efedf51ddf4f488fad9d8efdb37965', 'a8721d9055d4425d953c1aa2fc79b2a6',
                                                                                                                                                                                                                            '8088dffcdcce4bd7ab7bf445515497fb', '3b8462ffd3fd48e29f61a963f7f72c14', '21f3162401f74474844a57131aead15b', '2b69b0dcec5f4763b73354b1612bbd9e', '4de3261e0d754d44aff4d8e50110229b', '1130decc78884c3eb3cfa811fde24624',
    '75bb46c0f1834c99bcdfbc7ecb0ab2af')
  # where created before the end date
  AND created < '2017-03-31' + INTERVAL 1 DAY
  # and deleted after the start date
  AND (deleted IS NULL OR deleted > '2017-01-01')
# i.e.: was active at any point during the start and end date
GROUP BY instance.project_id
ORDER BY display_name;

# need to set the group_concat_max_len variable to be longer as rows are
# being cut (a warning is issued)
SELECT
  project_id,
  group_concat(
      IF(created < '2017-01-01', str_to_date('2017-01-01', '%Y-%m-%d'),
         created),
      ' - ',
      IF(IF(deleted IS NULL, NOW(), deleted) >
         '2017-03-31' + INTERVAL 1 DAY,
         str_to_date('2017-03-31' + INTERVAL 1 DAY, '%Y-%m-%d'),
         IF(deleted IS NULL, NOW(), deleted))
      ORDER BY created SEPARATOR ' | ') AS dates
FROM instance
WHERE created < '2017-03-31' + INTERVAL 1 DAY AND
      (deleted IS NULL OR deleted >= '2017-01-01')
GROUP BY project_id;

SELECT @@group_concat_max_len; # default is 1024
SELECT @@max_allowed_packet; # group concat max len can't be bigger than this
# it is rumoured that ORDER BY can reduce group concat max len by 2 thirds...
SET SESSION GROUP_CONCAT_MAX_LEN = 1024 * 1000; # only sets the session value
# SET GLOBAL GROUP_CONCAT_MAX_LEN = 1024; # sets across all queries...

SELECT
  project_id,
  display_name,
  description,
  chief_investigator,
  contact_email,
  organisation,
  description,
  quota_instances,
  quota_vcpus,
  quota_memory
    quota_volume_total,
  quota_snapshot
    quota_volume_count
FROM allocation
  LEFT JOIN project ON project.id = project_id
WHERE chief_investigator IN (
  'aisaac@unimelb.edu.au',
  'alonie@unimelb.edu.au',
  'bjpope@unimelb.edu.au',
  'samuel@unimelb.edu.au',
  'torsten.seemann@monash.edu',
  'simon.gladman@unimelb.edu.au',
  'pip.griffin@gmail.com',
  'mkuiper@unimelb.edu.au',
  'a.siebel@unimelb.edu.au',
  'minouye@unimelb.edu.au',
  'jason.li@unimelb.edu.au',
  'nuwan.goonasekera@unimelb.edu.au'
) OR contact_email IN (
  'aisaac@unimelb.edu.au',
  'alonie@unimelb.edu.au',
  'bjpope@unimelb.edu.au',
  'samuel@unimelb.edu.au',
  'torsten.seemann@monash.edu',
  'simon.gladman@unimelb.edu.au',
  'pip.griffin@gmail.com',
  'mkuiper@unimelb.edu.au',
  'a.siebel@unimelb.edu.au',
  'minouye@unimelb.edu.au',
  'jason.li@unimelb.edu.au',
  'nuwan.goonasekera@unimelb.edu.au'
);

SELECT
  display_name,
  project_id,
  description,
  chief_investigator,
  contact_email,
  organisation,
  description,
  quota_instances,
  quota_vcpus,
  quota_memory
    quota_volume_total,
  quota_snapshot
    quota_volume_count
FROM allocation
  LEFT JOIN project ON project.id = project_id
WHERE display_name LIKE '%bioinformatics%' AND organisation LIKE '%melb%';
# WHERE display_name LIKE '%lscc%';
# WHERE display_name LIKE '%vlsci%';

SELECT
  instance.project_id,
  display_name,
  description,
  COUNT(*)              AS instances,
  IFNULL(SUM(vcpus), 0) AS vcpus,
  ROUND(IFNULL(
            SUM(vcpus * TIMESTAMPDIFF(SECOND,
                                      # the start date, if created is < the start date
                                      IF(created < '2017-01-01', '2017-01-01',
                                         created),
                                      # the deleted date can be be before the end date, after the end date or null
                                      # so if deleted is null, take now else take the end date.
                                      # if that 'deleted' date is greater thant the end date,
                                      #   then take the end date
                                      #   else take the 'deleted' date (works if now < end date)
                                      IF(IF(deleted IS NULL, NOW(), deleted) >
                                         '2017-03-31' + INTERVAL 1 DAY,
                                         '2017-03-31' + INTERVAL 1 DAY,
                                         IF(deleted IS NULL, NOW(), deleted))))
            / 3600, 0)) AS vcpu_hours,
  quota_instances,
  quota_vcpus,
  quota_memory,
  quota_volume_total,
  organisation,
  contact_email,
  chief_investigator
FROM instance
  LEFT JOIN project ON instance.project_id = project.id
  LEFT JOIN allocation ON allocation.project_id = instance.project_id
WHERE
  instance.project_id IN (
    'fd6b9f4bf21b45b38ce4f99f117d5065', 'cfce812907214f35aa9f0c3d7d53bfcc',
    'bd23abf19f794ea48001da66af57f077', 'bb3d1cfcd3f64aaaad6251c36ec29d1a',
    'b2195695016549b7b2b07f7a3943386c', 'ad3c89a1f5c74176a837455bef0b0f31',
    'a3929895f9e94089ad042c9900e1ee82', '7ea859948c3a451c9baced6fee813ed1',
    '5a0ec9b9aa86427081b6643bf57ad926', '323bbc3d014345f9822665fa398da3a9',
    '24376b6176a5466b9f20bee02ee1f182', '12daa036fb264cdc99ad7ea6d2ffdab8',
    '0f9e376252c04620a861f1f477c39626', '09261a90f9b2414f81f7dbe0192f0013'
  )
  # where created before the end date
  AND created < '2017-03-31' + INTERVAL 1 DAY
  # and deleted after the start date
  AND (deleted IS NULL OR deleted > '2017-01-01')
# i.e.: was active at any point during the start and end date
GROUP BY instance.project_id
ORDER BY display_name;