import sys, re

from django.db import connection
from django.conf import settings

from pybb.models import PrivateMessage, MessageBox

db_engine = 'mysql'
if re.search('postgres', settings.DATABASE_ENGINE):
    db_engine = 'postgres'

DESCRIPTION = 'Convert linear private messages model to threaded one'

def migrate():
    cur = connection.cursor()


    print('Checking for messagebox table')
    try:
        check = MessageBox.objects.all().count()
    except:
        print('Table does not exist yet. Please run syncdb first.')
        sys.exit()

    print 'Altering privatemessage table'
    cur.execute("ALTER TABLE pybb_privatemessage ADD thread_id integer NULL")

    print('Updating thread_id for old messages')
    cur.execute("UPDATE pybb_privatemessage SET thread_id=id")

    print('Creating message boxes')
    cur.execute("DELETE FROM pybb_messagebox")
    sql = "INSERT INTO `pybb_messagebox`(`message_id`, `user_id`, `box`, `head`, `read`, `thread_read`, `message_count`)\
        SELECT `id`, `dst_user_id`, 'inbox', true, `read`, `read`, 1 FROM `pybb_privatemessage`"
    if db_engine == 'postgres':
        sql = re.sub('`', '"', sql)
    cur.execute(sql)
    sql = "INSERT INTO `pybb_messagebox`(`message_id`, `user_id`, `box`, `head`, `read`, `thread_read`, `message_count`)\
        SELECT `id`, `src_user_id`, 'outbox', true, true, true, 1 FROM `pybb_privatemessage`"
    if db_engine == 'postgres':
        sql = re.sub('`', '"', sql)
    cur.execute(sql)

    print('Altering privatemessage table')
    sql = 'ALTER TABLE `pybb_privatemessage` DROP `read`'
    if db_engine == 'postgres':
        sql = re.sub('`', '"', sql)
    cur.execute(sql)

    print('Complete!')
