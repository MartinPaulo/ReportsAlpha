import logging
import sys
from datetime import date

from ldap3 import Server, Connection

from scripts.cloud.utility import get_faculty

ldap_server = Server('centaur.unimelb.edu.au')
ldap_connection = Connection(ldap_server)
if not ldap_connection.bind():
    print("Could not bind to LDAP server")
    sys.exit(1)


def build_project_faculty(extract_db, load_db, start_day,
                          end_day=date.today()):
    logging.info("Building project faculty data from %s till %s ",
                 start_day, end_day)
    result_set = extract_db.get_uom_project_contact_email()
    for row in result_set:
        contact_email = row["contact_email"]
        project_id = row["tenant_uuid"]
        project_name = row["tenant_name"]
        faculties = find_project_leader_faculty(contact_email)
        logging.info("Leader %s belongs to %s", contact_email, faculties)
        load_db.save_faculty_data(faculties, contact_email, project_id,
                                  project_name)


def find_project_leader_faculty(project_leader):
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
