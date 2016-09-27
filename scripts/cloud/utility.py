from datetime import timedelta


def date_range(start_date, end_date):
    """
    A generator that returns all dates from and including the start date
    to the day before the end date.
    :param start_date: the first date to be yielded
    :param end_date: the day after the last date to be yielded.
    :return: yields the next date on
    """
    assert start_date < end_date, "Start date must be before end date"
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


def get_faculty(department_numbers):
    result = set()
    for departmentNumber in department_numbers:
        dep_no = int(departmentNumber[:3])
        if 100 <= dep_no < 250:
            result.add('FoA')  # Faculty of Arts: ARTS in spreadsheet
        elif 250 <= dep_no < 300:
            # Veterinary and Agricultural Sciences: VET SC in spreadsheet
            result.add('VAS')
        elif 300 <= dep_no < 400:
            result.add('FBE')  # Faculty of Business and Economics
        elif 400 <= dep_no < 460:
            result.add('MSE')  # Melbourne School Of Engineering
        elif 460 <= dep_no < 500:
            result.add('MGSE')  # Melbourne Graduate School of Education
        elif 500 <= dep_no < 600:
            result.add('MDHS')  # Medicine, Dentistry and Health Science
        elif 600 <= dep_no < 700:
            result.add('FoS')  # FoS? Faculty of Science: SCI in spreadsheet
        elif 700 <= dep_no < 730:
            result.add('ABP')  # Architecture, Building and Planning
        elif 730 <= dep_no < 750:
            result.add('MLS')  # Melbourne Law School
        elif 750 <= dep_no < 780:
            # Victorian College of the Arts & Melbourne Conservatorium of Music
            result.add('VCAMCM')
        elif 780 <= dep_no < 900:
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
