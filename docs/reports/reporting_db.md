# The NeCTAR reporting database

The NeCTAR reporting database is the one against which we were requested
to run our cloud reports. It is a set of tables populated by a python program 
that queries the production data and dumps it into the reporting database at 
10 minute intervals.

Note that the source OpenStack tables have data that is dirty. This is due to 
changes in the tables over time, errors in production etc. Hence the data in 
the reporting database is not perfect either.

## The instance table
  
The `instance` table contains a list of all the instances that have ever ben run 
on the NeCTAR cloud. It is essentially a subset of the Nova `instances` table.

The following columns are of interest:

* `created_by`: the user id of the user who created the instance
* `deleted`: the date on which the instance was deleted. If the instance
  is running this value will be null
* `created`: the date on which the instance was created. This should never
  be null.
* `cell_name`: the name of the cell in which the instance ran/is running
* `project_id`: the id of the project to which the instance belongs. Maps to
                `id` in the `project` table.

We use the `cell_name` column to identify the UoM data centers, as there is
currently a one to one mapping between the UoM cells and the UoM data centers.

This *may* change, so the tool that does the ETL checks for changes to cell 
names and alerts the administrators if any is found.

Note that a large number of the queries are trying to find instances active
on a given day

The following diagram shows the possibilities.

    Key:
        A  = day start
        B  = day end
        tc = time created
        td = time deleted

              A                                       B
              +                                       +
        tc    |                                       |     td
         +--------------------------------------------------+
              |                                       |
         +------------------------------------------------------------> NULL
              |                                       |
              |  +------------------------------------------+
              |                                       |
              |  +----------------------------------------------------> NULL
              |                                       |
         +-------------------------------------+      |
              |                                       |
              |  +------+                             |   Not sometimes wanted
              |                 +--------------+      |   Not sometimes wanted
              |        +--------------------+         |   Not sometimes wanted
              |                                       |
              +                                       +

    Here NULL indicates that the instance is still running.

Short running instances that are started and stopped between A and B are
excluded in some reports. This is done because if a project continually
starts and stops even the tiniest instance throughout the period between
A and B they will build up a huge weighting that doesn't reflect their
true usage.

This can be minimised by shrinking the time between A and B down to
seconds: but then the time taken to query the database, and the stored
derived data will both balloon.

So the difference between that reported and that allocated on a given day
shows the average headroom available to people to 'burst'.

## The project table

The `project` table contains a list of all the projects that have been approved
on the NeCTAR cloud.

The following columns are of interest

* `id`: the project id.
* `display_name`: the name shown for the project in the dashboard project
    drop down.
* `organisation`: the institute associated with with the project. This could
    do with some clean up (e.g.: *gmail.com* appears...)
* `quota_vcpus`: the total number of vcpu's that were approved for this
    project to use. Read from Keystone...
        
## The allocation table

The `allocation` table contains a subset of each allocation made in the
NeCTAR cloud.

The following columns are of interest:

* `project_id`: the project id, if the allocation was approved and a project
    was created.
* `contact_email`: the contact email of the person who applied for the 
    allocation. This is the original project owner.
* `modified_time`: the date on which the last change was made to the allocation
    record.
