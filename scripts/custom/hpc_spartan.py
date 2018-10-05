import csv

from scripts.cloud.utility import LDAP

# To get the spartan users we dumped the users from the karaage database
# to a text file, thus getting their username, their email and their full name
# (first name + surname)
# Then we used sreport on spartan to generate a list of all users and their
# usage using the default output (core seconds)
# # sreport cluster AccountUtilizationByUser cluster=spartan start=2016-01-01 end=2016-12-31
# we copied that output to a text file, then converted into a csv file
# In future we can just put it into a piped file from the git go (and change
# the time format to hours also, if need be):
#  sreport -P -t hours cluster AccountUtilizationByUser cluster=spartan start=2016-01-01 end=2016-12-31

if __name__ == "__main__":
    line = '=================================================================='
    o = '{full_name!s}, {email!s}, {faculty!s}, {used}'
    print(line)
    print('Year: %s' % 2016)
    print(line)
    print()
    print(o.format(**{
        'full_name': 'Name',
        'email': 'Email',
        'faculty': 'Faculty Attributed',
        'used': 'Usage',
    }))
    ldap = LDAP()
    users = dict()
    with open('input/spartan_users.csv', mode='r') as infile:
        reader = csv.reader(infile)
        next(reader)  # skip header row
        for row in reader:
            user = dict()
            user['username'] = row[0].strip()
            user['email'] = row[1].strip()
            user['full_name'] = row[2].strip()
            users[row[0].strip()] = user
    with open('input/spartanuseinminutes.csv', mode='r') as infile:
        reader = csv.reader(infile)
        next(reader)  # skip header row
        for row in reader:
            usage = dict()
            user = None
            try:
                user = users[row[1].strip()]
            except KeyError:
                print('Not found: %s' % row[1].strip())
                continue
            usage['faculty'], _name = ldap.find_faculty(user['email'])
            if usage['faculty'] is None:
                usage['faculty'] = 'Unknown'
            usage['full_name'] = user['full_name']
            usage['email'] = user['email']
            usage['used'] = row[2].strip()
            print(o.format(**usage))
