import logging
from json import dumps
from operator import itemgetter
from urllib.parse import urlencode

import requests
from django.conf import settings

GRAPHITE_JSON = 'json'
GRAPHITE_CAPACITY = 'capacity_768'


def _translate_data(response):
    """
    Example Graphite response =
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

    But NVD3 requires that the data points in each series have a
    proper value for each point, So we need to filter out the nulls and Nones.

    Also

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
    So we have to change the format as well.
    This function does both.
    """
    # so remove all the data points with a null or a None
    result = []
    for series in response:
        element = dict()
        element['key'] = series['target']
        element['values'] = [point for point in series['datapoints'] if
                             (point[0] != 'null' and point[0] is not None)]
        # we add an initial point of 0, if only to show a line rising from the
        # axis
        point = [0, series['datapoints'][0][1] - 1000]
        element['values'].insert(0, point)
        result.append(element)
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
        graphite_response = dumps(_translate_data(response.json()))
    else:
        graphite_response = response.text
    return graphite_response, response.headers['content-type']
