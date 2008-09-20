import sqlalchemy as SA
from sqlalchemy import sql
from datetime import datetime
import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.contrib.auth.models import User
from pybb.models import Category, Forum, Topic, Post, Profile

# Punbb database connection setup

ENCODING = 'cp1251'
settings = {'user': 'web', 'passwd': 'web-**', 'host': 'localhost',
            'db': 'pydev'}

uri = 'mysql://%(user)s:%(passwd)s@%(host)s/%(db)s'
uri %= settings
engine = SA.create_engine(uri, encoding='latin1')
conn = engine.connect()

meta = SA.MetaData()
meta.bind = engine

users_table = SA.Table('users', meta, autoload=True)
cats_table = SA.Table('categories', meta, autoload=True)
forums_table = SA.Table('forums', meta, autoload=True)
topics_table = SA.Table('topics', meta, autoload=True)
posts_table = SA.Table('posts', meta, autoload=True)

def decode(data):
    if data is None:
        return None
    return data.decode(ENCODING)

# Import begins

print 'Importing users'
users = {}
User.objects.all().delete()

for row in conn.execute(sql.select([users_table])):
    joined = datetime.fromtimestamp(row['registered'])
    last_login = datetime.fromtimestamp(row['last_visit'])
    user = User(username=decode(row['username']),
                email=row['email'],
                first_name=decode((row['realname'] or '')[:30]),
                date_joined=joined,
                last_login=last_login,
                )
    user.set_password(User.objects.make_random_password())
    user.save()

    users[row['id']] = user

    print user.username

    profile = user.pybb_profile
    profile.jabber = decode(row['jabber'])
    profile.icq = decode(row['icq'])
    profile.yahoo = decode(row['yahoo'])
    profile.msn = decode(row['msn'])
    profile.aim = decode(row['aim'])
    profile.location = decode(row['location'])
    profile.signature = decode(row['signature'])
    profile.show_signatures = bool(row['show_sig'])
    profile.time_zone = row['timezone']

print 'Importing categories'
cats = {}
Category.objects.all().delete()

for row in conn.execute(sql.select([cats_table])):
    cat = Category(name=decode(row['cat_name']),
                   position=row['disp_position'])
    cat.save()
    cats[row['id']] = cat

    print cat.name


print 'Importing forums'
forums = {}
Forum.objects.all().delete()

for row in conn.execute(sql.select([forums_table])):
    forum = Forum(name=decode(row['forum_name']),
                  position=row['disp_position'],
                  description=decode(row['forum_desc']),
                  category=cats[row['cat_id']])
    forum.save()
    forums[row['id']] = forum

    print forum.name


print 'Importing topics'
topics = {}
Topic.objects.all().delete()

for row in conn.execute(sql.select([topics_table])):
    created = datetime.fromtimestamp(row['posted'])
    updated = datetime.fromtimestamp(row['last_post'])

    username = row['poster']
    testuser = users.values()[0]
    for id, testuser in users.iteritems():
        if testuser.username == username:
            user = testuser
            break

    topic = Topic(name=decode(row['subject']),
                  forum=forums[row['forum_id']],
                  created=created,
                  updated=updated,
                  views=row['num_views'],
                  user=user)
    topic.save()
    topics[row['id']] = topic

    print topic.name


print 'Importing posts'
posts = {}
Post.objects.all().delete()

for row in conn.execute(sql.select([posts_table])):
    created = datetime.fromtimestamp(row['posted'])
    updated = row['edited'] and datetime.fromtimestamp(row['edited']) or None

    post = Post(topic=topics[row['topic_id']],
                created=created,
                updated=updated,
                user=users[row['poster_id']],
                user_ip=row['poster_ip'],
                body=decode(row['message']))
    post.save()
    #posts[row['id']] = topic

    print post.id
