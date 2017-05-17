#!/usr/bin/env python
"""
Lists the storage collections per year, giving their allocation and usage
"""
import sys
import time
from collections import defaultdict

import psycopg2
import psycopg2.extras
from sshtunnel import SSHTunnelForwarder

from scripts.custom.credentials import Credentials


class StorageDB:
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
              contacts_contact.first_name,
              contacts_contact.last_name,
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
        Returns: all the projects that have a suborganization
        """
        query = """
            SELECT
              applications_allocation.collection_id AS project_id,
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
                THEN 'Services'
              ELSE 'Unknown' END AS faculty
            FROM applications_allocation
              LEFT JOIN applications_request
                ON applications_allocation.application_id = applications_request.id
              LEFT JOIN applications_suborganization
                ON applications_request.institution_faculty_id =
                   applications_suborganization.id
            WHERE institution_id = 2
            GROUP BY collection_id, faculty
            ORDER BY collection_id;
        """
        self._db_cur.execute(query)
        return self._db_cur.fetchall()

    def get_allocated(self, year_wanted):
        """
        Returns:
        """
        query = """
            SELECT
              collection_id,
              name,
              sum(size) AS allocated
            FROM applications_allocation
              LEFT JOIN applications_request
                ON applications_allocation.application_id = applications_request.id
              LEFT JOIN applications_project
                ON applications_allocation.collection_id = applications_project.id
            WHERE storage_product_id IN (1, 4, 10, 23, 24)
                  AND COALESCE(applications_allocation.creation_date, '2014-11-14' :: DATE) < %(day_date)s :: DATE
                  AND applications_request.institution_id = 2
            GROUP BY collection_id, name
            ORDER BY collection_id;
        """
        self._db_cur.execute(query, {
            'day_date': '%s-12-31' % year_wanted
        })
        return self._db_cur.fetchall()

    def get_used(self, year_wanted, collection_id):
        query = """
            SELECT
            --   lt.max_date,
            --   lt.storage_product_id,
              SUM(rt.used_capacity) AS used
            FROM
              (
                -- get the max date for each product type
                SELECT
                  MAX(extraction_date) AS max_date,
                  storage_product_id
                FROM applications_ingest
                WHERE collection_id =%(collection_id)s
                      AND extraction_date < %(day_date)s :: DATE
                GROUP BY storage_product_id
              ) lt
              INNER JOIN
              (
                -- get the max date for each change in the used capacity of each
                -- product type
                SELECT
                  MAX(extraction_date) AS max_date,
                  used_capacity
                FROM applications_ingest
                WHERE collection_id = %(collection_id)s
                      AND extraction_date < %(day_date)s :: DATE
                GROUP BY used_capacity
              ) rt
                ON lt.max_date = rt.max_date;
        """
        self._db_cur.execute(query, {
            'day_date': '%s-12-31' % year_wanted,
            'collection_id': collection_id
        })
        return self._db_cur.fetchone()


def as_empty_string_if_null(target):
    return target.strip() if target else ''


db = StorageDB()
owners = dict()
contacts = db.get_contacts()
for contact in contacts:
    # There is more than one contact for some of the projects...
    if not owners.get(contact['id'], None):
        details = (as_empty_string_if_null(contact['first_name']),
                   as_empty_string_if_null(contact['last_name']),
                   as_empty_string_if_null(contact['email_address']),
                   as_empty_string_if_null(contact['business_email_address']))
        owners[contact['id']] = details
faculties = dict()
sub_orgs = db.get_sub_organizations()
for org in sub_orgs:
    if faculties.get(org['project_id'], None):
        print("Error: There is more than one faculty for %s %s" % (
            org['project_id'], org['faculty']), file=sys.stderr)
        sys.exit(2)
    faculties[org['project_id']] = org['faculty']

o = '{faculty!s}, {collection_id!s}, {collection_name!s}, ' \
    '{name!s}, {email_address!s},  {business_email_address!s}, ' \
    '{allocated!s}, {used!s}'
out_file = "output/storage_%s.txt" % time.strftime("%Y%m%d-%H%M%S")
with open(out_file, "w") as output:
    for year in [2014, 2015, 2016, 2017]:
        output.write('='*80 + '\n')
        output.write('Year: %s\n' % year)
        output.write('='*80 + '\n')
        output.write('\n')
        output.write(o.format(**{
            'faculty': 'Faculty',
            'collection_id': 'Collection ID',
            'collection_name': 'Collection Name',
            'name': 'Custodian Name',
            'email_address': 'Email',
            'business_email_address': 'Work Email',
            'allocated': 'Allocated',
            'used': 'Used',
        }) + '\n')
        allocated = db.get_allocated(year)
        used_index = 0
        by_faculty = defaultdict(list)
        for allocation in allocated:
            collection_id = allocation['collection_id']
            collection_name = allocation['name'].strip()
            allocated = allocation['allocated']

            faculty = faculties.get(collection_id)
            if not faculty:
                print("Error: No faculty found: %s %s" % (
                    collection_id, collection_name), file=sys.stderr)
                sys.exit(1)
            (first_name, last_name, email_address,
             business_email_address) = owners.get(collection_id,
                                                  ('', '', '', ''))
            used = db.get_used(year, collection_id)
            total_used = used['used'] if used and used['used'] else 0
            collection = {'collection_id': collection_id,
                          'collection_name': collection_name,
                          'faculty': faculty,
                          'name': '{0} {1}'.format(first_name,
                                                   last_name).strip(),
                          'email_address': email_address,
                          'business_email_address': business_email_address,
                          'allocated': allocated,
                          'used': total_used, }
            by_faculty[faculty].append(collection)
        for faculty in sorted(by_faculty):
            for collection in by_faculty[faculty]:
                output.write(o.format(**collection) + '\n')
        output.write('\n')

db.close_connection()
