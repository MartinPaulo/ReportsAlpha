#!/usr/bin/env python
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

import psycopg2
import psycopg2.extras
from django.template.loader import get_template
from sshtunnel import SSHTunnelForwarder

from scripts.cloud.utility import quarter_dates, LDAP, Faculties
from scripts.custom.credentials import Credentials


class DB:
    _db_connection = None
    _db_cur = None

    def __init__(self):
        ssh_tunnel = Credentials.ssh_tunnel
        db_config = Credentials.vicnode_db
        self._server = SSHTunnelForwarder(
            ((ssh_tunnel['host']), (int(ssh_tunnel['port']))),
            ssh_password=ssh_tunnel['ssh_password'],
            ssh_username=(ssh_tunnel['username']),
            ssh_pkey=(ssh_tunnel['private_key_file']),
            remote_bind_address=(db_config['host'], 5432),
            allow_agent=False
        )
        self._server.start()
        # we are about to bind to a 'local' server by means of an ssh tunnel
        # ssh tunnel: which will be seen as a local server...
        # so replace the loaded config host
        db_config['host'] = 'localhost'
        db_config['port'] = self._server.local_bind_port
        self._db_connection = psycopg2.connect(**db_config)
        self._db_cur = self._db_connection.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor)
        self.test_connection()

    def __del__(self):
        self.close_connection()

    def close_connection(self):
        if self._server:
            self._db_connection.close()
            self._server.stop()
            self._server = None

    def test_connection(self):
        self._db_cur.execute("SELECT * FROM applications_suborganization;")
        rows = self._db_cur.fetchall()

    def get_contacts(self):
        """
        Returns: every project name and it's chief investigator (can be more
        than one).
        """
        query = """
            SELECT
              collection.id,
              contacts_contact.email_address,
              contacts_contact.business_email_address
            FROM applications_project AS collection
              LEFT JOIN applications_custodian
                ON collection_id = collection.id
              LEFT JOIN contacts_contact
                ON applications_custodian.person_id = contacts_contact.id
            WHERE applications_custodian.role_id = 293
            ORDER BY id;
        """
        self._db_cur.execute(query)
        return self._db_cur.fetchall()

    def get_sub_organizations(self):
        """
        Returns: all the projects
        """
        query = """
            SELECT
              applications_request.project_id,
              contacts_organisation.short_name,
            CASE
              WHEN applications_suborganization.id = 1
                THEN 'ABP'
              WHEN applications_suborganization.id = 2
                THEN 'FBE'
              WHEN applications_suborganization.id = 3
                THEN 'FoA'
              WHEN applications_suborganization.id = 4
                THEN 'MGSE'
              WHEN applications_suborganization.id = 5
                THEN 'MSE'
              WHEN applications_suborganization.id = 6
                THEN 'MLS'
              WHEN applications_suborganization.id = 7
                THEN 'MDHS'
              WHEN applications_suborganization.id = 8
                THEN 'FoS'
              WHEN applications_suborganization.id = 9
                THEN 'VAS'
              WHEN applications_suborganization.id = 10
                THEN 'VCAMCM'
              WHEN applications_suborganization.id = 11
                THEN 'External'
              ELSE 'Unknown' END AS faculty
            FROM applications_request
              LEFT JOIN applications_suborganization
                ON applications_request.institution_faculty_id =
                   applications_suborganization.id
              LEFT JOIN contacts_organisation
                ON applications_request.institution_id = contacts_organisation.id
            WHERE -- institution_id = 2
              -- don't worry about this, as only UoM projects are assigned
              project_id NOTNULL
              AND name NOTNULL
            GROUP BY short_name, project_id, faculty
            ORDER BY project_id;
        """
        self._db_cur.execute(query)
        return self._db_cur.fetchall()

    def get_used(self, end_date):
        query = """
            SELECT
              collection_id,
              sum
            FROM (
                   SELECT
                     collection_id,
                     SUM(used_capacity) AS sum
                   FROM applications_ingest
                   WHERE storage_product_id IN (1, 4, 10, 23, 24)
                         -- and this is the last record
                         AND extraction_date =
                             (SELECT MAX(extraction_date)
                              FROM applications_ingest t2
                              WHERE t2.collection_id = applications_ingest.collection_id
                                    AND t2.storage_product_id =
                                        applications_ingest.storage_product_id
                                    AND t2.extraction_date < (DATE %(end)s))
                   GROUP BY collection_id
                   ORDER BY collection_id) totals
            WHERE sum NOTNULL AND sum > 0;
        """
        self._db_cur.execute(query, {
            'end': end_date.strftime("%Y-%m-%d")
        })
        return self._db_cur.fetchall()


import django
from scripts.config import Configuration

Configuration.get_production_db()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reports_beta.settings")
django.setup()

db = DB()
ldap = LDAP()

owners = dict()
contacts = db.get_contacts()
for contact in contacts:
    owners[contact['id']] = (
        contact['email_address'], contact['business_email_address'])

faculties = dict()
sub_orgs = db.get_sub_organizations()
for org in sub_orgs:
    faculties[org['project_id']] = Faculties(org['faculty'])
# note users can be in multiple projects. This code doesn't deal with that...
upper_bound_date = datetime.now().date()
five_quarters = timedelta(15 * 365 / 12)
t = get_template('bc_storage.tsv')
results = dict()
last_quarter = ''
result = ''
for start_date, end_date, abbreviation in quarter_dates(
        to_date=upper_bound_date):
    if end_date < (upper_bound_date - five_quarters):
        continue
    print(f'Working on {abbreviation}...')
    last_quarter = abbreviation
    faculty_totals = Faculties.get_new_totals()
    quarter_total = 0
    used = db.get_used(end_date)
    total_percentage = 0
    results['storage_results'] = []
    for total in used:
        collection_id = total['collection_id']
        storage_used = total['sum']
        faculty = faculties.get(collection_id, None)
        if not faculty:
            addresses = owners.get(collection_id, (None, None))
            email_address = addresses[0]
            business_email_address = addresses[1]
            if email_address is not None and len(email_address) > 0:
                faculty, name = ldap.find_faculty(email_address)
            if faculty is None and business_email_address is not None and len(
                    business_email_address) > 0:
                faculty, name = ldap.find_faculty(business_email_address)
            if faculty is None:
                faculty = Faculties.UNKNOWN
        faculty_totals[faculty] += storage_used
        quarter_total += storage_used
        time.sleep(0.1)
    for faculty, total in faculty_totals.items():
        percentage = round(total / quarter_total * 100, 2)
        results['storage_results'].append(
            (abbreviation, faculty, total, percentage))
        total_percentage += percentage
    result += t.render(results)
    print()
    # should be 100%
    print('Total percentage: %s' % total_percentage)
    print('Total used: %s' % quarter_total)
output_dir = Path('output')
with Path(output_dir, Path(f'{last_quarter}_bc_storage.txt')).open(
        mode='w') as outfile:
    outfile.write(result)

db.close_connection()
