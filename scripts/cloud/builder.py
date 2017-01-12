# coding=UTF-8
import calendar
import logging
from datetime import date, timedelta

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import mail_admins
from django.utils.dateparse import parse_date

from reports.models import CloudPrivateCell, CloudQuarterly, \
    CloudQuarterlyUsage
from scripts.cloud.build_project_faculty import get_faculties_for
from scripts.cloud.utility import date_range, Faculties, quarter_dates


def _get_non_null(value, default):
    """
    :return: value if it is not None, else default
    """
    return value if value is not None else default


def _last_record_date(model, field_name, attr_name, default_date):
    """ A utility method to get the latest date in a models backing table

    Args:
        model (model): The model that we want to find the last record for
        field_name (str): The field name to use in getting the latest record
        attr_name (str): The model attribute to read the date from
        default_date (date): The default to return if no record is found

    Returns:
        date: The latest date in the models backing table, else `default_date`

    """
    try:
        latest = model.objects.latest(field_name)
        result = parse_date(getattr(latest, attr_name))
    except ObjectDoesNotExist:
        logging.warning(
            "Could not find starting date for %s" % model)
        result = default_date
    return result


def build_active(extract_db, load_db, start_day=None, end_day=date.today()):
    """ Builds a count of users who run in UoM data centers (and the users
    belonging to UoM projects who run outside of UoM data centers).
    :param extract_db: The db from which to extract the data
    :param load_db: The db to move the transformed data to
    :param start_day: The day on which to start the data transformation on.
                    If None, then the date will be from the last day this
                    method was run on
    :param end_day: The date on which to stop the data transformation. Defaults
                    to today.
    """
    if not start_day:
        start_day = load_db.get_active_last_run_date()
    logging.info("Building active user data from %s till %s",
                 start_day, end_day)
    for day_date in date_range(start_day, end_day):
        logging.info("Building active user data for %s", day_date)
        others_at_uom = extract_db.get_count_of_others_at_uom(day_date)
        uom_only = extract_db.get_uom_only(day_date)
        elsewhere_only = extract_db.get_elsewhere_only(day_date)
        # in_both = extract_db.get_in_both(day_date)
        # but above line is slow, slow rather:
        all_outside = extract_db.get_all_outside(day_date)
        in_both = all_outside - elsewhere_only
        user_counts = {
            'date': day_date.strftime("%Y-%m-%d"),
            'others_at_uom': others_at_uom,
            'in_both': in_both,
            'elsewhere_only': elsewhere_only,
            'at_uom_only': uom_only
        }
        load_db.save_active(user_counts)


def build_used(extract_db, load_db, start_day=None, end_day=date.today()):
    if not start_day:
        start_day = load_db.get_used_last_run_date()
    logging.info("Building used data from %s till %s",
                 start_day, end_day)
    for day_date in date_range(start_day, end_day):
        logging.info("Building used data for %s", day_date)
        totals = Faculties.get_new_totals()
        result_set = extract_db.get_used_data(day_date)
        for row in result_set:
            project_id = row["project_id"]
            faculty = load_db.get_faculty_abbreviations(project_id)
            totals[faculty] += int(row["vcpus"])
        totals['date'] = day_date.strftime("%Y-%m-%d")
        load_db.save_used_data(totals)


def build_top_twenty(extract_db, load_db, start_day=None,
                     end_day=date.today()):
    """
    Build the top twenty projects by vcpu utilization.
    :param extract_db: The db from which to extract the data
    :param load_db: The db to move the transformed data to
    :param start_day: The day on which to start the data transformation on.
                    If None, then the date will be from the last day this
                    method was run on
    :param end_day: The date on which to stop the data transformation. Defaults
                    to today.
    """
    if not start_day:
        start_day = load_db.get_top_twenty_last_run_date()
    logging.info("Building top twenty data from %s till %s", start_day,
                 end_day)
    for day_date in date_range(start_day, end_day):
        logging.info("Building top twenty data for %s", day_date)
        result_set = extract_db.get_top_twenty_projects(day_date)
        for row in result_set:
            user_counts = {
                'date': row["date"],
                'project_id': row["project_id"],
                'vcpus': int(row["vcpus"]),
                'tenant_name': row["tenant_name"]
            }
            load_db.save_top_twenty_data(user_counts)


def build_faculty_allocated(extract_db, load_db, start_day=None,
                            end_day=date.today()):
    if not start_day:
        start_day = load_db.get_faculty_allocated_last_run_date()
    logging.info("Building cloud allocated data from %s till %s",
                 start_day, end_day)
    for day_date in date_range(start_day, end_day):
        logging.info("Building cloud allocated data for %s", day_date)
        totals = Faculties.get_new_totals()
        result_set = extract_db.get_allocated_totals(day_date)
        for row in result_set:
            project_id = row["project_id"]
            faculty = load_db.get_faculty_abbreviations(project_id)
            totals[faculty] += row["quota_vcpus"]
        load_db.save_faculty_allocated(day_date, totals)


