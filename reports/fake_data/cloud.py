import calendar
import copy
from datetime import datetime
from random import randint


def get_empty_set(key_value):
    return {"key": key_value, "values": []}


def populate_values(target_set):
    total_days = randint(0, 360)
    for month in range(1, 13):
        days_in_month = get_days_in_month(month)
        for day in range(1, days_in_month + 1):
            total_days += 1
            if randint(1, 120) == 60:
                total_days = 0
            timestamp = get_time_stamp(day, month)
            target_set["values"].append([timestamp, total_days])
    return target_set


def get_days_in_month(month):
    return calendar.monthrange(2015, month)[1]


def get_time_stamp(day, month):
    dt = datetime(2015, month, day)
    epoch = datetime.utcfromtimestamp(0)
    timestamp = int((dt - epoch).total_seconds()) * 1000
    return timestamp


def data():
    # we don't want to recalculate this on every load, so we attach it as an attribute to the function
    # if it hasn't been calculated...
    if not hasattr(data, 'uptime'):
        noble_park = populate_values(get_empty_set("noble park"))
        queensbury_1 = populate_values(get_empty_set("queensbury 1"))
        queensbury_2 = populate_values(get_empty_set("queensbury 2"))
        data.uptime = [noble_park, queensbury_1, queensbury_2]
    return data.uptime


MONTH = get_time_stamp(get_days_in_month(11), 11)
THREE_MONTHS = get_time_stamp(get_days_in_month(8), 8)
SIX_MONTHS = get_time_stamp(get_days_in_month(5), 5)


def determine(sample, duration):
    if (duration == 'oneMonth') and sample[0] < MONTH:
        return False
    elif (duration == 'threeMonths') and sample[0] < THREE_MONTHS:
        return False
    elif (duration == 'sixMonths') and sample[0] < SIX_MONTHS:
        return False
    return True


def get_uptime(duration, category):
    result = copy.deepcopy(data())
    for entry in result:
        entry['values'][:] = [sample for sample in entry['values'] if determine(sample, duration)]
    return result
