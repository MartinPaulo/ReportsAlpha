import logging
import sys

from ldap3 import Server, Connection

from reports.models import CloudProjectFaculty
from scripts.cloud.utility import Faculties

ldap_connection = None


def _bind_to_server():
    global ldap_connection
    ldap_server = Server('centaur.unimelb.edu.au')
    ldap_connection = Connection(ldap_server)
    if not ldap_connection.bind():
        print("Could not bind to LDAP server")
        sys.exit(1)


def build_project_faculty(extract_db, load_db, **kwargs):
    """
    Builds the table of projects

    :return: None

    TODO:
        * Log the projects that have changed faculty
        * Add the hooks that will be used to send required emails...
        * Also, we need to work out what to do if the faculties recorded for
          a project changed. Do we recalculate all our totals or just
          add the totals to the new faculty from this point on (what we do
          now)?
    """
    logging.info('Building project faculty data for all projects')
    result_set = extract_db.get_uom_project_contact_details()
    faculty_members_found = 0
    projects_found = len(result_set)
    for row in result_set:
        project_id = row['tenant_uuid']
        project_description = row['description']
        chief_investigator = row['chief_investigator']
        contact_email = row['contact_email']
        for_code = row['field_of_research']
        for_code_faculty = Faculties.get_from_for_code(for_code)
        # chief investigator is the prime determinant
        faculties = get_faculties_for(chief_investigator)
        if len(faculties) > 1:
            # is there an intersection with the for code? If so, take it
            if for_code_faculty in faculties:
                faculties = [for_code_faculty]
        # if there is no faculty, then try the contact email faculties
        if faculties == [Faculties.UNKNOWN]:
            faculties = get_faculties_for(contact_email)
            if len(faculties) > 1:
                # is there an intersection with the for code? If so, take it
                if for_code_faculty in faculties:
                    faculties = [for_code_faculty]
        # if there is no faculty, then use the for code one.
        if faculties == [Faculties.UNKNOWN]:
            faculties = [for_code_faculty]
        # We can still have more than one faculty in the list. Which one
        # should get precedence?
        if len(faculties) > 1:
            if Faculties.OTHER in faculties:
                faculties.remove(Faculties.OTHER)
            if Faculties.MDHS in faculties:
                faculties = [Faculties.MDHS]
                # at this point, we'll just take the first in the list
        faculty = faculties.pop()
        if faculty != Faculties.UNKNOWN:
            faculty_members_found += 1
        CloudProjectFaculty.objects.get_or_create(
            project_id=project_id,
            defaults={
                'description': project_description,
                'chief_investigator': chief_investigator,
                'contact_email': contact_email,
                'for_code': for_code,
                'allocated_faculty': faculty,
            }
        )
    logging.info('Of %s projects, %s were found', projects_found,
                 faculty_members_found)


def get_faculties_for(uom_email_address):
    """
    :param uom_email_address: A UoM email address to look up
    :return: A list of the faculties associated with the email address, ordered
             as they are returned from the LDAP system
    :rtype: list
    """
    result = None
    if uom_email_address:
        if not ldap_connection:
            _bind_to_server()
        query = '(&(objectclass=person)(mail=%s))' % uom_email_address
        ldap_connection.search('o=unimelb', query,
                               attributes=['department',
                                           'departmentNumber',
                                           'auEduPersonSubType'])
        if len(ldap_connection.entries) > 0:
            department_numbers = []
            for entry in ldap_connection.entries:
                if hasattr(entry, 'departmentNumber'):
                    department_numbers.extend(entry.departmentNumber)
            result = Faculties.get_from_departments(department_numbers)
    if not result:
        result = [Faculties.UNKNOWN]
    return result
