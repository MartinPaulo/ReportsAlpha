import logging

import psycopg2
import psycopg2.extras
from datetime import date
from sshtunnel import SSHTunnelForwarder

from scripts.config import Configuration


class DB(object):
    _db_connection = None
    _db_cur = None
    _server = None

    def __init__(self):
        db_config = Configuration.get_vicnode_db()
        ssh_host = Configuration.get_ssh_tunnel_info()

        self._server = SSHTunnelForwarder(
            ('118.138.243.250', 22),
            ssh_username="ubuntu",
            ssh_pkey='/Users/mpaulo/.ssh/new_mbp.pem',
            remote_bind_address=(db_config['host'], 5432)
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
        logging.info("Closing the VicNode DB connection")
        self._db_connection.close()
        logging.info("Stopping the ssh tunnel")
        self._server.stop()
        logging.info("The VicNode DB connection is closed")

    def test_connection(self):
        self._db_cur.execute("SELECT * FROM applications_suborganization;")
        rows = self._db_cur.fetchall()
        # print(rows)

    def get_allocated(self, day_date):
        """
        :param self:
        :param day_date:
        :return:
        """
        q_allocated = """
            SELECT
              sum(size),
              CASE
              WHEN storage_product_id = 1
                THEN 'computational'
              WHEN storage_product_id = 4
                THEN 'market'
              ELSE 'vault' END AS product
            FROM applications_allocation
            WHERE storage_product_id IN (1, 4, 10)
                  AND applications_allocation.last_modified <
                      (%(day_date)s :: DATE + '1 day' :: INTERVAL)
            GROUP BY storage_product_id;
        """
        self._db_cur.execute(q_allocated, {'day_date': day_date})
        return self._db_cur.fetchall()

    def get_allocated_by_faculty(self, day_date, product='all'):
        """
        :param product:
        :param self:
        :param day_date:
        :return:
        """
        products = (1, 4, 10)
        if product == 'computational':
            products = (1,)
        elif product == 'market':
            products = (4,)
        elif product == 'vault':
            products = (10,)
        q_allocated = """
            SELECT
              sum(size)          AS used,
              CASE
              WHEN institution_id != 2
                THEN 'external'
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
                THEN 'services'
              ELSE 'unknown' END AS faculty
            FROM applications_allocation
              LEFT JOIN applications_request
                ON applications_allocation.application_id =
                   applications_request.id
              LEFT JOIN applications_suborganization
                ON applications_request.institution_faculty_id =
                   applications_suborganization.id
            WHERE storage_product_id IN %(products)s
                  AND applications_allocation.last_modified <
                      (%(day_date)s :: DATE + '1 day' :: INTERVAL)
            GROUP BY faculty;
        """
        # print(self._db_cur.mogrify(q_allocated,
        #                      {'products': products, 'day_date': day_date}))
        self._db_cur.execute(q_allocated,
                             {'products': products, 'day_date': day_date})
        return self._db_cur.fetchall()

    def get_storage_used(self, day_date):
        q_used = """
            SELECT
              sum(used_capacity),
              CASE
              WHEN storage_product_id = 1
                THEN 'computational'
              WHEN storage_product_id = 4
                THEN 'market'
              ELSE 'vault' END AS product
            FROM applications_ingest t1
            WHERE storage_product_id IN (1, 4, 10)
                  -- and this is the last record
                  AND extraction_date =
                      (SELECT MAX(extraction_date)
                       FROM applications_ingest t2
                       WHERE t2.collection_id = t1.collection_id
                             AND t2.storage_product_id = t1.storage_product_id
                             AND t2.extraction_date <
                                (%(day_date)s :: DATE + '1 day' :: INTERVAL)
                      )
            GROUP BY product;
        """
        self._db_cur.execute(q_used, {'day_date': day_date})
        return self._db_cur.fetchall()

    def get_used_by_faculty(self, day_date, product='all'):
        products = (1, 4, 10)
        if product == 'computational':
            products = (1,)
        elif product == 'market':
            products = (4,)
        elif product == 'vault':
            products = (10,)
        q_used = """
            SELECT
              sum(used_capacity),
              CASE
                WHEN suborg_id IS NULL
                  THEN 'external'
                WHEN suborg_id = 1
                  THEN 'ABP'
                WHEN suborg_id = 2
                  THEN 'FBE'
                WHEN suborg_id = 3
                  THEN 'FoA'
                WHEN suborg_id = 4
                  THEN 'MGSE'
                WHEN suborg_id = 5
                  THEN 'MSE'
                WHEN suborg_id = 6
                  THEN 'MLS'
                WHEN suborg_id = 7
                  THEN 'MDHS'
                WHEN suborg_id = 8
                  THEN 'FoS'
                WHEN suborg_id = 9
                  THEN 'VAS'
                WHEN suborg_id = 10
                  THEN 'VCAMCM'
                WHEN suborg_id = 11
                  THEN 'services'
                ELSE 'unknown' END AS faculty
            FROM applications_ingest ingest
              LEFT JOIN (
                          SELECT
                            request.id,
                            coalesce(suborganization.id, -1) AS suborg_id
                          FROM applications_request request
                            LEFT JOIN applications_suborganization suborganization
                              ON institution_faculty_id = suborganization.id
                          WHERE
                            request.institution_id = '2'
                          ORDER BY id
                        ) AS names ON names.id = ingest.collection_id
            WHERE storage_product_id IN %(products)s
                  -- and this is the last record
                  AND extraction_date =
                      (SELECT MAX(extraction_date)
                       FROM applications_ingest t2
                       WHERE t2.collection_id = ingest.collection_id
                             AND t2.storage_product_id = ingest.storage_product_id
                             AND
                             t2.extraction_date <
                                (%(day_date)s :: DATE + '1 day' :: INTERVAL)
                      )
            GROUP BY faculty;
        """
        self._db_cur.execute(q_used,
                             {'products': products, 'day_date': day_date})
        return self._db_cur.fetchall()
