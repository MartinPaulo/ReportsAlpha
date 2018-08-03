import csv
import os
from datetime import date
from pathlib import Path

from django.template.loader import get_template

from reports_beta.local_settings import SPARTAN_MDHS_USERS
from scripts.cloud.utility import Faculties, quarter_dates, LDAP

# ssh into spartan: ssh -i ~/.ssh/mp_unimelb2 root@spartan-m.hpc.unimelb.edu.au
# Run the following sreport command with the desired date range:
# This produces a report giving Account|Login|Used, where used is in minutes
# sreport -P cluster AccountUtilizationByUser start=2017-01-01 end=2017-03-31 format=Accounts,Login,Used

# following prints job counts by cpu sizes, with a percentage of the cluster consumed
# sreport job SizesByAccount PrintJobCount cluster=spartan start=2016-10-01 end=2016-12-31

# To get the job count for the quarter, run the following and then sum the count of jobs to produce the grand total
# sreport job SizesByAccount PrintJobCount grouping=1 cluster=spartan start=2016-07-01 end=2016-09-30

# To get the core compute hours, run the following, then take the 'Reported' total
# sreport cluster Utilization cluster=spartan start=2016-07-01 end=2016-09-30 -t Hours

# For more on sreport see: https://slurm.schedmd.com/sreport.html

# to get the users:
# ssh -i ~/.ssh/mp_unimelb2 root@dashboard.hpc.unimelb.edu.au
# then run mysql

# use karaage;
# SELECT username, email, full_name, department
# FROM person
# WHERE institute_id = 1;

# The following selects the file as csv...

# SHOW VARIABLES LIKE "secure_file_priv"; # to see where we can save files to

# Then use the location to place your output file:

# SELECT username, email, full_name, department
# INTO OUTFILE '/var/lib/mysql-files/2017_q3_spartan_users.csv'
# FIELDS TERMINATED BY ','
# ENCLOSED BY '"'
# LINES TERMINATED BY '\n'
# FROM person
# WHERE institute_id = 1
# ORDER BY username;

quarters = []
file_names = []
spartan_users_csv = []
spartan_commissioned = date(2016, 4, 1)
for q_start, q_end, q_abbreviation in quarter_dates(
        from_date=spartan_commissioned):
    quarters.append((q_abbreviation, q_start, q_end))
    file_names.append(f'{q_abbreviation}_spartan.txt')
    spartan_users_csv.append(f'spartan_users_{q_abbreviation}.csv')

unknown_emails = set()
external_users = set()


def fix_nulls(s):
    return s.strip() if s else ''


def users_for_quarter(users_file_path):
    """
    Reads the mysql output.
    :param users_file_path:
    :return:
    """
    global users, infile, reader, row, user
    users = dict()
    with users_file_path.open(mode='r') as infile:
        reader = csv.DictReader(infile, delimiter="\t")
        next(reader)  # skip header row
        for row in reader:
            user = dict()
            for key in row.keys():
                user[key] = fix_nulls(row[key])
            users[user['username']] = user
    return users


def input_file_path(input_file_name):
    input_path = Path('input')
    input_file = Path(input_path, Path(input_file_name))
    if not input_file.exists():
        print(f'Missing input {input_file}')
        return None
    return input_file


def total_project_job_counts(input_file_name, allocated_projects):
    input_path = input_file_path(input_file_name)
    if not input_path:
        return None
    total_job_count = 0
    with input_path.open() as input_file:
        lines = input_file.readlines()
        for line in lines:
            if line.startswith('#'):
                continue
            # print(line)
            split = line.split()
            project_name = split[1]
            if project_name in allocated_projects:
                job_count = split[3]
                total_job_count += int(job_count)
    return total_job_count


def get_hours_and_minutes(sum_minutes):
    # the sreport output is in minutes. To move to hours:minutes
    # return f'{sum_minutes//60}:{sum_minutes % 60}'
    # and to just round down:
    return f'{sum_minutes//60}'


