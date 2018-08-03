from scripts.cloud.utility import quarter_dates, LDAP
from scripts.custom.hpc_edward import EdwardDB

line = '=================================================================='
unknown_emails = set()
external_users = set()


def get_from_department(department):
    if not department:
        return 'Unknown'
    map = {'Software Engineering': 'MSE',
           'Computing and Information System': 'MSE',
           'Chemistry': 'FoS',
           'Engineering': 'MSE',
           'Cluster Cloud Computing': 'MSE',
           'School of Engineering': 'MSE',
           'Computer': 'MSE',
           'Biochemistry': 'MDHS',
           'Graduate school of science': 'FoS',
           'mech eng': 'MSE',
           'IT': 'MSE',
           'Science': 'FoS',
           'Melbourne School of Engineering': 'MSE',
           'Department of Infrastructure Engineering': 'MSE',
           'Computer and Information systems': 'MSE',
           'Computer and Information Systems': 'MSE',
           'engineering and computing': 'MSE',
           'Computer Science': 'MSE',
           'Computer science': 'MSE',
           'Computing and Information system': 'MSE',
           'Department of Engineering': 'MSE',
           'Chemical& Biomolecular Engineering': 'MSE',
           'Physics': 'FoS',
           'engneering': 'MSE',
           'Bio21': 'Bio 21',
           'Mathematics and Statistics': 'FoS',
           'Maths & Stats': 'FoS',
           'computer science': 'MSE',
           'School of Chemistry, Bio21 Institute': 'Bio 21',
           'School of Information': 'MSE',
           'optometry and vision science': 'MDHS',
           'Mechcanical Engineering': 'MSE',
           'Computer and Information System': 'MSE',
           'Biomedical Engineering': 'MDHS',
           'Chemical and Biomolecular Engineering': 'MDHS',
           'Computing': 'MSE',
           'Biological Sciences': 'MDHS',
           'MIT': 'MSE',
           'School of Science': 'FoS',
           'Information system and computing': 'MSE',
           'Information technology': 'MSE',
           'CS-MIT': 'MSE',
           'Information Technology': 'MSE',
           'Engineering & IT': 'MSE',
           'Graduate school of Science': 'FoS',
           'Engineering and IT': 'MSE',
           'Mechanical Engineering': 'MSE',
           'Computing and Information Systems': 'MSE',
           'Masters in IT': 'MSE',
           'Engineering (Software)': 'MSE',
           'Chemical & Biomolecular Engineering': 'MDHS',
           'VLSCI': 'MDHS',
           'the University of Melbourne': 'Unknown',
           'Master of IT': 'MSE',
           'CS': 'MSE',
           'ICT': 'MSE',
           'CIS': 'MSE',
           'Florey Neuroscience Institutes': 'MDHS',
           'Anatomy and Neuroscience': 'MDHS',
           'Mathematics': 'FoS'
           }
    return map[department]


if __name__ == "__main__":
    print("Edward usage: cores * wall time per faculty")
    print()
    db = EdwardDB()
    ldap = LDAP()
    students_not_found = 0
    staff_not_found = 0
    for start_date, end_date in quarter_dates():
        print(line)
        print('From: %s  To: %s' % (start_date, end_date))
        print(line)
        print()
        job_count = db.get_job_count(start_date, end_date)['count']
        quarter = db.get_quarter_usage(start_date, end_date)
        active_users = len(quarter)
        jobs = len(quarter)
        faculty_totals = {'FoA': 0, 'VAS': 0, 'FBE': 0, 'MSE': 0, 'MGSE': 0,
                          'MDHS': 0, 'FoS': 0, 'ABP': 0, 'MLS': 0,
                          'VCAMCM': 0, 'Bio 21': 0, 'Staff': 0, 'External': 0,
                          'Unknown': 0}

        for user in quarter:
            faculty, _name = ldap.find_faculty(user['email'])
            if faculty is None:
                faculty = get_from_department(user['department'].strip())
            else:
                faculty = faculty.split()[0]
            if faculty == 'Unknown':
                if user['email'] not in unknown_emails:
                    unknown_emails.add(user['email'])
                    if 'student' in user['email']:
                        students_not_found += 1
                    else:
                        staff_not_found += 1
            if faculty == 'External':
                external_users.add(user['email'])
            faculty_totals[faculty] += int(user['cpu_usage'])
        for faculty, total in sorted(faculty_totals.items()):
            print('{}, {}'.format(faculty, total))
        print()
        print('Jobs: %s' % job_count)
        print('Active users: %s' % active_users)
        print()
    db.close_connection()
    print(line)
    print()
    print('Unknown is made up of:')
    print('   Staff not found: %s' % staff_not_found)
    print('   Students not found: %s' % students_not_found)
