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
        SELECT *
        FROM
          (SELECT sum(size) AS computational
           FROM applications_allocation
           WHERE storage_product_id = 1
                 AND last_modified <
                 (%(day_date)s :: DATE + '1 day' :: INTERVAL)
                 ) a
          CROSS JOIN
          (SELECT sum(size) AS market
           FROM applications_allocation
           WHERE storage_product_id = 4
                 AND last_modified <
                 (%(day_date)s :: DATE + '1 day' :: INTERVAL)
                 ) b
          CROSS JOIN
          (SELECT sum(size) AS vault
           FROM applications_allocation
           WHERE storage_product_id = 10
                 AND last_modified <
                 (%(day_date)s :: DATE + '1 day' :: INTERVAL)
                 ) c;
        """
        if not day_date:
            day_date = date.today()
        self._db_cur.execute(q_allocated, {'day_date': day_date})
        return self._db_cur.fetchall()
