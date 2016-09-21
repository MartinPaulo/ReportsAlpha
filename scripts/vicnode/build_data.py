import logging

from datetime import date, timedelta

from scripts.cloud.utility import date_range


def build_allocated(extract_db, load_db, start_day=None, end_day=date.today()):
    if not start_day:
        start_day = load_db.get_storage_allocated_last_run_date()
    logging.info("Building storage data allocated from %s till %s",
                 start_day, end_day)
    for day_date in date_range(start_day, end_day):
        logging.info("Building storage data allocated for %s", day_date)
        result_set = extract_db.get_allocated(day_date)
        for result in result_set:
            load_db.save_storage_allocated(day_date, result)


def build_allocated_by_faculty(extract_db, load_db, start_day=None,
                               end_day=date.today()):
    if not start_day:
        start_day = load_db.get_storage_allocated_by_faculty_last_run_date()
    logging.info("Building storage data allocated by faculty from %s till %s",
                 start_day, end_day)
    for day_date in date_range(start_day, end_day):
        logging.info("Building storage data allocated by faculty for %s",
                     day_date)
        faculty_totals = {'FoA': 0, 'VAS': 0, 'FBE': 0, 'MSE': 0,
                          'MGSE': 0, 'MDHS': 0, 'FoS': 0, 'ABP': 0,
                          'MLS': 0, 'VCAMCM': 0,
                          'unknown': 0, 'external': 0, 'services': 0}
        result_set = extract_db.get_allocated_by_faculty(day_date)
        for result in result_set:
            faculty_totals[result['faculty']] += result["used"]
        load_db.save_storage_allocated_by_faculty(day_date, faculty_totals)
