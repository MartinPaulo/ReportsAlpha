import logging
from functools import wraps

import psycopg2
import psycopg2.extras
from django.conf import settings
from sshtunnel import SSHTunnelForwarder

from scripts.config import Configuration

VAULT = 'vault'
COMPUTATIONAL = 'computational'
MARKET = 'market'


def connection_required(f):
    """
    It is possible that you might close the connection: and then try to use
    the instance later on. This simply throws an exception if you try to do
    this. Better than hunting down odd exceptions?
    :param f:
    :return:
    """

    @wraps(f)
    def wrapper(self, *args, **kwargs):
        if not self._server:
            raise Exception("Connection has been closed")
        return f(self, *args, **kwargs)

    return wrapper


class DB(object):
    """
    Read: https://colinnewell.wordpress.com/2016/01/21/hand-coding-sql-with-psycopg2-for-odoo/
    """
    _db_connection = None
    _db_cur = None
    _server = None

    def __init__(self):
        db_config = Configuration.get_vicnode_db()
        ssh_intermediate = Configuration.get_ssh_tunnel_info()

        self._server = SSHTunnelForwarder(
            ((ssh_intermediate['host']), (int(ssh_intermediate['port']))),
            ssh_password=ssh_intermediate['ssh_password'],
            ssh_username=(ssh_intermediate['username']),
            ssh_pkey=(ssh_intermediate['private_key_file']),
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
            logging.info("Closing the VicNode DB connection")
            self._db_connection.close()
            logging.info("Stopping the ssh tunnel")
            self._server.stop()
            logging.info("The VicNode DB connection is closed")
            self._server = None

    @staticmethod
    def get_product_code(product):
        products = settings.STORAGE_PRODUCT_CODES
        if product == COMPUTATIONAL:
            products = settings.COMPUTE_PRODUCT_CODES
        elif product == MARKET:
            products = settings.MARKET_PRODUCT_CODES
        elif product == VAULT:
            products = settings.VAULT_MARKET_CODES
        return products

    @connection_required
    def test_connection(self):
        self._db_cur.execute("SELECT * FROM applications_suborganization;")
        rows = self._db_cur.fetchall()
        # print(rows)

    @connection_required
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
              WHEN storage_product_id IN %(compute)s
                THEN 'computational'
              WHEN storage_product_id IN %(market)s
                THEN 'market'
              ELSE 'vault' END AS product
            FROM applications_allocation
            WHERE storage_product_id IN %(all_types)s
                  AND applications_allocation.last_modified <
                      (%(day_date)s :: DATE + '1 day' :: INTERVAL)
            GROUP BY storage_product_id;
        """
        self._db_cur.execute(q_allocated, {
            'compute': settings.COMPUTE_PRODUCT_CODES,
            'market': settings.MARKET_PRODUCT_CODES,
            'all_types': settings.STORAGE_PRODUCT_CODES,
            'day_date': day_date
        })
        return self._db_cur.fetchall()

    @connection_required
    def get_allocated_by_faculty(self, day_date, product='all'):
        """
        :param product:
        :param self:
        :param day_date:
        :return:
        """
        products = self.get_product_code(product)
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
        self._db_cur.execute(q_allocated, {
            'products': products,
            'day_date': day_date
        })
        return self._db_cur.fetchall()

    @connection_required
    def get_storage_used(self, day_date):
        q_used = """
            SELECT
              sum(used_capacity),
              CASE
              WHEN storage_product_id IN %(compute)s
                THEN 'computational'
              WHEN storage_product_id IN %(market)s
                THEN 'market'
              ELSE 'vault' END AS product
            FROM applications_ingest t1
            WHERE storage_product_id IN %(all_types)s
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
        self._db_cur.execute(q_used, {
            'compute': settings.COMPUTE_PRODUCT_CODES,
            'market': settings.MARKET_PRODUCT_CODES,
            'all_types': settings.STORAGE_PRODUCT_CODES,
            'day_date': day_date
        })
        return self._db_cur.fetchall()

    @connection_required
    def get_used_by_faculty(self, day_date, product='all'):
        products = self.get_product_code(product)
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
        self._db_cur.execute(q_used, {
            'products': products,
            'day_date': day_date
        })
        return self._db_cur.fetchall()

    @connection_required
    def get_headroom_unused(self, day_date):
        q_used = """
            SELECT
              sum(allocated_capacity - used_capacity) AS headroom,
              CASE
              WHEN storage_product_id IN %(compute)s
                THEN 'computational'
              WHEN storage_product_id IN %(market)s
                THEN 'market'
              ELSE 'vault' END AS product
            FROM applications_ingest AS t1
            WHERE storage_product_id IN %(all_types)s
                  -- and this is the last record
                  AND extraction_date =
                      (SELECT MAX(extraction_date)
                       FROM applications_ingest t2
                       WHERE t2.collection_id = t1.collection_id
                             AND t2.storage_product_id = t1.storage_product_id
                             AND t2.extraction_date <
                                (%(day_date)s :: DATE + '1 day' :: INTERVAL)
                      )
            GROUP BY storage_product_id;
        """
        self._db_cur.execute(q_used, {
            'compute': settings.COMPUTE_PRODUCT_CODES,
            'market': settings.MARKET_PRODUCT_CODES,
            'all_types': settings.STORAGE_PRODUCT_CODES,
            'day_date': day_date
        })
        return self._db_cur.fetchall()

    @connection_required
    def get_headroom_unused_by_faculty(self, day_date, product='all'):
        products = self.get_product_code(product)
        q_used = """
            SELECT  sum(allocated_capacity - used_capacity) AS headroom,
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
                             AND t2.extraction_date <
                                        (%(day_date)s :: DATE + '1 day' :: INTERVAL)
                      )
            GROUP BY faculty;
            """
        self._db_cur.execute(q_used, {
            'products': products,
            'day_date': day_date
        })
        return self._db_cur.fetchall()

    @connection_required
    def get_storage_capacity(self):
        query = """
            SELECT
              capacity * 1000   AS capacity,
              CASE
              WHEN id IN %(compute)s
                THEN 'computational'
              WHEN id IN %(market)s
                THEN 'market'
              ELSE 'vault' END AS product
            FROM applications_storageproduct
            WHERE id IN %(all_types)s;
        """
        self._db_cur.execute(query, {
            'compute': settings.COMPUTE_PRODUCT_CODES,
            'market': settings.MARKET_PRODUCT_CODES,
            'all_types': settings.STORAGE_PRODUCT_CODES
        })
        return self._db_cur.fetchall()

    @connection_required
    def get_storage_types(self):
        """
        :return:
            The set of storage types in the vicnode database
        """
        query = """
            SELECT
              value
            FROM applications_storageproduct
              LEFT JOIN labels_label
                ON labels_label.id =
                  applications_storageproduct.product_name_id;
        """
        result = set()
        self._db_cur.execute(query)
        result_set = self._db_cur.fetchall()
        for row in result_set:
            result.add(row['value'])
        return result
