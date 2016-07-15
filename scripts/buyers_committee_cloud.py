#!/usr/bin/env python

from ldap3 import Server, Connection, ALL


# This looks up the current position of the staff member: and to the position that they were in when
# they started their project.

def get_faculty(department_numbers):
    result = set()
    for departmentNumber in department_numbers:
        depNo = int(departmentNumber[:3])
        if 100 <= depNo < 250:
            result.add('FoA')  # Faculty of Arts: ARTS in spreadsheet
        elif 250 <= depNo < 300:
            result.add('VAS')  # VAS? Veterinary and Agricultural Sciences: VET SC in spreadsheet
        elif 300 <= depNo < 400:
            result.add('FBE')  # Faculty of Business and Economics
        elif 400 <= depNo < 460:
            result.add('MSE')  # Melbourne School Of Engineering
        elif 460 <= depNo < 500:
            result.add('MGSE')  # Melbourne Graduate School of Education
        elif 500 <= depNo < 600:
            result.add('MDHS')  # Medicine, Dentistry and Health Science
        elif 600 <= depNo < 700:
            result.add('FoS')  # FoS? Faculty of Science: SCI in spreadsheet
        elif 700 <= depNo < 730:
            result.add('ABP')  # Architecture, Building and Planning
        elif 730 <= depNo < 750:
            result.add('MLS')  # Melbourne Law School
        elif 750 <= depNo < 780:
            result.add('VCAMCM')  # Victorian College of the Arts and Melbourne Conservatorium of Music
        elif 780 <= depNo < 900:
            result.add('Bio 21')
        else:
            result.add('Staff')
    return result


def process_file(input_file):
    f = open(input_file, 'r')
    total = 0
    not_found = 0
    staff_no_department = 0
    student_no_department = 0
    undergrad_no_department = 0
    belong_to_more_than_one = 0
    faculty_totals = {'FoA': 0, 'VAS': 0, 'FBE': 0, 'MSE': 0, 'MGSE': 0, 'MDHS': 0, 'FoS': 0, 'ABP': 0, 'MLS': 0,
                      'VCAMCM': 0, 'Bio 21': 0, 'Staff': 0}
    for line in f:
        total += 1
        # user_id, naked_member, first_login_date = [x.strip() for x in line.split(',')]
        project_id, project_leader = [x.strip() for x in line.split(',')]
        query = '(&(objectclass=person)(mail=%s))' % project_leader
        conn.search('o=unimelb', query, attributes=['department', 'departmentNumber', 'auEduPersonSubType'])
        if len(conn.entries) == 0:
            not_found += 1
            continue
        department_no = []
        for entry in conn.entries:
            if hasattr(entry, 'department'):
                if not hasattr(entry, 'departmentNumber'):
                    raise ValueError('WARNING: %s in %s has department without department number!' % (
                        project_leader, entry.department))
            if hasattr(entry, 'departmentNumber'):
                department_no.extend(entry.departmentNumber)
        if len(department_no) == 0:
            if 'student' not in project_leader:
                staff_no_department += 1
            else:
                # print('%s, department not found' % naked_member)
                student_no_department += 1
                if hasattr(entry, 'auEduPersonSubType'):
                    if entry.auEduPersonSubType == 'undergrad':
                        undergrad_no_department += 1
        faculties = get_faculty(department_no)
        if len(faculties) > 1:
            belong_to_more_than_one += 1
        # print('%s, %s ' % (naked_member, " ".join(str(faculty) for faculty in faculties)))
        for faculty in faculties:
            # faculty_totals[faculty] += 1 / len(faculties)
            faculty_totals[faculty] += 1

    print('')
    print('For file %s' % input_file)
    total_found = 0
    for faculty in faculty_totals:
        total_found += faculty_totals[faculty]
    total_percentage = 0
    print('faculty, total, percentage')
    for faculty in sorted(faculty_totals.keys()):
        percentage = faculty_totals[faculty] / total_found * 100
        print('%7s, %5s, %5s' % (faculty, round(faculty_totals[faculty], 2), round(percentage, 2)))
        total_percentage += percentage
    print('')
    print('Faculties found: %s' % total_found)
    print('Total percentage: %s' % total_percentage)
    print('No longer in LDAP system:     %s' % not_found)
    print('Student with no department information: %s of which %s are undergrads' % (
        student_no_department, undergrad_no_department))
    print('Staff with no dept:   %s' % staff_no_department)
    print('People who belong to more that one faculty:   %s' % belong_to_more_than_one)
    print('Total processed:   %s' % total)
    return faculty_totals, total_found


server = Server('centaur.unimelb.edu.au')
conn = Connection(server)
if conn.bind():
    quarter_1, total_found_1 = process_file('/Users/mpaulo/temp/data/q1_active_users.txt')
    quarter_2, total_found_2 = process_file('/Users/mpaulo/temp/data/q2_active_users.txt')
    print()
    print('faculty,  q1 %,  q2 %, % change')
    for faculty in sorted(quarter_1.keys()):
        percentage_1 = round(quarter_1[faculty] / total_found_1 * 100, 2)
        percentage_2 = round(quarter_2[faculty] / total_found_2 * 100, 2)
        divisor = percentage_2
        if divisor == 0:
            divisor = 1
        percentage_change = round((percentage_2 - percentage_1) * 100 / divisor, 2)
        print('%7s, %5s, %5s, %0.2f' % (faculty, percentage_1, percentage_2, percentage_change))
