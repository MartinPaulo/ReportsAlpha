from datetime import timedelta


def date_range(start_date, end_date):
    """
    A generator that returns all dates from and including the start date
    to the day before the end date.
    :param start_date: the first date to be yielded
    :param end_date: the day after the last date to be yielded.
    :return: yields the next date on
    """
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


def get_faculty(department_numbers):
    result = set()
    for departmentNumber in department_numbers:
        depNo = int(departmentNumber[:3])
        if 100 <= depNo < 250:
            result.add('FoA')  # Faculty of Arts: ARTS in spreadsheet
        elif 250 <= depNo < 300:
            result.add(
                'VAS')  # VAS? Veterinary and Agricultural Sciences: VET SC in spreadsheet
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
            result.add(
                'VCAMCM')  # Victorian College of the Arts and Melbourne Conservatorium of Music
        elif 780 <= depNo < 900:
            result.add('MDHS')  # Medicine, Dentistry and Health Science
            # result.add('Bio 21') # Bio 21 goes to MDHS
        else:
            result.add('Other')
    return result


def get_new_faculty_totals():
    return {'FoA': 0, 'VAS': 0, 'FBE': 0, 'MSE': 0,
            'MGSE': 0, 'MDHS': 0, 'FoS': 0, 'ABP': 0,
            'MLS': 0,
            'VCAMCM': 0, 'Unknown': 0, 'Other': 0}