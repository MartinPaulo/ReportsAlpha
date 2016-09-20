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
