import sqlalchemy as SA
from sqlalchemy import sql
from datetime import datetime
import os
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from pybb.models import Category, Forum, Topic, Post, Profile

class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--user', help=u'Punbb DB username'),
        make_option('--password', help=u'Punbb DB password'),
        make_option('--host', default='localhost', help=u'Punbb DB host'),
        make_option('--port', help=u'Punbb DB port'),
        make_option('--encoding', default='cp1251', help=u'Punbb DB encoding'),
        make_option('--engine', default='mysql', help=u'Punbb DB engine [postgres, mysql etc]'),
    )
    help = u'Imports Punbb database. Attention: old contents of pybb database will be removed'
    args = '<db name>'

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError('Punbb database name required')
        else:
            dbname = args[0]

        uri = '%s://' % options['engine']
        if options['user'] is not None:
            uri += options['user']
        if options['password'] is not None:
            uri += ':%s' % options['password']
        if options['host'] is not None:
            uri += '@%s' % options['host']
        if options['port'] is not None:
            uri += ':%s' % options['port']
        uri += '/%s' % dbname

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
            return data.decode(options['encoding'], 'replace')

        # Import begins

        print 'Importing users'
        users = {}
        User.objects.all().delete()

        for count, row in enumerate(conn.execute(sql.select([users_table]))):
            joined = datetime.fromtimestamp(row['registered'])
            last_login = datetime.fromtimestamp(row['last_visit'])
            if len(row['password']) == 40:
                hash = 'sha1$$' + row['password']
            else:
                hash = 'md5$$' + row['password']
            user = User(username=decode(row['username']),
                        email=row['email'],
                        first_name=decode((row['realname'] or '')[:30]),
                        date_joined=joined,
                        last_login=last_login,
                        password=hash
                        )
            if user.username == 'lorien':
                user.is_superuser = True
                user.is_staff = True
            user.save()

            users[row['id']] = user

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

        print 'Total: %d' % (count + 1)
        print 'Imported: %d' % len(users)
        print

        print 'Importing categories'
        cats = {}
        Category.objects.all().delete()

        for count, row in enumerate(conn.execute(sql.select([cats_table]))):
            cat = Category(name=decode(row['cat_name']),
                           position=row['disp_position'])
            cat.save()
            cats[row['id']] = cat

        print 'Total: %d' % (count + 1)
        print 'Imported: %d' % len(cats)
        print

        print 'Importing forums'
        forums = {}
        Forum.objects.all().delete()

        for count, row in enumerate(conn.execute(sql.select([forums_table]))):
            forum = Forum(name=decode(row['forum_name']),
                          position=row['disp_position'],
                          description=decode(row['forum_desc']),
                          category=cats[row['cat_id']])
            forum.save()
            forums[row['id']] = forum

        print 'Total: %d' % (count + 1)
        print 'Imported: %d' % len(forums)
        print


        print 'Importing topics'
        topics = {}
        Topic.objects.all().delete()

        for count, row in enumerate(conn.execute(sql.select([topics_table]))):
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
                          views=row['num_views'],
                          user=user)
            topic.save()
            topic._pybb_updated = updated
            topic._pybb_created = created
            topic._pybb_punbb_id = row['id']
            topic._pybb_posts = 0
            #print topic._pybb_updated
            topics[row['id']] = topic

        print 'Total: %d' % (count + 1)
        print 'Imported: %d' % len(topics)
        print


        print 'Importing posts'
        posts = {}
        Post.objects.all().delete()

        imported = 0
        for count, row in enumerate(conn.execute(sql.select([posts_table]))):
            created = datetime.fromtimestamp(row['posted'])
            updated = row['edited'] and datetime.fromtimestamp(row['edited']) or None

            post = Post(topic=topics[row['topic_id']],
                        created=created,
                        updated=updated,
                        user=users[row['poster_id']],
                        user_ip=row['poster_ip'],
                        body=decode(row['message']))
            
            # postmarkups feels bad on some posts :-/
            try:
                post.save()
            except Exception, ex:
                print post.id, ex
                print decode(row['message'])
                print
            else:
                imported += 1
                topics[row['topic_id']]._pybb_posts += 1
                #posts[row['id']] = topic

        print 'Total: %d' % (count + 1)
        print 'Imported: %d' % imported
        print

        print 'Restoring topics updated and created values'
        for topic in topics.itervalues():
            topic.updated = topic._pybb_updated
            topic.created = topic._pybb_created
            topic.save()


        print 'Remove topics without posts (if any)'
        ids = []
        for topic in topics.itervalues():
            if not topic._pybb_posts:
                ids.append(topic._pybb_punbb_id)
                topic.delete()

        print 'Removed: %d' % len(ids)
        print ','.join(map(str, ids))
        print
