import calendar
from collections import Counter
from datetime import timedelta, date
from enum import Enum, unique

from ldap3 import Server, Connection


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


def quarter_dates(from_date=None, to_date=None):
    """
    Args:
        from_date (date): The lower date to generate from. If `None` then will
                          default to 2012-01-01
        to_date (date): The upper date to generate to. If `None` then will
                        default to date.today()

    Yields:
        quarter_start (date), quarter_end (date), quarter_abbreviation: The
        quarter start and end dates from the start of NecTAR in 2012 till the
        last complete quarter before the to_date yielded in sets of three

    Examples:
        >>> for q_start, q_end, q_abbreviation in quarter_dates(to_date=date(2013, 6, 1)):
        ...     print(f'{q_start}, {q_end}, {q_abbreviation}')
        ...
        2012-01-01, 2012-03-31, 2012Q1
        2012-04-01, 2012-06-30, 2012Q2
        2012-07-01, 2012-09-30, 2012Q3
        2012-10-01, 2012-12-31, 2012Q4
        2013-01-01, 2013-03-31, 2013Q1
        >>> for q_start, q_end, q_abbreviation in quarter_dates(from_date=date(2012, 5, 5), to_date=date(2013, 6, 1)):
        ...     print(f'{q_start}, {q_end}, {q_abbreviation}')
        ...
        2012-07-01, 2012-09-30, 2012Q3
        2012-10-01, 2012-12-31, 2012Q4
        2013-01-01, 2013-03-31, 2013Q1
    """
    # Maybe this function should become a class?
    start_date = date(2012, 1, 1) if from_date is None else from_date
    end_date = date.today() if to_date is None else to_date
    start_year = start_date.year
    while start_year <= end_date.year:
        quarter_starts = [date(start_year, month, 1) for month in
                          (1, 4, 7, 10)]
        quarter_ends = [
            date(start_year, month, calendar.monthrange(start_year, month)[1])
            for month in (3, 6, 9, 12)]
        quarter_abbreviations = ['%sQ%s' % (start_year, i) for i in
                                 (1, 2, 3, 4)]
        quarters = list(
            zip(quarter_starts, quarter_ends, quarter_abbreviations))
        start_year += 1
        for quarter in quarters:
            if start_date <= quarter[0] and quarter[1] < end_date:
                yield quarter[0], quarter[1], quarter[2]


def _append(result, new_item):
    """
    Will append `new_item` to `result` iff `new_item` not already in `result`

    Args:
        result (list): the list to append `new_item` to if not already there
        new_item: the object to append if not already in `result`
    """
    if new_item not in result:
        result.append(new_item)


