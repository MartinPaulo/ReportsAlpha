import logging
from datetime import date

from scripts.cloud.utility import date_range, get_new_faculty_totals


def build_used(extract_db, load_db, start_day, end_day=date.today()):
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
