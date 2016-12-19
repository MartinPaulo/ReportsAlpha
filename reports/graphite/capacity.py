"""
Fetches the cloud capacity readings from the NeCTAR graphite system.

You can see these readings as used by NeCTAR at
http://status.rc.nectar.org.au/capacity/

The graphite system can return data in either a csv or a json format.
It can even, if you so desire, return images containing the rendered data!

For a server at, say: http://status1.mgmt.rc.nectar.org.au/

* The following will return an image showing the capacity for the 8192 instance
  size over the last 31 days
  http://status1.mgmt.rc.nectar.org.au/render/?from=-31d&target=cell.np.capacity_8192
* The following will return the csv behind the image
  http://status1.mgmt.rc.nectar.org.au/render/?format=csv&from=-31d&target=cell.np.capacity_8192
* The following will return the json behind the image
  http://status1.mgmt.rc.nectar.org.au/render/?format=json&from=-31d&target=cell.np.capacity_8192

The returned data can be given an alias. So to rename cell.np.capacity_8192
to a more friendly name
http://status1.mgmt.rc.nectar.org.au/render/?format=json&from=-31d&target=alias(cell.np.capacity_8192, 'Noble Park')

You can find more about the functions graphite supports here
http://graphite.readthedocs.io/en/latest/functions.html

As set up the Graphite system will return series that have nulls recorded
against some of the times. This indicates that a sample was not read at that
point. There are several strategies that can be used: to either fill in values
from either side of those points, rewrite the value to 0, discard the  null
values or render broken lines. Manufacturing fake data doesn't sit right. So
we opt to simply remove those points before passing the data on to nvd3.
"""
import csv
import logging
from io import StringIO
from json import dumps
from urllib.parse import urlencode

import requests
from django.conf import settings

# The nvd3 selected duration mapped to graphite's expected from argument
# equivalents
DURATION_MAPPING = {
    "year": '-1y',
    "sixMonths": '-6mon',
    "threeMonths": '-3mon',
    "oneMonth": '-31d',
}

GRAPHITE_JSON = 'json'
GRAPHITE_CAPACITY = 'capacity_768'

LOG = logging.getLogger("reports.graphite")


def _translate_json(response):
    """
    Example Graphite JSON response =
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

    Our nvd3 expected response =
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
    So we choose to change the format as well.
    This function does both.
    """
    # so remove all the data points with a null or a None
    result = []
    for series in response:
        element = dict()
        element['key'] = series['target']
        element['values'] = [point for point in series['datapoints'] if
                             (point[0] != 'null' and point[0] is not None)]
        # we add an initial point of 0, to show a line rising from the
        # axis. It's a bit disconcerting to see it start in mid-space
        point = [0, series['datapoints'][0][1] - 1000]
        element['values'].insert(0, point)
        result.append(element)
    return result


def _map_duration_to_graphite(selected):
    """
    :return: the selected duration mapped to graphite's expected from argument
    """
    return DURATION_MAPPING[selected]


def _translate_csv(csv_text):
    """
    The csv text contains lines without values. For example:
    ```
    'QH2 and NP', '2016-12-04 13:00:00', '1490.0'
    'QH2 and NP', '2016-12-04 13:00:00', ''
    ```
    As they are stripped out from the json that is fed to the nvd3 graphs we
    strip them out from the csv as well.
    :return: The input csv text with those entries that have an empty last
    column value stripped out.
    """
    with StringIO(csv_text) as csv_in, StringIO() as csv_out:
        c_w = csv.writer(csv_out)
        for row in csv.reader(csv_in):
            if row[-1]:
                c_w.writerow(row)
        return csv_out.getvalue()


def fetch(instance_size, data_format, duration):
    """
    :param instance_size: The instance size for which the capacity is desired
    :param data_format: Either `csv` or `json` & gives the desired format
    :param duration: The time period the samples should cover
    :return: The capacity data from graphite for the duration in the
    requested format
    """
    cells = [('cell.melbourne', 'QH2 and NP'),
             ('cell.qh2-uom', 'QH2-UoM'),
             ('cell.np', 'NP'),
             ('cell.qh2', 'QH2')]
    graphite_args = [
        ('format', data_format),
        ('from', DURATION_MAPPING[duration])]
    graphite_args.extend(
        [('target', "alias(%s.%s, '%s')" % (cell, instance_size, alias)) for
         cell, alias in cells])
    graphite_url = settings.GRAPHITE_SERVER.rstrip(
        '/') + "/render/?" + urlencode(graphite_args)
    LOG.info("From graphite fetching: %s", graphite_url)
    response = requests.get(graphite_url, timeout=10)
    response.raise_for_status()
    if data_format == 'json':
        graphite_response = dumps(_translate_json(response.json()))
    else:
        graphite_response = _translate_csv(response.text)
    return graphite_response, response.headers['content-type']