if __name__ == "__main__":
    import django
    from scripts.config import Configuration

    Configuration.get_production_db()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reports_beta.settings")
    django.setup()
    t = get_template('bc_spartan.tsv')
    last_quarter = quarters[-1][0]
    spartan_users_csv = f'input/spartan_users_{last_quarter}.tsv'
    ldap = LDAP()
    i = -1
    output_dir = Path('output')
    with Path(output_dir, Path(f'{last_quarter}_bc_spartan_2.txt')).open(
            mode='w') as outfile:
        for file_name in file_names:
            allocated_projects = set()
            i += 1
            current_quarter = quarters[i][0]
            f_in = input_file_path(f'{current_quarter}_spartan_users.tsv')
            if not f_in:
                continue
            users = users_for_quarter(f_in)
            input_dir = Path('input')
            f_in = Path(input_dir, Path(file_name))
            if not f_in.exists():
                print(f'Missing input {f_in}')
                continue
            with f_in.open() as infile:
                faculty_totals = Faculties.get_new_totals()
                faculty_project_count = Faculties.get_new_totals()
                reader = csv.reader(infile, delimiter='|')
                next(reader)  # skip header row
                active_users = 0
                for row in reader:
                    username = row[1].strip()
                    if not len(username):
                        #  if there's no username, we can't look up the user...
                        continue
                    active_users += 1
                    project = row[0].strip()
                    faculty = Faculties.UNKNOWN
                    if project.startswith('comp'):
                        # a computer science project
                        faculty = Faculties.MSE
                    else:
                        if username in users:
                            # not all users are from UoM, hence might not be
                            # in the set of known UoM users...
                            user = users[username]
                            faculty = Faculties.get_faculty_from_department(
                                user['department'], user['email'])
                            if faculty == Faculties.UNKNOWN:
                                faculty, _name = ldap.find_faculty(
                                    user['email'])
                                if faculty is Faculties.UNKNOWN:
                                    if user['email'] not in unknown_emails:
                                        unknown_emails.add(user['email'])
                                if faculty is Faculties.EXTERNAL:
                                    external_users.add(user['email'])
                        else:
                            # some users aren't in Kaarage's database because
                            # the query limits it to UniMelb users
                            # This shouldn't be a problem going forward, as we
                            # are going to use project owners who have to
                            # belong to both an institute and a faculty.
                            if username in SPARTAN_MDHS_USERS:
                                faculty = Faculties.MDHS
                            else:
                                faculty = Faculties.EXTERNAL
                            # print(f'--->{username}, faculty: {faculty}')
                    if isinstance(faculty, Faculties):
                        faculty_totals[faculty] += int(row[2].strip())
                        faculty_project_count[faculty] += 1
                        if faculty is not Faculties.EXTERNAL:
                            allocated_projects.add(project)
                    else:
                        print(f'Unrecognized faculty {faculty}')
                grand_total = 0
                hpc_core_hours = {'hpc_hours': []}
                for faculty, total in faculty_totals.items():
                    grand_total += total
                    hpc_core_hours['hpc_hours'].append(
                        (faculty.value, get_hours_and_minutes(total)))
                hpc_core_hours['hpc_total_core_hours'] = str(
                    get_hours_and_minutes(grand_total))
                hpc_core_hours['quarter'] = current_quarter
                grand_total = 0
                for faculty, project_count in faculty_project_count.items():
                    grand_total += project_count
                hpc_core_hours['hpc_project_count'] = []
                for faculty, total in faculty_project_count.items():
                    hpc_core_hours['hpc_project_count'].append(
                        (faculty.value, total))
                hpc_core_hours['hpc_job_count'] = total_project_job_counts(
                    f'{current_quarter}_spartan_job_count.txt',
                    allocated_projects)
                render = t.render(hpc_core_hours)
                outfile.write(render)
