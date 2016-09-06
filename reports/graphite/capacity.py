import logging
from json import dumps
from operator import itemgetter
from urllib.parse import urlencode

import requests
from django.conf import settings

GRAPHITE_JSON = 'json'
GRAPHITE_CAPACITY = 'capacity_768'


def _fill_nulls(data, template):
    """
    :return: a generator that yields the template timestamp with a value
    taken from the actual data if possible, otherwise yields the template
    timestamp with the last value taken from the data. If there is no
    last value, the default of 0.0 is used.

    *Note* for this to work the data and the template have to have the
    same time stamps. Something that the nectar metrics nova module ensures.
    """
    data = dict([(timestamp, value) for value, timestamp in data])
    previous_value = 0.0
    for point in template:
        value = None
        timestamp = point[1]
        if timestamp in data:
            value = data[timestamp]
        if value is None:
            yield [previous_value, timestamp]
        else:
            previous_value = value
            yield [value, timestamp]


def _fill_null_data_points(response):
    """
    A sample Graphite response =
    [
        {
            "target": "Kitchenware",
            "datapoints": [
                [null, 1324130400],
                [0.0, 1324216800],
                [null, 1413208800]
            ]
        },
        {
            "target": "Wetware",
            "datapoints": [
                [0.0, 1324130400],
                [null, 1324216800]
            ]
        },
    ]
    But NVD3 requires that the data points in each series have the same
    length and timestamp. So we need to extend the graphite data sets to the
    same length and fill in any null values with something more acceptable.
    """
    # Find the longest data point series and use it to build a template.
    longest = sorted(
        [(len(series['datapoints']), series['datapoints'])
         for series in response], key=itemgetter(0))[-1][1]
    template = [[None, t] for v, t in longest]
    for series in response:
        data_points = series['datapoints']
        # replace the original series with a new one built from the template
        series['datapoints'] = list(_fill_nulls(data_points, template))
    return response


def _translate_data(response):
    """
    Example Graphite response =
    [
        {
            "target": "Cumulative",
            "datapoints": [
                [10.2, 1324130400],
                [12.1, 1324216800],
                [20.2, 1413208800]
            ]
        },
    ]

    Example nvd3 expected response =
    [
        {
            "key": "Cumulative",
            "values": [
                [10.2, 1324130400],
                [12.1, 1324216800],
                [20.2, 1413208800]
            ]
        },
    ]
    :return: This function maps from the one to the other
    """
    result = []
    for series in response:
        result.append(
            {
                'key': series['target'],
                'values': series['datapoints']
            }
        )
    return result


def _map_duration_to_graphite(selected):
    """
    :return: the selected duration mapped to graphite's expected from argument
    """
    return {
        "year": '-1y',
        "sixMonths": '-6mon',
        "threeMonths": '-3mon',
        "oneMonth": '-31d',
    }[selected]


def fetch(capacity, desired_format, duration):
    """
    :return: The capacity data from graphite for the duration in the
    requested format
    """
    cells = [('cell.melbourne', 'QH2 and NP'),
             ('cell.qh2-uom', 'QH2-UoM')]
    graphite_args = [
        ('format', desired_format),
        ('from', _map_duration_to_graphite(duration))]
    graphite_args.extend(
        [('target', "alias(%s.%s, '%s')" % (cell, capacity, alias)) for
         cell, alias in cells])
    graphite_url = settings.GRAPHITE_SERVER.rstrip('/') \
                   + "/render/?" + urlencode(graphite_args)
    logging.info("Fetching: " + graphite_url)
    response = requests.get(graphite_url)
    response.raise_for_status()
    if desired_format == 'json':
        filled_data = _fill_null_data_points(response.json())
        translated_data = _translate_data(filled_data)
        graphite_response = dumps(translated_data)
    else:
        graphite_response = response.text
    return graphite_response, response.headers['content-type']
