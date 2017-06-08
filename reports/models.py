import datetime

from django.db import models
from django.utils import timezone
from markdown import markdown


class Report(models.Model):
    report_title = models.CharField(max_length=100)
    pub_date = models.DateTimeField('date published')
    d3_file_name = models.CharField(max_length=100, default='.js')
    description = models.TextField(blank=True, null=True)
    description_html = models.TextField(editable=False, default='')
    related = models.OneToOneField('Report', on_delete=models.DO_NOTHING,
                                   null=True, blank=True)

    def __str__(self):
        return self.report_title

    def was_published_recently(self):
        """
        A handy field to let us see the newly created reports in the
        Admin console.
        :return: True if was published in the last day, False otherwise
        """
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now

    def save(self, *args, **kwargs):
        self.description_html = markdown(self.description)
        super(Report, self).save(*args, *kwargs)

    was_published_recently.admin_order_field = 'pub_date'
    was_published_recently.boolean = True
    was_published_recently.short_description = 'Published recently?'


class CloudCapacity(models.Model):
    date = models.TextField(primary_key=True)
    nectar_contribution = models.IntegerField()
    uom_contribution = models.IntegerField()
    co_contribution = models.IntegerField()

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.date)

    class Meta:
        managed = False
        db_table = 'cloud_capacity'


class CloudProjectFaculty(models.Model):
    project_id = models.TextField(unique=True, max_length=32,
                                  null=False, primary_key=True,
                                  default="0",
                                  help_text="The projects ID")
    chief_investigator = models.CharField(max_length=75, blank=True, null=True,
                                          help_text="The nominated chief "
                                                    "investigator's email")
    contact_email = models.CharField(max_length=75, blank=True, null=True,
                                     help_text="The applicant's email")
    # TODO: The following is the project description
    name = models.CharField(max_length=64, blank=True, null=True,
                            help_text="The project name")
    for_code = models.CharField(max_length=6, blank=True, null=True,
                                help_text="The highest weighted FOR code")
    allocated_faculty = models.CharField(max_length=7, blank=True, null=True,
                                         help_text="The faculty we have "
                                                   "decided the project "
                                                   "belongs to")

    class Meta:
        db_table = 'cloud_project_faculty'


class CloudTotalsByFaculty(models.Model):
    # All field names lowercased.
    date = models.TextField(unique=True, blank=False, null=False,
                            primary_key=True,
                            help_text="The date on which the values "
                                      "in the row were calculated")
    foa = models.IntegerField(db_column='FoA', blank=False, null=False)
    vas = models.IntegerField(db_column='VAS', blank=False, null=False)
    fbe = models.IntegerField(db_column='FBE', blank=False, null=False)
    mse = models.IntegerField(db_column='MSE', blank=False, null=False)
    mgse = models.IntegerField(db_column='MGSE', blank=False, null=False)
    mdhs = models.IntegerField(db_column='MDHS', blank=False, null=False)
    fos = models.IntegerField(db_column='FoS', blank=False, null=False)
    abp = models.IntegerField(db_column='ABP', blank=False, null=False)
    mls = models.IntegerField(db_column='MLS', blank=False, null=False)
    vcamcm = models.IntegerField(db_column='VCAMCM', blank=False, null=False)
    services = models.IntegerField(db_column='Other', blank=False, null=False)
    unknown = models.IntegerField(db_column='Unknown', blank=False, null=False)

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.date)

    class Meta:
        abstract = True


class CloudAllocated(CloudTotalsByFaculty):
    """
    Contains the totals for the vcpu's allocated by each faculty
    """

    class Meta:
        db_table = 'cloud_allocated'


class CloudUsed(CloudTotalsByFaculty):
    """
    Contains the totals for the number of vcpu's fired up by each faculty
    """

    class Meta:
        db_table = 'cloud_used'


class CloudActiveUsers(models.Model):
    """
    Contains the active users.
    """
    date = models.TextField(primary_key=True, blank=False, null=False,
                            help_text="The date on which the values in "
                                      "the row were calculated")
    at_uom_only = models.IntegerField(blank=False, null=False,
                                      help_text="The number of UoM users who "
                                                "are only running VM's in UoM "
                                                "cells")
    elsewhere_only = models.IntegerField(blank=False, null=False,
                                         help_text="The number of UoM users "
                                                   "who are only running VM's "
                                                   "in cells outside of UoM")
    in_both = models.IntegerField(blank=False, null=False,
                                  help_text="The number of UoM users who are "
                                            "running VM's in both UoM cells "
                                            "and cells outside of UoM")
    others_at_uom = models.IntegerField(blank=False, null=False,
                                        help_text="Users not from UoM who are "
                                                  "running VM's in UoM cells")

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.date)

    class Meta:
        managed = False
        db_table = 'cloud_active_users'


