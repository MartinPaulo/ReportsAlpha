# Cloud Active Projects

This is the count of users belonging to UoM projects that have either started, 
stopped, or have running instances in UoM data centres on the given day.

It also gives the number of users belonging to UoM projects who are running
instances outside of the UoM data centres on the given day.

Finally, the count of users belonging to non UoM projects who are running 
instances inside of UoM data centers is shown.

The graph is derived by calculating the following figures for each day 
(`day_date`):

* [Others @ UoM](#others--uom): The number of users who belong to non-UoM 
  projects running instances in UoM data centers on the `day_date`.
* [UoM @ elsewhere only](#uom--elsewhere-only): The number of users belonging
  to UoM projects who are are running instances only in non UoM data centers 
  on the `day_date`. 
* [UoM @ UoM only](#Auom--uom-only): The number of users belonging to UoM 
  projects who are running instances only in the UoM data centers on 
  the `day_date`.
* [UoM @ UoM and elsewhere](#uom--uom-and-elsewhere): The number of users 
  belonging to UoM projects who have running instances in both UoM and 
  non Uom data centers on the `day_date`.
  
The resultant set of totals on the day is then stored into
the reporting database for quick retrieval by the web front end. 
  
## Others @ UoM

The count of users belonging to non UoM projects who start, stop, and
have running instances in UoM data centers on the given day.

We find the instances in the UoM data centers that on the day that have been 
started, stopped or been running through the entire day that do not belong to
UoM projects. We then count the number of users who created these instances.

* Instances that have both been started and terminated on the same day are
  included.
* The projects include personal projects.

```mysql
SELECT COUNT(DISTINCT created_by) AS others_at_uom
FROM instance
WHERE
  /* stopped on the day */
  ((deleted BETWEEN '2016-10-29' AND DATE_ADD('2016-10-29', INTERVAL 1 DAY))
      /* OR started on the day */
      OR (created BETWEEN '2016-10-29' AND DATE_ADD('2016-10-29', INTERVAL 1 DAY))
      /* OR running through the day */
      OR (created < '2016-10-29' AND (deleted IS NULL OR deleted > DATE_ADD('2016-10-29', INTERVAL 1 DAY))))
  /* AND in the UoM data centers*/
  AND cell_name IN ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2')
  /* AND the project is not with UoM */
  AND project_id NOT IN (SELECT id
                         FROM project
                         WHERE organisation LIKE '%melb%');
```

## UoM @ elsewhere only

The number of users in UoM projects who are running instances
only in data centers that do not belong to UoM on the given day.

We find the users belonging to UoM projects that have, on the given day, 
started, stopped or had instances running through the entire day in non UoM
data centers. From that list we filter out all of the users that also launched, 
stopped or ran instances in the UoM data centers.

We then count the remaining users. 

* Instances that have both been started and terminated on the same day are
  included.
* The projects include personal projects.

```mysql
SELECT COUNT(DISTINCT created_by) AS elsewhere_only
FROM instance
WHERE 
  ((deleted BETWEEN '2016-10-29' AND DATE_ADD('2016-10-29', INTERVAL 1 DAY))
      OR (created BETWEEN '2016-10-29' AND DATE_ADD('2016-10-29', INTERVAL 1 DAY))
      OR (created < '2016-10-29' AND (deleted IS NULL OR deleted > DATE_ADD('2016-10-29', INTERVAL 1 DAY))))
  AND cell_name NOT IN ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2')
  AND project_id IN (SELECT DISTINCT id
                     FROM project
                     WHERE organisation LIKE '%melb%')
  /* and not running any instances in melbourne on the day */
  AND created_by NOT IN (
     SELECT DISTINCT created_by
     FROM instance
     WHERE
       ((deleted BETWEEN '2016-10-29' AND DATE_ADD('2016-10-29', INTERVAL 1 DAY))
            OR (created BETWEEN '2016-10-29' AND DATE_ADD('2016-10-29', INTERVAL 1 DAY))
            OR (created < '2016-10-29' AND (deleted IS NULL OR deleted > DATE_ADD('2016-10-29', INTERVAL 1 DAY))))
       AND cell_name IN ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2')
       AND project_id IN (SELECT DISTINCT id
                          FROM project
                          WHERE organisation LIKE '%melb%'));
```

## UoM @ UoM only

The number of users in UoM projects who have run instances only in the 
UoM data centers on the given day.

We find the users belonging to UoM projects that have, on the given day, 
started, stopped or had instances running through the entire day in UoM
data centers. From that list we filter out all of the users that also launched, 
stopped or ran instances in other data centers.

We then count the remaining users. 

* Instances that have both been started and terminated on the same day are
  included.
* The projects include personal projects.

```mysql
SELECT COUNT(DISTINCT created_by) AS UoM_only
FROM instance
WHERE 
  /* stopped on the day */
  ((deleted BETWEEN '2016-10-29' AND DATE_ADD('2016-10-29', INTERVAL 1 DAY))
      /* OR started on the day */
      OR (created BETWEEN '2016-10-29' AND DATE_ADD('2016-10-29', INTERVAL 1 DAY))
      /* OR running through the day */
      OR (created < '2016-10-29' AND (deleted IS NULL OR deleted > DATE_ADD('2016-10-29', INTERVAL 1 DAY))))
  /* AND in the UoM data centers*/
  AND cell_name IN ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2')
  /* AND the project is with UoM */
  AND project_id IN (SELECT DISTINCT id
                     FROM project
                     WHERE organisation LIKE '%melb%')
  /* AND not having run any instances in any other zone on the day */
  AND created_by NOT IN (
        /* MySQL doesn't support the EXCEPT operator */
        SELECT DISTINCT created_by
        FROM instance
        WHERE
            ((deleted BETWEEN '2016-10-29' AND DATE_ADD('2016-10-29', INTERVAL 1 DAY))
            OR (created BETWEEN '2016-10-29' AND DATE_ADD('2016-10-29', INTERVAL 1 DAY))
            OR (created < '2016-10-29' AND (deleted IS NULL OR deleted > DATE_ADD('2016-10-29', INTERVAL 1 DAY))))
            AND cell_name NOT IN ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2')
            AND project_id IN (SELECT DISTINCT id
                              FROM project
                              WHERE organisation LIKE '%melb%'));
```

## UoM @ UoM and elsewhere

The count of users belonging to UoM projects who start, stop, and have running
instances in both UoM and non Uom data centers on the given day.

We have created a left join between users running inside and outside UoM
data centers, but this is a very slow query. 

So we rather count the total number of users in UoM projects who are running 
instances outside of UoM data centers on the given day. We then subtract the 
count of users who are running purely outside of UoM data centers, calculated
by [UoM @ elsewhere only](#uom--elsewhere-only). 

```mysql
SELECT COUNT(DISTINCT created_by) AS uom_users_outside_uom
FROM instance
WHERE
  (((deleted BETWEEN '2016-10-29' AND DATE_ADD('2016-10-29', INTERVAL 1 DAY))
    OR (created BETWEEN '2016-10-29' AND DATE_ADD('2016-10-29', INTERVAL 1 DAY))
    OR (created < '2016-10-29' AND (deleted IS NULL OR deleted > DATE_ADD('2016-10-29', INTERVAL 1 DAY))))
  AND cell_name NOT IN ('nectar!qh2-uom', 'nectar!melbourne!np', 'nectar!melbourne!qh2')
  AND project_id IN (SELECT DISTINCT id
                     FROM project
                     WHERE organisation LIKE '%melb%'));
```
