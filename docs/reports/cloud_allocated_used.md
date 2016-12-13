# Cloud Allocated/Used

## Cloud Allocated

This is the total number of vcpus allocated in keystone to those UoM projects
whose last modified date is less than or equal to the given day. 

The query finds the contact email and the quota vcpu's for each 
project whose allocation last modified date was before the date the
query is being run on.

```mysql
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
```

The application then iterates across the result set, using the project id
to look the project's faculty in the table of cached projects/owners/faculties
and allocates the quota vcpu's for that project to the project's faculty (if 
found). If not found the quota vcpu's totals are added to the 'Unknown' 
category.

The resultant set of totals for the Faculties on the day is then stored into
the reporting database for quick retrieval by the web front end.

### The last modified date

Some explanation is required as to why the last modified date is used.

When a new allocation is requested, the allocation system creates an entry
in a database table to represent it. If the allocation is subsequently amended
the allocation system makes a copy of that original record, then *modifies*
the original record to reflect the changes, and finally updates the last
modified date of the original record to show the date on which the update was
done.

This algorithm has the interesting effect that for a given project
the record with the earliest creation date and the highest last modified
date ordinarily reflects the current state of the allocation. And the record
with the highest creation date reflects the last change to the allocation.

Hence if you want to track the changes to the allocation over time, then
the last modified date is the only sane way to do this.

So when we pointed at the raw allocation data this report would effectively
take only the row with the closest last modified date to the date on which
the report was being run in order to see the state of the allocation at that
point in time.

However, we were asked to use the reporting database rather than the raw 
allocation database. And in so doing a slight oddity has crept in. For any
given allocation the reporting database will only keep a copy of the record
with the highest modified time. Thus we've lost the ability to step through the 
allocations in time, tracking their changes.

This is because any project that was initially provisioned before the requested
date then subsequently modified afterward will be excluded. Which doesn't give 
a fair reflection of the state on a given day if the query is being stepped
through past data.

We need to correct this in the reporting database: however, CRAMS is being 
deployed shortly, replacing the allocation system. So rather than fixing this, 
then rewriting it all again when CRAMS ships, we will do one big fix when
CRAMS is deployed. Until then our historical tracking of allocations is not
that accurate: but we can state that the final figure **on** the axis does
reflect our total commitment on that date.

## Cloud Used

Shows the sum of the the vcpu's being used by UoM projects on the given day.

Notes:
    
* Personal projects are excluded.
* Instances started and stopped on the day are also excluded.

The query finds the project id, the sum of the running instance vcpu's and the
display name for each UoM project on the day the query is being run for.

```mysql
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
     AND (deleted > DATE_ADD(%(day_date)s, INTERVAL 1 DAY) OR deleted IS NULL))
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
```

The application then iterates across the result set, using the project id
to look the project's faculty in the table of cached projects/owners/faculties
and allocates the vcpu's for that project to the project's faculty (if 
found). If not found the vcpu's totals are added to the 'Unknown' category.

The resultant set of vcpu totals for the Faculties on the day is then stored 
into the reporting database for quick retrieval by the web front end.