@unique
class Faculties(Enum):
    """
    The known faculties and some utility methods to work with them
    """
    ABP = 'ABP'  # Architecture, Building and Planning
    EXTERNAL = 'External'  # From outside the university
    FBE = 'FBE'  # Faculty of Business and Economics
    FOA = 'FoA'  # Faculty of Arts: ARTS in spreadsheet
    FOS = 'FoS'  # FoS? Faculty of Science: SCI in spreadsheet
    MDHS = 'MDHS'  # Medicine, Dentistry and Health Science
    MGSE = 'MGSE'  # Melbourne Graduate School of Education
    MLS = 'MLS'  # Melbourne Law School
    MSE = 'MSE'  # Melbourne School Of Engineering
    OTHER = 'Other'  # Staff, really.
    UNKNOWN = 'Unknown'
    VAS = 'VAS'  # Veterinary and Agricultural Sciences: VET SC in spreadsheet
    # Victorian College of the Arts & Melbourne Conservatorium  of Music
    VCAMCM = 'VCAMCM'

    @classmethod
    def get_from_department(cls, department):
        # if not department:
        #     return Faculties.UNKNOWN
        misspellings = {
            'null': cls.UNKNOWN,
            'economics': cls.FBE,
            'economcis': cls.FBE,
            'fbe': cls.FBE,
            'sir peter mac dept of oncology': cls.MDHS,
            'software engineering': cls.MSE,
            'chemistry': cls.FOS,
            'engineering': cls.MSE,
            'cluster cloud computing': cls.MSE,
            'school of engineering': cls.MSE,
            'computer': cls.MSE,
            'biochemistry': cls.MDHS,
            'centre for health policy': cls.MDHS,
            'mech eng': cls.MSE,
            'mechanical enginering': cls.MSE,
            'electrical and electronic': cls.MSE,
            'electrical and electronic engineering': cls.MSE,
            'electrical and electronics engineering': cls.MSE,
            'medicine, dentistry and health science': cls.MDHS,
            'school of population and global health': cls.MDHS,
            'medicine': cls.MDHS,
            'asia institute': cls.FOA,
            'shaps': cls.FOA,
            'it': cls.MSE,
            'mse': cls.MSE,
            'science': cls.FOS,
            'science department': cls.FOS,
            'civil engineering': cls.MSE,
            'faculty of science': cls.FOS,
            'melbourne school of engineering': cls.MSE,
            'infrastructure engineering': cls.MSE,
            'infrastructural enigineering': cls.MSE,
            'department of insfrastructure engineering': cls.MSE,
            'department of infrastructure engineering': cls.MSE,
            'computer and information systems': cls.MSE,
            'engineering and computing': cls.MSE,
            'engeneering': cls.MSE,
            'genetics genomics and development': cls.MDHS,
            'm.eng of mechatronics': cls.MSE,
            'computer science': cls.MSE,
            'software engineer': cls.MSE,
            'school of infomation': cls.MSE,
            'computing & information': cls.MSE,
            'msc cs': cls.MSE,
            'distributed computing': cls.MSE,
            'master of information technology': cls.MSE,
            'it department': cls.MSE,
            'infrastructure engineerin': cls.MSE,
            'institute of computational science': cls.MSE,
            'cluster and cloud computing': cls.MSE,
            'comp90024': cls.MSE,
            'resplat': cls.OTHER,
            'staff': cls.OTHER,
            'master of science computer science': cls.MSE,
            'internet technology': cls.MSE,
            'department of information technology': cls.MSE,
            'computing and information system': cls.MSE,
            'department of engineering': cls.MSE,
            'chemical& biomolecular engineering': cls.MSE,
            'physics': cls.FOS,
            'engneering': cls.MSE,
            'school of biosciences': cls.FOS,
            'mspgh (centre for epidemiology and biostatistics)': cls.FOS,
            'biosciences': cls.FOS,
            'bio21': cls.FOS,  # should be FOS?
            'mathematics and statistics': cls.FOS,
            'department mathematics and statistics': cls.FOS,
            'maths & stats': cls.FOS,
            'earth science': cls.FOS,
            'school of mathematics and statistics': cls.FOS,
            'school of mathematics': cls.FOS,
            'school of chemistry, bio21 institute': cls.MDHS,
            'school of information': cls.MSE,
            'information': cls.MSE,
            'melbourne school of information': cls.MSE,
            'optometry and vision science': cls.MDHS,
            'medicine dentistry and health science': cls.MDHS,
            'mechanical': cls.MSE,
            'mechcanical engineering': cls.MSE,
            'computer and information system': cls.MSE,
            'biomedical engineering': cls.MDHS,
            'chemical and biomolecular engineering': cls.MDHS,
            'computing': cls.MSE,
            'biological sciences': cls.MDHS,
            'mit': cls.MSE,
            'school of science': cls.FOS,
            'information system and computing': cls.MSE,
            'cs-mit': cls.MSE,
            'information technology': cls.MSE,
            'engineering & it': cls.MSE,
            'graduate school of science': cls.FOS,
            'engineering and it': cls.MSE,
            'mechanical engineering': cls.MSE,
            'department of mechanical engineering': cls.MSE,
            'computing and information systems': cls.MSE,
            'masters in it': cls.MSE,
            'engineering (software)': cls.MSE,
            'chemical & biomolecular engineering': cls.MDHS,
            'vlsci': cls.MDHS,
            'the university of melbourne': cls.UNKNOWN,
            'university of melbourne': cls.UNKNOWN,
            'melbourne university': cls.UNKNOWN,
            'unimelb': cls.UNKNOWN,
            'student': cls.UNKNOWN,
            'master of it': cls.MSE,
            'cs': cls.MSE,
            'ict': cls.MSE,
            'cis': cls.MSE,
            'florey neuroscience institutes': cls.MDHS,
            'anatomy and neuroscience': cls.MDHS,
            'mathematics': cls.FOS,
            'coepp': cls.FOS,
            'school of ecosystem and forest sciences faculty of science': cls.FOS,
            'earth sciences': cls.FOS,
            'psychiatry': cls.MDHS,
            'psychology': cls.MDHS,
            'melbourne school of psychological sciences': cls.MDHS,
            'school of ecosystem and forest sciences, faculty of science': cls.FOS,
            'faculty of veterinary and agricultural sciences': cls.FOS,
            'infrastructure services': cls.OTHER,
            'infrastructure': cls.OTHER,
            'research platform services': cls.OTHER,
            'eee': cls.MSE,
            # electrical and electronic engineering
            'orygen, the national centre of excellence in youth mental health': cls.MDHS,
            'peter mac': cls.MDHS,
            'wehi': cls.MDHS,
            'population and global health': cls.MDHS,
            'centre for youth mental health': cls.MDHS,
            'the university of melbourne centre for cancer research': cls.MDHS,
            'umccr': cls.MDHS,
            'cesare': cls.EXTERNAL,
            'department of infrastructure enginneering': cls.MSE,
            'finance, bmm labs': cls.FBE,
            'fluids': cls.FOS,
            'genetics, genomics and development': cls.MDHS,
            'microbiology & immunology': cls.MDHS,
            'electrical and electronics': cls.MSE,
            'department of optometry and vision science': cls.MDHS,
            'cymh': cls.MDHS,
            'psychological sciences': cls.MDHS,
            'centre for epidemiology and biostatistics': cls.MDHS,
            'melbourne institute of applied economic and social research': cls.FBE,
            'accounting': cls.FBE,
            'architecture': cls.ABP,
            'ie': cls.MSE,
            'melbourne institute': cls.FBE,
            'miaesr': cls.FBE,
            # melbourne school of population and global health
            'mspgh': cls.MDHS,
            # quantitative and applied ecology group
            'quaeco': cls.FOS,
        }
        department_lower = department.lower()
        try:
            faculty = misspellings[department_lower]
        except KeyError:
            # its a string we haven't seen before...
            # so some hail mary broad strokes
            if 'florey' in department_lower:
                faculty = cls.MDHS
            elif 'chemical' in department_lower:
                faculty = cls.MSE
            elif 'mdhs' in department_lower:
                faculty = cls.MDHS
            elif 'epidemiology' in department_lower:
                faculty = cls.MDHS
            elif 'medicine' in department_lower:
                faculty = cls.MDHS
            elif 'psychological' in department_lower:
                faculty = cls.MDHS
            elif 'dental' in department_lower:
                faculty = cls.MDHS
            elif 'pathology' in department_lower:
                faculty = cls.MDHS
            elif 'cbe' in department_lower:  # chemical and biomolecular engineering
                faculty = cls.MSE
            elif 'psychiatry' in department_lower:
                faculty = cls.MDHS
            elif 'bioinformatics' in department_lower:
                faculty = cls.FOS
            elif 'oncology' in department_lower:
                faculty = cls.MDHS
            elif 'chemistry' in department_lower:
                faculty = cls.FOS
            elif 'glasgow' in department_lower:
                faculty = cls.MDHS
            elif 'physics' in department_lower:
                faculty = cls.FOS
            elif 'engineering' in department_lower:
                faculty = cls.MSE
            elif 'engneering' in department_lower:
                faculty = cls.MSE
            elif 'science it' in department_lower:
                faculty = cls.MSE
            elif 'department of it' in department_lower:
                faculty = cls.MSE
            elif 'information system' in department_lower:
                faculty = cls.MSE
            elif 'math' in department_lower:
                faculty = cls.FOS
            elif 'math' in department_lower:
                faculty = cls.FOS
            elif 'science' in department_lower:  # will hoover up bioscience as well
                faculty = cls.FOS
            elif 'finance' in department_lower:
                faculty = cls.FBE
            elif 'business' in department_lower:
                faculty = cls.FBE
            elif 'architecture' in department_lower:
                faculty = cls.ABP
            elif 'design' in department_lower:
                faculty = cls.ABP
            elif 'microbiology' in department_lower:
                faculty = cls.MDHS
            else:
                faculty = cls.UNKNOWN
        return faculty

    @classmethod
    def get_faculty_from_department(cls, department, user_name):
        # should be changed to deal with list of departments?
        result = set()
        if len(department):
            result.add(cls.get_from_department(department))
            if cls.UNKNOWN in result:
                print(
                    f"Department not found: '{department.lower()}': '', user: {user_name}''")
        else:
            result.add(cls.UNKNOWN)
        return result.pop()

    @classmethod
    def get_from_departments(cls, department_numbers):
        """
        :return: Translates the list of department numbers passed in into a list
        of faculties and returns it as a list with the same ordering as the
        department numbers. Duplicate faculties are ignored.
        """
        # Set order of priority
        # faculties = [
        #     ('^(0[0-9]{3})$', cls.OTHER),  # Chancellery
        #     ('^(1[0-9]{3})$', cls.FOA),
        #     ('^(2[0-9]{3})$', cls.VAS),
        #     ('^(3[0-9]{3})$', cls.FBE),
        #     ('^(4[0-9]{3})$', cls.MSE),
        #     ('^(5[0-9]{3})$', cls.MDHS),
        #     ('^(6[0-9]{3})$', cls.FOS),
        #     ('^(97[0-9]{2})$', cls.OTHER),  # University Services
        #     ('^(7[4-5]{1}[0-9]{2})$', cls.VCAMCM),
        #     ('4600', cls.MGSE),
        #     ('7020', cls.ABP),
        #     ('7320', cls.MLS),
        #     ('7890', cls.FOS)  # Bio21 Institute
        # ]
        result = []  # we don't use a set, as we want to preserve the ordering
        for department_number in department_numbers:
            # # assert (not department_number.lower().endswith('h')), \
            # #     f"Department {department_number} ends with 'H'"
            # faculty_match = None
            # for regex, faculty in faculties:
            #     if re.match(regex, department_number):
            #         _append(result, faculty_match)
            # print("Dept: {0} -----> Faculty: {1}".format(faculty_match))
            #
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
            else:
                _append(result, cls.OTHER)
        # we are going to preference the most common faculty
        return Counter(result).most_common()[0][0]

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
        # need to be careful here: as we are using 'starts with' we need to
        # make sure that one of these sets will not 'shadow' another one.
        # TODO: write a test to check this...
        mdhs_codes = (
            '11', '0304', '0604', '0606', '0903', '1004', '1701', '1702')
        mse_codes = ('01', '02', '06', '08', '09', '10')
        mgse_codes = ('13',)
        fos_codes = ('03', '04', '05')
        foa_codes = ('19', '20', '22')
        vas_codes = ('07',)
        abp_codes = ('12',)
        fbe_codes = ('14', '1501', '1502',)
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

    @classmethod
    def get_new_totals(cls):
        """
        :return: A dictionary containing the known faculties as keys and the
        associated values being an int 0.

        Examples:
        .. code-block:: python
            >>> totals = Faculties.get_new_totals()
            >>> totals[Faculties.ABP] == 0
            True
            >>> for faculty in Faculties: # when new, all faculties are 0
            ...     assert totals[faculty] == 0
            >>> totals2 = Faculties.get_new_totals() # totals aren't linked...
            >>> totals[Faculties.FOA] = 1
            >>> totals[Faculties.FOA]
            1
            >>> totals2[Faculties.FBE]
            0
            >>> totals[Faculties.OTHER] += 1
            >>> totals[Faculties.OTHER]
            1
            >>> totals[Faculties('MDHS')] +=1
            >>> totals[Faculties.MDHS]
            1
        """
        return dict((faculty, 0) for faculty in Faculties)

    @classmethod
    def get_faculties_list(cls):
        """
        :return: A list of all the faculty abbreviations sorted in ascending
        order

        Example:
        .. code-block:: python
            >>> heading = 'Quarter'
            >>> for faculty in Faculties.get_faculties_list():
            ...     heading += ', %s' % faculty
            >>> heading += ', Total'
            >>> print(heading)
            Quarter, ABP, External, FBE, FoA, FoS, MDHS, MGSE, MLS, MSE, Other, Unknown, VAS, VCAMCM, Total

        """
        return sorted([member.value for member in Faculties])


