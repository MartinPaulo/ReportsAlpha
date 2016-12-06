# Cloud Top Twenty

This report shows the top twenty UoM projects by vcpu count on the 
given day.

* Instances that have both been started and terminated on the same day are
  *excluded*. This is because our granularity is a day. So if a project 
    continually starts and stops even the tiniest instance on the day they
    will build up a huge weighting that doesn't reflect their true usage. 
* The projects include personal projects. However, it would be very surprising
  if they were to make it onto this list.

```mysql
SELECT
  '2016-11-30'   AS 'date', /* lazy way of getting date into result set */
  i.project_id,
  SUM(i.vcpus)   AS vcpus,
  a.display_name AS tenant_name
FROM instance i
  LEFT JOIN
  (SELECT  id, organisation, display_name FROM project t1) a
    ON i.project_id = a.id
WHERE
  /* stopped on the day */
  ((i.deleted BETWEEN '2016-11-30' AND DATE_ADD('2016-11-30', INTERVAL 1 DAY))
   /* OR started on the day */
   OR (i.created BETWEEN '2016-11-30' AND DATE_ADD('2016-11-30', INTERVAL 1 DAY))
   /* OR running through the day */
   OR (created < '2016-11-30' AND (deleted IS NULL OR deleted > DATE_ADD('2016-11-30', INTERVAL 1 DAY))))
  /*  AND not started and stopped on the day */
  AND NOT (
    (i.deleted BETWEEN '2016-11-30' AND DATE_ADD('2016-11-30', INTERVAL 1 DAY))
    AND (i.created BETWEEN '2016-11-30' AND DATE_ADD('2016-11-30', INTERVAL 1 DAY)))
  /*  AND a UoM project */
  AND a.organisation LIKE '%melb%'
GROUP BY i.project_id
ORDER BY vcpus DESC
/* It is the top twenty... */
LIMIT 20;
```