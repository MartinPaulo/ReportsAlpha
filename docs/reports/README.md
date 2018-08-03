# Reports Overview

This set of pages describe how the data behind the reports is gathered together
and presented.

## Cloud Reports

Start by reading about the [NeCTAR Reporting Database](reporting_db.md).

Then read about the reports you are interested in.

* [Cloud Active Projects](cloud_active_projects.md)
* [Cloud Allocated/Used](cloud_allocated_used.md)
* [Cloud Available Capacity](cloud_available_capacity.md)


## Some links

* [UoM-ResPlat-DevOps](https://github.com/UoM-ResPlat-DevOps)
* [UoM-ResPlat-DevOps/rdsi-reporting](https://github.com/UoM-ResPlat-DevOps/rdsi-reporting)
* [VicNode](https://github.com/VicNode)
* [VicNode/scripts](https://github.com/VicNode/scripts)

## TODO

* Upgrade the reporting application to django 2
* Upgrade the reporting application to the latest and greatest UoM look and feel
* Possibly write some puppet scripts to deploy the reporting application
* Integrate the buyers committee scripts into the reporting application
* Create a single "utilties" package
* Add tests to the reporting application
* Incorporate the changes made to the NeCTAR reporting application
* Incorporate Gnocchi
* Repeatability on running


For Karaage:

* Add department list to Karaage
* Alter SQL run against Karaage
* For utilization, use the grand total, not the individual users
* Sreport output should be in hours...
* Add required plugins to Karaage/slurm
* Handle users who are in VHO's yet working for UoM