def test_db(extract_db, load_db, start_day=None, end_day=date.today()):
    """
    There are two tests that we need to do on the extract db:
    1) Is the reporting database still fetching data (it sometimes fails)
    2) Have new cells been added to the list of known cells?
    """
    # find out when we last took readings from the instances table
    if not start_day:
        start_day = load_db.get_used_last_run_date()
    logging.info("Checking if entries since last run date %s ", start_day)
    count = extract_db.count_instances_since(start_day)
    if count <= 0:
        warning_message = "No instances have been launched since %s"
        mail_admins("No instance warning!", warning_message % start_day)
        logging.warning(warning_message, start_day)
    else:
        logging.info("There have been %s instances launched since %s", count,
                     start_day)
    found_cell_names = extract_db.get_cell_names()
    differences = settings.CELL_NAMES.symmetric_difference(found_cell_names)
    if len(differences):
        warning_message = "NeCTAR cell names have been changed! "
        information = "Cell Names have changed. The differences are: %s"
        logging.warning(information, differences)
        mail_admins(warning_message, information % differences)


def build_capacity(unknown_source, load_db, start_day=None,
                   end_day=date.today()):
    if not start_day:
        start_day = load_db.get_cloud_capacity_last_run_date()
    logging.info("Building cloud capacity data from %s till %s",
                 start_day, end_day)
    for day_date in date_range(start_day, end_day):
        logging.info("Building cloud capacity data for %s", day_date)
        capacity_totals = unknown_source.get_cloud_capacity(day_date)
        load_db.save_cloud_capacity(day_date, capacity_totals)


def build_private_cell_data(extract_db, load_db, start_day=None,
                            end_day=date.today()):
    if not start_day:
        start_day = _last_record_date(CloudPrivateCell, 'id', 'date',
                                      date.today() - timedelta(1))
    logging.info("Building private cell data from %s till %s",
                 start_day, end_day)
    for day_date in date_range(start_day, end_day):
        logging.info("Building private cell data for %s", day_date)
        result_set = extract_db.get_private_cell_data(day_date)
        for row in result_set:
            project_id = row['project_id']
            faculty = load_db.get_faculty_abbreviations(project_id)
            CloudPrivateCell.objects.update_or_create(
                date=day_date.strftime("%Y-%m-%d"),
                project_id=project_id,
                defaults={
                    'vcpus': row['vcpus'],
                    'instances': row['instances'],
                    'organization': _get_non_null(row['organisation'],
                                                  'Unknown'),
                    'display_name': row['display_name'],
                    'faculty': faculty
                }
            )


def build_buyers_committee(extract_db, load_db, **kwargs):
    logging.info("Building quarterly usage data")
    usage_start_date = _last_record_date(CloudQuarterlyUsage,
                                         'date',
                                         'date',
                                         date(2011, 12, 31))
    quarterly_start_date = _last_record_date(CloudQuarterly, 'date', 'date',
                                             date(2011, 12, 31))
    for start_date, end_date in quarter_dates():
        if usage_start_date < start_date:
            projects_active = extract_db.get_projects_active(start_date,
                                                             end_date)
            uom_projects_active = extract_db.get_uom_projects_active(
                start_date,
                end_date)
            uom_participation = extract_db.get_projects_active_with_uom_participation(
                start_date,
                end_date)
            uom_users_active = extract_db.get_uom_users_active(start_date,
                                                               end_date)
            CloudQuarterlyUsage.objects.update_or_create(
                date=end_date.strftime("%Y-%m-%d"),
                projects_active=projects_active,
                uom_projects_active=uom_projects_active,
                uom_participation=uom_participation,
                uom_users_active=uom_users_active
            )
        if quarterly_start_date < start_date:
            totals = Faculties.get_new_totals()
            result_set = extract_db.get_email_of_active_uom_users(start_date,
                                                                  end_date)
            for row in result_set:
                contact_email = row['email']
                faculties = get_faculties_for(contact_email)
                for faculty in faculties:
                    totals[faculty] += 1
            CloudQuarterly.objects.update_or_create(
                date=end_date.strftime("%Y-%m-%d"),
                defaults={
                    'foa': totals['FoA'],
                    'vas': totals['VAS'],
                    'fbe': totals['FBE'],
                    'mse': totals['MSE'],
                    'mgse': totals['MGSE'],
                    'mdhs': totals['MDHS'],
                    'fos': totals['FoS'],
                    'abp': totals['ABP'],
                    'mls': totals['MLS'],
                    'vcamcm': totals['VCAMCM'],
                    'services': totals['Other'],
                    'unknown': totals['Unknown']
                }
            )
