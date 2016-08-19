import logging
from datetime import date

from scripts.cloud.utility import date_range


def build_active(extract_db, load_db, start_day, end_day=date.today()):
    logging.info("Building active user data from %s till %s ",
                 start_day, end_day)
    # on the 2016-03-11 we have 452 UoM users in total, with
    # 309 running elsewhere,
    # 233 running at UoM and 92 users are running in both UoM
    # and elsewhere. so we have:
    # set A = 309, set B = 233, A ∪ B = 452 and A ∩ B = 92
    for day_date in date_range(start_day, end_day):
        user_counts = {
            'date': day_date.strftime("%Y-%m-%d"),
            'others_at_uom': extract_db.get_count_of_others_at_uom(day_date),
            'in_both': extract_db.get_in_both(day_date),
            'elsewhere_only': extract_db.get_elsewhere_only(day_date),
            'at_uom_only': extract_db.get_uom_only(day_date)
        }
        load_db.save_active(user_counts)
