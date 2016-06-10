import calendar
import copy
from datetime import datetime
from random import randint


def get_empty_set(key_value):
    return {'key': key_value, 'values': []}


def get_days_in_month(month):
    return calendar.monthrange(2015, month)[1]


def get_time_stamp(day, month):
    dt = datetime(2015, month, day)
    epoch = datetime.utcfromtimestamp(0)
    timestamp = int((dt - epoch).total_seconds()) * 1000
    return timestamp


def generate_uptime(target_set):
    total_days = randint(0, 360)
    for month in range(1, 13):
        days_in_month = get_days_in_month(month)
        for day in range(1, days_in_month + 1):
            total_days += 1
            if randint(1, 120) == 60:
                total_days = 0
            timestamp = get_time_stamp(day, month)
            target_set['values'].append([timestamp, total_days])
    return target_set


def generate_active_users(target_set):
    # 1800 users in total
    total_days = 0
    for month in range(1, 13):
        days_in_month = get_days_in_month(month)
        for day in range(1, days_in_month + 1):
            total_days += 1
            new_users = randint(250 + total_days // 4, 450 + total_days // 4)
            timestamp = get_time_stamp(day, month)
            target_set['values'].append([timestamp, new_users])
    return target_set


def uptime():
    # we don't want to recalculate this on every load, so we attach it as an attribute to the function
    # if it hasn't been calculated...
    if not hasattr(uptime, 'data'):
        noble_park = generate_uptime(get_empty_set('noble park'))
        queensbury_1 = generate_uptime(get_empty_set('queensbury 1'))
        queensbury_2 = generate_uptime(get_empty_set('queensbury 2'))
        uptime.data = [noble_park, queensbury_1, queensbury_2]
    return uptime.data


def active_users():
    if not hasattr(active_users, 'data'):
        active_users.data = [generate_active_users(get_empty_set(center))
                             for center in ['noble park', 'queensbury 1', 'queensbury 2', 'other data centers']]
    return active_users.data


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


def filter_by_duration(duration, target):
    print(target)
    for entry in target:
        entry['values'][:] = [sample for sample in entry['values'] if determine(sample, duration)]
    return target


def get_uptime(duration, category):
    result = copy.deepcopy(uptime())
    return filter_by_duration(duration, result)


def get_active_users(duration, category):
    result = copy.deepcopy(active_users())
    return filter_by_duration(duration, result);
