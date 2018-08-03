# coding=UTF-8
import logging
from datetime import date, timedelta

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import mail_admins
from django.utils.dateparse import parse_date

from reports.models import CloudPrivateCell, CloudQuarterly, \
    CloudQuarterlyUsage, CloudProjectFaculty, CloudQuarterlyCoreHours
from scripts.cloud.utility import date_range, Faculties, quarter_dates, LDAP


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
            'Could not find starting date for %s' % model)
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
    logging.info("Checking if entries since start day %s ", start_day)
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
        # The cell names change order between runs...
        # This message goes out every day until something is done about
        # the change in cell names. This is too verbose. The change should
        # somehow be remembered and a new message only sent if they change
        # again
        warning_message = "NeCTAR cell names have been changed! "
        information = "Cell Names have changed. The differences are: %s"
        logging.warning(information, differences)
        mail_admins(warning_message, information % differences,
                    fail_silently=True)


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
    usage_start_date = _last_record_date(CloudQuarterlyUsage, 'date', 'date',
                                         date(2011, 12, 31))
    quarterly_start_date = _last_record_date(CloudQuarterly, 'date', 'date',
                                             date(2011, 12, 31))
    cpu_hours_start_date = _last_record_date(CloudQuarterlyCoreHours, 'date',
                                             'date', date(2011, 12, 31))
    for start_date, end_date, _quarter in quarter_dates():
        if usage_start_date < start_date:
            _build_activity_figures(extract_db, start_date, end_date)
        if quarterly_start_date < start_date:
            _build_users_faculties(extract_db, start_date, end_date)
        if cpu_hours_start_date < start_date:
            _build_cpu_hours(extract_db, start_date, end_date)


def _build_cpu_hours(extract_db, start_date, end_date):
    logging.info('Building quarterly core hours')
    core_hours = extract_db.get_core_hours(start_date, end_date)
    vcpu_hours = Faculties.get_new_totals()
    for core_hour in core_hours:
        project_id = core_hour['project_id']
        try:
            project_faculty = CloudProjectFaculty.objects.get(
                project_id=project_id)
            project_faculty = project_faculty.allocated_faculty
            vcpu_hours[Faculties(project_faculty)] += core_hour[
                'vcpu_hours']
        except CloudProjectFaculty.DoesNotExist:
            logging.warning(
                '%s with id %s does not have a faculty assigned' % (
                    core_hour['project_name'], project_id))
    CloudQuarterlyCoreHours.objects.update_or_create(
        date=end_date.strftime("%Y-%m-%d"),
        defaults={
            'foa': vcpu_hours[Faculties.FOA],
            'vas': vcpu_hours[Faculties.VAS],
            'fbe': vcpu_hours[Faculties.FBE],
            'mse': vcpu_hours[Faculties.MSE],
            'mgse': vcpu_hours[Faculties.MGSE],
            'mdhs': vcpu_hours[Faculties.MDHS],
            'fos': vcpu_hours[Faculties.FOS],
            'abp': vcpu_hours[Faculties.ABP],
            'mls': vcpu_hours[Faculties.MLS],
            'vcamcm': vcpu_hours[Faculties.VCAMCM],
            'services': vcpu_hours[Faculties.OTHER],
            'unknown': vcpu_hours[Faculties.UNKNOWN]
        }
    )


def _build_users_faculties(extract_db, start_date, end_date):
    user_totals = Faculties.get_new_totals()
    active_uom_users = extract_db.get_email_of_active_uom_users(start_date,
                                                                end_date)
    ldap = LDAP()
    for uom_user in active_uom_users:
        faculties = ldap.find_faculty(uom_user['email'])
        user_totals[faculties[0]] += 1
    CloudQuarterly.objects.update_or_create(
        date=end_date.strftime("%Y-%m-%d"),
        defaults={
            'foa': user_totals['FoA'],
            'vas': user_totals['VAS'],
            'fbe': user_totals['FBE'],
            'mse': user_totals['MSE'],
            'mgse': user_totals['MGSE'],
            'mdhs': user_totals['MDHS'],
            'fos': user_totals['FoS'],
            'abp': user_totals['ABP'],
            'mls': user_totals['MLS'],
            'vcamcm': user_totals['VCAMCM'],
            'services': user_totals['Other'],
            'unknown': user_totals['Unknown']
        }
    )


def _build_activity_figures(extract_db, start_date, end_date):
    projects_active = extract_db.get_projects_active(start_date,
                                                     end_date)
    uom_approved_projects_active = extract_db.get_approved_uom_projects_active(
        start_date,
        end_date)
    uom_all_projects_active = extract_db.get_all_uom_projects_active(
        start_date,
        end_date
    )
    uom_participation = extract_db.get_all_projects_active_with_uom_participation(
        start_date,
        end_date)
    all_users_active = extract_db.get_admins_active(start_date,
                                                    end_date)
    uom_users_active = extract_db.get_uom_users_active(start_date,
                                                       end_date)
    CloudQuarterlyUsage.objects.update_or_create(
        date=end_date.strftime("%Y-%m-%d"),
        projects_active=projects_active,
        uom_projects_active=uom_approved_projects_active,
        all_uom_projects_active=uom_all_projects_active,
        uom_participation=uom_participation,
        all_users_active=all_users_active,
        uom_users_active=uom_users_active
    )

