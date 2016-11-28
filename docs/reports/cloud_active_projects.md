# Cloud Active Projects

This is the count of users belonging to UoM projects that have either started, 
stopped, or have running instances in UoM data centres on the given day.

It also gives the number of users belonging to UoM projects who are running
instances outside of the UoM data centres on the given day.

Finally, the count of users belonging to non UoM projects who are running 
instances inside of UoM data centers is shown.

The graph is derived by calculating the following figures for each day 
(`day_date`):

* [Others @ UoM](#others_at_uom): The count of users who belong to non-UoM 
  projects running instances in UoM data centers on the `day_date`.
* `UoM @ UoM and elsewhere`: The count of users belonging to UoM projects who 
  are running instances in both UoM and non UoM data centers on the `day_date`. 
* `UoM @ elsewhere`: The number of users belonging to UoM projects who are 
  running instances only in data centers that do not belong to UoM on 
  the `day_date`.
* `UoM @ UoM only`: The number of users belonging to UoM projects who are 
  running instances only in the UoM data centers on the `day_date`.
  
## The NeCTAR reporting database

The NeCTAR reporting database is the one against which we were requested
to run our reports. It is a set of tables populated by a python script that 
queries the production data and dumps it into the reporting database.

The source OpenStack tables have data that is dirty. This is due to changes
in the tables over time, errors in production etc. Hence the data in the
reporting database is not perfect.

### The instance table
  
The instance table contains a list of all the instances that have ever ben run 
on the NeCTAR cloud. It is pretty much a subset of the Nova instances table.

The following columns are of interest:

* `created_by`: the user id of the user who created the instance
* `deleted`: the date on which the instance was deleted. If the instance
  is running this value will be null
* `created`: the date on which the instance was created. This should never
  be null.
* `cell_name`: the name of the cell in which the instance ran/is running
* `project_id`: the id of the project to which the instance belongs

## Others @ UoM

We find the instances on the day that have been started, stopped or been
running through the entire day to those that belong to UoM projects. We
then count the number of users who created these instances.

Instances started and stopped on the day are thus included.

```mysql
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
```
