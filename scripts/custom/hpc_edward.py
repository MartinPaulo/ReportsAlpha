import MySQLdb
from sshtunnel import SSHTunnelForwarder

from scripts.cloud.utility import LDAP
from scripts.custom.credentials import Credentials


class EdwardDB:
    _db_connection = None
    _db_cur = None


    def __init__(self):
        ssh_tunnel = Credentials.local_ssh_tunnel
        db_config = Credentials.edward_db
        self._server = SSHTunnelForwarder(
            ((ssh_tunnel['host']), (int(ssh_tunnel['port']))),
            ssh_password=ssh_tunnel['ssh_password'],
            ssh_username=(ssh_tunnel['username']),
            remote_bind_address=(db_config['host'], 3306),
            allow_agent=False
        )
        self._server.start()
        # we are about to bind to a 'local' server by means of an ssh tunnel
        # ssh tunnel: which will be seen as a local server...
        # so replace the loaded config host
        db_config['port'] = self._server.local_bind_port
        self._db_connection = MySQLdb.connect(**db_config)
        self._db_cur = self._db_connection.cursor(MySQLdb.cursors.DictCursor)
        self.test_connection()

    def query(self, query, params):
        return self._db_cur.execute(query, params)

    def get_totals(self, year_wanted):
        """ The cpu_usage is in seconds, so we want it in minutes if we want
        to match spartan's default output..."""
        query = """
            SELECT
              cpu_job.user_id,
              CONCAT(auth_user.first_name, ' ', auth_user.last_name) AS name,
              auth_user.email,
              SUM(cpu_usage) / 60                                    AS cpu_usage,
              SUM(mem)                                               AS mem,
              SUM(vmem)                                              AS vmem
            FROM cpu_job
              LEFT JOIN auth_user ON cpu_job.user_id = auth_user.id
            WHERE email <> ''
                  AND YEAR(date) = %(year)s
            GROUP BY
              user_id
            ORDER BY user_id;
        """
        self._db_cur.execute(query, {
            'year': '%s' % year_wanted
        })
        return self._db_cur.fetchall()

    def __del__(self):
        self.close_connection()

    def close_connection(self):
        if self._server:
            self._db_connection.close()
            self._server.stop()
            self._server = None

    def test_connection(self):
        self._db_cur.execute(
            "SELECT count(*) AS count FROM applications_application;")
        row = self._db_cur.fetchone()
        if row['count'] is None:
            raise Exception('Empy count found?')

    def find_user(self, user_id):
        query = """
            SELECT
              email
            FROM auth_user
            WHERE username = %(user_id)s;
        """
        self._db_cur.execute(query, {
            'user_id': '%s' % user_id
        })
        return self._db_cur.fetchall()

    def get_quarter_usage(self, start_date, end_date):
        query = """
            SELECT
              cpu_job.user_id,
              auth_user.email,
              department,
              SUM(cpu_usage) / 60 AS cpu_usage,
              SUM(mem)       AS mem,
              SUM(vmem)      AS vmem
            FROM cpu_job
              LEFT JOIN person ON cpu_job.user_id = person.user_id
              LEFT JOIN auth_user ON cpu_job.user_id = auth_user.id
            WHERE email <> ''
              AND (date BETWEEN %(start)s AND DATE_ADD(%(end)s, INTERVAL 1 DAY))
              AND (cpu_job.project_id LIKE '%%Melb%%'
                   OR cpu_job.project_id LIKE '%%Col%%')
            GROUP BY
              user_id
            ORDER BY user_id;
        """
        self._db_cur.execute(query, {
            'start': start_date.strftime("%Y-%m-%d"),
            'end': end_date.strftime("%Y-%m-%d")
        })
        return self._db_cur.fetchall()

    def get_job_count(self, start_date, end_date):
        query = """
            SELECT count(*) AS count
            FROM cpu_job
            WHERE (date BETWEEN %(start)s AND DATE_ADD(%(end)s, INTERVAL 1 DAY))
            ORDER BY user_id;
        """
        self._db_cur.execute(query, {
            'start': start_date.strftime("%Y-%m-%d"),
            'end': end_date.strftime("%Y-%m-%d")
        })
        return self._db_cur.fetchone()

if __name__ == "__main__":
    line = '=================================================================='
    o = '{name!s}, {email!s}, {faculty!s}, {cpu_usage!s}, {mem!s}, {vmem!s}'
    db = EdwardDB()
    ldap = LDAP()
    try:
        for year in [2013, 2014, 2015, 2016]:
            print(line)
            print('Year: %s' % year)
            print(line)
            print()
            print(o.format(**{
                'name': 'Name',
                'email': 'Email',
                'faculty': 'Faculty Attributed',
                'cpu_usage': 'CPU Usage',
                'mem': 'Memory',
                'vmem': 'Virtual Memory'
            }))
            totals = db.get_totals(year)
            for total in totals:
                total['faculty'], _name = ldap.find_faculty(total['email'])
                if total['faculty'] is None:
                    total['faculty'] = 'Unknown'
                # total['faculty'], _name = 'Unknown', 'Unknown'
                print(o.format(**total))
            print()
    finally:
        db.close_connection()
