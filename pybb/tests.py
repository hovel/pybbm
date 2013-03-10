# -*- coding: utf-8 -*-

import time, datetime
import os

from django.contrib.auth.models import User, Permission
from django.core import mail
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.test.client import Client
from pybb.templatetags.pybb_tags import pybb_is_topic_unread, pybb_topic_unread, pybb_forum_unread

try:
    from lxml import html
except ImportError:
    raise Exception('PyBB requires lxml for self testing')

from pybb import defaults
from pybb.models import *

__author__ = 'zeus'


class SharedTestModule(object):

    def create_user(self):
        self.user = User.objects.create_user('zeus', 'zeus@localhost', 'zeus')

    def login_client(self, username='zeus', password='zeus'):
        self.client.login(username=username, password=password)

    def create_initial(self, post=True):
        self.category = Category(name='foo')
        self.category.save()
        self.forum = Forum(name='xfoo', description='bar', category=self.category)
        self.forum.save()
        self.topic = Topic(name='etopic', forum=self.forum, user=self.user)
        self.topic.save()
        if post:
            self.post = Post(topic=self.topic, user=self.user, body='bbcode [b]test[b]')
            self.post.save()

    def get_form_values(self, response, form="post-form"):
        return dict(html.fromstring(response.content).xpath('//form[@class="%s"]' % form)[0].form_values())

    def get_with_user(self, url, username=None, password=None):
        if username: 
            self.client.login(username=username, password=password)
        r = self.client.get(url)
        self.client.logout()
        return r


