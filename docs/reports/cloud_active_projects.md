Cloud Active Projects
=====================

This is the count of users belonging to UoM projects that have either started, 
stopped, or have running instances in UoM data centres on the given day.

It also gives the number of users belonging to UoM projects who are running
instances outside of the UoM data centres on the given day.

Finally, the count of users belonging to non UoM projects who are running 
instances inside of UoM data centers is also shown.

The graph is derived by calculating the following figures for each day 
(`day_date`):

* `Others @ UoM`: The count of users who belong to non-UoM projects running
  instances in UoM data centers on the `day_date`.
* `UoM @ UoM and elsewhere`: The count of users belonging to UoM projects who 
  are running instances in both UoM and non UoM data centers on the `day_date`. 
* `UoM @ elsewhere`: The number of users belonging to UoM projects who are 
  running instances only in data centers that do not belong to UoM on 
  the `day_date`.
* `UoM @ UoM only`: The number of users belonging to UoM projects who are running 
  instances only in the UoM data centers on the `day_date`.
  
