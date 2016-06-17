import calendar
import copy
from datetime import datetime
from random import randint

import numpy


def get_empty_set(key_value):
    return {'key': key_value, 'values': []}


def get_days_in_month(month):
    return calendar.monthrange(2015, month)[1]


EPOCH = datetime.utcfromtimestamp(0)


def get_day_as_time_stamp(day, month):
    return int((datetime(2015, month, day) - EPOCH).total_seconds()) * 1000


def generate_uptime(target_set):
    total_days = randint(0, 360)
    for month in range(1, 13):
        days_in_month = get_days_in_month(month)
        for day in range(1, days_in_month + 1):
            total_days += 1
            if randint(1, 120) == 60:
                total_days = 0
            timestamp = get_day_as_time_stamp(day, month)
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
            timestamp = get_day_as_time_stamp(day, month)
            target_set['values'].append([timestamp, new_users])
    return target_set


# def get_data_center_capacity(center):
#     return {  # physical cores
#         "NP": 1800,  # vcpu's 3672
#         "QH2": 2656,  # vcpu's 5312
#         "QH2-UoM": 2176,  # vcpu's 4352
#     }[center]

def get_data_center_capacity(center):
    return {
        'NeCTAR Contribution': 2000,
        'UoM Contribution': 3000,
        'Co-investment': 1000,
    }[center]

def generate_capacity(target_set, source):
    total_days = 0
    for month in range(1, 13):
        days_in_month = get_days_in_month(month)
        for day in range(1, days_in_month + 1):
            total_days += 1
            value = get_data_center_capacity(source)
            if month < 4 and source == 'NeCTAR Contribution':
                value -= 200
            if month < 7 and source == 'UoM Contribution':
                value -= 600
            if source == 'Co-investment':
                value -= 500 - 50 * month
            timestamp = get_day_as_time_stamp(day, month)
            target_set['values'].append([timestamp, value])
    return target_set


def generate_allocated(target_set, divider=1):
    start_value = randint(10, 800) // divider
    total_days = 0
    for month in range(1, 13):
        days_in_month = get_days_in_month(month)
        for day in range(1, days_in_month + 1):
            total_days += 1
            if randint(1, 13) == month:
                start_value = start_value + randint(10, 20)
            timestamp = get_day_as_time_stamp(day, month)
            target_set['values'].append([timestamp, start_value])
    return target_set


def get_free(category):
    return {
        "768": 1800,
        "2048": 657,
        "4096": 315,
        "6144": 205,
        "8192": 135,
        "12288": 83,
        "16384": 58,
        "32768": 26,
        "49152": 16,
        "65536": 12
    }[category]


def smooth_triangle(data, degree, drop_vals=False):
    """performs moving triangle smoothing with a variable degree.
    From: http://www.swharden.com/blog/2010-06-20-smoothing-window-data-averaging-in-python-moving-triangle-tecnique/
    Note that if dropVals is False, output length will be identical
    to input length, but with copies of data at the flanking regions"""
    triangle = numpy.array(list(range(degree)) + [degree] + list(range(degree))[::-1]) + 1
    smoothed = []
    for i in range(degree, len(data) - degree * 2):
        point = data[i:i + len(triangle)] * triangle
        smoothed.append(sum(point) / sum(triangle))
    if drop_vals:
        return smoothed
    # smoothed += smoothed[0] * (degree + degree / 2)
    while len(smoothed) < len(data):
        smoothed = numpy.append(smoothed, smoothed[::-1])
    return smoothed


def generate_available_capacity(target_set, category):
    data = numpy.random.random(365)  # a year of data
    data = numpy.array(data * get_free(category), dtype=int)
    # for i in range(100):
    #     data[i] += i ** ((150 - i) / 80.0)  # give it a funny trend
    data = smooth_triangle(data, 10)
    day_in_year = 0
    for month in range(1, 13):
        days_in_month = get_days_in_month(month)
        for day in range(1, days_in_month + 1):
            timestamp = get_day_as_time_stamp(day, month)
            target_set['values'].append([timestamp, int(data[day_in_year])])
            day_in_year += 1
    return target_set