class LDAP:
    _server = None

    @staticmethod
    def append_if_not_in(target, faculty):
        if not faculty in target:
            target.append(faculty)

    def __init__(self):
        self._server = Server('centaur.unimelb.edu.au')

    def find_faculty(self, email):
        """
        Given an email, use the LDAP system to find the users department and
        then use the department to try and find the Faculty. Returns the
        Faculty and and the users display name in a tuple.

        Requires a connection within the UoM network.

        Examples:
            >>> ldap = LDAP()
            >>> ldap.find_faculty('martin.paulo@unimelb.edu.au')
            (<Faculties.OTHER: 'Other'>, 'Martin Paulo')
            >>> ldap.find_faculty('unknown@unimelb.edu.au')
            (<Faculties.UNKNOWN: 'Unknown'>, None)
        """
        if email is None:
            return Faculties.UNKNOWN, None
        if 'unimelb' not in email:
            return Faculties.EXTERNAL, None
        query = '(&(objectclass=person)(mail=%s))' % email
        with Connection(self._server, auto_bind=True) as conn:
            conn.search('o=unimelb', query,
                        attributes=['department', 'departmentNumber',
                                    'displayName'])
            if len(conn.entries) == 0:
                return Faculties.UNKNOWN, None
            department_numbers = []
            display_names = []
            for entry in conn.entries:
                if hasattr(entry, 'departmentNumber'):
                    department_numbers.extend(entry.departmentNumber)
                if hasattr(entry, 'displayName'):
                    display_names.extend(entry.displayName)
            display_name = None
            display_name = display_names[0]
            faculty = Faculties.get_from_departments(department_numbers)
            return faculty, display_name