def _get_quarter_abbreviation(quarter_end_date):
    """
    By working out the quarter abbreviation from the date value here
    we can see in the output that we are matching the date arguments
    passed into the methods
    :param quarter_end_date: a string in the format 'YYYY-MM-DD'.
    E.g.: '2012-03-31'
    :return: A string giving the quarter abbreviation. E.g.: '2012Q1'
    """
    quarter_d = {3: 'Q1', 6: 'Q2', 9: 'Q3', 12: 'Q4'}
    d = date(*[int(x) for x in quarter_end_date.split('-')])
    return f'{d.year}{quarter_d[d.month]}'

def get_quarterly_users_and_percentages(start_day, end_day, **kwargs):
    """
    returns the contents of the cloud_quarterly table with percentages
    """
    logging.info('Fetching quarterly usage percentages from database')
    quarters = CloudQuarterly.objects.filter(
        date__gte=start_day,
        date__lte=end_day).order_by(
        '-date')[:1]
    quarter_d = {3: 'Q1', 6: 'Q2', 9: 'Q3', 12: 'Q4'}
    result = dict()
    result['cloud_users'] = []
    result['total_projects_active'] = 0
    fields = CloudQuarterly._meta.get_fields()
    for quarter in reversed(quarters):
        # sum the faculty totals for a grand total
        total = 0
        for field in fields:
            if field.name is 'unknown' or field.name is 'date':
                continue
            total += int(getattr(quarter, field.name))
        quarter_header = _get_quarter_abbreviation(getattr(quarter, 'date'))
        total_percentage = 0
        # add the percentage for each faculty
        for field in fields:
            if field.name is 'unknown' or field.name is 'date':
                continue
            percentage = int(getattr(quarter, field.name)) / total * 100
            result['cloud_users'].append((
                quarter_header,  # quarter abbreviation
                field.name.upper(),  # faculty
                int(getattr(quarter, field.name)),  # active users
                round(percentage, 2)))  # percentage of UoM users
            total_percentage += percentage
        # the total percentage should be 100, all going well
        return result


def get_quarterly_cpu_hours(start_day, end_day, **kwargs):
    """
    Gets the quarterly usage in core hours.
    """
    logging.info('Fetching quarterly core hours and percentages from database')
    result = dict()
    result['cloud_hours'] = []
    # faculties_list = Faculties.get_faculties_list()
    quarters = CloudQuarterlyCoreHours.objects.filter(
        date__gte=start_day,
        date__lte=end_day).order_by(
        '-date')[:1]
    fields = CloudQuarterlyCoreHours._meta.get_fields()
    assert len(quarters) == 1
    quarter = quarters.first()
    # sum the faculty totals for a grand total
    total = 0
    for field in fields:
        if field.name is 'unknown' or field.name is 'date':
            continue
        total += int(getattr(quarter, field.name))
    # by working out the quarter abbreviation from the date value
    # we can see that we are matching the date arguments
    quarter_header = _get_quarter_abbreviation(getattr(quarter, 'date'))
    total_percentage = 0
    # add the percentage for each faculty
    for field in fields:
        if field.name is 'unknown' or field.name is 'date':
            continue
        percentage = int(getattr(quarter, field.name)) / total * 100
        result['cloud_hours'].append((
            quarter_header,  # quarter abbreviation
            field.name.upper(),  # faculty
            int(getattr(quarter, field.name)),  # active users
            round(percentage, 2)))  # percentage of UoM users
        total_percentage += percentage
    # the total percentage should be 100, all going well
    return result


def get_quarterly_usage_figures(start_day, end_day, **kwargs):
    """
    :param start_day:
    :param end_day:
    :param kwargs:
    :return: The usage figures for the quarter that falls between the start
    day and the end day
    """
    logging.info('Fetching quarterly usage from database')
    result = dict()
    # faculties_list = Faculties.get_faculties_list()
    quarters = CloudQuarterlyUsage.objects.filter(
        date__gte=start_day,
        date__lte=end_day).order_by(
        '-date')[:1]
    assert len(quarters) == 1
    quarter = quarters.first()
    result['total_projects_active'] = int(
        getattr(quarter, 'projects_active'))
    result['uom_projects_active'] = int(
        getattr(quarter, 'uom_projects_active'))
    result['uom_users_active'] = int(getattr(quarter, 'uom_users_active'))
    return result
