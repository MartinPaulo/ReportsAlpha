# Cloud Available Capacity

The Cloud Available Capacity graph shows the advertised available capacity of 
the UoM cells over time. The graph show the slots available per flavor (based
on the flavor's RAM size), which is how the scheduler picks the zone to
run an instance in.

The data used is taken from the NeCTAR [graphite](https://graphiteapp.org/) 
system. The user selects the instance size they are interested in from a
drop down, then that and the currently selected duration is sent to the
server which in turn issues a request to the graphite system.

As set up the graphite system will return a series that have nulls recorded
against some of the times that make up the point sets. This indicates that a 
sample was not read at that time. There are several strategies that can be 
used: to either fill in values from either side of those points, rewrite the 
value to 0, discard the  null values or render broken lines. Manufacturing 
fake data doesn't sit right. So we opt to simply remove filter out those points
on our server before returning the data to the browser.

