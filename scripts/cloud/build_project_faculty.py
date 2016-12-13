import logging
import sys

from ldap3 import Server, Connection

from scripts.cloud.utility import Faculties

ldap_connection = None


def bind_to_server():
    global ldap_connection
    ldap_server = Server('centaur.unimelb.edu.au')
    ldap_connection = Connection(ldap_server)
    if not ldap_connection.bind():
        print("Could not bind to LDAP server")
        sys.exit(1)


def build_project_faculty(extract_db, load_db, start_day):
    # TODO:
    # Log the projects that have changed faculty
    # Add the hooks that will be used to send required emails...
    # Also, we need to work out what to do if the faculties recorded for
    # a project changed. Do we recalculate all our totals Or just
    # add the totals to the new faculty from this point on (what we do now)?
    logging.info("Building project faculty data for all projects")
    result_set = extract_db.get_uom_project_contact_email()
    faculty_members_found = 0
    more_than_one_faculty = 0
    projects_found = len(result_set)
    for row in result_set:
        contact_email = row["contact_email"]
        project_id = row["tenant_uuid"]
        project_name = row["tenant_name"]
        faculties = get_faculties_for(contact_email)
        if len(faculties) > 1:
            more_than_one_faculty += 1
        if faculties != [Faculties.UNKNOWN]:
            faculty_members_found += 1
        load_db.save_faculty_data(faculties[0], contact_email, project_id,
                                  project_name)
    logging.info("Of %s projects, %s were found, with %s having "
                 "more than one faculty", projects_found,
                 faculty_members_found, more_than_one_faculty)


def get_faculties_for(contact_email):
    """
    :return: A list of the faculties associated with the contact email, ordered
    as they are returned from the LDAP system
    """
    if not ldap_connection:
        bind_to_server()
    query = '(&(objectclass=person)(mail=%s))' % contact_email
    ldap_connection.search('o=unimelb', query,
                           attributes=['department',
                                       'departmentNumber',
                                       'auEduPersonSubType'])
    faculties = None
    if len(ldap_connection.entries) > 0:
        department_numbers = []
        for entry in ldap_connection.entries:
            if hasattr(entry, 'departmentNumber'):
                department_numbers.extend(entry.departmentNumber)
        faculties = Faculties.get_from_departments(department_numbers)
    if not faculties:
        faculties = [Faculties.UNKNOWN]
    return faculties