class CloudTopTwenty(models.Model):
    """
    The top twenty UoM users of the cloud, by date.
    """
    date = models.TextField(primary_key=True,
                            help_text="The date on which the values "
                                      "were calculated")
    project_id = models.CharField(primary_key=True, max_length=32,
                                  help_text="The project ID")
    vcpus = models.IntegerField(help_text="The project VCPU count on the date")
    tenant_name = models.CharField(max_length=64,
                                   help_text="The project's formal name")

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.date)

    class Meta:
        managed = False
        db_table = 'cloud_top_twenty'
        unique_together = (('date', 'project_id'),)


class CloudPrivateCell(models.Model):
    """
    The projects that have an instances running for at least a day in
    our private cell
    """
    date = models.TextField(help_text="The date on which the values "
                                      "were calculated")
    project_id = models.CharField(max_length=32, help_text="The project ID")
    vcpus = models.IntegerField(help_text="The project VCPU count on the date")
    instances = models.IntegerField(
        help_text="The project instance count on the date")
    display_name = models.CharField(max_length=64,
                                    help_text="The project's formal name")
    organization = models.CharField(max_length=255,
                                    help_text="The organization the project "
                                              "belongs to")
    faculty = models.CharField(max_length=10,
                               default="Unknown",
                               help_text="The faculty the project belongs to")

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.date)

    class Meta:
        db_table = 'cloud_private_cell'
        unique_together = (('date', 'project_id'),)


class StorageTotalsByProduct(models.Model):
    date = models.TextField(primary_key=True, blank=False, null=False,
                            help_text="The date on which the values in "
                                      "the row were calculated"
                            )
    computational = models.DecimalField(blank=False,
                                        null=False,
                                        decimal_places=2,
                                        max_digits=15)
    market = models.DecimalField(blank=False,
                                 null=False,
                                 decimal_places=2,
                                 max_digits=15)
    vault = models.DecimalField(blank=False,
                                null=False,
                                decimal_places=2,
                                max_digits=15)

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.date)

    class Meta:
        managed = False
        abstract = True


class StorageAllocated(StorageTotalsByProduct):
    class Meta:
        managed = False
        db_table = 'storage_allocated'


class StorageUsed(StorageTotalsByProduct):
    class Meta:
        managed = False
        db_table = 'storage_used'


class StorageHeadroomUnused(StorageTotalsByProduct):
    class Meta:
        managed = False
        db_table = 'storage_headroom_unused'


class StorageCapacity(StorageTotalsByProduct):
    class Meta:
        managed = False
        db_table = 'storage_capacity'


class StorageHeadroomUnallocated(StorageTotalsByProduct):
    class Meta:
        managed = False
        db_table = 'storage_headroom_unallocated'


class StorageTotalsByFaculty(models.Model):
    date = models.TextField(primary_key=True, blank=False, null=False,
                            help_text="The date on which the values in "
                                      "the row were calculated")
    foa = models.DecimalField(db_column='FoA', blank=False, null=False,
                              decimal_places=2,
                              max_digits=15)
    vas = models.DecimalField(db_column='VAS', blank=False, null=False,
                              decimal_places=2,
                              max_digits=15)
    fbe = models.DecimalField(db_column='FBE', blank=False, null=False,
                              decimal_places=2,
                              max_digits=15)
    mse = models.DecimalField(db_column='MSE', blank=False, null=False,
                              decimal_places=2,
                              max_digits=15)
    mgse = models.DecimalField(db_column='MGSE', blank=False, null=False,
                               decimal_places=2,
                               max_digits=15)
    mdhs = models.DecimalField(db_column='MDHS', blank=False, null=False,
                               decimal_places=2,
                               max_digits=15)
    fos = models.DecimalField(db_column='FoS', blank=False, null=False,
                              decimal_places=2,
                              max_digits=15)
    abp = models.DecimalField(db_column='ABP', blank=False, null=False,
                              decimal_places=2,
                              max_digits=15)
    mls = models.DecimalField(db_column='MLS', blank=False, null=False,
                              decimal_places=2,
                              max_digits=15)
    vcamcm = models.DecimalField(db_column='VCAMCM', blank=False, null=False,
                                 decimal_places=2,
                                 max_digits=15)
    external = models.DecimalField(blank=False, null=False, decimal_places=2,
                                   max_digits=15)
    services = models.DecimalField(blank=False, null=False, decimal_places=2,
                                   max_digits=15)
    unknown = models.DecimalField(blank=False, null=False, decimal_places=2,
                                  max_digits=15)

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.date)

    class Meta:
        managed = False
        abstract = True


