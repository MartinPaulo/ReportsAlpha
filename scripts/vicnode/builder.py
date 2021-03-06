import logging
from datetime import date

from django.conf import settings
from django.core.mail import mail_admins

from scripts.cloud.utility import date_range
from scripts.db.vicnode_db import VAULT, COMPUTATIONAL, MARKET


def _get_new_faculty_totals():
    """
    TODO: need to harmonize the cloud the storage totals
    :return: A dictionary with the keys being the faculties and the values
             set to 0.
    """
    return {'FoA': 0, 'VAS': 0, 'FBE': 0, 'MSE': 0,
            'MGSE': 0, 'MDHS': 0, 'FoS': 0, 'ABP': 0,
            'MLS': 0, 'VCAMCM': 0,
            'unknown': 0, 'external': 0, 'services': 0}


def _get_product_totals():
    return {COMPUTATIONAL: 0, MARKET: 0, VAULT: 0}


def build_allocated(extract_db, load_db, start_day=None, end_day=date.today()):
    if not start_day:
        start_day = load_db.get_storage_allocated_last_run_date()
    logging.info("Building storage data allocated from %s till %s",
                 start_day, end_day)
    for day_date in date_range(start_day, end_day):
        logging.info("Building storage data allocated for %s", day_date)
        product_totals = _get_product_totals()
        result_set = extract_db.get_allocated(day_date)
        for result in result_set:
            product_totals[result['product']] += result["sum"]
        load_db.save_storage_allocated(day_date, product_totals)


def _build_allocated_by_faculty(extract_db, load_db, start_day=None,
                                end_day=date.today()):
    if not start_day:
        start_day = load_db.get_storage_allocated_by_faculty_last_run_date()
    logging.info("Building storage allocated by faculty from %s till %s",
                 start_day, end_day)
    for day_date in date_range(start_day, end_day):
        logging.info("Building storage allocated by faculty for %s",
                     day_date)
        faculty_totals = _get_new_faculty_totals()
        result_set = extract_db.get_allocated_by_faculty(day_date)
        for result in result_set:
            faculty_totals[result['faculty']] += result["used"]
        load_db.save_storage_allocated_by_faculty(day_date, faculty_totals)


