import logging
from datetime import date

from scripts.cloud.utility import date_range, get_new_faculty_totals


def build_faculty_allocated(extract_db, load_db, start_day=None,
                            end_day=date.today()):
    if not start_day:
        start_day = load_db.get_faculty_allocated_last_run_date()
    logging.info("Building allocated data from %s till %s",
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
