import logging
import os
from datetime import date, timedelta

import django
from django.template.loader import get_template

from scripts.cloud.utility import quarter_dates
from scripts.db import local_db


def get_start_day(days):
    result = None
    if days != 'None':
        result = date.today() - timedelta(days=int(days))
    logging.info("Start date chosen is %s", result)
    return result


if __name__ == "__main__":
    # Configuration.get_production_db()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reports_beta.settings")
    django.setup()
    t = get_template('bc_cloud.tsv')
    _args = {'load_db': local_db.DB(),
             'extract_db': None}  #: reporting_db.DB()}
    from scripts.cloud import builder as nectar

    # nectar.build_buyers_committee(**_args)
    for q_start, q_end, abbreviation in quarter_dates():
        _args['start_day'] = q_start
        _args['end_day'] = q_end
        # _args['abbreviation'] = abbreviation
        percentage_dict = nectar.get_quarterly_users_and_percentages(**_args)
        vcpu_hours_dict = nectar.get_quarterly_cpu_hours(**_args)
        usage_dict = nectar.get_quarterly_usage_figures(**_args)
        result_dict = {**percentage_dict, **vcpu_hours_dict, **usage_dict}
        print(t.render(result_dict))
