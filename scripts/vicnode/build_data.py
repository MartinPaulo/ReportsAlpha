import logging

from datetime import date, timedelta

from scripts.cloud.utility import date_range


def _get_faculty_totals():
    return {'FoA': 0, 'VAS': 0, 'FBE': 0, 'MSE': 0,
            'MGSE': 0, 'MDHS': 0, 'FoS': 0, 'ABP': 0,
            'MLS': 0, 'VCAMCM': 0,
            'unknown': 0, 'external': 0, 'services': 0}


def build_allocated(extract_db, load_db, start_day=None, end_day=date.today()):
    if not start_day:
        start_day = load_db.get_storage_allocated_last_run_date()
    logging.info("Building storage data allocated from %s till %s",
                 start_day, end_day)
    for day_date in date_range(start_day, end_day):
        logging.info("Building storage data allocated for %s", day_date)
        product_totals = {'computational': 0, 'market': 0, 'vault': 0}
        result_set = extract_db.get_allocated(day_date)
        for result in result_set:
            product_totals[result['product']] += result["sum"]
        load_db.save_storage_allocated(day_date, product_totals)


def build_allocated_by_faculty(extract_db, load_db, start_day=None,
                               end_day=date.today()):
    if not start_day:
        start_day = load_db.get_storage_allocated_by_faculty_last_run_date()
    logging.info("Building storage allocated by faculty from %s till %s",
                 start_day, end_day)
    for day_date in date_range(start_day, end_day):
        logging.info("Building storage allocated by faculty for %s",
                     day_date)
        faculty_totals = _get_faculty_totals()
        result_set = extract_db.get_allocated_by_faculty(day_date)
        for result in result_set:
            faculty_totals[result['faculty']] += result["used"]
        load_db.save_storage_allocated_by_faculty(day_date, faculty_totals)


def build_allocated_by_faculty_compute(extract_db, load_db, start_day=None,
                                       end_day=date.today()):
    if not start_day:
        start_day = \
            load_db.get_storage_allocated_by_faculty_compute_last_run_date()
    logging.info("Building storage compute allocated by faculty "
                 "from %s till %s",
                 start_day, end_day)
    for day_date in date_range(start_day, end_day):
        logging.info("Building storage compute allocated by faculty for %s",
                     day_date)
        faculty_totals = _get_faculty_totals()
        result_set = extract_db.get_allocated_by_faculty(day_date,
                                                         'computational')
        for result in result_set:
            faculty_totals[result['faculty']] += result["used"]
        load_db.save_storage_allocated_by_faculty_compute(day_date,
                                                          faculty_totals)


def build_allocated_by_faculty_market(extract_db, load_db, start_day=None,
                                      end_day=date.today()):
    if not start_day:
        start_day = \
            load_db.get_storage_allocated_by_faculty_market_last_run_date()
    logging.info("Building storage market allocated by faculty "
                 "from %s till %s",
                 start_day, end_day)
    for day_date in date_range(start_day, end_day):
        logging.info("Building storage market allocated by faculty for %s",
                     day_date)
        faculty_totals = _get_faculty_totals()
        result_set = extract_db.get_allocated_by_faculty(day_date,
                                                         'market')
        for result in result_set:
            faculty_totals[result['faculty']] += result["used"]
        load_db.save_storage_allocated_by_faculty_market(day_date,
                                                         faculty_totals)


def build_allocated_by_faculty_vault(extract_db, load_db, start_day=None,
                                     end_day=date.today()):
    if not start_day:
        start_day = \
            load_db.get_storage_allocated_by_faculty_vault_last_run_date()
    logging.info("Building storage vault allocated by faculty "
                 "from %s till %s",
                 start_day, end_day)
    for day_date in date_range(start_day, end_day):
        logging.info("Building storage vault allocated by faculty for %s",
                     day_date)
        faculty_totals = _get_faculty_totals()
        result_set = extract_db.get_allocated_by_faculty(day_date,
                                                         'vault')
        for result in result_set:
            faculty_totals[result['faculty']] += result["used"]
        load_db.save_storage_allocated_by_faculty_vault(day_date,
                                                        faculty_totals)


def build_used(extract_db, load_db, start_day, end_day=date.today()):
    if not start_day:
        start_day = load_db.get_storage_used_last_run_date()
    logging.info("Building storage used from %s till %s",
                 start_day, end_day)
    for day_date in date_range(start_day, end_day):
        logging.info("Building storage used for %s", day_date)
        product_totals = {'computational': 0, 'market': 0, 'vault': 0}
        result_set = extract_db.get_storage_used(day_date)
        for result in result_set:
            product_totals[result['product']] += result["sum"]
        load_db.save_storage_used(day_date, product_totals)


def build_used_by_faculty(extract_db, load_db, start_day,
                          end_day=date.today()):
    if not start_day:
        start_day = load_db.get_storage_used_by_faculty_last_run_date()
    logging.info("Building storage used by faculty from %s till %s",
                 start_day, end_day)
    for day_date in date_range(start_day, end_day):
        logging.info("Building storage used by faculty for %s", day_date)
        faculty_totals = _get_faculty_totals()
        result_set = extract_db.get_used_by_faculty(day_date)
        for result in result_set:
            faculty_totals[result['faculty']] += result["used"]
        load_db.save_storage_used_by_faculty(day_date, faculty_totals)