class FeaturesTest(TestCase, SharedTestModule):
    def setUp(self):
        self.ORIG_PYBB_ENABLE_ANONYMOUS_POST = defaults.PYBB_ENABLE_ANONYMOUS_POST
        self.ORIG_PYBB_PREMODERATION = defaults.PYBB_PREMODERATION
        defaults.PYBB_PREMODERATION = False
        defaults.PYBB_ENABLE_ANONYMOUS_POST = False
        self.create_user()
        self.create_initial()
        mail.outbox = []

    def test_base(self):
        # Check index page
        url = reverse('pybb:index')
        response = self.client.get(url)
        parser = html.HTMLParser(encoding='utf8')
        tree = html.fromstring(response.content, parser=parser)
        self.assertContains(response, u'foo')
        self.assertContains(response, self.forum.get_absolute_url())
        self.assertTrue(defaults.PYBB_DEFAULT_TITLE in tree.xpath('//title')[0].text_content())
        self.assertEqual(len(response.context['categories']), 1)

    def test_forum_page(self):
        # Check forum page
        response = self.client.get(self.forum.get_absolute_url())
        self.assertEqual(response.context['forum'], self.forum)
        tree = html.fromstring(response.content)
        self.assertTrue(tree.xpath('//a[@href="%s"]' % self.topic.get_absolute_url()))
        self.assertTrue(tree.xpath('//title[contains(text(),"%s")]' % self.forum.name))
        self.assertFalse(tree.xpath('//a[contains(@href,"?page=")]'))
        self.assertFalse(response.context['is_paginated'])

    def test_category_page(self):
        response = self.client.get(self.category.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.forum.get_absolute_url())

    def test_profile_language_default(self):
        user = User.objects.create_user(username='user2', password='user2', email='user2@example.com')
        self.assertEqual(user.get_profile().language, settings.LANGUAGE_CODE)

    def test_profile_edit(self):
        # Self profile edit
        self.login_client()
        response = self.client.get(reverse('pybb:edit_profile'))
        self.assertEqual(response.status_code, 200)
        values = self.get_form_values(response, 'profile-edit')
        values['signature'] = 'test signature'
        response = self.client.post(reverse('pybb:edit_profile'), data=values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.client.get(self.post.get_absolute_url(), follow=True)
        self.assertContains(response, 'test signature')
        # Test empty signature
        values['signature'] = ''
        response = self.client.post(reverse('pybb:edit_profile'), data=values, follow=True)
        self.assertEqual(len(response.context['form'].errors), 0)

    def test_pagination_and_topic_addition(self):
        for i in range(0, defaults.PYBB_FORUM_PAGE_SIZE + 3):
            topic = Topic(name='topic_%s_' % i, forum=self.forum, user=self.user)
            topic.save()
        url = reverse('pybb:forum', args=[self.forum.id])
        response = self.client.get(url)
        self.assertEqual(len(response.context['topic_list']), defaults.PYBB_FORUM_PAGE_SIZE)
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(response.context['paginator'].num_pages,
                         ((defaults.PYBB_FORUM_PAGE_SIZE + 3) / defaults.PYBB_FORUM_PAGE_SIZE) + 1)

    def test_bbcode_and_topic_title(self):
        response = self.client.get(self.topic.get_absolute_url())
        tree = html.fromstring(response.content)
        self.assertTrue(self.topic.name in tree.xpath('//title')[0].text_content())
        self.assertContains(response, self.post.body_html)
        self.assertContains(response, u'bbcode <strong>test</strong>')

    def test_topic_addition(self):
        self.login_client()
        add_topic_url = reverse('pybb:add_topic', kwargs={'forum_id': self.forum.id})
        response = self.client.get(add_topic_url)
        values = self.get_form_values(response)
        values['body'] = 'new topic test'
        values['name'] = 'new topic name'
        values['poll_type'] = 0
        response = self.client.post(add_topic_url, data=values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Topic.objects.filter(name='new topic name').exists())

    def test_post_deletion(self):
        post = Post(topic=self.topic, user=self.user, body='bbcode [b]test[b]')
        post.save()
        post.delete()
        Topic.objects.get(id=self.topic.id)
        Forum.objects.get(id=self.forum.id)

    def test_topic_deletion(self):
        topic = Topic(name='xtopic', forum=self.forum, user=self.user)
        topic.save()
        post = Post(topic=topic, user=self.user, body='one')
        post.save()
        post = Post(topic=topic, user=self.user, body='two')
        post.save()
        post.delete()
        Topic.objects.get(id=topic.id)
        Forum.objects.get(id=self.forum.id)
        topic.delete()
        Forum.objects.get(id=self.forum.id)

    def test_forum_updated(self):
        time.sleep(1)
        topic = Topic(name='xtopic', forum=self.forum, user=self.user)
        topic.save()
        post = Post(topic=topic, user=self.user, body='one')
        post.save()
        post = Post.objects.get(id=post.id)
        self.assertTrue(self.forum.updated==post.created)

    def test_read_tracking(self):
        topic = Topic(name='xtopic', forum=self.forum, user=self.user)
        topic.save()
        post = Post(topic=topic, user=self.user, body='one')
        post.save()
        client = Client()
        client.login(username='zeus', password='zeus')
        # Topic status
        tree = html.fromstring(client.get(topic.forum.get_absolute_url()).content)
        self.assertTrue(tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % topic.get_absolute_url()))
        # Forum status
        tree = html.fromstring(client.get(reverse('pybb:index')).content)
        self.assertTrue(tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % topic.forum.get_absolute_url()))
        # Visit it
        client.get(topic.get_absolute_url())
        # Topic status - readed
        tree = html.fromstring(client.get(topic.forum.get_absolute_url()).content)
        # Visit others
        for t in topic.forum.topics.all():
            client.get(t.get_absolute_url())
        self.assertFalse(tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % topic.get_absolute_url()))
        # Forum status - readed
        tree = html.fromstring(client.get(reverse('pybb:index')).content)
        self.assertFalse(tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % topic.forum.get_absolute_url()))
        # Post message
        add_post_url = reverse('pybb:add_post', kwargs={'topic_id': topic.id})
        response = client.get(add_post_url)
        values = self.get_form_values(response)
        values['body'] = 'test tracking'
        response = client.post(add_post_url, values, follow=True)
        self.assertContains(response, 'test tracking')
        # Topic status - readed
        tree = html.fromstring(client.get(topic.forum.get_absolute_url()).content)
        self.assertFalse(tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % topic.get_absolute_url()))
        # Forum status - readed
        tree = html.fromstring(client.get(reverse('pybb:index')).content)
        self.assertFalse(tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % topic.forum.get_absolute_url()))
        post = Post(topic=topic, user=self.user, body='one')
        post.save()
        client.get(reverse('pybb:mark_all_as_read'))
        tree = html.fromstring(client.get(reverse('pybb:index')).content)
        self.assertFalse(tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % topic.forum.get_absolute_url()))
        # Empty forum - readed
        f = Forum(name='empty', category=self.category)
        f.save()
        tree = html.fromstring(client.get(reverse('pybb:index')).content)
        self.assertFalse(tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % f.get_absolute_url()))

    def test_read_tracking_multi_user(self):
        topic_1 = self.topic
        topic_2 = Topic(name='topic_2', forum=self.forum, user=self.user)
        topic_2.save()
       
        Post(topic=topic_2, user=self.user, body='one').save()

        user_ann = User.objects.create_user('ann', 'ann@localhost', 'ann')
        client_ann = Client()
        client_ann.login(username='ann', password='ann')

        user_bob = User.objects.create_user('bob', 'bob@localhost', 'bob')
        client_bob = Client()
        client_bob.login(username='bob', password='bob')

        # Two topics, each with one post. everything is unread, so the db should reflect that:
        self.assertEqual(TopicReadTracker.objects.all().count(), 0)
        self.assertEqual(ForumReadTracker.objects.all().count(), 0)

        # user_ann reads topic_1, she should get one topic read tracker, there should be no forum read trackers
        client_ann.get(topic_1.get_absolute_url())
        self.assertEqual(TopicReadTracker.objects.all().count(), 1)
        self.assertEqual(TopicReadTracker.objects.filter(user=user_ann).count(), 1)
        self.assertEqual(TopicReadTracker.objects.filter(user=user_ann, topic=topic_1).count(), 1)
        self.assertEqual(ForumReadTracker.objects.all().count(), 0)

        # user_bob reads topic_1, he should get one topic read tracker, there should be no forum read trackers
        client_bob.get(topic_1.get_absolute_url())
        self.assertEqual(TopicReadTracker.objects.all().count(), 2)
        self.assertEqual(TopicReadTracker.objects.filter(user=user_bob).count(), 1)
        self.assertEqual(TopicReadTracker.objects.filter(user=user_bob, topic=topic_1).count(), 1)

        # user_bob reads topic_2, he should get a forum read tracker, 
        #  there should be no topic read trackers for user_bob
        client_bob.get(topic_2.get_absolute_url())
        self.assertEqual(TopicReadTracker.objects.all().count(), 1)
        self.assertEqual(ForumReadTracker.objects.all().count(), 1)
        self.assertEqual(ForumReadTracker.objects.filter(user=user_bob).count(), 1)
        self.assertEqual(ForumReadTracker.objects.filter(user=user_bob, forum=self.forum).count(), 1)
        self.assertEqual(TopicReadTracker.objects.filter(user=user_bob).count(), 0)
        self.assertListEqual(
            [t.unread for t in pybb_topic_unread([topic_1, topic_2], user_bob)],
            [False, False])

        # user_ann creates topic_3, they should get a new topic read tracker in the db 
        add_topic_url = reverse('pybb:add_topic', kwargs={'forum_id': self.forum.id})
        response = client_ann.get(add_topic_url)
        values = self.get_form_values(response)
        values['body'] = 'topic_3'
        values['name'] = 'topic_3'
        values['poll_type'] = 0
        response = client_ann.post(add_topic_url, data=values, follow=True)
        self.assertEqual(TopicReadTracker.objects.all().count(), 2)
        self.assertEqual(TopicReadTracker.objects.filter(user=user_ann).count(), 2)
        self.assertEqual(ForumReadTracker.objects.all().count(), 1)

        topic_3 = Topic.objects.order_by('-updated')[0]
        self.assertEqual(topic_3.name, 'topic_3')

        # user_ann posts to topic_1, a topic they've already read, no new trackers should be created
        add_post_url = reverse('pybb:add_post', kwargs={'topic_id': topic_1.id})
        response = client_ann.get(add_post_url)
        values = self.get_form_values(response)
        values['body'] = 'test tracking'
        response = client_ann.post(add_post_url, values, follow=True)
        self.assertEqual(TopicReadTracker.objects.all().count(), 2)
        self.assertEqual(TopicReadTracker.objects.filter(user=user_ann).count(), 2)
        self.assertEqual(ForumReadTracker.objects.all().count(), 1)

        # user_bob has two unread topics, 'topic_1' and 'topic_3'.
        #   This is because user_ann created a new topic and posted to an existing topic,
        #   after user_bob got his forum read tracker.
        # user_bob reads 'topic_1'
        #   user_bob gets a new topic read tracker, and the existing forum read tracker stays the same.
        #   'topic_3' appears unread for user_bob
        #
        self.assertEqual(ForumReadTracker.objects.all().count(), 1)
        previous_time = ForumReadTracker.objects.all()[0].time_stamp

        client_bob.get(topic_1.get_absolute_url())
        self.assertEqual(ForumReadTracker.objects.all().count(), 1)
        self.assertEqual(ForumReadTracker.objects.all()[0].time_stamp, previous_time)
        self.assertEqual(TopicReadTracker.objects.all().count(), 3)
        self.assertEqual(TopicReadTracker.objects.filter(user=user_bob).count(), 1)

        # user_bob reads the last unread topic, 'topic_3'.
        # user_bob's existing forum read tracker updates and his topic read tracker disappears
        #
        self.assertEqual(ForumReadTracker.objects.all().count(), 1)
        previous_time = ForumReadTracker.objects.all()[0].time_stamp

        client_bob.get(topic_3.get_absolute_url())
        self.assertEqual(ForumReadTracker.objects.all().count(), 1)
        self.assertGreater(ForumReadTracker.objects.all()[0].time_stamp, previous_time)
        self.assertEqual(TopicReadTracker.objects.all().count(), 2)
        self.assertEqual(TopicReadTracker.objects.filter(user=user_bob).count(), 0)

    def test_read_tracking_multi_forum(self):
        topic_1 = self.topic
        topic_2 = Topic(name='topic_2', forum=self.forum, user=self.user)
        topic_2.save()
       
        Post(topic=topic_2, user=self.user, body='one').save()

        forum_1 = self.forum
        forum_2 = Forum(name='forum_2', description='bar', category=self.category)
        forum_2.save()

        Topic(name='garbage', forum=forum_2, user=self.user).save()

        client = Client()
        client.login(username='zeus', password='zeus')

        # everything starts unread
        self.assertEqual(ForumReadTracker.objects.all().count(), 0)
        self.assertEqual(TopicReadTracker.objects.all().count(), 0)

        # user reads topic_1, they should get one topic read tracker, there should be no forum read trackers
        client.get(topic_1.get_absolute_url())
        self.assertEqual(TopicReadTracker.objects.all().count(), 1)
        self.assertEqual(TopicReadTracker.objects.filter(user=self.user).count(), 1)
        self.assertEqual(TopicReadTracker.objects.filter(user=self.user, topic=topic_1).count(), 1)

        # user reads topic_2, they should get a forum read tracker, 
        #  there should be no topic read trackers for the user
        client.get(topic_2.get_absolute_url())
        self.assertEqual(TopicReadTracker.objects.all().count(), 0)
        self.assertEqual(ForumReadTracker.objects.all().count(), 1)
        self.assertEqual(ForumReadTracker.objects.filter(user=self.user).count(), 1)
        self.assertEqual(ForumReadTracker.objects.filter(user=self.user, forum=self.forum).count(), 1)

    def test_pybb_is_topic_unread_filter(self):
        forum_1 = self.forum
        topic_1 = self.topic
        topic_2 = Topic.objects.create(name='topic_2', forum=forum_1, user=self.user)

        forum_2 = Forum.objects.create(name='forum_2', description='forum2', category=self.category)
        topic_3 = Topic.objects.create(name='topic_2', forum=forum_2, user=self.user)

        Post(topic=topic_1, user=self.user, body='one').save()
        Post(topic=topic_2, user=self.user, body='two').save()
        Post(topic=topic_3, user=self.user, body='three').save()

        user_ann = User.objects.create_user('ann', 'ann@localhost', 'ann')
        client_ann = Client()
        client_ann.login(username='ann', password='ann')

        # Two topics, each with one post. everything is unread, so the db should reflect that:
        self.assertTrue(pybb_is_topic_unread(topic_1, user_ann))
        self.assertTrue(pybb_is_topic_unread(topic_2, user_ann))
        self.assertTrue(pybb_is_topic_unread(topic_3, user_ann))
        self.assertListEqual(
            [t.unread for t in pybb_topic_unread([topic_1, topic_2, topic_3], user_ann)],
            [True, True, True])

        client_ann.get(topic_1.get_absolute_url())
        topic_1 = Topic.objects.get(id=topic_1.id)
        topic_2 = Topic.objects.get(id=topic_2.id)
        topic_3 = Topic.objects.get(id=topic_3.id)
        self.assertFalse(pybb_is_topic_unread(topic_1, user_ann))
        self.assertTrue(pybb_is_topic_unread(topic_2, user_ann))
        self.assertTrue(pybb_is_topic_unread(topic_3, user_ann))
        self.assertListEqual(
            [t.unread for t in pybb_topic_unread([topic_1, topic_2, topic_3], user_ann)],
            [False, True, True])

        client_ann.get(topic_2.get_absolute_url())
        topic_1 = Topic.objects.get(id=topic_1.id)
        topic_2 = Topic.objects.get(id=topic_2.id)
        topic_3 = Topic.objects.get(id=topic_3.id)
        self.assertFalse(pybb_is_topic_unread(topic_1, user_ann))
        self.assertFalse(pybb_is_topic_unread(topic_2, user_ann))
        self.assertTrue(pybb_is_topic_unread(topic_3, user_ann))
        self.assertListEqual(
            [t.unread for t in pybb_topic_unread([topic_1, topic_2, topic_3], user_ann)],
            [False, False, True])

        client_ann.get(topic_3.get_absolute_url())
        topic_1 = Topic.objects.get(id=topic_1.id)
        topic_2 = Topic.objects.get(id=topic_2.id)
        topic_3 = Topic.objects.get(id=topic_3.id)
        self.assertFalse(pybb_is_topic_unread(topic_1, user_ann))
        self.assertFalse(pybb_is_topic_unread(topic_2, user_ann))
        self.assertFalse(pybb_is_topic_unread(topic_3, user_ann))
        self.assertListEqual(
            [t.unread for t in pybb_topic_unread([topic_1, topic_2, topic_3], user_ann)],
            [False, False, False])

    def test_read_tracker_when_topics_forum_changed(self):
        forum_1 = Forum.objects.create(name='f1', description='bar', category=self.category)
        forum_2 = Forum.objects.create(name='f2', description='bar', category=self.category)
        topic_1 = Topic.objects.create(name='t1', forum=forum_1, user=self.user)
        topic_2 = Topic.objects.create(name='t2', forum=forum_2, user=self.user)

        Post.objects.create(topic=topic_1, user=self.user, body='one')
        Post.objects.create(topic=topic_2, user=self.user, body='two')

        user_ann = User.objects.create_user('ann', 'ann@localhost', 'ann')
        client_ann = Client()
        client_ann.login(username='ann', password='ann')

        # Everything is unread
        self.assertListEqual(
            [t.unread for t in pybb_topic_unread([topic_1, topic_2], user_ann)],
            [True, True])
        self.assertListEqual(
            [t.unread for t in pybb_forum_unread([forum_1, forum_2], user_ann)],
            [True, True])

        # read all
        client_ann.get(reverse('pybb:mark_all_as_read'))
        self.assertListEqual(
            [t.unread for t in pybb_topic_unread([topic_1, topic_2], user_ann)],
            [False, False])
        self.assertListEqual(
            [t.unread for t in pybb_forum_unread([forum_1, forum_2], user_ann)],
            [False, False])

        post = Post.objects.create(topic=topic_1, user=self.user, body='three')

        topic_1 = Topic.objects.get(id=topic_1.id)
        topic_2 = Topic.objects.get(id=topic_2.id)
        self.assertEqual(topic_1.updated, post.updated or post.created)
        self.assertEqual(forum_1.updated, post.updated or post.created)
        self.assertListEqual(
            [t.unread for t in pybb_topic_unread([topic_1, topic_2], user_ann)],
            [True, False])
        self.assertListEqual(
            [t.unread for t in pybb_forum_unread([forum_1, forum_2], user_ann)],
            [True, False])

        post.topic = topic_2
        post.save()
        topic_1 = Topic.objects.get(id=topic_1.id)
        topic_2 = Topic.objects.get(id=topic_2.id)
        forum_1 = Forum.objects.get(id=forum_1.id)
        forum_2 = Forum.objects.get(id=forum_2.id)
        self.assertEqual(topic_2.updated, post.updated or post.created)
        self.assertEqual(forum_2.updated, post.updated or post.created)
        self.assertListEqual(
            [t.unread for t in pybb_topic_unread([topic_1, topic_2], user_ann)],
            [False, True])
        self.assertListEqual(
            [t.unread for t in pybb_forum_unread([forum_1, forum_2], user_ann)],
            [False, True])

        topic_2.forum = forum_1
        topic_2.save()
        topic_1 = Topic.objects.get(id=topic_1.id)
        topic_2 = Topic.objects.get(id=topic_2.id)
        forum_1 = Forum.objects.get(id=forum_1.id)
        forum_2 = Forum.objects.get(id=forum_2.id)
        self.assertEqual(forum_1.updated, post.updated or post.created)
        self.assertListEqual(
            [t.unread for t in pybb_topic_unread([topic_1, topic_2], user_ann)],
            [False, True])
        self.assertListEqual(
            [t.unread for t in pybb_forum_unread([forum_1, forum_2], user_ann)],
            [True, False])

    def test_latest_topics(self):
        topic_1 = self.topic
        topic_1.updated = datetime.datetime.utcnow()
        topic_2 = Topic.objects.create(name='topic_2', forum=self.forum, user=self.user)
        topic_2.updated = datetime.datetime.utcnow() + datetime.timedelta(days=-1)

        category_2 = Category.objects.create(name='cat2')
        forum_2 = Forum.objects.create(name='forum_2', category=category_2)
        topic_3 = Topic.objects.create(name='topic_3', forum=forum_2, user=self.user)
        topic_3.updated = datetime.datetime.utcnow() + datetime.timedelta(days=-2)

        self.login_client()
        response = self.client.get(reverse('pybb:topic_latest'))
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(list(response.context['topic_list']), [topic_1, topic_2, topic_3])

        topic_2.forum.hidden = True
        topic_2.forum.save()
        response = self.client.get(reverse('pybb:topic_latest'))
        self.assertListEqual(list(response.context['topic_list']), [topic_3])

        topic_2.forum.hidden = False
        topic_2.forum.save()
        category_2.hidden = True
        category_2.save()
        response = self.client.get(reverse('pybb:topic_latest'))
        self.assertListEqual(list(response.context['topic_list']), [topic_1, topic_2])

        topic_2.forum.hidden = False
        topic_2.forum.save()
        category_2.hidden = False
        category_2.save()
        topic_1.on_moderation = True
        topic_1.save()
        response = self.client.get(reverse('pybb:topic_latest'))
        self.assertListEqual(list(response.context['topic_list']), [topic_1, topic_2, topic_3])

        topic_1.user = User.objects.create_user('another', 'another@localhost', 'another')
        topic_1.save()
        response = self.client.get(reverse('pybb:topic_latest'))
        self.assertListEqual(list(response.context['topic_list']), [topic_2, topic_3])

        topic_1.forum.moderators.add(self.user)
        response = self.client.get(reverse('pybb:topic_latest'))
        self.assertListEqual(list(response.context['topic_list']), [topic_1, topic_2, topic_3])

        topic_1.forum.moderators.remove(self.user)
        self.user.is_superuser = True
        self.user.save()
        response = self.client.get(reverse('pybb:topic_latest'))
        self.assertListEqual(list(response.context['topic_list']), [topic_1, topic_2, topic_3])

        self.client.logout()
        response = self.client.get(reverse('pybb:topic_latest'))
        self.assertListEqual(list(response.context['topic_list']), [topic_2, topic_3])

    def test_hidden(self):
        client = Client()
        category = Category(name='hcat', hidden=True)
        category.save()
        forum_in_hidden = Forum(name='in_hidden', category=category)
        forum_in_hidden.save()
        topic_in_hidden = Topic(forum=forum_in_hidden, name='in_hidden', user=self.user)
        topic_in_hidden.save()

        forum_hidden = Forum(name='hidden', category=self.category, hidden=True)
        forum_hidden.save()
        topic_hidden = Topic(forum=forum_hidden, name='hidden', user=self.user)
        topic_hidden.save()

        post_hidden = Post(topic=topic_hidden, user=self.user, body='hidden')
        post_hidden.save()

        post_in_hidden = Post(topic=topic_in_hidden, user=self.user, body='hidden')
        post_in_hidden.save()

        
        self.assertFalse(category.id in [c.id for c in client.get(reverse('pybb:index')).context['categories']])
        self.assertEqual(client.get(category.get_absolute_url()).status_code, 302)
        self.assertEqual(client.get(forum_in_hidden.get_absolute_url()).status_code, 302)
        self.assertEqual(client.get(topic_in_hidden.get_absolute_url()).status_code, 302)

        self.assertNotContains(client.get(reverse('pybb:index')), forum_hidden.get_absolute_url())
        self.assertNotContains(client.get(reverse('pybb:feed_topics')), topic_hidden.get_absolute_url())
        self.assertNotContains(client.get(reverse('pybb:feed_topics')), topic_in_hidden.get_absolute_url())

        self.assertNotContains(client.get(reverse('pybb:feed_posts')), post_hidden.get_absolute_url())
        self.assertNotContains(client.get(reverse('pybb:feed_posts')), post_in_hidden.get_absolute_url())
        self.assertEqual(client.get(forum_hidden.get_absolute_url()).status_code, 302)
        self.assertEqual(client.get(topic_hidden.get_absolute_url()).status_code, 302)

        client.login(username='zeus', password='zeus')
        self.assertFalse(category.id in [c.id for c in client.get(reverse('pybb:index')).context['categories']])
        self.assertNotContains(client.get(reverse('pybb:index')), forum_hidden.get_absolute_url())
        self.assertEqual(client.get(category.get_absolute_url()).status_code, 403)
        self.assertEqual(client.get(forum_in_hidden.get_absolute_url()).status_code, 403)
        self.assertEqual(client.get(topic_in_hidden.get_absolute_url()).status_code, 403)
        self.assertEqual(client.get(forum_hidden.get_absolute_url()).status_code, 403)
        self.assertEqual(client.get(topic_hidden.get_absolute_url()).status_code, 403)
        self.user.is_staff = True
        self.user.save()
        self.assertTrue(category.id in [c.id for c in client.get(reverse('pybb:index')).context['categories']])
        self.assertContains(client.get(reverse('pybb:index')), forum_hidden.get_absolute_url())
        self.assertEqual(client.get(category.get_absolute_url()).status_code, 200)
        self.assertEqual(client.get(forum_in_hidden.get_absolute_url()).status_code, 200)
        self.assertEqual(client.get(topic_in_hidden.get_absolute_url()).status_code, 200)
        self.assertEqual(client.get(forum_hidden.get_absolute_url()).status_code, 200)
        self.assertEqual(client.get(topic_hidden.get_absolute_url()).status_code, 200)

    def test_inactive(self):
        self.login_client()
        url = reverse('pybb:add_post', kwargs={'topic_id': self.topic.id})
        response = self.client.get(url)
        values = self.get_form_values(response)
        values['body'] = 'test ban'
        response = self.client.post(url, values, follow=True)
        self.assertEqual(len(Post.objects.filter(body='test ban')), 1)
        self.user.is_active = False
        self.user.save()
        values['body'] = 'test ban 2'
        self.client.post(url, values, follow=True)
        self.assertEqual(len(Post.objects.filter(body='test ban 2')), 0)

    def get_csrf(self, form):
        return form.xpath('//input[@name="csrfmiddlewaretoken"]/@value')[0]

    def test_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.login(username='zeus', password='zeus')
        post_url = reverse('pybb:add_post', kwargs={'topic_id': self.topic.id})
        response = client.get(post_url)
        values = self.get_form_values(response)
        del values['csrfmiddlewaretoken']
        response = client.post(post_url, values, follow=True)
        self.assertNotEqual(response.status_code, 200)
        response = client.get(self.topic.get_absolute_url())
        values = self.get_form_values(response)
        response = client.post(reverse('pybb:add_post', kwargs={'topic_id': self.topic.id}), values, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_user_blocking(self):
        user = User.objects.create_user('test', 'test@localhost', 'test')
        self.user.is_superuser = True
        self.user.save()
        self.login_client()
        self.assertEqual(self.client.get(reverse('pybb:block_user', args=[user.username]), follow=True).status_code, 200)
        user = User.objects.get(username=user.username)
        self.assertFalse(user.is_active)

    def test_ajax_preview(self):
        self.login_client()
        response = self.client.post(reverse('pybb:post_ajax_preview'), data={'data': '[b]test bbcode ajax preview[b]'})
        self.assertContains(response, '<strong>test bbcode ajax preview</strong>')

    def test_headline(self):
        self.forum.headline = 'test <b>headline</b>'
        self.forum.save()
        client = Client()
        self.assertContains(client.get(self.forum.get_absolute_url()), 'test <b>headline</b>')

    def test_quote(self):
        self.login_client()
        response = self.client.get(reverse('pybb:add_post', kwargs={'topic_id': self.topic.id}), data={'quote_id': self.post.id, 'body': 'test tracking'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.post.body)

    def test_edit_post(self):
        self.login_client()
        edit_post_url = reverse('pybb:edit_post', kwargs={'pk': self.post.id})
        response = self.client.get(edit_post_url)
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content)
        values = dict(tree.xpath('//form[@method="post"]')[0].form_values())
        values['body'] = 'test edit'
        response = self.client.post(edit_post_url, data=values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.get(pk=self.post.id).body, 'test edit')
        response = self.client.get(self.post.get_absolute_url(), follow=True)
        self.assertContains(response, 'test edit')

        # Check admin form
        self.user.is_staff = True
        self.user.save()
        response = self.client.get(edit_post_url)
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content)
        values = dict(tree.xpath('//form[@method="post"]')[0].form_values())
        values['body'] = 'test edit'
        values['login'] = 'new_login'
        response = self.client.post(edit_post_url, data=values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test edit')

    def test_admin_post_add(self):
        self.user.is_staff = True
        self.user.save()
        self.login_client()
        response = self.client.post(reverse('pybb:add_post', kwargs={'topic_id': self.topic.id}), data={'quote_id': self.post.id, 'body': 'test admin post', 'user': 'zeus'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test admin post')

    def test_stick(self):
        self.user.is_superuser = True
        self.user.save()
        self.login_client()
        self.assertEqual(self.client.get(reverse('pybb:stick_topic', kwargs={'pk': self.topic.id}), follow=True).status_code, 200)
        self.assertEqual(self.client.get(reverse('pybb:unstick_topic', kwargs={'pk': self.topic.id}), follow=True).status_code, 200)

    def test_delete_view(self):
        post = Post(topic=self.topic, user=self.user, body='test to delete')
        post.save()
        self.user.is_superuser = True
        self.user.save()
        self.login_client()
        response = self.client.post(reverse('pybb:delete_post', args=[post.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        # Check that topic and forum exists ;)
        self.assertEqual(Topic.objects.filter(id=self.topic.id).count(), 1)
        self.assertEqual(Forum.objects.filter(id=self.forum.id).count(), 1)

        # Delete topic
        response = self.client.post(reverse('pybb:delete_post', args=[self.post.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.filter(id=self.post.id).count(), 0)
        self.assertEqual(Topic.objects.filter(id=self.topic.id).count(), 0)
        self.assertEqual(Forum.objects.filter(id=self.forum.id).count(), 1)

    def test_open_close(self):
        self.user.is_superuser = True
        self.user.save()
        self.login_client()
        add_post_url = reverse('pybb:add_post', args=[self.topic.id])
        response = self.client.get(add_post_url)
        values = self.get_form_values(response)
        values['body'] = 'test closed'
        response = self.client.get(reverse('pybb:close_topic', args=[self.topic.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(add_post_url, values, follow=True)
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse('pybb:open_topic', args=[self.topic.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(add_post_url, values, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_subscription(self):
        user = User.objects.create_user(username='user2', password='user2', email='user2@example.com')
        client = Client()
        client.login(username='user2', password='user2')
        response = client.get(reverse('pybb:add_subscription', args=[self.topic.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(user in list(self.topic.subscribers.all()))

        # create a new reply (with another user)
        self.client.login(username='zeus', password='zeus')
        add_post_url = reverse('pybb:add_post', args=[self.topic.id])
        response = self.client.get(add_post_url)
        values = self.get_form_values(response)
        values['body'] = 'test subscribtion юникод'
        response = self.client.post(add_post_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        new_post = Post.objects.get(pk=2)

        # there should only be one email in the outbox (to user2@example.com)
        self.assertEqual(len(mail.outbox),1)
        self.assertTrue([msg for msg in mail.outbox if new_post.get_absolute_url() in msg.body])

        # unsubscribe
        client.login(username='user2', password='user2')
        self.assertTrue([msg for msg in mail.outbox if new_post.get_absolute_url() in msg.body])
        response = client.get(reverse('pybb:delete_subscription', args=[self.topic.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(user not in list(self.topic.subscribers.all()))

    def test_topic_updated(self):
        topic = Topic(name='etopic', forum=self.forum, user=self.user)
        topic.save()
        time.sleep(1)
        post = Post(topic=topic, user=self.user, body='bbcode [b]test[b]')
        post.save()
        client = Client()
        response = client.get(self.forum.get_absolute_url())
        self.assertEqual(response.context['topic_list'][0], topic)
        time.sleep(1)
        post = Post(topic=self.topic, user=self.user, body='bbcode [b]test[b]')
        post.save()
        client = Client()
        response = client.get(self.forum.get_absolute_url())
        self.assertEqual(response.context['topic_list'][0], self.topic)

    def test_topic_deleted(self):
        forum_1 = Forum.objects.create(name='new forum', category=self.category)
        topic_1 = Topic.objects.create(name='new topic', forum=forum_1, user=self.user)
        post_1 = Post.objects.create(topic=topic_1, user=self.user, body='test')
        time.sleep(2)
        self.assertEqual(topic_1.updated, post_1.created)
        self.assertEqual(forum_1.updated, post_1.created)

        topic_2 = Topic.objects.create(name='another topic', forum=forum_1, user=self.user)
        post_2 = Post.objects.create(topic=topic_2, user=self.user, body='another test')
        time.sleep(2)
        self.assertEqual(topic_2.updated, post_2.created)
        self.assertEqual(forum_1.updated, post_2.created)

        topic_2.delete()
        self.assertEqual(forum_1.updated, post_1.created)
        self.assertEqual(forum_1.topic_count, 1)
        self.assertEqual(forum_1.post_count, 1)

        post_1.delete()
        self.assertEqual(forum_1.topic_count, 0)
        self.assertEqual(forum_1.post_count, 0)

    def test_user_view(self):
        resp = self.client.get(reverse('pybb:user', kwargs={'username': self.user.username}))
        self.assertEqual(resp.status_code, 200)

    def test_post_count(self):
        topic = Topic(name='etopic', forum=self.forum, user=self.user)
        topic.save()
        post = Post(topic=topic, user=self.user, body='test') # another post
        post.save()
        self.assertEqual(self.user.get_profile().post_count, 2)
        post.body = 'test2'
        post.save()
        self.assertEqual(Profile.objects.get(pk=self.user.get_profile().pk).post_count, 2)
        post.delete()
        self.assertEqual(Profile.objects.get(pk=self.user.get_profile().pk).post_count, 1)

    def tearDown(self):
        defaults.PYBB_ENABLE_ANONYMOUS_POST = self.ORIG_PYBB_ENABLE_ANONYMOUS_POST
        defaults.PYBB_PREMODERATION = self.ORIG_PYBB_PREMODERATION


class AnonymousTest(TestCase, SharedTestModule):

    def setUp(self):
        self.ORIG_PYBB_ENABLE_ANONYMOUS_POST = defaults.PYBB_ENABLE_ANONYMOUS_POST
        self.ORIG_PYBB_ANONYMOUS_USERNAME = defaults.PYBB_ANONYMOUS_USERNAME
        defaults.PYBB_ENABLE_ANONYMOUS_POST = True
        defaults.PYBB_ANONYMOUS_USERNAME = 'Anonymous'
        self.user = User.objects.create_user('Anonymous', 'Anonymous@localhost', 'Anonymous')
        self.category = Category.objects.create(name='foo')
        self.forum = Forum.objects.create(name='xfoo', description='bar', category=self.category)
        self.topic = Topic.objects.create(name='etopic', forum=self.forum, user=self.user)
        add_post_permission = Permission.objects.get_by_natural_key('add_post', 'pybb', 'post')
        self.user.user_permissions.add(add_post_permission)

    def test_anonymous_posting(self):
        post_url = reverse('pybb:add_post', kwargs={'topic_id': self.topic.id})
        response = self.client.get(post_url)
        values = self.get_form_values(response)
        values['body'] = 'test anonymous'
        response = self.client.post(post_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(Post.objects.filter(body='test anonymous')), 1)
        self.assertEqual(Post.objects.get(body='test anonymous').user, self.user)

    def tearDown(self):
        defaults.PYBB_ENABLE_ANONYMOUS_POST = self.ORIG_PYBB_ENABLE_ANONYMOUS_POST
        defaults.PYBB_ANONYMOUS_USERNAME = self.ORIG_PYBB_ANONYMOUS_USERNAME


def premoderate_test(user, post):
    """
    Test premoderate function
    Allow post without moderation for staff users only
    """
    if user.username.startswith('allowed'):
        return True
    return False

class PreModerationTest(TestCase, SharedTestModule):

    def setUp(self):
        self.ORIG_PYBB_PREMODERATION = defaults.PYBB_PREMODERATION
        defaults.PYBB_PREMODERATION = premoderate_test
        self.create_user()
        self.create_initial()
        mail.outbox = []

    def test_premoderation(self):
        self.client.login(username='zeus', password='zeus')
        add_post_url = reverse('pybb:add_post', kwargs={'topic_id': self.topic.id})
        response = self.client.get(add_post_url)
        values = self.get_form_values(response)
        values['body'] = 'test premoderation'
        response = self.client.post(add_post_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        post = Post.objects.get(body='test premoderation')
        self.assertEqual(post.on_moderation, True)

        # Post is visible by author
        response = self.client.get(post.get_absolute_url(), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test premoderation')

        # Post is not visible by anonymous user
        client = Client()
        response = client.get(post.get_absolute_url(), follow=True)
        self.assertRedirects(response, settings.LOGIN_URL+'?next=%s' % post.get_absolute_url())
        response = client.get(self.topic.get_absolute_url(), follow=True)
        self.assertNotContains(response, 'test premoderation')

        # But visible by superuser (with permissions)
        user = User.objects.create_user('admin', 'zeus@localhost', 'admin')
        user.is_superuser = True
        user.save()
        client.login(username='admin', password='admin')
        response = client.get(post.get_absolute_url(), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test premoderation')

        # user with names stats with allowed can post without premoderation
        user = User.objects.create_user('allowed_zeus', 'zeus@localhost', 'allowed_zeus')
        client.login(username='allowed_zeus', password='allowed_zeus')
        response = client.get(add_post_url)
        values = self.get_form_values(response)
        values['body'] = 'test premoderation staff'
        response = client.post(add_post_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        post = Post.objects.get(body='test premoderation staff')
        client = Client()
        response = client.get(post.get_absolute_url(), follow=True)
        self.assertContains(response, 'test premoderation staff')

        # Superuser can moderate
        user.is_superuser = True
        user.save()
        admin_client = Client()
        admin_client.login(username='admin', password='admin')
        post = Post.objects.get(body='test premoderation')
        response = admin_client.get(reverse('pybb:moderate_post', kwargs={'pk': post.id}), follow=True)
        self.assertEqual(response.status_code, 200)

        # Now all can see this post:
        client = Client()
        response = client.get(post.get_absolute_url(), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test premoderation')

        # Other users can't moderate
        post.on_moderation = True
        post.save()
        client.login(username='zeus', password='zeus')
        response = client.get(reverse('pybb:moderate_post', kwargs={'pk': post.id}), follow=True)
        self.assertEqual(response.status_code, 403)

        # If user create new topic it goes to moderation if MODERATION_ENABLE
        # When first post is moderated, topic becomes moderated too
        self.client.login(username='zeus', password='zeus')
        add_topic_url = reverse('pybb:add_topic', kwargs={'forum_id': self.forum.id})
        response = self.client.get(add_topic_url)
        values = self.get_form_values(response)
        values['body'] = 'new topic test'
        values['name'] = 'new topic name'
        values['poll_type'] = 0
        response = self.client.post(add_topic_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'new topic test')

        client = Client()
        response = client.get(self.forum.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'new topic name')
        response = client.get(Topic.objects.get(name='new topic name').get_absolute_url())
        self.assertEqual(response.status_code, 302)
        response = admin_client.get(reverse('pybb:moderate_post',
                                     kwargs={'pk': Post.objects.get(body='new topic test').id}),
                                     follow=True)
        self.assertEqual(response.status_code, 200)

        response = client.get(self.forum.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'new topic name')
        response = client.get(Topic.objects.get(name='new topic name').get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        defaults.PYBB_PREMODERATION = self.ORIG_PYBB_PREMODERATION

        
class AttachmentTest(TestCase, SharedTestModule):
    def setUp(self):
        self.PYBB_ATTACHMENT_ENABLE = defaults.PYBB_ATTACHMENT_ENABLE
        defaults.PYBB_ATTACHMENT_ENABLE = True
        self.ORIG_PYBB_PREMODERATION = defaults.PYBB_PREMODERATION
        defaults.PYBB_PREMODERATION = False
        self.file = open(os.path.join(os.path.dirname(__file__), 'static', 'pybb', 'img','attachment.png'))
        self.create_user()
        self.create_initial()

    def test_attachment_one(self):
        add_post_url = reverse('pybb:add_post', kwargs={'topic_id': self.topic.id})
        self.login_client()
        response = self.client.get(add_post_url)
        values = self.get_form_values(response)
        values['body'] = 'test attachment'
        values['attachments-0-file'] = self.file
        response = self.client.post(add_post_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Post.objects.filter(body='test attachment').exists())

    def test_attachment_two(self):
        add_post_url = reverse('pybb:add_post', kwargs={'topic_id': self.topic.id})
        self.login_client()
        response = self.client.get(add_post_url)
        values = self.get_form_values(response)
        values['body'] = 'test attachment'
        values['attachments-0-file'] = self.file
        del values['attachments-INITIAL_FORMS']
        del values['attachments-TOTAL_FORMS']
        with self.assertRaises(ValidationError):
            self.client.post(add_post_url, values, follow=True)

    def tearDown(self):
        defaults.PYBB_ATTACHMENT_ENABLE = self.PYBB_ATTACHMENT_ENABLE
        defaults.PYBB_PREMODERATION = self.ORIG_PYBB_PREMODERATION


class PollTest(TestCase, SharedTestModule):
    def setUp(self):
        self.create_user()
        self.create_initial()
        self.PYBB_POLL_MAX_ANSWERS = defaults.PYBB_POLL_MAX_ANSWERS
        defaults.PYBB_POLL_MAX_ANSWERS = 2

    def test_poll_add(self):
        add_topic_url = reverse('pybb:add_topic', kwargs={'forum_id': self.forum.id})
        self.login_client()
        response = self.client.get(add_topic_url)
        values = self.get_form_values(response)
        values['body'] = 'test poll body'
        values['name'] = 'test poll name'
        values['poll_type'] = 0 # poll_type = None, create topic without poll answers
        values['poll_question'] = 'q1'
        values['poll_answers-0-text'] = 'answer1'
        values['poll_answers-1-text'] = 'answer2'
        values['poll_answers-TOTAL_FORMS'] = 2
        response = self.client.post(add_topic_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        new_topic = Topic.objects.get(name='test poll name')
        self.assertIsNone(new_topic.poll_question)
        self.assertFalse(PollAnswer.objects.filter(topic=new_topic).exists()) # no answers here

        values['name'] = 'test poll name 1'
        values['poll_type'] = 1
        values['poll_answers-0-text'] = 'answer1' # not enough answers
        values['poll_answers-TOTAL_FORMS'] = 1
        response = self.client.post(add_topic_url, values, follow=True)
        self.assertFalse(Topic.objects.filter(name='test poll name 1').exists())

        values['name'] = 'test poll name 1'
        values['poll_type'] = 1
        values['poll_answers-0-text'] = 'answer1' # too many answers
        values['poll_answers-1-text'] = 'answer2'
        values['poll_answers-2-text'] = 'answer3'
        values['poll_answers-TOTAL_FORMS'] = 3
        response = self.client.post(add_topic_url, values, follow=True)
        self.assertFalse(Topic.objects.filter(name='test poll name 1').exists())

        values['name'] = 'test poll name 1'
        values['poll_type'] = 1 # poll type = single choice, create answers
        values['poll_question'] = 'q1'
        values['poll_answers-0-text'] = 'answer1' # two answers - what do we need to create poll
        values['poll_answers-1-text'] = 'answer2'
        values['poll_answers-TOTAL_FORMS'] = 2
        response = self.client.post(add_topic_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        new_topic = Topic.objects.get(name='test poll name 1')
        self.assertEqual(new_topic.poll_question, 'q1')
        self.assertEqual(PollAnswer.objects.filter(topic=new_topic).count(), 2)

    def test_regression_adding_poll_with_removed_answers(self):
        add_topic_url = reverse('pybb:add_topic', kwargs={'forum_id': self.forum.id})
        self.login_client()
        response = self.client.get(add_topic_url)
        values = self.get_form_values(response)
        values['body'] = 'test poll body'
        values['name'] = 'test poll name'
        values['poll_type'] = 1
        values['poll_question'] = 'q1'
        values['poll_answers-0-text'] = ''
        values['poll_answers-0-DELETE'] = 'on'
        values['poll_answers-1-text'] = ''
        values['poll_answers-1-DELETE'] = 'on'
        values['poll_answers-TOTAL_FORMS'] = 2
        response = self.client.post(add_topic_url, values, follow=True)
        self.assertFalse(Topic.objects.filter(name='test poll name').exists())

    def test_regression_poll_deletion_after_second_post(self):
        self.login_client()

        add_topic_url = reverse('pybb:add_topic', kwargs={'forum_id': self.forum.id})
        response = self.client.get(add_topic_url)
        values = self.get_form_values(response)
        values['body'] = 'test poll body'
        values['name'] = 'test poll name'
        values['poll_type'] = 1 # poll type = single choice, create answers
        values['poll_question'] = 'q1'
        values['poll_answers-0-text'] = 'answer1' # two answers - what do we need to create poll
        values['poll_answers-1-text'] = 'answer2'
        values['poll_answers-TOTAL_FORMS'] = 2
        response = self.client.post(add_topic_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        new_topic = Topic.objects.get(name='test poll name')
        self.assertEqual(new_topic.poll_question, 'q1')
        self.assertEqual(PollAnswer.objects.filter(topic=new_topic).count(), 2)

        add_post_url = reverse('pybb:add_post', kwargs={'topic_id': new_topic.id})
        response = self.client.get(add_post_url)
        values = self.get_form_values(response)
        values['body'] = 'test answer body'
        response = self.client.post(add_post_url, values, follow=True)
        self.assertEqual(PollAnswer.objects.filter(topic=new_topic).count(), 2)

    def test_poll_edit(self):
        edit_topic_url = reverse('pybb:edit_post', kwargs={'pk': self.post.id})
        self.login_client()
        response = self.client.get(edit_topic_url)
        values = self.get_form_values(response)
        values['poll_type'] = 1 # add_poll
        values['poll_question'] = 'q1'
        values['poll_answers-0-text'] = 'answer1'
        values['poll_answers-1-text'] = 'answer2'
        values['poll_answers-TOTAL_FORMS'] = 2
        response = self.client.post(edit_topic_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Topic.objects.get(id=self.topic.id).poll_type, 1)
        self.assertEqual(Topic.objects.get(id=self.topic.id).poll_question, 'q1')
        self.assertEqual(PollAnswer.objects.filter(topic=self.topic).count(), 2)

        values = self.get_form_values(self.client.get(edit_topic_url))
        values['poll_type'] = 2 # change_poll type
        values['poll_question'] = 'q100' # change poll question
        values['poll_answers-0-text'] = 'answer100' # change poll answers
        values['poll_answers-1-text'] = 'answer200'
        values['poll_answers-TOTAL_FORMS'] = 2
        response = self.client.post(edit_topic_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Topic.objects.get(id=self.topic.id).poll_type, 2)
        self.assertEqual(Topic.objects.get(id=self.topic.id).poll_question, 'q100')
        self.assertEqual(PollAnswer.objects.filter(topic=self.topic).count(), 2)
        self.assertTrue(PollAnswer.objects.filter(text='answer100').exists())
        self.assertTrue(PollAnswer.objects.filter(text='answer200').exists())
        self.assertFalse(PollAnswer.objects.filter(text='answer1').exists())
        self.assertFalse(PollAnswer.objects.filter(text='answer2').exists())

        values['poll_type'] = 0 # remove poll
        values['poll_answers-0-text'] = 'answer100' # no matter how many answers we provide
        values['poll_answers-TOTAL_FORMS'] = 1
        response = self.client.post(edit_topic_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Topic.objects.get(id=self.topic.id).poll_type, 0)
        self.assertIsNone(Topic.objects.get(id=self.topic.id).poll_question)
        self.assertEqual(PollAnswer.objects.filter(topic=self.topic).count(), 0)

    def test_poll_voting(self):
        def recreate_poll(poll_type):
            self.topic.poll_type = poll_type
            self.topic.save()
            PollAnswer.objects.filter(topic=self.topic).delete()
            PollAnswer.objects.create(topic=self.topic, text='answer1')
            PollAnswer.objects.create(topic=self.topic, text='answer2')

        self.login_client()
        recreate_poll(poll_type=Topic.POLL_TYPE_SINGLE)
        vote_url = reverse('pybb:topic_poll_vote', kwargs={'pk': self.topic.id})
        my_answer = PollAnswer.objects.all()[0]
        values = {'answers': my_answer.id}
        response = self.client.post(vote_url, data=values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Topic.objects.get(id=self.topic.id).poll_votes(), 1)
        self.assertEqual(PollAnswer.objects.get(id=my_answer.id).votes(), 1)
        self.assertEqual(PollAnswer.objects.get(id=my_answer.id).votes_percent(), 100.0)

        # already voted
        response = self.client.post(vote_url, data=values, follow=True)
        self.assertEqual(response.status_code, 400) # bad request status

        recreate_poll(poll_type=Topic.POLL_TYPE_MULTIPLE)
        values = {'answers': [a.id for a in PollAnswer.objects.all()]}
        response = self.client.post(vote_url, data=values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertListEqual([a.votes() for a in PollAnswer.objects.all()], [1, 1, ])
        self.assertListEqual([a.votes_percent() for a in PollAnswer.objects.all()], [50.0, 50.0, ])

    def tearDown(self):
        defaults.PYBB_POLL_MAX_ANSWERS = self.PYBB_POLL_MAX_ANSWERS


class FiltersTest(TestCase, SharedTestModule):
    def setUp(self):
        self.create_user()
        self.create_initial(post=False)

    def test_filters(self):
        add_post_url = reverse('pybb:add_post', kwargs={'topic_id': self.topic.id})
        self.login_client()
        response = self.client.get(add_post_url)
        values = self.get_form_values(response)
        values['body'] = u'test\n \n \n\nmultiple empty lines\n'
        response = self.client.post(add_post_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.all()[0].body, u'test\nmultiple empty lines')
        
from pybb import permissions
from django.db.models import Q

class CustomPermissionHandler(permissions.DefaultPermissionHandler):
    """ 
    a custom permission handler which changes the meaning of "hidden" forum:
    "hidden" forum or category is visible for all logged on users, not only staff 
    """
        
    def filter_categories(self, user, qs):
        return qs.filter(hidden=False) if user.is_anonymous() else qs
    
    def may_view_category(self, user, category):
        return user.is_authenticated() if category.hidden else True
    
    def filter_forums(self, user, qs):
        if user.is_anonymous():
            qs = qs.filter(Q(hidden=False)&Q(category__hidden=False))
        return qs        
    
    def may_view_forum(self, user, forum):
        return user.is_authenticated() if forum.hidden or forum.category.hidden else True
    
    def filter_topics(self, user, qs):
        if user.is_anonymous():
            qs = qs.filter(Q(forum__hidden=False)&Q(forum__category__hidden=False))
        return qs

    def may_view_topic(self, user, topic):
        return self.may_view_forum(user, topic.forum)

    def filter_posts(self, user, qs):
        if user.is_anonymous():
            qs = qs.filter(Q(topic__forum__hidden=False)&Q(topic__forum__category__hidden=False))
        return qs

    def may_view_post(self, user, post):
        return self.may_view_forum(user, post.topic.forum)


class CustomPermissionHandlerTest(TestCase, SharedTestModule):
    """ test custom permission handler """
    
    def setUp(self):
        from pybb import views
        self.create_user()
        # create public and hidden categories, forums, posts
        c_pub = Category(name='public'); c_pub.save()
        c_hid = Category(name='private', hidden=True); c_hid.save()
        Forum(name='pub1', category=c_pub).save()
        Forum(name='priv1', category=c_hid).save()
        Forum(name='private_in_public_cat', hidden=True, category=c_pub).save()
        for f in Forum.objects.all():
            t = Topic(name='a topic', forum=f, user=self.user)
            t.save()
            Post(topic=t, user=self.user, body='test').save()
        
        # override the permission handler. this cannot be done with @override_settings as
        # permissions.perms is already imported at this point, instead we got to monkeypatch
        # the modules (not really nice, but only an issue in tests)
        views.perms = permissions.perms = permissions._resolve_class('pybb.tests.CustomPermissionHandler')
    
    def tearDown(self):
        from pybb import views
        # reset permission handler (otherwise other tests may fail)
        views.perms = permissions.perms = permissions._resolve_class('pybb.permissions.DefaultPermissionHandler')
    
    def test_category_permission(self):
        for c in Category.objects.all():
            # anon user may not see category
            r=self.get_with_user(c.get_absolute_url())
            if c.hidden:
                self.assertEqual(r.status_code, 302)
            else:
                self.assertEqual(r.status_code, 200)
            # logged on user may see all categories
            r=self.get_with_user(c.get_absolute_url(), 'zeus', 'zeus')        
            self.assertEqual(r.status_code, 200)
            
    def test_forum_permission(self):
        for f in Forum.objects.all():
            r=self.get_with_user(f.get_absolute_url())
            self.assertEqual(r.status_code, 302 if f.hidden or f.category.hidden else 200)
            r=self.get_with_user(f.get_absolute_url(), 'zeus', 'zeus')            
            self.assertEqual(r.status_code, 200)
            
    def test_topic_permission(self):
        for t in Topic.objects.all():
            r=self.get_with_user(t.get_absolute_url())
            self.assertEqual(r.status_code, 302 if t.forum.hidden or t.forum.category.hidden else 200)
            r=self.get_with_user(t.get_absolute_url(), 'zeus', 'zeus')            
            self.assertEqual(r.status_code, 200)
            
    def test_post_permission(self):
        for p in Post.objects.all():
            r=self.get_with_user(p.get_absolute_url())
            self.assertEqual(r.status_code, 302 if p.topic.forum.hidden or p.topic.forum.category.hidden else 301)
            r=self.get_with_user(p.get_absolute_url(), 'zeus', 'zeus')            
            self.assertEqual(r.status_code, 301)
            
class LogonRedirectTest(TestCase, SharedTestModule):
    """ test whether anonymous user gets redirected, whereas unauthorized user gets PermissionDenied """
    
    def setUp(self):
        # create users
        staff = User.objects.create_user('staff', 'staff@localhost', 'staff')
        staff.is_staff = True
        staff.save()
        nostaff = User.objects.create_user('nostaff', 'nostaff@localhost', 'nostaff')
        nostaff.is_staff = False
        nostaff.save()
        
        # create topic, post in hidden category 
        self.category = Category(name='private', hidden=True)
        self.category.save()
        self.forum = Forum(name='priv1', category=self.category)
        self.forum.save()
        self.topic = Topic(name='a topic', forum=self.forum, user=staff)
        self.topic.save()
        self.post = Post(body='body post', topic=self.topic, user=staff, on_moderation=True)
        self.post.save()            
                    
    def test_redirect_category(self):
        # access without user should be redirected
        r = self.get_with_user(self.category.get_absolute_url())
        self.assertRedirects(r, settings.LOGIN_URL+'?next=%s' % self.category.get_absolute_url())
        # access with (unauthorized) user should get 403 (forbidden)
        r = self.get_with_user(self.category.get_absolute_url(), 'nostaff', 'nostaff')
        self.assertEquals(r.status_code, 403)
        # allowed user is allowed
        r = self.get_with_user(self.category.get_absolute_url(), 'staff', 'staff')
        self.assertEquals(r.status_code, 200)
    
    def test_redirect_forum(self):
        # access without user should be redirected
        r = self.get_with_user(self.forum.get_absolute_url())
        self.assertRedirects(r, settings.LOGIN_URL+'?next=%s' % self.forum.get_absolute_url())
        # access with (unauthorized) user should get 403 (forbidden)
        r = self.get_with_user(self.forum.get_absolute_url(), 'nostaff', 'nostaff')
        self.assertEquals(r.status_code, 403)
        # allowed user is allowed
        r = self.get_with_user(self.forum.get_absolute_url(), 'staff', 'staff')
        self.assertEquals(r.status_code, 200)
    
    def test_redirect_topic(self):
        # access without user should be redirected
        r = self.get_with_user(self.topic.get_absolute_url())
        self.assertRedirects(r, settings.LOGIN_URL+'?next=%s' % self.topic.get_absolute_url())
        # access with (unauthorized) user should get 403 (forbidden)
        r = self.get_with_user(self.topic.get_absolute_url(), 'nostaff', 'nostaff')
        self.assertEquals(r.status_code, 403)
        # allowed user is allowed
        r = self.get_with_user(self.topic.get_absolute_url(), 'staff', 'staff')
        self.assertEquals(r.status_code, 200)
    
    def test_redirect_post(self):
        # access without user should be redirected
        r = self.get_with_user(self.post.get_absolute_url())
        self.assertRedirects(r, settings.LOGIN_URL+'?next=%s' % self.post.get_absolute_url())
        # access with (unauthorized) user should get 403 (forbidden)
        r = self.get_with_user(self.post.get_absolute_url(), 'nostaff', 'nostaff')
        self.assertEquals(r.status_code, 403)
        # allowed user is allowed
        r = self.get_with_user(self.post.get_absolute_url(), 'staff', 'staff')
        self.assertEquals(r.status_code, 301)

    