import calendar
import logging
from datetime import date, datetime

import cssselect as cssselect
from lxml import etree
import requests
from dateutil.relativedelta import relativedelta

from scripts.config import Configuration

# assumeinitialstates default to an assumed state if the initial state is not
#                      known ( yes | no )
# initialassumedhoststate the initial host state to assume if the initial
#                      state is not known
#                     ( unspecified | current | up | down | unreachable)
# initialassumedservicestate the initial service state to assume if the
#                      initial state is not known
#                 ( unspecified | current | ok | warning | unknown | critical )
# assumestateretention if nagios was down, assume the state didn't
#                       change during the down time
#                       - should match server configuration
#                      ( yes | no )
# includesoftstates ordinarily only hard down states are reported. If yes then
#                    soft states are also reported on. The recommendation is
#                    to not report on soft states..
#                      ( yes | no )
# assumestatesduringnotrunning
# show_log_entries= should the log entries also be returned?
#                   Just needs to be included to take effect.
# backtrack how many log files to check back for the initial state.
#            the default is 4
# csvoutput= the output be csv. "host=all" or "service=all" must be set as well
#            Just needs to be included to take effect.
# t1 the start time
# t2 the end time
# host the host to query.
# service the service to query
NATIONAL_AVAILABILITY_QUERY_TEMPLATE = "/avail.cgi" \
                              "?t1=%s" \
                              "&t2=%s" \
                              "&show_log_entries=" \
                              "&servicegroup=f5-endpoints" \
                              "&assumeinitialstates=yes" \
                              "&assumestateretention=yes" \
                              "&assumestatesduringnotrunning=yes" \
                              "&includesoftstates=yes" \
                              "&initialassumedhoststate=3" \
                              "&initialassumedservicestate=6" \
                              "&timeperiod=[+Current+time+range+]" \
                              "&backtrack=4"

# hostgroup=nova-compute-uom
# Get all hosts for last seven days as CSV
# https://mon.rc.nectar.org.au/cgi-bin/nagios3/avail.cgi?host=all&timeperiod=last7days&csvoutput=

# Get for all hosts from t1 till t1 with some extra details
# https://mon.rc.nectar.org.au/cgi-bin/nagios3/avail.cgi?host=all&t1=1456444800&t2=1472169600&timeperiod=[+Current+time+range+]&assumeinitialstates=yes&initialassumedhoststate=3&initialassumedservicestate=6&assumestateretention=yes&assumestatesduringnotrunning=yes&csvoutput=

# The service group to use for calculating if services are up and
# their availability.
NAGIOS_SERVICE_GROUP = 'f5-endpoints'


def gm_timestamp(date_object):
    return calendar.timegm(
        datetime.combine(date_object, datetime.min.time()).utctimetuple())


def parse_service_availability(row):
    host, service, ok, warn, unknown, crit, undet = row.getchildren()
    host_name = "".join([t for t in host.itertext()])
    nagios_service_name = "".join([t for t in service.itertext()])
    return {"name": nagios_service_name,
            "host": host_name,
            "ok": ok.text.split(' ')[0],
            "warning": warn.text.split(' ')[0],
            "unknown": unknown.text.split(' ')[0],
            "critical": crit.text.split(' ')[0]}


def parse_availability(html):
    tr = cssselect.GenericTranslator()
    h = etree.HTML(html)
    table = None
    for i, e in enumerate(h.xpath(tr.css_to_xpath('.dataTitle')), -1):
        if 'Service State Breakdowns' not in e.text:
            # skip all tables bar the one with the results we want
            continue
        table = h.xpath(tr.css_to_xpath('table.data'))[i]
        break
    services = {}
    if table is not None:
        for row in table.xpath(tr.css_to_xpath("tr.dataOdd, tr.dataEven")):
            if 'colspan' in row.getchildren()[0].attrib:
                # skip the average row
                continue
            service = parse_service_availability(row)
            services[service['name']] = service
    return services


def read_national(load_db,
                  start_day=date.today() - relativedelta(months=6),
                  end_day=date.today()):
    query = NATIONAL_AVAILABILITY_QUERY_TEMPLATE % (
        gm_timestamp(start_day),
        gm_timestamp(end_day))
    url = Configuration.get_nagios_url() + query
    resp = requests.get(url, auth=Configuration.get_nagios_auth())
    services = parse_availability(resp.text)
    for service in services:
        logging.info(" " + services[service]['host'] + " " + services[service]['ok'])