class StorageAllocatedByFaculty(StorageTotalsByFaculty):
    class Meta:
        managed = False
        db_table = 'storage_allocated_by_faculty'


class StorageAllocatedByFacultyCompute(StorageTotalsByFaculty):
    class Meta:
        managed = False
        db_table = 'storage_allocated_by_faculty_compute'


class StorageAllocatedByFacultyMarket(StorageTotalsByFaculty):
    class Meta:
        managed = False
        db_table = 'storage_allocated_by_faculty_market'


class StorageAllocatedByFacultyVault(StorageTotalsByFaculty):
    class Meta:
        managed = False
        db_table = 'storage_allocated_by_faculty_vault'


class StorageUsedByFaculty(StorageTotalsByFaculty):
    class Meta:
        managed = False
        db_table = 'storage_used_by_faculty'


class StorageUsedByFacultyCompute(StorageTotalsByFaculty):
    class Meta:
        managed = False
        db_table = 'storage_used_by_faculty_compute'


class StorageUsedByFacultyMarket(StorageTotalsByFaculty):
    class Meta:
        managed = False
        db_table = 'storage_used_by_faculty_market'


class StorageUsedByFacultyVault(StorageTotalsByFaculty):
    class Meta:
        managed = False
        db_table = 'storage_used_by_faculty_vault'


class StorageHeadroomUnusedByFaculty(StorageTotalsByFaculty):
    class Meta:
        managed = False
        db_table = 'storage_headroom_unused_by_faculty'


class StorageHeadroomUnusedByFacultyCompute(StorageTotalsByFaculty):
    class Meta:
        managed = False
        db_table = 'storage_headroom_unused_by_faculty_compute'


class StorageHeadroomUnusedByFacultyMarket(StorageTotalsByFaculty):
    class Meta:
        managed = False
        db_table = 'storage_headroom_unused_by_faculty_market'


class StorageHeadroomUnusedByFacultyVault(StorageTotalsByFaculty):
    class Meta:
        managed = False
        db_table = 'storage_headroom_unused_by_faculty_vault'


class BroadcastEmail(models.Model):
    """
    Email that is sent to all users of the application.
    """
    subject = models.CharField(max_length=200)
    created = models.DateTimeField(default=timezone.now)
    message = models.TextField()

    def __str__(self):
        return self.subject

    class Meta:
        verbose_name = "Broadcast Email"
        verbose_name_plural = "Broadcast Emails"


class CloudQuarterly(CloudTotalsByFaculty):
    """
    Contains the quarterly number of active users by faculty
    Note that the date column here is the date of the quarter end
    """

    class Meta:
        db_table = 'cloud_quarterly'


class CloudQuarterlyUsage(models.Model):
    """
    Contains the quarterly usage figures for the research cloud
    Note that the date column here is the date of the quarter end
    """
    date = models.TextField(unique=True, blank=False, null=False,
                            primary_key=True,
                            default=timezone.now,
                            help_text="The quarter end date")
    projects_active = models.IntegerField(blank=False, null=False,
                                          help_text="The total count of "
                                                    "active projects")
    uom_projects_active = models.IntegerField(blank=False, null=False,
                                              default=0,
                                              help_text="The count of approved"
                                                        " UoM projects active")
    all_uom_projects_active = models.IntegerField(blank=False, null=False,
                                                  default=0,
                                                  help_text="The count of all "
                                                            "UoM projects "
                                                            "active")
    uom_participation = models.IntegerField(blank=False, null=False,
                                            default=0,
                                            help_text="The count of projects "
                                                      "active with UoM users")
    all_users_active = models.IntegerField(blank=False, null=False,
                                            default=0,
                                            help_text="The count of all users "
                                                      "active")
    uom_users_active = models.IntegerField(blank=False, null=False,
                                           default=0,
                                           help_text="The total count of UoM "
                                                     "users active")

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.date)

    class Meta:
        db_table = 'cloud_quarterly_usage'
