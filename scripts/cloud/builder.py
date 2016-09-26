import logging
from datetime import date

from scripts.cloud.utility import date_range, get_new_faculty_totals


def build_active(extract_db, load_db, start_day=None, end_day=date.today()):
    if not start_day:
        start_day = load_db.get_active_last_run_date()
    logging.info("Building active user data from %s till %s",
                 start_day, end_day)
    # on the 2016-03-11 we have 452 UoM users in total, with
    # 309 running elsewhere,
    # 233 running at UoM and 92 users are running in both UoM
    # and elsewhere. so we have:
    # set A = 309, set B = 233, A ∪ B = 452 and A ∩ B = 92
    for day_date in date_range(start_day, end_day):
        logging.info("Building active user data for %s", day_date)
        user_counts = {
            'date': day_date.strftime("%Y-%m-%d"),
            'others_at_uom': extract_db.get_count_of_others_at_uom(day_date),
            'in_both': extract_db.get_in_both(day_date),
            'elsewhere_only': extract_db.get_elsewhere_only(day_date),
            'at_uom_only': extract_db.get_uom_only(day_date)
        }
        load_db.save_active(user_counts)


def build_used(extract_db, load_db, start_day=None, end_day=date.today()):
    if not start_day:
        start_day = load_db.get_used_last_run_date()
    logging.info("Building used data from %s till %s",
                 start_day, end_day)
    for day_date in date_range(start_day, end_day):
        logging.info("Building used data for %s", day_date)
        faculty_totals = get_new_faculty_totals()
        result_set = extract_db.get_used_data(day_date)
        for row in result_set:
            project_id = row["project_id"]
            faculties = load_db.get_faculty_abbreviations(project_id)
            for faculty in faculties:
                faculty_totals[faculty] += int(row["vcpus"])
        faculty_totals['date'] = day_date.strftime("%Y-%m-%d")
        load_db.save_used_data(faculty_totals)


def build_top_twenty(extract_db, load_db, start_day=None,
                     end_day=date.today()):
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
        faculty_totals = get_new_faculty_totals()
        result_set = extract_db.get_allocated_totals(day_date)
        for row in result_set:
            project_id = row["tenant_uuid"]
            faculties = load_db.get_faculty_abbreviations(project_id)
            for faculty in faculties:
                # faculty_totals[faculty] += 1 / len(faculties)
                # currently each faculty will be assigned the projects cores...
                faculty_totals[faculty] += row["cores"]
        load_db.save_faculty_allocated(day_date, faculty_totals)