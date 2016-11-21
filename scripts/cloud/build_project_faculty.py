import logging
import sys

from ldap3 import Server, Connection

from scripts.cloud.utility import get_faculty

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
    # Only look the people up on LDAP if the lead has changed
    # Log the projects that have changed faculty
    # Log the number that were not updated
    # Add the hooks that will be used to send required emails...
    # Also, we need to work out what to do if the faculties recorded for
    # a project changed. Do we recalculate it all?
    logging.info("Building project faculty data for all projects")
    result_set = extract_db.get_uom_project_contact_email()
    faculty_members_found = 0
    more_than_one_faculty = 0
    projects_found = len(result_set)
    for row in result_set:
        contact_email = row["contact_email"]
        project_id = row["tenant_uuid"]
        project_name = row["tenant_name"]
        faculties = find_project_leader_faculty(contact_email)
        logging.info("Leader %s belongs to %s", contact_email, faculties)
        if len(faculties) > 1:
            more_than_one_faculty += 1
        if faculties != {'Unknown'}:
            faculty_members_found += 1
        load_db.save_faculty_data(faculties, contact_email, project_id,
                                  project_name)
    logging.info("Of %s projects, %s were found, with %s having "
                 "more than one faculty", projects_found,
                 faculty_members_found, more_than_one_faculty)


def find_project_leader_faculty(project_leader):
    if not ldap_connection:
        bind_to_server()
    query = '(&(objectclass=person)(mail=%s))' % project_leader
    ldap_connection.search('o=unimelb', query,
                           attributes=['department',
                                       'departmentNumber',
                                       'auEduPersonSubType'])
    faculties = None
    if len(ldap_connection.entries) > 0:
        department_no = []
        for entry in ldap_connection.entries:
            if hasattr(entry, 'departmentNumber'):
                department_no.extend(entry.departmentNumber)
        faculties = get_faculty(department_no)
    if not faculties:
        faculties = {'Unknown'}
    return faculties
