from django.db import connection

from pybb.models import Forum, Topic

DESCRIPTION = 'Change of max_length of Profile.language field.'

def migrate():
    cur = connection.cursor()

    print 'Altering profile table'
    cur.execute("ALTER TABLE pybb_profile MODIFY language VARCHAR(10) NOT NULL")