def _build_allocated_by_faculty_compute(extract_db, load_db, start_day=None,
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
        faculty_totals = _get_new_faculty_totals()
        result_set = extract_db.get_allocated_by_faculty(day_date,
                                                         COMPUTATIONAL)
        for result in result_set:
            faculty_totals[result['faculty']] += result["used"]
        load_db.save_storage_allocated_by_faculty_compute(day_date,
                                                          faculty_totals)


def _build_allocated_by_faculty_market(extract_db, load_db, start_day=None,
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
        faculty_totals = _get_new_faculty_totals()
        result_set = extract_db.get_allocated_by_faculty(day_date,
                                                         MARKET)
        for result in result_set:
            faculty_totals[result['faculty']] += result["used"]
        load_db.save_storage_allocated_by_faculty_market(day_date,
                                                         faculty_totals)


def _build_allocated_by_faculty_vault(extract_db, load_db, start_day=None,
                                      end_day=date.today()):
    if not start_day:
        start_day = \
            load_db.get_storage_allocated_by_faculty_vault_last_run_date()
    logging.info("Building storage vault allocated by faculty "
                 "from %s till %s",
                 start_day, end_day)
    for day_date in date_range(start_day, end_day):
        logging.info("Building storage vault allocated by faculty "
                     "for %s",
                     day_date)
        faculty_totals = _get_new_faculty_totals()
        result_set = extract_db.get_allocated_by_faculty(day_date,
                                                         VAULT)
        for result in result_set:
            faculty_totals[result['faculty']] += result["used"]
        load_db.save_storage_allocated_by_faculty_vault(day_date,
                                                        faculty_totals)


def build_allocated_by_faculty(**kwargs):
    _build_allocated_by_faculty(**kwargs)
    _build_allocated_by_faculty_compute(**kwargs)
    _build_allocated_by_faculty_market(**kwargs)
    _build_allocated_by_faculty_vault(**kwargs)


def build_used(extract_db, load_db, start_day, end_day=date.today()):
    if not start_day:
        start_day = load_db.get_storage_used_last_run_date()
    logging.info("Building storage used from %s till %s",
                 start_day, end_day)
    for day_date in date_range(start_day, end_day):
        logging.info("Building storage used for %s", day_date)
        product_totals = _get_product_totals()
        result_set = extract_db.get_storage_used(day_date)
        for result in result_set:
            product_totals[result['product']] += result["sum"]
        load_db.save_storage_used(day_date, product_totals)


def _build_used_by_faculty(extract_db, load_db, start_day,
                           end_day=date.today()):
    if not start_day:
        start_day = load_db.get_storage_used_by_faculty_last_run_date()
    logging.info("Building storage used by faculty from %s till %s",
                 start_day, end_day)
    for day_date in date_range(start_day, end_day):
        logging.info("Building storage used by faculty for %s", day_date)
        faculty_totals = _get_new_faculty_totals()
        result_set = extract_db.get_used_by_faculty(day_date)
        for result in result_set:
            faculty_totals[result['faculty']] += result["sum"]
        load_db.save_storage_used_by_faculty(day_date, faculty_totals)


def _build_used_by_faculty_compute(extract_db, load_db, start_day,
                                   end_day=date.today()):
    if not start_day:
        start_day = load_db.get_storage_used_by_faculty_compute_last_run_date()
    logging.info("Building storage compute used by faculty from %s till %s",
                 start_day, end_day)
    for day_date in date_range(start_day, end_day):
        logging.info("Building storage compute used by faculty for %s",
                     day_date)
        faculty_totals = _get_new_faculty_totals()
        result_set = extract_db.get_used_by_faculty(day_date, COMPUTATIONAL)
        for result in result_set:
            faculty_totals[result['faculty']] += result["sum"]
        load_db.save_storage_used_by_faculty_compute(day_date, faculty_totals)


def _build_used_by_faculty_market(extract_db, load_db, start_day,
                                  end_day=date.today()):
    if not start_day:
        start_day = load_db.get_storage_used_by_faculty_market_last_run_date()
    logging.info("Building storage market used by faculty from %s till %s",
                 start_day, end_day)
    for day_date in date_range(start_day, end_day):
        logging.info("Building storage market used by faculty for %s",
                     day_date)
        faculty_totals = _get_new_faculty_totals()
        result_set = extract_db.get_used_by_faculty(day_date, MARKET)
        for result in result_set:
            faculty_totals[result['faculty']] += result["sum"]
        load_db.save_storage_used_by_faculty_market(day_date, faculty_totals)


def _build_used_by_faculty_vault(extract_db, load_db, start_day,
                                 end_day=date.today()):
    last_run_day = load_db.get_storage_used_by_faculty_vault_last_run_date()
    if not start_day or start_day < last_run_day:
        start_day = last_run_day
    logging.info("Building storage vault used by faculty from %s till %s",
                 start_day, end_day)
    for day_date in date_range(start_day, end_day):
        logging.info("Building storage vault used by faculty for %s", day_date)
        faculty_totals = _get_new_faculty_totals()
        result_set = extract_db.get_used_by_faculty(day_date, VAULT)
        for result in result_set:
            faculty_totals[result['faculty']] += result["sum"]
        load_db.save_storage_used_by_faculty_vault(day_date, faculty_totals)


def build_used_by_faculty(**kwargs):
    _build_used_by_faculty(**kwargs)
    _build_used_by_faculty_compute(**kwargs)
    _build_used_by_faculty_market(**kwargs)
    _build_used_by_faculty_vault(**kwargs)


def build_headroom_unused(extract_db, load_db, start_day,
                          end_day=date.today()):
    if not start_day:
        start_day = load_db.get_headroom_unused_last_run_date()
    logging.info("Building storage headroom unused from %s till %s",
                 start_day, end_day)
    for day_date in date_range(start_day, end_day):
        logging.info("Building storage headroom unused for %s", day_date)
        product_totals = _get_product_totals()
        result_set = extract_db.get_headroom_unused(day_date)
        for result in result_set:
            product_totals[result['product']] += result["headroom"]
        load_db.save_headroom_unused(day_date, product_totals)


def _build_headroom_unused_by_faculty(extract_db, load_db, start_day,
                                      end_day=date.today()):
    if not start_day:
        start_day = load_db.get_headroom_unused_by_faculty_last_run_date()
    logging.info("Building storage headroom unused by faculty from %s till %s",
                 start_day, end_day)
    for day_date in date_range(start_day, end_day):
        logging.info("Building storage headroom unused by faculty for %s",
                     day_date)
        faculty_totals = _get_new_faculty_totals()
        result_set = extract_db.get_headroom_unused_by_faculty(day_date)
        for result in result_set:
            faculty_totals[result['faculty']] += result["headroom"]
        load_db.save_storage_headroom_unused_by_faculty(day_date,
                                                        faculty_totals)


def _build_headroom_unused_by_faculty_compute(extract_db, load_db, start_day,
                                              end_day=date.today()):
    if not start_day:
        start_day = load_db.get_headroom_unused_by_faculty_compute_last_run_date()
    logging.info(
        "Building storage headroom compute unused by faculty from %s till %s",
        start_day, end_day)
    for day_date in date_range(start_day, end_day):
        logging.info(
            "Building storage headroom compute unused by faculty for %s",
            day_date)
        faculty_totals = _get_new_faculty_totals()
        result_set = extract_db.get_headroom_unused_by_faculty(day_date,
                                                               COMPUTATIONAL)
        for result in result_set:
            faculty_totals[result['faculty']] += result["headroom"]
        load_db.save_storage_headroom_unused_by_faculty_compute(day_date,
                                                                faculty_totals)


def _build_headroom_unused_by_faculty_market(extract_db, load_db, start_day,
                                             end_day=date.today()):
    if not start_day:
        start_day = load_db.get_headroom_unused_by_faculty_market_last_run_date()
    logging.info(
        "Building storage headroom market unused by faculty from %s till %s",
        start_day, end_day)
    for day_date in date_range(start_day, end_day):
        logging.info(
            "Building storage headroom market unused by faculty for %s",
            day_date)
        faculty_totals = _get_new_faculty_totals()
        result_set = extract_db.get_headroom_unused_by_faculty(day_date,
                                                               MARKET)
        for result in result_set:
            faculty_totals[result['faculty']] += result["headroom"]
        load_db.save_storage_headroom_unused_by_faculty_market(day_date,
                                                               faculty_totals)


def _build_headroom_unused_by_faculty_vault(extract_db, load_db, start_day,
                                            end_day=date.today()):
    if not start_day:
        start_day = load_db.get_headroom_unused_by_faculty_vault_last_run_date()
    logging.info(
        "Building storage headroom vault unused by faculty from %s till %s",
        start_day, end_day)
    for day_date in date_range(start_day, end_day):
        logging.info(
            "Building storage headroom vault unused by faculty for %s",
            day_date)
        faculty_totals = _get_new_faculty_totals()
        result_set = extract_db.get_headroom_unused_by_faculty(day_date, VAULT)
        for result in result_set:
            faculty_totals[result['faculty']] += result["headroom"]
        load_db.save_storage_headroom_unused_by_faculty_vault(day_date,
                                                              faculty_totals)


def build_headroom_unused_by_faculty(**kwargs):
    _build_headroom_unused_by_faculty(**kwargs)
    _build_headroom_unused_by_faculty_compute(**kwargs)
    _build_headroom_unused_by_faculty_market(**kwargs)
    _build_headroom_unused_by_faculty_vault(**kwargs)


def build_capacity(extract_db, load_db, **kwargs):
    """
    Will only find the value for the day on which this is run.
    This is because the VicNode reporting database doesn't keep a historical
    record of the changes.
    """
    day_date = date.today()
    logging.info("Building storage capacity for %s", day_date)
    product_totals = _get_product_totals()
    # There is no date so we will overwrite with the latest value
    # if this is run multiple times on a given day.
    result_set = extract_db.get_storage_capacity()
    for result in result_set:
        product_totals[result['product']] += result["capacity"]
    load_db.save_storage_capacity(day_date, product_totals)


def build_headroom_unallocated(load_db, start_day, end_day=date.today(),
                               **kwargs):
    if not start_day:
        start_day = load_db.get_storage_headroom_unallocated_last_run_date()
    logging.info("Building storage headroom unallocated from %s till %s",
                 start_day, end_day)
    for day_date in date_range(start_day, end_day):
        logging.info("Building storage headroom unallocated for %s", day_date)
        product_totals = _get_product_totals()
        result_set = load_db.get_storage_headroom_unallocated(day_date)
        for result in result_set:
            product_totals[COMPUTATIONAL] += int(result["compute_headroom"])
            product_totals[MARKET] += int(result["market_headroom"])
            product_totals[VAULT] += int(result["vault_headroom"])
        load_db.save_storage_headroom_unallocated(day_date, product_totals)


def test_db(extract_db, **kwargs):
    """
    Have new storage types been create? If so we need to notify the
    administrators...
    """
    logging.info("Testing to see if new storage types have been created")
    storage_types = extract_db.get_storage_types()
    if settings.STORAGE_PRODUCT_TYPES != storage_types:
        warning_message = "VicNode storage types have been changed"
        mail_admins(warning_message,
                    "Differences are: %s" %
                    (settings.STORAGE_PRODUCT_TYPES ^ storage_types))
        logging.warning(warning_message)
    return None