def uptime():
    # we don't want to recalculate this on every load, so we attach it as an attribute to the function
    # if it hasn't been calculated...
    if not hasattr(uptime, 'data'):
        uptime.data = [generate_uptime(get_empty_set(center)) for center in ['NP', 'QH2', 'QH2-UoM']]
    return copy.deepcopy(uptime.data)


def active_users():
    # we don't want to recalculate this on every load, so we attach it as an attribute to the function
    # if it hasn't been calculated...
    if not hasattr(active_users, 'data'):
        active_users.data = [generate_active_users(get_empty_set(center))
                             for center in ['NP', 'QH2', 'QH2-UoM', 'Other data centers']]
    return copy.deepcopy(active_users.data)


def available_capacity(category):
    # we don't want to recalculate this on every load, so we attach it as an attribute to the function
    # if it hasn't been calculated...
    if not hasattr(available_capacity, category):
        data = [generate_available_capacity(get_empty_set(center), category)
                for center in ['NP', 'QH2', 'QH2-UoM']]
        setattr(available_capacity, category, data)
    return copy.deepcopy(getattr(available_capacity, category))


def capacity():
    # we don't want to recalculate this on every load, so we attach it as an attribute to the function
    # if it hasn't been calculated...
    if not hasattr(capacity, 'data'):
        capacity.data = [generate_capacity(get_empty_set(source), source) for source in
                         ['NeCTAR Contribution', 'UoM Contribution', 'Co-investment']]
    return copy.deepcopy(capacity.data)


def allocated():
    # we don't want to recalculate this on every load, so we attach it as an attribute to the function
    # if it hasn't been calculated...
    if not hasattr(allocated, 'data'):
        allocated.data = [generate_allocated(get_empty_set(center)) for center in
                          ['VCAMCM', 'VAS', 'FoS', 'MDHS', 'MLS', 'MSE', 'MGSE', 'FBE', 'FoA', 'ABP']]
    return copy.deepcopy(allocated.data)


def used():
    # we don't want to recalculate this on every load, so we attach it as an attribute to the function
    # if it hasn't been calculated...
    if not hasattr(used, 'data'):
        used.data = [generate_allocated(get_empty_set(center), 2) for center in
                     ['VCAMCM', 'VAS', 'FoS', 'MDHS', 'MLS', 'MSE', 'MGSE', 'FBE', 'FoA', 'ABP']]
    return copy.deepcopy(used.data)


MONTH = get_day_as_time_stamp(get_days_in_month(11), 11)
THREE_MONTHS = get_day_as_time_stamp(get_days_in_month(8), 8)
SIX_MONTHS = get_day_as_time_stamp(get_days_in_month(5), 5)


def determine(sample, duration):
    if (duration == 'oneMonth') and sample[0] < MONTH:
        return False
    elif (duration == 'threeMonths') and sample[0] < THREE_MONTHS:
        return False
    elif (duration == 'sixMonths') and sample[0] < SIX_MONTHS:
        return False
    return True


def filter_by_duration(duration, target):
    for entry in target:
        entry['values'][:] = [sample for sample in entry['values'] if determine(sample, duration)]
    return target


def get_uptime(duration, category):
    return filter_by_duration(duration, uptime())


def get_active_users(duration, category):
    return filter_by_duration(duration, active_users())


def get_cloud_available_capacity(duration, category):
    return filter_by_duration(duration, available_capacity(category))


def get_cloud_capacity(duration, category):
    return filter_by_duration(duration, capacity())


def get_cloud_allocated(duration):
    return filter_by_duration(duration, allocated())


def get_cloud_used(duration):
    return filter_by_duration(duration, used())