import calendar
from datetime import timedelta, date


def date_range(start_date, end_date):
    """ A generator that returns all dates from and including the start date
    to the day before the end date.

    Args:
        start_date (date): the first date to be yielded
        end_date (date): the day after the last date to be yielded.

    Yields:
        date: The next date in the range of `start_date` to `end_date` - 1 day
    """
    assert start_date < end_date, "Start date must be before end date"
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


def quarter_dates(to_date=None):
    """
    Args:
        to_date (date): The upper date to generate to. If `None` then will
                        default to date.today()

    Yields:
        quarter_start (date), quarter_end (date): The quarter start and end
        dates from the start of NecTAR in 2012 till the last complete quarter
        before the to_date
        yielded in pairs

    Examples:
        >>> for q_start, q_end in quarter_dates(date(2013, 2, 1)):
        >>>     print('%s %s' % (q_start, q_end))
        2012-01-01 2012-03-31
        2012-04-01 2012-06-30
        2012-07-01 2012-09-30
        2012-10-01 2012-12-31
    """
    year = 2012
    end_date = date.today() if to_date is None else to_date
    while year <= end_date.year:
        quarter_starts = [date(year, month, 1) for month in (1, 4, 7, 10)]
        quarter_ends = [
            date(year, month, calendar.monthrange(year, month)[1])
            for month in (3, 6, 9, 12)]
        quarters = list(zip(quarter_starts, quarter_ends))
        year += 1
        for quarter in quarters:
            if quarter[1] < end_date:
                yield quarter[0], quarter[1]


def _append(result, new_item):
    """
    Will append `new_item` to `result` iff `new_item` not already in `result`

    Args:
        result (list): the list to append `new_item` to if not already there
        new_item: the object to append if not already in `result`
    """
    if new_item not in result:
        result.append(new_item)


class Faculties:
    """
    The list of known faculties and some utility methods to work with them
    """
    OTHER = 'Other'  # Staff, really.
    UNKNOWN = 'Unknown'
    # Victorian College of the Arts & Melbourne Conservatorium  of Music
    VCAMCM = 'VCAMCM'
    MLS = 'MLS'  # Melbourne Law School
    ABP = 'ABP'  # Architecture, Building and Planning
    FOS = 'FoS'  # FoS? Faculty of Science: SCI in spreadsheet
    MDHS = 'MDHS'  # Medicine, Dentistry and Health Science
    MGSE = 'MGSE'  # Melbourne Graduate School of Education
    MSE = 'MSE'  # Melbourne School Of Engineering
    FBE = 'FBE'  # Faculty of Business and Economics
    FOA = 'FoA'  # Faculty of Arts: ARTS in spreadsheet
    VAS = 'VAS'  # Veterinary and Agricultural Sciences: VET SC in spreadsheet

    @classmethod
    def get_from_departments(cls, department_numbers):
        """
        :return: Translates the list of department numbers passed in into a list
        of faculties and returns it as a list with the same ordering as the
        department numbers. Duplicate faculties are ignored.
        """
        result = []  # we don't use a set, as we want to preserve the ordering
        for department_number in department_numbers:
            dep_no = int(department_number[:3])
            if 100 <= dep_no < 250:
                _append(result, cls.FOA)
            elif 250 <= dep_no < 300:
                _append(result, cls.VAS)
            elif 300 <= dep_no < 400:
                _append(result, cls.FBE)
            elif 400 <= dep_no < 460:
                _append(result, cls.MSE)
            elif 460 <= dep_no < 500:
                _append(result, cls.MGSE)
            elif 500 <= dep_no < 600:
                _append(result, cls.MDHS)
            elif 600 <= dep_no < 700:
                _append(result, cls.FOS)
            elif 700 <= dep_no < 730:
                _append(result, cls.ABP)
            elif 730 <= dep_no < 750:
                _append(result, cls.MLS)
            elif 750 <= dep_no < 780:
                _append(result, cls.VCAMCM)
            elif 780 <= dep_no < 900:
                _append(result, cls.MDHS)
                # result.add('Bio 21') # Bio 21 goes to MDHS
            else:
                _append(result, cls.OTHER)
        return result

    @classmethod
    def get_new_totals(cls):
        """
        :return: A dictionary containing the known faculties as keys and the
        associated values being an int 0.
        """
        return {cls.ABP: 0, cls.FBE: 0, cls.FOA: 0, cls.FOS: 0,
                cls.MDHS: 0, cls.MGSE: 0, cls.MLS: 0, cls.MSE: 0,
                cls.OTHER: 0, cls.UNKNOWN: 0, cls.VAS: 0, cls.VCAMCM: 0}

    @classmethod
    def get_from_for_code(cls, for_code):
        """
        :return: Faculty that best matches the FOR code argument 
        
        :param for_code: str giving the FOR code
         
        .. seealso:: 
            * http://www.abs.gov.au/ausstats/abs@.nsf/0/6BB427AB9696C225CA2574180004463E
            * http://w3.unisa.edu.au/res/admin/for.asp
        """
        if not for_code:
            return cls.UNKNOWN
        mdhs_codes = (
            '11', '0304', '0604', '0606', '0903', '1004', '1701', '1702')
        mse_codes = ('01', '02', '06', '08', '09', '10')
        fos_codes = ('03', '04', '05')
        vas_codes = ('07',)
        abp_codes = ('12',)
        mgse_codes = ('13',)
        fbe_codes = ('14', '1501', '1502',)
        foa_codes = ('19', '20', '22')
        if for_code.startswith(mdhs_codes):
            return cls.MDHS
        elif for_code.startswith(mse_codes):
            return cls.MSE
        elif for_code.startswith(mgse_codes):
            return cls.MGSE
        elif for_code.startswith(fos_codes):
            return cls.FOS
        elif for_code.startswith(foa_codes):
            return cls.FOA
        elif for_code.startswith(vas_codes):
            return cls.VAS
        elif for_code.startswith(abp_codes):
            return cls.ABP
        elif for_code.startswith(fbe_codes):
            return cls.FBE
        return cls.UNKNOWN
