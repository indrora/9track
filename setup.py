from project import db as db
from project.models import User
from project.models import Root
from project import scanner

import getpass
import sys
import os.path
import os

def bool_prompt(prompt, default=True):
    while True:
        val = raw_input(prompt)
        if len(val) == 0:
            return default
        elif val in ('y', 'Y', 'yes', 'YES', 'Yes' ):
            return True
        elif val in ('n', 'N', 'No', 'no', 'NO'):
            return False
        else:
            continue

if os.path.isfile("project/ceefax.db3"):
    print("Error: I'm already configured. Destroy ceefax.db3 to reconfigure.")

print(" -- ceefax configuration -- ")
db.create_all()
print(" -- initial user setup --")
uname = raw_input("Username: ")
passw = getpass.getpass()

u = User.create(uname, passw)
db.session.add(u)

print(" An initial library set")
print(" A selection of initial libraries should be configured. ")
libs = []

home = os.getenv("HOME", None)
if home is not None:
    standard_dirs = ( "Pictures", "Documents", "Public" )

    for dirname in standard_dirs:
        realpath = os.path.join(home, dirname)
        if os.path.isdir(realpath):
           if bool_prompt( ( "Add %s <%s>? [Yn]:" % ( dirname, realpath ) )):
                libs.append( (dirname, realpath ))

while True:
    name = raw_input("Name: ")
    path = raw_input("Path: ")
    if ( len(name) == 0 or len(path) == 0):
        break;
    else:
        if not os.path.isdir(path):
            print("That doesn't exist, dolt!")
            continue
        else:
            libs.append( (name, path) )
for name, path in libs:
    root = Root(None, path, name, u, 'private')
    db.session.add(root)
    scanner.scan(root)
    


# Clean up.
db.session.commit()

