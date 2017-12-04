# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import datetime, time
import inspect
import math
import os
from unittest import skip
from django.contrib.auth.models import AnonymousUser, Permission
from django.conf import settings
from django.core import mail
from django.core.cache import cache

from pybb.compat import is_authenticated, is_anonymous

try:
    from django.core.urlresolvers import reverse
except ImportError:
    from django.urls import reverse
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.db.models import Q
from django.template import Context, Template
from django.test import TestCase
from django.test.client import Client
from django.test.utils import override_settings
from django.utils import dateformat, timezone
from django.utils.translation.trans_real import get_supported_language_variant


from pybb import permissions, views as pybb_views
from pybb.templatetags.pybb_tags import pybb_is_topic_unread, pybb_topic_unread, pybb_forum_unread, \
    pybb_get_latest_topics, pybb_get_latest_posts

from pybb import compat, util

User = compat.get_user_model()
username_field = compat.get_username_field()

try:
    from lxml import html
except ImportError:  # pragma: no cover
    raise Exception('PyBB requires lxml for self testing')

from pybb import defaults
from pybb.models import Category, Forum, Topic, Post, PollAnswer, PollAnswerUser, \
    TopicReadTracker, ForumReadTracker, ForumSubscription

if getattr(connection.features, 'supports_microsecond_precision', False):
    def sleep_only_if_required(s):
        pass
else:
    from time import sleep as sleep_only_if_required

Profile = util.get_pybb_profile_model()

__author__ = 'zeus'


class SharedTestModule(object):
    def create_user(self):
        self.user = User.objects.create_user('zeus', 'zeus@localhost', 'zeus')

    def login_client(self, username='zeus', password='zeus'):
        self.client.login(username=username, password=password)

    def create_post(self, _sleep=False, **kwargs):
        """
        Creates a post and return it.
        Sleep for 1 second if using a DB which does not support microsecond precision (MySQL).
        If your test does not care about time precision (because your test don't check post order
        or read tracking), you can disable the sleep, even for MySQL, with `_sleep=False`
        """
        post = Post(**kwargs)
        post.save()
        if _sleep:
            sleep_only_if_required(1)
        return post

    def create_post_via_http(self, client, forum_id=None, topic_id=None, _sleep=False, **post_kwargs):
        """
        Creates a post via http and return the response.
        Sleep for 1 second if using a DB which does not support microsecond precision (MySQL).
        See doc about `create_post` method for more information about sleeping.
        """
        if topic_id:
            url = reverse('pybb:add_post', kwargs={'topic_id': topic_id})
        elif forum_id:
            url = reverse('pybb:add_topic', kwargs={'forum_id': forum_id})
        else:
            raise Exception('`topic_id` or `forum_id` is required')
        response = client.get(url, follow=True)
        if response.status_code < 400:
            values = self.get_form_values(response)
            values.update(post_kwargs)
            response = client.post(url, data=values, follow=True)
            if response.status_code < 400 and _sleep:
                sleep_only_if_required(1)
        return response

    def create_initial(self, post=True):
        self.category = Category.objects.create(name='foo')
        self.forum = Forum.objects.create(name='xfoo', description='bar', category=self.category)
        self.topic = Topic.objects.create(name='etopic', forum=self.forum, user=self.user)
        if post:
            self.post = self.create_post(topic=self.topic, user=self.user, body='bbcode [b]test[/b]')

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
        Forum.objects.create(name='xfoo1', description='bar1', category=self.category, parent=self.forum)
        url = reverse('pybb:index')
        response = self.client.get(url)
        parser = html.HTMLParser(encoding='utf8')
        tree = html.fromstring(response.content, parser=parser)
        self.assertContains(response, 'foo')
        self.assertContains(response, self.forum.get_absolute_url())
        self.assertTrue(defaults.PYBB_DEFAULT_TITLE in tree.xpath('//title')[0].text_content())
        self.assertEqual(len(response.context['categories']), 1)
        self.assertEqual(len(response.context['categories'][0].forums_accessed), 1)

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
        Forum.objects.create(name='xfoo1', description='bar1', category=self.category, parent=self.forum)
        response = self.client.get(self.category.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.forum.get_absolute_url())
        self.assertEqual(len(response.context['object'].forums_accessed), 1)

    def test_profile_language_default(self):
        user = User.objects.create_user(username='user2', password='user2',
                                        email='user2@example.com')
        self.assertEqual(util.get_pybb_profile(user).language,
                         get_supported_language_variant(settings.LANGUAGE_CODE))

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
        url = self.forum.get_absolute_url()
        response = self.client.get(url)
        self.assertEqual(len(response.context['topic_list']), defaults.PYBB_FORUM_PAGE_SIZE)
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(response.context['paginator'].num_pages,
                         int((defaults.PYBB_FORUM_PAGE_SIZE + 3) / defaults.PYBB_FORUM_PAGE_SIZE) + 1)

    def test_bbcode_and_topic_title(self):
        response = self.client.get(self.topic.get_absolute_url())
        tree = html.fromstring(response.content)
        self.assertTrue(self.topic.name in tree.xpath('//title')[0].text_content())
        self.assertContains(response, self.post.body_html)
        self.assertContains(response, 'bbcode <strong>test</strong>')

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

    def test_topic_read_before_post_addition(self):
        """
        Test if everything is okay when :
            - user A create the topic
            - but before associated post is created, user B display the forum
        """
        topic = Topic(name='xtopic', forum=self.forum, user=self.user)
        topic.save()
        #topic is saved, but post is not yet created at this time

        #an other user is displaing the forum before the post creation
        user_ann = User.objects.create_user('ann', 'ann@localhost', 'ann')
        client = Client()
        client.login(username='ann', password='ann')

        self.assertEqual(client.get(topic.get_absolute_url()).status_code, 404)
        self.assertEqual(topic.forum.post_count, 1)
        self.assertEqual(topic.forum.topic_count, 1)
        #do we need to correct this ?
        #self.assertEqual(topic.forum.topics.count(), 1)
        self.assertEqual(topic.post_count, 0)

        #Now, TopicReadTracker is not created because the topic detail view raise a 404
        #If its creation is not finished. So we create it manually to add a test, just in case
        #we have an other way where TopicReadTracker could be set for a not complete topic.
        TopicReadTracker.objects.create(user=user_ann, topic=topic, time_stamp=topic.created)

        #before correction, raised TypeError: can't compare datetime.datetime to NoneType
        pybb_topic_unread([topic,], user_ann)

        #before correction, raised IndexError: list index out of range
        last_post = topic.last_post

        #post creation now.
        self.create_post(topic=topic, user=self.user, body='one')

        self.assertEqual(client.get(topic.get_absolute_url()).status_code, 200)
        self.assertEqual(topic.forum.post_count, 2)
        self.assertEqual(topic.forum.topic_count, 2)
        self.assertEqual(topic.forum.topics.count(), 2)
        self.assertEqual(topic.post_count, 1)

    def test_post_deletion(self):
        self.create_post(topic=self.topic, user=self.user, body='bbcode [b]test[/b]')
        Topic.objects.get(id=self.topic.id)
        Forum.objects.get(id=self.forum.id)

    def test_topic_deletion(self):
        topic = Topic(name='xtopic', forum=self.forum, user=self.user)
        topic.save()
        post = self.create_post(topic=topic, user=self.user, body='one')
        post = self.create_post(topic=topic, user=self.user, body='two')
        post.delete()
        Topic.objects.get(id=topic.id)
        Forum.objects.get(id=self.forum.id)
        topic.delete()
        Forum.objects.get(id=self.forum.id)

    def test_forum_updated(self):
        topic = Topic(name='xtopic', forum=self.forum, user=self.user)
        topic.save()
        post = self.create_post(topic=topic, user=self.user, body='one')
        post = Post.objects.get(id=post.id)
        self.assertTrue(self.forum.updated == post.created)

    def test_read_tracking(self):
        topic = Topic(name='xtopic', forum=self.forum, user=self.user)
        topic.save()
        post = self.create_post(topic=topic, user=self.user, body='one', _sleep=True)
        client = Client()
        client.login(username='zeus', password='zeus')
        # Topic status
        tree = html.fromstring(client.get(topic.forum.get_absolute_url()).content)
        self.assertTrue(tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % topic.get_absolute_url()))
        # Forum status
        tree = html.fromstring(client.get(reverse('pybb:index')).content)
        self.assertTrue(
            tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % topic.forum.get_absolute_url()))
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
        self.assertFalse(
            tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % topic.forum.get_absolute_url()))
        # Post message
        response = self.create_post_via_http(client, topic_id=topic.id, body='test tracking', _sleep=True)
        self.assertContains(response, 'test tracking')
        # Topic status - readed
        tree = html.fromstring(client.get(topic.forum.get_absolute_url()).content)
        self.assertFalse(tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % topic.get_absolute_url()))
        # Forum status - readed
        tree = html.fromstring(client.get(reverse('pybb:index')).content)
        self.assertFalse(
            tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % topic.forum.get_absolute_url()))
        post = self.create_post(topic=topic, user=self.user, body='one')
        client.get(reverse('pybb:mark_all_as_read'))
        tree = html.fromstring(client.get(reverse('pybb:index')).content)
        self.assertFalse(
            tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % topic.forum.get_absolute_url()))
        # Empty forum - readed
        f = Forum(name='empty', category=self.category)
        f.save()
        tree = html.fromstring(client.get(reverse('pybb:index')).content)
        self.assertFalse(tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % f.get_absolute_url()))

    def test_read_tracking_multi_user(self):
        topic_1 = self.topic
        topic_2 = Topic(name='topic_2', forum=self.forum, user=self.user)
        topic_2.save()
        self.create_post(topic=topic_2, user=self.user, body='one')

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
        sleep_only_if_required(1)
        self.assertEqual(TopicReadTracker.objects.all().count(), 2)
        self.assertEqual(TopicReadTracker.objects.filter(user=user_bob).count(), 1)
        self.assertEqual(TopicReadTracker.objects.filter(user=user_bob, topic=topic_1).count(), 1)

        # user_bob reads topic_2, he should get a forum read tracker,
        #  there should be no topic read trackers for user_bob
        client_bob.get(topic_2.get_absolute_url())
        sleep_only_if_required(1)
        self.assertEqual(TopicReadTracker.objects.all().count(), 1)
        self.assertEqual(ForumReadTracker.objects.all().count(), 1)
        self.assertEqual(ForumReadTracker.objects.filter(user=user_bob).count(), 1)
        self.assertEqual(ForumReadTracker.objects.filter(user=user_bob, forum=self.forum).count(), 1)
        self.assertEqual(TopicReadTracker.objects.filter(user=user_bob).count(), 0)
        self.assertListEqual([t.unread for t in pybb_topic_unread([topic_1, topic_2], user_bob)], [False, False])

        # user_ann creates topic_3, they should get a new topic read tracker in the db
        self.create_post_via_http(client_ann, forum_id=self.forum.id,
                                  body='topic_3', name='topic_3', poll_type=0)
        self.assertEqual(TopicReadTracker.objects.all().count(), 2)
        self.assertEqual(TopicReadTracker.objects.filter(user=user_ann).count(), 2)
        self.assertEqual(ForumReadTracker.objects.all().count(), 1)
        topic_3 = Topic.objects.order_by('-updated', '-id')[0]
        self.assertEqual(topic_3.name, 'topic_3')

        # user_ann posts to topic_1, a topic they've already read, no new trackers should be created
        self.create_post_via_http(client_ann, topic_id=topic_1.id, body='test tracking')
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
        previous_time = ForumReadTracker.objects.all()[0].time_stamp
        client_bob.get(topic_1.get_absolute_url())
        sleep_only_if_required(1)
        self.assertEqual(ForumReadTracker.objects.all().count(), 1)
        self.assertEqual(ForumReadTracker.objects.all()[0].time_stamp, previous_time)
        self.assertEqual(TopicReadTracker.objects.filter(user=user_bob).count(), 1)
        self.assertEqual(TopicReadTracker.objects.filter(user=user_ann).count(), 2)
        self.assertEqual(TopicReadTracker.objects.all().count(), 3)

        # user_bob reads the last unread topic, 'topic_3'.
        # user_bob's existing forum read tracker updates and his topic read tracker disappears
        #
        previous_time = ForumReadTracker.objects.all()[0].time_stamp
        client_bob.get(topic_3.get_absolute_url())
        sleep_only_if_required(1)
        self.assertEqual(ForumReadTracker.objects.all().count(), 1)
        self.assertGreater(ForumReadTracker.objects.all()[0].time_stamp, previous_time)
        self.assertEqual(TopicReadTracker.objects.all().count(), 2)
        self.assertEqual(TopicReadTracker.objects.filter(user=user_bob).count(), 0)

    def test_read_tracking_multi_forum(self):
        topic_1 = self.topic
        topic_2 = Topic(name='topic_2', forum=self.forum, user=self.user)
        topic_2.save()
        self.create_post(topic=topic_2, user=self.user, body='one').save()

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

    def test_read_tracker_after_posting(self):
        client = Client()
        client.login(username='zeus', password='zeus')
        self.create_post_via_http(client, topic_id=self.topic.id, body='test tracking')
        # after posting in topic it should be readed
        # because there is only one topic, so whole forum should be marked as readed
        self.assertEqual(TopicReadTracker.objects.filter(user=self.user, topic=self.topic).count(), 0)
        self.assertEqual(ForumReadTracker.objects.filter(user=self.user, forum=self.forum).count(), 1)

    def test_pybb_is_topic_unread_filter(self):
        forum_1 = self.forum
        topic_1 = self.topic
        topic_2 = Topic.objects.create(name='topic_2', forum=forum_1, user=self.user)

        forum_2 = Forum.objects.create(name='forum_2', description='forum2', category=self.category)
        topic_3 = Topic.objects.create(name='topic_2', forum=forum_2, user=self.user)

        self.create_post(topic=topic_1, user=self.user, body='one')
        self.create_post(topic=topic_2, user=self.user, body='two')
        self.create_post(topic=topic_3, user=self.user, body='three')

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

    def test_is_forum_unread_filter(self):
        Forum.objects.all().delete()

        forum_parent = Forum.objects.create(name='f1', category=self.category)
        forum_child1 = Forum.objects.create(name='f2', category=self.category, parent=forum_parent)
        forum_child2 = Forum.objects.create(name='f3', category=self.category, parent=forum_parent)
        topic_1 = Topic.objects.create(name='topic_1', forum=forum_parent, user=self.user)
        topic_2 = Topic.objects.create(name='topic_2', forum=forum_child1, user=self.user)
        topic_3 = Topic.objects.create(name='topic_3', forum=forum_child2, user=self.user)

        self.create_post(topic=topic_1, user=self.user, body='one')
        self.create_post(topic=topic_2, user=self.user, body='two')
        self.create_post(topic=topic_3, user=self.user, body='three')

        user_ann = User.objects.create_user('ann', 'ann@localhost', 'ann')
        client_ann = Client()
        client_ann.login(username='ann', password='ann')

        forum_parent = Forum.objects.get(id=forum_parent.id)
        forum_child1 = Forum.objects.get(id=forum_child1.id)
        forum_child2 = Forum.objects.get(id=forum_child2.id)
        self.assertListEqual([f.unread for f in pybb_forum_unread([forum_parent, forum_child1, forum_child2], user_ann)],
                             [True, True, True])

        # unless we read parent topic, there is unreaded topics in child forums
        client_ann.get(topic_1.get_absolute_url())
        forum_parent = Forum.objects.get(id=forum_parent.id)
        forum_child1 = Forum.objects.get(id=forum_child1.id)
        forum_child2 = Forum.objects.get(id=forum_child2.id)
        self.assertListEqual([f.unread for f in pybb_forum_unread([forum_parent, forum_child1, forum_child2], user_ann)],
                             [True, True, True])

        # still unreaded topic in one of the child forums
        client_ann.get(topic_2.get_absolute_url())
        forum_parent = Forum.objects.get(id=forum_parent.id)
        forum_child1 = Forum.objects.get(id=forum_child1.id)
        forum_child2 = Forum.objects.get(id=forum_child2.id)
        self.assertListEqual([f.unread for f in pybb_forum_unread([forum_parent, forum_child1, forum_child2], user_ann)],
                             [True, False, True])

        # all topics readed
        client_ann.get(topic_3.get_absolute_url())
        forum_parent = Forum.objects.get(id=forum_parent.id)
        forum_child1 = Forum.objects.get(id=forum_child1.id)
        forum_child2 = Forum.objects.get(id=forum_child2.id)
        self.assertListEqual([f.unread for f in pybb_forum_unread([forum_parent, forum_child1, forum_child2], user_ann)],
                             [False, False, False])

    def test_read_tracker_when_topics_forum_changed(self):
        forum_1 = Forum.objects.create(name='f1', description='bar', category=self.category)
        forum_2 = Forum.objects.create(name='f2', description='bar', category=self.category)
        topic_1 = Topic.objects.create(name='t1', forum=forum_1, user=self.user)
        topic_2 = Topic.objects.create(name='t2', forum=forum_2, user=self.user)

        self.create_post(topic=topic_1, user=self.user, body='one')
        self.create_post(topic=topic_2, user=self.user, body='two')

        user_ann = User.objects.create_user('ann', 'ann@localhost', 'ann')
        client_ann = Client()
        client_ann.login(username='ann', password='ann')

        # Everything is unread
        self.assertListEqual([t.unread for t in pybb_topic_unread([topic_1, topic_2], user_ann)], [True, True])
        self.assertListEqual([t.unread for t in pybb_forum_unread([forum_1, forum_2], user_ann)], [True, True])

        # read all
        client_ann.get(reverse('pybb:mark_all_as_read'))
        sleep_only_if_required(1)
        self.assertListEqual([t.unread for t in pybb_topic_unread([topic_1, topic_2], user_ann)], [False, False])
        self.assertListEqual([t.unread for t in pybb_forum_unread([forum_1, forum_2], user_ann)], [False, False])

        post = self.create_post(topic=topic_1, user=self.user, body='three')
        post = Post.objects.get(id=post.id)  # get post with timestamp from DB

        topic_1 = Topic.objects.get(id=topic_1.id)
        topic_2 = Topic.objects.get(id=topic_2.id)
        self.assertEqual(topic_1.updated, post.updated or post.created)
        self.assertEqual(forum_1.updated, post.updated or post.created)
        self.assertListEqual([t.unread for t in pybb_topic_unread([topic_1, topic_2], user_ann)], [True, False])
        self.assertListEqual([t.unread for t in pybb_forum_unread([forum_1, forum_2], user_ann)], [True, False])

        post.topic = topic_2
        post.save()
        topic_1 = Topic.objects.get(id=topic_1.id)
        topic_2 = Topic.objects.get(id=topic_2.id)
        forum_1 = Forum.objects.get(id=forum_1.id)
        forum_2 = Forum.objects.get(id=forum_2.id)
        self.assertEqual(topic_2.updated, post.updated or post.created)
        self.assertEqual(forum_2.updated, post.updated or post.created)
        self.assertListEqual([t.unread for t in pybb_topic_unread([topic_1, topic_2], user_ann)], [False, True])
        self.assertListEqual([t.unread for t in pybb_forum_unread([forum_1, forum_2], user_ann)], [False, True])

        topic_2.forum = forum_1
        topic_2.save()
        topic_1 = Topic.objects.get(id=topic_1.id)
        topic_2 = Topic.objects.get(id=topic_2.id)
        forum_1 = Forum.objects.get(id=forum_1.id)
        forum_2 = Forum.objects.get(id=forum_2.id)
        self.assertEqual(forum_1.updated, post.updated or post.created)
        self.assertListEqual([t.unread for t in pybb_topic_unread([topic_1, topic_2], user_ann)], [False, True])
        self.assertListEqual([t.unread for t in pybb_forum_unread([forum_1, forum_2], user_ann)], [True, False])

    def test_open_first_unread_post(self):
        forum_1 = self.forum
        topic_1 = Topic.objects.create(name='topic_1', forum=forum_1, user=self.user)
        topic_2 = Topic.objects.create(name='topic_2', forum=forum_1, user=self.user)

        post_1_1 = self.create_post(topic=topic_1, user=self.user, body='1_1')
        post_1_2 = self.create_post(topic=topic_1, user=self.user, body='1_2')
        post_2_1 = self.create_post(topic=topic_2, user=self.user, body='2_1')

        user_ann = User.objects.create_user('ann', 'ann@localhost', 'ann')
        client_ann = Client()
        client_ann.login(username='ann', password='ann')

        response = client_ann.get(topic_1.get_absolute_url(), data={'first-unread': 1}, follow=True)
        self.assertRedirects(response, '%s?page=%d#post-%d' % (topic_1.get_absolute_url(), 1, post_1_1.id))
        sleep_only_if_required(1)

        response = client_ann.get(topic_1.get_absolute_url(), data={'first-unread': 1}, follow=True)
        self.assertRedirects(response, '%s?page=%d#post-%d' % (topic_1.get_absolute_url(), 1, post_1_2.id))
        sleep_only_if_required(1)

        response = client_ann.get(topic_2.get_absolute_url(), data={'first-unread': 1}, follow=True)
        self.assertRedirects(response, '%s?page=%d#post-%d' % (topic_2.get_absolute_url(), 1, post_2_1.id))
        sleep_only_if_required(1)

        post_1_3 = self.create_post(topic=topic_1, user=self.user, body='1_3')
        post_1_4 = self.create_post(topic=topic_1, user=self.user, body='1_4')

        response = client_ann.get(topic_1.get_absolute_url(), data={'first-unread': 1}, follow=True)
        self.assertRedirects(response, '%s?page=%d#post-%d' % (topic_1.get_absolute_url(), 1, post_1_3.id))

    def test_latest_topics(self):
        topic_1 = self.topic
        topic_1.updated = timezone.now()
        topic_1.save()
        topic_2 = Topic.objects.create(name='topic_2', forum=self.forum, user=self.user)
        topic_2.updated = timezone.now() + datetime.timedelta(days=-1)
        topic_2.save()

        category_2 = Category.objects.create(name='cat2')
        forum_2 = Forum.objects.create(name='forum_2', category=category_2)
        topic_3 = Topic.objects.create(name='topic_3', forum=forum_2, user=self.user)
        topic_3.updated = timezone.now() + datetime.timedelta(days=-2)
        topic_3.save()

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

        post_hidden = self.create_post(topic=topic_hidden, user=self.user, body='hidden')

        post_in_hidden = self.create_post(topic=topic_in_hidden, user=self.user, body='hidden')

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

        user = User.objects.create_user('someguy', 'email@abc.xyz', 'password')
        client.login(username='someguy', password='password')

        response = client.get(reverse('pybb:add_post', kwargs={'topic_id': self.topic.id}))
        self.assertEqual(response.status_code, 200, response)

        response = client.get(reverse('pybb:add_post', kwargs={'topic_id': self.topic.id}), data={'quote_id': post_hidden.id})
        self.assertEqual(response.status_code, 403, response)

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
        response = self.create_post_via_http(client, topic_id=self.topic.id, csrfmiddlewaretoken=None)
        self.assertNotEqual(response.status_code, 200)
        response = self.create_post_via_http(client, topic_id=self.topic.id)
        self.assertEqual(response.status_code, 200)

    def test_user_blocking(self):
        user = User.objects.create_user('test', 'test@localhost', 'test')
        topic = Topic.objects.create(name='topic', forum=self.forum, user=user)
        p1 = self.create_post(topic=topic, user=user, body='bbcode [b]test[/b]')
        p2 = self.create_post(topic=topic, user=user, body='bbcode [b]test[/b]')
        self.user.is_superuser = True
        self.user.save()
        self.login_client()
        response = self.client.get(reverse('pybb:block_user', args=[user.username]), follow=True)
        self.assertEqual(response.status_code, 405)
        response = self.client.post(reverse('pybb:block_user', args=[user.username]), follow=True)
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(username=user.username)
        self.assertFalse(user.is_active)
        self.assertEqual(Topic.objects.filter().count(), 2)
        self.assertEqual(Post.objects.filter(user=user).count(), 2)

        user.is_active = True
        user.save()
        self.assertEqual(Topic.objects.count(), 2)
        response = self.client.post(reverse('pybb:block_user', args=[user.username]),
                                    data={'block_and_delete_messages': 'block_and_delete_messages'}, follow=True)
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(username=user.username)
        self.assertFalse(user.is_active)
        self.assertEqual(Topic.objects.count(), 1)
        self.assertEqual(Post.objects.filter(user=user).count(), 0)

    def test_user_unblocking(self):
        user = User.objects.create_user('test', 'test@localhost', 'test')
        user.is_active=False
        user.save()
        self.user.is_superuser = True
        self.user.save()
        self.login_client()
        response = self.client.get(reverse('pybb:unblock_user', args=[user.username]), follow=True)
        self.assertEqual(response.status_code, 405)
        response = self.client.post(reverse('pybb:unblock_user', args=[user.username]), follow=True)
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(username=user.username)
        self.assertTrue(user.is_active)

    def test_ajax_preview(self):
        self.login_client()
        response = self.client.post(reverse('pybb:post_ajax_preview'), data={'data': '[b]test bbcode ajax preview[/b]'})
        self.assertContains(response, '<strong>test bbcode ajax preview</strong>')

    def test_headline(self):
        self.forum.headline = 'test <b>headline</b>'
        self.forum.save()
        client = Client()
        self.assertContains(client.get(self.forum.get_absolute_url()), 'test <b>headline</b>')

    def test_quote(self):
        self.login_client()
        response = self.client.get(reverse('pybb:add_post', kwargs={'topic_id': self.topic.id}),
                                   data={'quote_id': self.post.id, 'body': 'test tracking'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.post.body)

    def test_edit_post(self):
        self.login_client()
        edit_post_url = reverse('pybb:edit_post', kwargs={'pk': self.post.id})
        response = self.client.get(edit_post_url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(Post.objects.get(id=self.post.id).updated)
        tree = html.fromstring(response.content)
        values = dict(tree.xpath('//form[@method="post"]')[0].form_values())
        values['body'] = 'test edit'
        response = self.client.post(edit_post_url, data=values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.get(pk=self.post.id).body, 'test edit')
        response = self.client.get(self.post.get_absolute_url(), follow=True)
        self.assertContains(response, 'test edit')
        self.assertIsNotNone(Post.objects.get(id=self.post.id).updated)

        # Check admin form
        orig_conf = defaults.PYBB_ENABLE_ADMIN_POST_FORM

        self.user.is_staff = True
        self.user.save()

        defaults.PYBB_ENABLE_ADMIN_POST_FORM = False
        response = self.client.get(edit_post_url)
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content)
        values = dict(tree.xpath('//form[@method="post"]')[0].form_values())
        self.assertNotIn('login', values)
        values['body'] = 'test edit'
        values['login'] = 'new_login'
        response = self.client.post(edit_post_url, data=values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test edit')
        self.assertNotContains(response, 'new_login')

        defaults.PYBB_ENABLE_ADMIN_POST_FORM = True
        response = self.client.get(edit_post_url)
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content)
        values = dict(tree.xpath('//form[@method="post"]')[0].form_values())
        self.assertIn('login', values)
        values['body'] = 'test edit 2'
        values['login'] = 'new_login 2'
        response = self.client.post(edit_post_url, data=values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test edit 2')
        self.assertContains(response, 'new_login 2')

        defaults.PYBB_ENABLE_ADMIN_POST_FORM = orig_conf

    def test_admin_post_add(self):
        self.user.is_staff = True
        self.user.save()
        self.login_client()
        response = self.create_post_via_http(self.client, topic_id=self.topic.id,
                                             quote_id=self.post.id, body='test admin post', user='zeus')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test admin post')

    def test_stick(self):
        self.user.is_superuser = True
        self.user.save()
        self.login_client()
        self.assertEqual(
            self.client.get(reverse('pybb:stick_topic', kwargs={'pk': self.topic.id}), follow=True).status_code, 200)
        self.assertEqual(
            self.client.get(reverse('pybb:unstick_topic', kwargs={'pk': self.topic.id}), follow=True).status_code, 200)

    def test_delete_view(self):
        post = self.create_post(topic=self.topic, user=self.user, body='test to delete')
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
        user2 = User.objects.create_user('user2', 'user2@someserver.com', 'user2')
        client = Client()
        client.login(username='user2', password='user2')

        response = self.client.get(reverse('pybb:close_topic', args=[self.topic.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        response = self.create_post_via_http(client, topic_id=self.topic.id, body='test closed')
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse('pybb:open_topic', args=[self.topic.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        response = self.create_post_via_http(client, topic_id=self.topic.id, body='test closed')
        self.assertEqual(response.status_code, 200)

    def test_subscription(self):
        user2 = User.objects.create_user(username='user2', password='user2', email='user2@someserver.com')
        user3 = User.objects.create_user(username='user3', password='user3', email='user3@example.com')
        client = Client()

        client.login(username='user2', password='user2')
        subscribe_url = reverse('pybb:add_subscription', args=[self.topic.id])
        response = client.get(self.topic.get_absolute_url())
        subscribe_links = html.fromstring(response.content).xpath('//a[@href="%s"]' % subscribe_url)
        self.assertEqual(len(subscribe_links), 1)

        response = client.get(subscribe_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(user2, self.topic.subscribers.all())

        self.topic.subscribers.add(user3)

        # create a new reply (with another user)
        self.client.login(username='zeus', password='zeus')

        response = self.create_post_via_http(self.client, topic_id=self.topic.id,
                                             body='test subscribtion юникод')
        self.assertEqual(response.status_code, 200)
        new_post = Post.objects.order_by('-id')[0]

        # there should only be one email in the outbox (to user2) because @example.com are ignored
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], user2.email)
        self.assertTrue([msg for msg in mail.outbox if new_post.get_absolute_url() in msg.body])

        # unsubscribe
        client.login(username='user2', password='user2')
        self.assertTrue([msg for msg in mail.outbox if new_post.get_absolute_url() in msg.body])
        response = client.get(reverse('pybb:delete_subscription', args=[self.topic.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(user2, self.topic.subscribers.all())

    def test_subscription_disabled(self):
        orig_conf = defaults.PYBB_DISABLE_SUBSCRIPTIONS
        defaults.PYBB_DISABLE_SUBSCRIPTIONS = True

        user2 = User.objects.create_user(username='user2', password='user2', email='user2@someserver.com')
        user3 = User.objects.create_user(username='user3', password='user3', email='user3@someserver.com')
        client = Client()

        client.login(username='user2', password='user2')
        subscribe_url = reverse('pybb:add_subscription', args=[self.topic.id])
        response = client.get(self.topic.get_absolute_url())
        subscribe_links = html.fromstring(response.content).xpath('//a[@href="%s"]' % subscribe_url)
        self.assertEqual(len(subscribe_links), 0)

        response = client.get(subscribe_url, follow=True)
        self.assertEqual(response.status_code, 403)

        self.topic.subscribers.add(user3)

        # create a new reply (with another user)
        self.client.login(username='zeus', password='zeus')
        response = self.create_post_via_http(self.client, topic_id=self.topic.id,
                                             body='test subscribtion юникод')
        self.assertEqual(response.status_code, 200)
        new_post = Post.objects.order_by('-id')[0]

        # there should be one email in the outbox (user3)
        #because already subscribed users will still receive notifications.
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], user3.email)

        defaults.PYBB_DISABLE_SUBSCRIPTIONS = orig_conf

    def _test_notification_emails_init(self):
        user2 = User.objects.create_user(username='user2', password='user2', email='user2@someserver.com')
        profile2 = util.get_pybb_profile(user2)
        profile2.language = 'en'
        profile2.save()
        user3 = User.objects.create_user(username='user3', password='user3', email='user3@someserver.com')
        profile3 = util.get_pybb_profile(user3)
        profile3.language = 'fr'
        profile3.save()
        self.topic.subscribers.add(user2)
        self.topic.subscribers.add(user3)

        # create a new reply (with another user)
        self.client.login(username='zeus', password='zeus')
        add_post_url = reverse('pybb:add_post', args=[self.topic.id])
        response = self.client.get(add_post_url)
        values = self.get_form_values(response)
        values['body'] = 'test notification HTML'
        response = self.client.post(add_post_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        new_post = Post.objects.order_by('-id')[0]

        return user2, user3, new_post

    def test_notification_emails_alternative(self):
        user2, user3, new_post = self._test_notification_emails_init()
        # there should be two emails in the outbox (user2 and user3)
        self.assertEqual(len(mail.outbox), 2)
        email = mail.outbox[0]
        self.assertEqual(email.to[0], user2.email)

        # HTML alternative must be available
        self.assertEqual(len(email.alternatives), 1)
        self.assertEqual(email.alternatives[0][1], 'text/html')

    def test_notification_emails_content(self):
        user2, user3, new_post = self._test_notification_emails_init()
        # there should be two emails in the outbox (user2 and user3)
        self.assertEqual(len(mail.outbox), 2)
        email = mail.outbox[0]
        html_body = email.alternatives[0][0]
        text_body = email.body

        # emails (txt and HTML) must contains links to post AND to topic AND to unsubscribe.
        delete_url = reverse('pybb:delete_subscription', args=[self.topic.id])
        post_url = new_post.get_absolute_url()
        topic_url = new_post.topic.get_absolute_url()
        links = html.fromstring(html_body).xpath('//a')
        found = {'post_url': False, 'topic_url': False, 'delete_url': False,}
        for link in links:
            if delete_url in link.attrib['href']:
                found['delete_url'] = True
            elif post_url in link.attrib['href']:
                found['post_url'] = True
            elif topic_url in link.attrib['href']:
                found['topic_url'] = True
        self.assertTrue(found['delete_url'])
        self.assertTrue(found['post_url'])
        self.assertTrue(found['topic_url'])
        self.assertIn(post_url, text_body)
        self.assertIn(topic_url, text_body)
        self.assertIn(delete_url, text_body)


    def test_notification_emails_translation(self):
        user2, user3, new_post = self._test_notification_emails_init()
        # there should be two emails in the outbox (user2 and user3)
        self.assertEqual(len(mail.outbox), 2)
        if mail.outbox[0].to[0] == user2.email:
            email_en, email_fr = mail.outbox[0], mail.outbox[1]
        else:  # pragma: no cover
            email_fr, email_en = mail.outbox[0], mail.outbox[1]

        subject_en = "New answer in topic that you subscribed."
        self.assertEqual(email_en.subject, subject_en)
        self.assertNotEqual(email_fr.subject, subject_en)

    def test_notifications_disabled(self):
        orig_conf = defaults.PYBB_DISABLE_NOTIFICATIONS
        defaults.PYBB_DISABLE_NOTIFICATIONS = True

        user2 = User.objects.create_user(username='user2', password='user2', email='user2@someserver.com')
        user3 = User.objects.create_user(username='user3', password='user3', email='user3@someserver.com')
        client = Client()

        client.login(username='user2', password='user2')
        subscribe_url = reverse('pybb:add_subscription', args=[self.topic.id])
        response = client.get(self.topic.get_absolute_url())
        subscribe_links = html.fromstring(response.content).xpath('//a[@href="%s"]' % subscribe_url)
        self.assertEqual(len(subscribe_links), 1)
        response = client.get(subscribe_url, follow=True)
        self.assertEqual(response.status_code, 200)

        self.topic.subscribers.add(user3)

        # create a new reply (with another user)
        self.client.login(username='zeus', password='zeus')
        response = self.create_post_via_http(client, topic_id=self.topic.id,
                                             body='test subscribtion юникод')
        self.assertEqual(response.status_code, 200)
        new_post = Post.objects.order_by('-id')[0]

        # there should be no email in the outbox
        self.assertEqual(len(mail.outbox), 0)

        defaults.PYBB_DISABLE_NOTIFICATIONS = orig_conf

    def test_forum_subscription(self):
        url = reverse('pybb:forum_subscription', kwargs={'pk': self.forum.id})
        user2 = User.objects.create_user(username='user2', password='user2', email='user2@dns.com')
        user3 = User.objects.create_user(username='user3', password='user3', email='user3@dns.com')
        client = Client()
        client.login(username='user2', password='user2')
        parser = html.HTMLParser(encoding='utf8')

        # Check we have the "Subscribe" link
        response = client.get(self.forum.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content, parser=parser)
        self.assertTrue(['Subscribe'], tree.xpath('//a[@href="%s"]/text()' % url))

        # check anonymous can't subscribe :
        anonymous_client = Client()
        response = anonymous_client.get(url)
        self.assertEqual(response.status_code, 302)

        # click on this link with a logged account
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content, parser=parser)

        # Check we have 4 radio inputs
        radio_ids = tree.xpath('//input[@type="radio"]/@id')
        self.assertEqual(['id_type_0', 'id_type_1', 'id_topics_0', 'id_topics_1'], radio_ids)

        # submit the form to be notified for new topics
        values = self.get_form_values(response, form='forum_subscription')
        values.update({'type': ForumSubscription.TYPE_NOTIFY, 'topics': 'new', })
        response = client.post(url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('subscription' in response.context_data)
        self.assertEqual(response.context_data['subscription'].forum, self.forum)
        tree = html.fromstring(response.content, parser=parser)
        self.assertTrue(['Manage subscription'], tree.xpath('//a[@href="%s"]/text()' % url))

        client = Client()
        client.login(username='user3', password='user3')
        response = client.get(url)
        values = self.get_form_values(response, form='forum_subscription')
        values.update({'type': ForumSubscription.TYPE_SUBSCRIBE, 'topics': 'new', })
        response = client.post(url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('subscription' in response.context_data)
        self.assertTrue(response.context_data['subscription'].forum, self.forum)
        # Check there is still only zeus who subscribe to topic
        usernames = list(self.topic.subscribers.all().values_list('username', flat=True))
        self.assertEqual(usernames, [self.user.username, ])

        topic = Topic(name='newtopic', forum=self.forum, user=self.user)
        topic.save()
        # user2 should have a mail
        self.assertEqual(1, len(mail.outbox))
        self.assertEqual([user2.email, ], mail.outbox[0].to)
        self.assertEqual('New topic in forum that you subscribed.', mail.outbox[0].subject)
        self.assertTrue('User zeus post a new topic' in mail.outbox[0].body)
        self.assertTrue(topic.get_absolute_url() in mail.outbox[0].body)
        self.assertTrue(url in mail.outbox[0].body)
        post = self.create_post(topic=topic, user=self.user, body='body')

        # Now, user3 should be subscribed to this new topic
        usernames = topic.subscribers.all().order_by('username')
        usernames = list(usernames.values_list('username', flat=True))
        self.assertEqual(usernames, ['user3', self.user.username])
        self.assertEqual(2, len(mail.outbox))
        self.assertEqual([user3.email, ], mail.outbox[1].to)
        self.assertEqual('New answer in topic that you subscribed.', mail.outbox[1].subject)

        # Now, we unsubscribe user3 to be auto subscribed
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content, parser=parser)

        # Check we have 5 radio inputs
        radio_ids = tree.xpath('//input[@type="radio"]/@id')
        expected_inputs = [
            'id_type_0', 'id_type_1', 'id_type_2',
            'id_topics_0', 'id_topics_1'
        ]
        self.assertEqual(expected_inputs, radio_ids)
        self.assertEqual(tree.xpath('//input[@id="id_type_2"]/@value'), ['unsubscribe', ])
        self.assertEqual(tree.xpath('//input[@id="id_type_1"]/@checked'), ['checked', ])
        values = self.get_form_values(response, form='forum_subscription')
        values['type'] = 'unsubscribe'
        response = client.post(url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('subscription' in response.context_data)
        self.assertIsNone(response.context_data['subscription'])
        # user3 should not be subscribed anymore to any forum
        with self.assertRaises(ForumSubscription.DoesNotExist):
            ForumSubscription.objects.get(user=user3)
        # but should still be still subscribed to the topic
        usernames = list(topic.subscribers.all().order_by('id').values_list('username', flat=True))
        self.assertEqual(usernames, [self.user.username, 'user3', ])

        # Update user2's subscription to be autosubscribed to all posts
        client = Client()
        client.login(username='user2', password='user2')
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content, parser=parser)
        self.assertEqual(tree.xpath('//input[@id="id_type_0"]/@checked'), ['checked', ])
        values = self.get_form_values(response, form='forum_subscription')
        values['type'] = ForumSubscription.TYPE_SUBSCRIBE
        values['topics'] = 'all'
        response = client.post(url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        # user2 shoud now be subscribed to all self.forum's topics
        subscribed_topics = list(user2.subscriptions.all().order_by('name').values_list('name', flat=True))
        expected_topics = list(self.forum.topics.all().order_by('name').values_list('name', flat=True))
        self.assertEqual(subscribed_topics, expected_topics)

        # unsubscribe user2 to all topics
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content, parser=parser)
        self.assertEqual(tree.xpath('//input[@id="id_type_2"]/@value'), ['unsubscribe', ])
        values = self.get_form_values(response, form='forum_subscription')
        values['type'] = 'unsubscribe'
        values['topics'] = 'all'
        response = client.post(url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        # user2 shoud now be subscribed to zero topic
        topics = list(user2.subscriptions.all().values_list('name', flat=True))
        self.assertEqual(topics, [])

    def test_topic_updated(self):
        topic = Topic(name='new topic', forum=self.forum, user=self.user)
        topic.save()
        post = self.create_post(_sleep=True, topic=topic, user=self.user, body='bbcode [b]test[/b]')
        client = Client()
        response = client.get(self.forum.get_absolute_url())
        self.assertEqual(response.context['topic_list'][0], topic)
        post = self.create_post(topic=self.topic, user=self.user, body='bbcode [b]test[/b]')
        client = Client()
        response = client.get(self.forum.get_absolute_url())
        self.assertEqual(response.context['topic_list'][0], self.topic)

    def test_topic_deleted(self):
        forum_1 = Forum.objects.create(name='new forum', category=self.category)
        topic_1 = Topic.objects.create(name='new topic', forum=forum_1, user=self.user)
        post_1 = self.create_post(topic=topic_1, user=self.user, body='test')
        post_1 = Post.objects.get(id=post_1.id)

        self.assertEqual(topic_1.updated, post_1.created)
        self.assertEqual(forum_1.updated, post_1.created)

        sleep_only_if_required(1)
        topic_2 = Topic.objects.create(name='another topic', forum=forum_1, user=self.user)
        post_2 = self.create_post(topic=topic_2, user=self.user, body='another test')
        post_2 = Post.objects.get(id=post_2.id)

        self.assertEqual(topic_2.updated, post_2.created)
        self.assertEqual(forum_1.updated, post_2.created)

        topic_2.delete()
        forum_1 = Forum.objects.get(id=forum_1.id)
        self.assertEqual(forum_1.updated, post_1.created)
        self.assertEqual(forum_1.topic_count, 1)
        self.assertEqual(forum_1.post_count, 1)

        post_1.delete()
        forum_1 = Forum.objects.get(id=forum_1.id)
        self.assertEqual(forum_1.topic_count, 0)
        self.assertEqual(forum_1.post_count, 0)

    def test_user_views(self):
        response = self.client.get(reverse('pybb:user', kwargs={'username': self.user.username}))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('pybb:user_posts', kwargs={'username': self.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object_list'].count(), 1)

        response = self.client.get(reverse('pybb:user_topics', kwargs={'username': self.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object_list'].count(), 1)

        self.topic.forum.hidden = True
        self.topic.forum.save()

        self.client.logout()

        response = self.client.get(reverse('pybb:user_posts', kwargs={'username': self.user.username}))
        self.assertEqual(response.context['object_list'].count(), 0)

        response = self.client.get(reverse('pybb:user_topics', kwargs={'username': self.user.username}))
        self.assertEqual(response.context['object_list'].count(), 0)

    def test_post_count(self):
        topic = Topic(name='etopic', forum=self.forum, user=self.user)
        topic.save()
        post = self.create_post(topic=topic, user=self.user, body='test')
        self.assertEqual(util.get_pybb_profile(self.user).post_count, 2)
        post.body = 'test2'
        post.save()
        self.assertEqual(Profile.objects.get(pk=util.get_pybb_profile(self.user).pk).post_count, 2)
        post.delete()
        self.assertEqual(Profile.objects.get(pk=util.get_pybb_profile(self.user).pk).post_count, 1)

    def test_latest_topics_tag(self):
        Topic.objects.all().delete()
        for i in range(10):
            Topic.objects.create(name='topic%s' % i, user=self.user, forum=self.forum)
        latest_topics = pybb_get_latest_topics(context=None, user=self.user)
        self.assertEqual(len(latest_topics), 5)
        self.assertEqual(latest_topics[0].name, 'topic9')
        self.assertEqual(latest_topics[4].name, 'topic5')

    def test_latest_posts_tag(self):
        Post.objects.all().delete()
        for i in range(10):
            self.create_post(body='post%s' % i, user=self.user, topic=self.topic)
        latest_topics = pybb_get_latest_posts(context=None, user=self.user)
        self.assertEqual(len(latest_topics), 5)
        self.assertEqual(latest_topics[0].body, 'post9')
        self.assertEqual(latest_topics[4].body, 'post5')

    def test_multiple_objects_returned(self):
        """
        see issue #87: https://github.com/hovel/pybbm/issues/87
        """
        self.assertFalse(self.user.is_superuser)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.topic.on_moderation)
        self.assertEqual(self.topic.user, self.user)
        user1 = User.objects.create_user('geyser', 'geyser@localhost', 'geyser')
        self.topic.forum.moderators.add(self.user)
        self.topic.forum.moderators.add(user1)

        self.login_client()
        response = self.client.get(reverse('pybb:add_post', kwargs={'topic_id': self.topic.id}))
        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        defaults.PYBB_ENABLE_ANONYMOUS_POST = self.ORIG_PYBB_ENABLE_ANONYMOUS_POST
        defaults.PYBB_PREMODERATION = self.ORIG_PYBB_PREMODERATION

    def test_managing_forums(self):
        _attach_perms_class('pybb.tests.CustomPermissionHandler')
        forum2 = Forum.objects.create(name='foo2', description='bar2', category=self.category)
        Forum.objects.create(name='foo3', description='bar3', category=self.category)
        moderator = User.objects.create_user('moderator', 'moderator@localhost', 'moderator')
        self.login_client()

        #test the visibility of the button and the access to the page
        response = self.client.get(reverse('pybb:user', kwargs={'username': moderator.username}))
        self.assertNotContains(
            response, '<a href="%s"' % reverse(
                    'pybb:edit_privileges', kwargs={'username': moderator.username}
                )
            )
        response = self.client.get(reverse('pybb:edit_privileges', kwargs={'username': moderator.username}))
        self.assertEqual(response.status_code, 403)
        add_change_forum_permission = Permission.objects.get_by_natural_key('change_forum','pybb','forum')
        self.user.user_permissions.add(add_change_forum_permission)
        self.user.is_staff = True
        self.user.save()
        response = self.client.get(reverse('pybb:user', kwargs={'username': moderator.username}))
        self.assertContains(
            response, '<a href="%s"' % reverse(
                    'pybb:edit_privileges', kwargs={'username': moderator.username}
                )
            )
        response = self.client.get(reverse('pybb:edit_privileges', kwargs={'username': moderator.username}))
        self.assertEqual(response.status_code, 200)

        # test if there are as many chechkboxs as forums in the category
        inputs = dict(html.fromstring(response.content).xpath('//form[@class="%s"]' % "privileges-edit")[0].inputs)
        self.assertEqual(
            len(response.context['form'].authorized_forums),
            len(inputs['cat_%d' % self.category.pk])
            )

        # test to add user as moderator
        # get csrf token
        values = self.get_form_values(response, "privileges-edit")
        # dynamic contruction of the list corresponding to custom may_change_forum
        available_forums = [forum for forum in self.category.forums.all() if not forum.pk % 3 == 0]
        values['cat_%d' % self.category.pk] = [forum.pk for forum in available_forums]
        response = self.client.post(
            reverse('pybb:edit_privileges', kwargs={'username': moderator.username}), data=values, follow=True
            )
        self.assertEqual(response.status_code, 200)

        correct_list = sorted(available_forums, key=lambda forum: forum.pk)
        moderator_list = sorted([forum for forum in moderator.forum_set.all()], key=lambda forum: forum.pk)
        self.assertEqual(correct_list, moderator_list)

        # test to remove user as moderator
        values['cat_%d' % self.category.pk] = [available_forums[0].pk, ]
        response = self.client.post(
                reverse('pybb:edit_privileges', kwargs={'username': moderator.username}), data=values, follow=True
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual([available_forums[0], ], [forum for forum in moderator.forum_set.all()])
        values['cat_%d' % self.category.pk] = []
        response = self.client.post(
                reverse('pybb:edit_privileges', kwargs={'username': moderator.username}), data=values, follow=True
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(0, moderator.forum_set.count())
        self.user.user_permissions.remove(add_change_forum_permission)
        _detach_perms_class()

class MoveAndSplitPostTest(TestCase, SharedTestModule):

    def create_initial(self):
        if not getattr(self, 'user', None):
            self.create_user()
        self.category = Category.objects.create(name='foo', position=1)
        self.forum_1 = Forum.objects.create(name='forum_1', category=self.category, position=1)
        self.topic = Topic.objects.create(name='abc', forum=self.forum_1, user=self.user, views=7)
        self.posts = []
        self.posts.append(self.create_post(topic=self.topic, user=self.user, body='zero'))
        self.posts.append(self.create_post(topic=self.topic, user=self.user, body='one'))
        self.posts.append(self.create_post(topic=self.topic, user=self.user, body='two'))
        self.posts.append(self.create_post(topic=self.topic, user=self.user, body='three'))
        self.posts.append(self.create_post(topic=self.topic, user=self.user, body='four'))
        self.posts.append(self.create_post(topic=self.topic, user=self.user, body='five'))

        self.forum_2 = Forum.objects.create(name='forum_2', category=self.category, position=2)
        self.forum_3 = Forum.objects.create(name='forum_3', category=self.category, hidden=True)

        self.moderator = User.objects.create_user('moderator', 'moderator@localhost', 'moderator')
        self.forum_1.moderators.add(self.moderator)
        self.forum_2.moderators.add(self.moderator)

    def test_move_topic(self):
        self.create_initial()
        move_topic_url = reverse('pybb:move_post', kwargs={'pk': self.topic.head.pk})

        # user can not move posts, even if he is the author
        response = self.get_with_user(move_topic_url, 'zeus', 'zeus')
        self.assertEqual(response.status_code, 403)

        # moderator can
        self.login_client('moderator', 'moderator')
        response = self.client.get(move_topic_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.forum_1.topic_count, 1)
        self.assertEqual(self.forum_1.post_count, 6)

        # check form values
        form_values = self.get_form_values(response, 'move-post-form')
        move_to_choices = response.context['form'].fields['move_to'].choices
        self.assertTrue('name' in response.context['form'].fields)
        self.assertTrue('number' not in response.context['form'].fields)
        self.assertEqual(len(move_to_choices), 1)
        self.assertEqual(move_to_choices[0][0], '%s' % self.category)
        self.assertEqual(len(move_to_choices[0][1]), 1)
        # moderator has no access to forum 3 (hidden), so he can't move the topic in this forum
        self.assertEqual(move_to_choices[0][1][0][0], self.forum_2.pk)

        # move in forum_2
        form_values['move_to'] = self.forum_2.pk
        response = self.client.post(move_topic_url, form_values, follow=True)
        forum_1 = Forum.objects.get(pk=self.forum_1.pk)
        forum_2 = Forum.objects.get(pk=self.forum_2.pk)
        topic = Topic.objects.get(pk=self.topic.pk)
        self.assertEqual(topic.forum.pk, forum_2.pk)
        self.assertEqual(forum_1.topic_count, 0)
        self.assertEqual(forum_1.post_count, 0)
        self.assertEqual(forum_2.topic_count, 1)
        self.assertEqual(forum_2.post_count, 6)
        self.assertEqual(topic.views, 8)  # +1 because topic is currently viewed by moderator

    def test_split_posts_all(self):
        self.create_initial()
        split_posts_url = reverse('pybb:move_post', kwargs={'pk': self.posts[2].pk})

        self.login_client('moderator', 'moderator')
        response = self.client.get(split_posts_url)
        self.assertEqual(response.status_code, 200)

        # check form values
        form_values = self.get_form_values(response, 'move-post-form')
        move_to_choices = response.context['form'].fields['move_to'].choices
        self.assertTrue('name' in response.context['form'].fields)
        self.assertTrue('number' in response.context['form'].fields)
        self.assertEqual(len(move_to_choices), 1)
        self.assertEqual(move_to_choices[0][0], '%s' % self.category)
        self.assertEqual(len(move_to_choices[0][1]), 2)
        # moderator has no access to forum 3 (hidden), so he can't move the topic in this forum
        # but forum_1 is in choices because we can split in the same forum
        self.assertEqual(move_to_choices[0][1][0][0], self.forum_1.pk)
        self.assertEqual(move_to_choices[0][1][1][0], self.forum_2.pk)

        # move 4 last posts in forum_2
        form_values['move_to'] = self.forum_2.pk
        form_values['number'] = -1
        form_values['name'] = 'new topic'
        response = self.client.post(split_posts_url, form_values, follow=True)
        forum_1 = Forum.objects.get(pk=self.forum_1.pk)
        forum_2 = Forum.objects.get(pk=self.forum_2.pk)
        topic_1 = Topic.objects.get(pk=self.topic.pk)
        # initial topic is still in the forum 1
        self.assertEqual(topic_1.forum.pk, forum_1.pk)
        # it has now only 2 posts
        self.assertEqual(topic_1.posts.count(), 2)
        # head post of the topic is post "zero"
        self.assertEqual(topic_1.head.pk, self.posts[0].pk)
        # last post of the topic is post "one"
        self.assertEqual(topic_1.last_post.pk, self.posts[1].pk)

        try:
            # new topic exists
            topic_2 = Topic.objects.get(forum=forum_2)
        except:
            self.fail('A new topic in forum 2 should have been created by spliting posts')

        # it has new name
        self.assertEqual(topic_2.name, 'new topic')
        # it has 4 posts
        self.assertEqual(topic_2.posts.count(), 4)
        # head post of the topic is post "two"
        self.assertEqual(topic_2.head.pk, self.posts[2].pk)
        # last post of the topic is post "five"
        self.assertEqual(topic_2.last_post.pk, self.posts[5].pk)

        # check topic and forum counters
        self.assertEqual(topic_1.post_count, 2)
        self.assertEqual(topic_1.views, 7)
        self.assertEqual(forum_1.topic_count, 1)
        self.assertEqual(forum_1.post_count, 2)
        self.assertEqual(topic_2.post_count, 4)
        self.assertEqual(forum_2.topic_count, 1)
        self.assertEqual(forum_2.post_count, 4)
        self.assertEqual(topic_2.views, 1)  # +1 because topic is currently viewed by moderator

    def test_split_posts_last(self):
        self.create_initial()
        split_posts_url = reverse('pybb:move_post', kwargs={'pk': self.posts[5].pk})

        self.login_client('moderator', 'moderator')
        response = self.client.get(split_posts_url)
        self.assertEqual(response.status_code, 200)

        form_values = self.get_form_values(response, 'move-post-form')

        # move last post in forum_2
        form_values['move_to'] = self.forum_2.pk
        form_values['number'] = -1
        response = self.client.post(split_posts_url, form_values, follow=True)
        forum_1 = Forum.objects.get(pk=self.forum_1.pk)
        forum_2 = Forum.objects.get(pk=self.forum_2.pk)
        self.assertEqual(forum_1.topic_count, 1)
        self.assertEqual(forum_1.post_count, 5)
        self.assertEqual(forum_2.topic_count, 1)
        self.assertEqual(forum_2.post_count, 1)
        topic_2 = Post.objects.get(pk=self.posts[5].pk).topic
        self.assertNotEqual(self.topic.pk, topic_2.pk)
        self.assertEqual(self.topic.name, topic_2.name)
        self.assertEqual(self.topic.slug, topic_2.slug)  # same slug because not in same forum

    def test_split_posts_some_same_forum(self):
        self.create_initial()
        split_posts_url = reverse('pybb:move_post', kwargs={'pk': self.posts[1].pk})

        self.login_client('moderator', 'moderator')
        response = self.client.get(split_posts_url)
        self.assertEqual(response.status_code, 200)

        form_values = self.get_form_values(response, 'move-post-form')

        # post stay in same forum but are splited in a new topic
        form_values['move_to'] = self.forum_1.pk
        form_values['number'] = 2
        response = self.client.post(split_posts_url, form_values, follow=True)
        forum_1 = Forum.objects.get(pk=self.forum_1.pk)
        forum_2 = Forum.objects.get(pk=self.forum_2.pk)
        topic_1 = Topic.objects.get(pk=self.topic.pk)
        topic_2 = Post.objects.get(pk=self.posts[1].pk).topic
        # splited in 2 topics
        self.assertNotEqual(topic_1.pk, topic_2.pk)
        self.assertEqual(topic_1.name, topic_2.name)
        self.assertNotEqual(topic_1.slug, topic_2.slug)  # can't keep same slug in same forum
        self.assertEqual(topic_1.posts.count(), 3)
        self.assertEqual(topic_2.posts.count(), 3)
        # stay in same forum
        self.assertEqual(topic_1.forum.pk, topic_2.forum.pk)
        # posts 0 4 5 are still in topic 1
        self.assertEqual(topic_1.head.pk, self.posts[0].pk)
        self.assertEqual(topic_1.last_post.pk, self.posts[5].pk)
        # posts 1 2 3 are now in topic 2
        self.assertEqual(topic_2.head.pk, self.posts[1].pk)
        self.assertEqual(topic_2.last_post.pk, self.posts[3].pk)

    def test_split_posts_some_other_forum(self):
        self.create_initial()
        split_posts_url = reverse('pybb:move_post', kwargs={'pk': self.posts[1].pk})

        self.login_client('moderator', 'moderator')
        response = self.client.get(split_posts_url)
        self.assertEqual(response.status_code, 200)

        form_values = self.get_form_values(response, 'move-post-form')

        # posts splited in forum 2
        form_values['move_to'] = self.forum_2.pk
        form_values['number'] = 2
        response = self.client.post(split_posts_url, form_values, follow=True)
        forum_1 = Forum.objects.get(pk=self.forum_1.pk)
        forum_2 = Forum.objects.get(pk=self.forum_2.pk)
        topic_1 = Topic.objects.get(pk=self.topic.pk)
        topic_2 = Post.objects.get(pk=self.posts[1].pk).topic
        # splited in 2 topics
        self.assertNotEqual(topic_1.pk, topic_2.pk)
        self.assertEqual(topic_1.posts.count(), 3)
        self.assertEqual(topic_2.posts.count(), 3)
        # not anymore in same forum
        self.assertNotEqual(topic_1.forum.pk, topic_2.forum.pk)
        # posts 0 4 5 are still in topic 1
        self.assertEqual(topic_1.head.pk, self.posts[0].pk)
        self.assertEqual(topic_1.last_post.pk, self.posts[5].pk)
        # posts 1 2 3 are now in topic 2
        self.assertEqual(topic_2.head.pk, self.posts[1].pk)
        self.assertEqual(topic_2.last_post.pk, self.posts[3].pk)


class AnonymousTest(TestCase, SharedTestModule):
    def setUp(self):
        self.ORIG_PYBB_ENABLE_ANONYMOUS_POST = defaults.PYBB_ENABLE_ANONYMOUS_POST
        self.ORIG_PYBB_ANONYMOUS_USERNAME = defaults.PYBB_ANONYMOUS_USERNAME
        self.PYBB_ANONYMOUS_VIEWS_CACHE_BUFFER = defaults.PYBB_ANONYMOUS_VIEWS_CACHE_BUFFER

        defaults.PYBB_ENABLE_ANONYMOUS_POST = True
        defaults.PYBB_ANONYMOUS_USERNAME = 'Anonymous'
        self.user = User.objects.create_user('Anonymous', 'Anonymous@localhost', 'Anonymous')
        self.category = Category.objects.create(name='foo')
        self.forum = Forum.objects.create(name='xfoo', description='bar', category=self.category)
        self.topic = Topic.objects.create(name='etopic', forum=self.forum, user=self.user)
        self.post = self.create_post(body='body post', topic=self.topic, user=self.user)
        add_post_permission = Permission.objects.get_by_natural_key('add_post', 'pybb', 'post')
        self.user.user_permissions.add(add_post_permission)

    def tearDown(self):
        defaults.PYBB_ENABLE_ANONYMOUS_POST = self.ORIG_PYBB_ENABLE_ANONYMOUS_POST
        defaults.PYBB_ANONYMOUS_USERNAME = self.ORIG_PYBB_ANONYMOUS_USERNAME
        defaults.PYBB_ANONYMOUS_VIEWS_CACHE_BUFFER = self.PYBB_ANONYMOUS_VIEWS_CACHE_BUFFER

    def test_anonymous_posting(self):
        response = self.create_post_via_http(self.client, topic_id=self.topic.id,
                                             body='test anonymous')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(Post.objects.filter(body='test anonymous')), 1)
        self.assertEqual(Post.objects.get(body='test anonymous').user, self.user)

    def test_anonymous_cache_topic_views(self):
        self.assertNotIn(util.build_cache_key('anonymous_topic_views', topic_id=self.topic.id), cache)
        url = self.topic.get_absolute_url()
        self.client.get(url)
        self.assertEqual(cache.get(util.build_cache_key('anonymous_topic_views', topic_id=self.topic.id)), 1)
        for _ in range(defaults.PYBB_ANONYMOUS_VIEWS_CACHE_BUFFER - 2):
            self.client.get(url)
        self.assertEqual(Topic.objects.get(id=self.topic.id).views, 0)
        self.assertEqual(cache.get(util.build_cache_key('anonymous_topic_views', topic_id=self.topic.id)),
                         defaults.PYBB_ANONYMOUS_VIEWS_CACHE_BUFFER - 1)
        self.client.get(url)
        self.assertEqual(Topic.objects.get(id=self.topic.id).views, defaults.PYBB_ANONYMOUS_VIEWS_CACHE_BUFFER)
        self.assertEqual(cache.get(util.build_cache_key('anonymous_topic_views', topic_id=self.topic.id)), 0)

        views = Topic.objects.get(id=self.topic.id).views

        defaults.PYBB_ANONYMOUS_VIEWS_CACHE_BUFFER = None
        self.client.get(url)
        self.assertEqual(Topic.objects.get(id=self.topic.id).views, views + 1)
        self.assertEqual(cache.get(util.build_cache_key('anonymous_topic_views', topic_id=self.topic.id)), 0)

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

        response = self.create_post_via_http(self.client, topic_id=self.topic.id,
                                             body='test premoderation')
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
        self.assertRedirects(response, settings.LOGIN_URL + '?next=%s' % post.get_absolute_url())
        response = client.get(self.topic.get_absolute_url(), follow=True)
        self.assertNotContains(response, 'test premoderation')

        # But visible by superuser (with permissions)
        user = User.objects.create_user('admin', 'admin@localhost', 'admin')
        user.is_superuser = True
        user.save()
        client.login(username='admin', password='admin')
        response = client.get(post.get_absolute_url(), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test premoderation')

        # user with names stats with allowed can post without premoderation
        user = User.objects.create_user('allowed_zeus', 'allowed_zeus@localhost', 'allowed_zeus')
        client.login(username='allowed_zeus', password='allowed_zeus')
        response = self.create_post_via_http(client, topic_id=self.topic.id,
                                             body='test premoderation staff')
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
        response = self.create_post_via_http(self.client, forum_id=self.forum.id,
                                             body='new topic test', name='new topic name', poll_type=0)
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
        self.file_name = os.path.join(os.path.dirname(__file__), 'static', 'pybb', 'img', 'attachment.png')
        self.create_user()
        self.create_initial()

    def test_attachment_one(self):
        self.login_client()
        with open(self.file_name, 'rb') as fp:
            response = self.create_post_via_http(self.client, topic_id=self.topic.id,
                                                 **{'body': 'test attachment',
                                                    'attachments-0-file': fp})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Post.objects.filter(body='test attachment').exists())
        post = Post.objects.filter(body='test attachment')[0]
        self.assertEqual(post.attachments.count(), 1)

    def test_attachment_two(self):
        self.login_client()
        with open(self.file_name, 'rb') as fp:
            with self.assertRaises(ValidationError):
                self.create_post_via_http(self.client, topic_id=self.topic.id,
                                          **{'body': 'test attachment',
                                             'attachments-0-file': fp,
                                             'attachments-INITIAL_FORMS': None,
                                             'attachments-TOTAL_FORMS': None,})

    def test_attachment_usage(self):
        self.login_client()
        body = (
            'test attachment: '
            '[img][file-1][/img]'
            '[img][file-2][/img]'
            '[img][file-1][/img]'
            '[file-3]'
            '[file-a]'
        )
        with open(self.file_name, 'rb') as fp, open(self.file_name, 'rb') as fp2:
            response = self.create_post_via_http(self.client, topic_id=self.topic.id,
                                                 **{'body': body,
                                                    'attachments-0-file': fp,
                                                    'attachments-1-file': fp2,
                                                    'attachments-TOTAL_FORMS': 2,})
        self.assertEqual(response.status_code, 200)
        post = response.context['post']
        imgs = html.fromstring(post.body_html).xpath('//img')
        self.assertEqual(len(imgs), 3)
        self.assertTrue('[file-3]' in post.body_html)
        self.assertTrue('[file-a]' in post.body_html)

        src1 = imgs[0].attrib.get('src')
        src2 = imgs[1].attrib.get('src')
        src3 = imgs[2].attrib.get('src')
        attachments = [a for a in post.attachments.order_by('pk')]
        self.assertEqual(src1, attachments[0].file.url)
        self.assertEqual(src2, attachments[1].file.url)
        self.assertEqual(src1, src3)

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
        self.login_client()
        values = {}
        values['body'] = 'test poll body'
        values['name'] = 'test poll name'
        values['poll_type'] = 0 # poll_type = None, create topic without poll answers
        values['poll_question'] = 'q1'
        values['poll_answers-0-text'] = 'answer1'
        values['poll_answers-1-text'] = 'answer2'
        values['poll_answers-TOTAL_FORMS'] = 2
        response = self.create_post_via_http(self.client, forum_id=self.forum.id, **values)
        self.assertEqual(response.status_code, 200)
        new_topic = Topic.objects.get(name='test poll name')
        self.assertIsNone(new_topic.poll_question)
        self.assertFalse(PollAnswer.objects.filter(topic=new_topic).exists()) # no answers here

        values['name'] = 'test poll name 1'
        values['poll_type'] = 1
        values['poll_answers-0-text'] = 'answer1' # not enough answers
        values['poll_answers-TOTAL_FORMS'] = 1
        response = self.create_post_via_http(self.client, forum_id=self.forum.id, **values)
        self.assertFalse(Topic.objects.filter(name='test poll name 1').exists())

        values['name'] = 'test poll name 1'
        values['poll_type'] = 1
        values['poll_answers-0-text'] = 'answer1' # too many answers
        values['poll_answers-1-text'] = 'answer2'
        values['poll_answers-2-text'] = 'answer3'
        values['poll_answers-TOTAL_FORMS'] = 3
        response = self.create_post_via_http(self.client, forum_id=self.forum.id, **values)
        self.assertFalse(Topic.objects.filter(name='test poll name 1').exists())

        values['name'] = 'test poll name 1'
        values['poll_type'] = 1 # poll type = single choice, create answers
        values['poll_question'] = 'q1'
        values['poll_answers-0-text'] = 'answer1' # two answers - what do we need to create poll
        values['poll_answers-1-text'] = 'answer2'
        values['poll_answers-TOTAL_FORMS'] = 2
        response = self.create_post_via_http(self.client, forum_id=self.forum.id, **values)
        self.assertEqual(response.status_code, 200)
        new_topic = Topic.objects.get(name='test poll name 1')
        self.assertEqual(new_topic.poll_question, 'q1')
        self.assertEqual(PollAnswer.objects.filter(topic=new_topic).count(), 2)

    def test_regression_adding_poll_with_removed_answers(self):
        self.login_client()
        values = {}
        values['body'] = 'test poll body'
        values['name'] = 'test poll name'
        values['poll_type'] = 1
        values['poll_question'] = 'q1'
        values['poll_answers-0-text'] = ''
        values['poll_answers-0-DELETE'] = 'on'
        values['poll_answers-1-text'] = ''
        values['poll_answers-1-DELETE'] = 'on'
        values['poll_answers-TOTAL_FORMS'] = 2
        response = self.create_post_via_http(self.client, forum_id=self.forum.id, **values)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Topic.objects.filter(name='test poll name').exists())

    def test_regression_poll_deletion_after_second_post(self):
        self.login_client()
        values = {}
        values['body'] = 'test poll body'
        values['name'] = 'test poll name'
        values['poll_type'] = 1 # poll type = single choice, create answers
        values['poll_question'] = 'q1'
        values['poll_answers-0-text'] = 'answer1' # two answers - what do we need to create poll
        values['poll_answers-1-text'] = 'answer2'
        values['poll_answers-TOTAL_FORMS'] = 2
        response = self.create_post_via_http(self.client, forum_id=self.forum.id, **values)
        self.assertEqual(response.status_code, 200)
        new_topic = Topic.objects.get(name='test poll name')
        self.assertEqual(new_topic.poll_question, 'q1')
        self.assertEqual(PollAnswer.objects.filter(topic=new_topic).count(), 2)

        response = self.create_post_via_http(self.client, topic_id=new_topic.id,
                                             body='test answer body')
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
        self.assertEqual(response.status_code, 403) # bad request status

        recreate_poll(poll_type=Topic.POLL_TYPE_MULTIPLE)
        values = {'answers': [a.id for a in PollAnswer.objects.all()]}
        response = self.client.post(vote_url, data=values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertListEqual([a.votes() for a in PollAnswer.objects.all()], [1, 1])
        self.assertListEqual([a.votes_percent() for a in PollAnswer.objects.all()], [50.0, 50.0])

        response = self.client.post(vote_url, data=values, follow=True)
        self.assertEqual(response.status_code, 403)  # already voted

        cancel_vote_url = reverse('pybb:topic_cancel_poll_vote', kwargs={'pk': self.topic.id})
        response = self.client.post(cancel_vote_url, data=values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertListEqual([a.votes() for a in PollAnswer.objects.all()], [0, 0])
        self.assertListEqual([a.votes_percent() for a in PollAnswer.objects.all()], [0, 0])

        response = self.client.post(vote_url, data=values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertListEqual([a.votes() for a in PollAnswer.objects.all()], [1, 1])
        self.assertListEqual([a.votes_percent() for a in PollAnswer.objects.all()], [50.0, 50.0])

    def test_poll_voting_on_closed_topic(self):
        self.login_client()
        self.topic.poll_type = Topic.POLL_TYPE_SINGLE
        self.topic.save()
        PollAnswer.objects.create(topic=self.topic, text='answer1')
        PollAnswer.objects.create(topic=self.topic, text='answer2')
        self.topic.closed = True
        self.topic.save()

        vote_url = reverse('pybb:topic_poll_vote', kwargs={'pk': self.topic.id})
        my_answer = PollAnswer.objects.all()[0]
        values = {'answers': my_answer.id}
        response = self.client.post(vote_url, data=values, follow=True)
        self.assertEqual(response.status_code, 403)

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
        values['body'] = 'test\n \n \n\nmultiple empty lines\n'
        response = self.client.post(add_post_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.all()[0].body, 'test\nmultiple empty lines')


class CustomPermissionHandler(permissions.DefaultPermissionHandler):
    """
    a custom permission handler which changes the meaning of "hidden" forum:
    "hidden" forum or category is visible for all logged on users, not only staff
    """

    def filter_categories(self, user, qs):
        return qs.filter(hidden=False) if is_anonymous(user) else qs

    def may_view_category(self, user, category):
        return is_authenticated(user) if category.hidden else True

    def filter_forums(self, user, qs):
        if is_anonymous(user):
            qs = qs.filter(Q(hidden=False) & Q(category__hidden=False))
        return qs

    def may_view_forum(self, user, forum):
        return is_authenticated(user) if forum.hidden or forum.category.hidden else True

    def filter_topics(self, user, qs):
        if is_anonymous(user):
            qs = qs.filter(Q(forum__hidden=False) & Q(forum__category__hidden=False))
        qs = qs.filter(closed=False)  # filter out closed topics for test
        return qs

    def may_view_topic(self, user, topic):
        return self.may_view_forum(user, topic.forum)

    def filter_posts(self, user, qs):
        if is_anonymous(user):
            qs = qs.filter(Q(topic__forum__hidden=False) & Q(topic__forum__category__hidden=False))
        return qs

    def may_view_post(self, user, post):
        return self.may_view_forum(user, post.topic.forum)

    def may_create_poll(self, user):
        return False

    def may_edit_topic_slug(self, user):
        return True

    def may_change_forum(self, user, forum):
        return not forum.pk % 3 == 0

class MarkupParserTest(TestCase, SharedTestModule):

    def setUp(self):
        # Reinit Engines because they are stored in memory and the current bbcode engine stored
        # may be the old one, depending the test order exec.
        self.ORIG_PYBB_MARKUP_ENGINES = util.PYBB_MARKUP_ENGINES
        self.ORIG_PYBB_QUOTE_ENGINES = util.PYBB_QUOTE_ENGINES
        util.PYBB_MARKUP_ENGINES = {
            'bbcode': 'pybb.markup.bbcode.BBCodeParser',  # default parser
            'bbcode_custom': 'test_project.markup_parsers.CustomBBCodeParser',  # overrided default parser
            'liberator': 'test_project.markup_parsers.LiberatorParser',  # completely new parser
            'fake': 'pybb.markup.base.BaseParser',  # base parser
            'markdown': defaults.markdown  # old-style callable parser,
        }
        util.PYBB_QUOTE_ENGINES = {
            'bbcode': 'pybb.markup.bbcode.BBCodeParser',  # default parser
            'bbcode_custom': 'test_project.markup_parsers.CustomBBCodeParser',  # overrided default parser
            'liberator': 'test_project.markup_parsers.LiberatorParser',  # completely new parser
            'fake': 'pybb.markup.base.BaseParser',  # base parser
            'markdown': lambda text, username="": '>' + text.replace('\n', '\n>').replace('\r', '\n>') + '\n'  # old-style callable parser
        }

    def tearDown(self):
        util._MARKUP_ENGINES = {}
        util._QUOTE_ENGINES = {}
        util.PYBB_MARKUP_ENGINES = self.ORIG_PYBB_MARKUP_ENGINES
        util.PYBB_QUOTE_ENGINES = self.ORIG_PYBB_QUOTE_ENGINES

    def test_markup_engines(self):

        def _test_engine(parser_name, text_to_html_map):
            for item in text_to_html_map:
                self.assertIn(util._get_markup_formatter(parser_name)(item[0]), item[1:])

        text_to_html_map = [
            ['[b]bold[/b]', '<strong>bold</strong>'],
            ['[i]italic[/i]', '<em>italic</em>'],
            ['[u]underline[/u]', '<u>underline</u>'],
            ['[s]striked[/s]', '<strike>striked</strike>'],
            [
                '[img]http://domain.com/image.png[/img]',
                '<img src="http://domain.com/image.png"></img>',
                '<img src="http://domain.com/image.png">'
            ],
            ['[url=google.com]search in google[/url]', '<a href="http://google.com">search in google</a>'],
            ['http://google.com', '<a href="http://google.com">http://google.com</a>'],
            ['[list][*]1[*]2[/list]', '<ul><li>1</li><li>2</li></ul>'],
            [
                '[list=1][*]1[*]2[/list]',
                '<ol><li>1</li><li>2</li></ol>',
                '<ol style="list-style-type:decimal;"><li>1</li><li>2</li></ol>'
            ],
            ['[quote="post author"]quote[/quote]', '<blockquote><em>post author</em><br>quote</blockquote>'],
            [
                '[code]code[/code]',
                '<div class="code"><pre>code</pre></div>',
                '<pre><code>code</code></pre>']
            ,
        ]
        _test_engine('bbcode', text_to_html_map)

        text_to_html_map = text_to_html_map + [
            ['[ul][li]1[/li][li]2[/li][/ul]', '<ul><li>1</li><li>2</li></ul>'],
            [
                '[youtube]video_id[/youtube]',
                (
                    '<iframe src="http://www.youtube.com/embed/video_id?wmode=opaque" '
                    'data-youtube-id="video_id" allowfullscreen="" frameborder="0" '
                    'height="315" width="560"></iframe>'
                )
            ],
        ]
        _test_engine('bbcode_custom', text_to_html_map)

        text_to_html_map = [
            ['Windows and Mac OS are wonderfull OS !', 'GNU Linux and FreeBSD are wonderfull OS !'],
            ['I love PHP', 'I love Python'],
        ]
        _test_engine('liberator', text_to_html_map)

        text_to_html_map = [
            ['[b]bold[/b]', '[b]bold[/b]'],
            ['*italic*', '*italic*'],
        ]
        _test_engine('fake', text_to_html_map)
        _test_engine('not_existent', text_to_html_map)

        text_to_html_map = [
            ['**bold**', '<p><strong>bold</strong></p>'],
            ['*italic*', '<p><em>italic</em></p>'],
            [
                '![alt text](http://domain.com/image.png "title")',
                '<p><img alt="alt text" src="http://domain.com/image.png" title="title" /></p>'
            ],
            [
                '[search in google](https://www.google.com)',
                '<p><a href="https://www.google.com">search in google</a></p>'
            ],
            [
                '[google] some text\n[google]: https://www.google.com',
                '<p><a href="https://www.google.com">google</a> some text</p>'
            ],
            ['* 1\n* 2', '<ul>\n<li>1</li>\n<li>2</li>\n</ul>'],
            ['1. 1\n2. 2', '<ol>\n<li>1</li>\n<li>2</li>\n</ol>'],
            ['> quote', '<blockquote>\n<p>quote</p>\n</blockquote>'],
            ['```\ncode\n```', '<p><code>code</code></p>'],
        ]
        _test_engine('markdown', text_to_html_map)

    def test_quote_engines(self):

        def _test_engine(parser_name, text_to_quote_map):
            for item in text_to_quote_map:
                self.assertEqual(util._get_markup_quoter(parser_name)(item[0]), item[1])
                self.assertEqual(util._get_markup_quoter(parser_name)(item[0], 'username'), item[2])

        text_to_quote_map = [
            ['quote text', '[quote=""]quote text[/quote]\n', '[quote="username"]quote text[/quote]\n']
        ]
        _test_engine('bbcode', text_to_quote_map)
        _test_engine('bbcode_custom', text_to_quote_map)

        text_to_quote_map = [
            ['quote text', 'quote text', 'posted by: username\nquote text']
        ]
        _test_engine('liberator', text_to_quote_map)

        text_to_quote_map = [
            ['quote text', 'quote text', 'quote text']
        ]
        _test_engine('fake', text_to_quote_map)
        _test_engine('not_existent', text_to_quote_map)

        text_to_quote_map = [
            ['quote\r\ntext', '>quote\n>\n>text\n', '>quote\n>\n>text\n']
        ]
        _test_engine('markdown', text_to_quote_map)

    def test_body_cleaners(self):
        user = User.objects.create_user('zeus', 'zeus@localhost', 'zeus')
        staff = User.objects.create_user('staff', 'staff@localhost', 'staff')
        staff.is_staff = True
        staff.save()

        from pybb.markup.base import rstrip_str
        cleaners_map = [
            ['pybb.markup.base.filter_blanks', 'some\n\n\n\ntext\n\nwith\nnew\nlines', 'some\ntext\n\nwith\nnew\nlines'],
            [rstrip_str, 'text    \n    \nwith whitespaces     ', 'text\n\nwith whitespaces'],
        ]
        for cleaner, source, dest in cleaners_map:
            self.assertEqual(util.get_body_cleaner(cleaner)(user, source), dest)
            self.assertEqual(util.get_body_cleaner(cleaner)(staff, source), dest)


def _attach_perms_class(class_name):
    """
    override the permission handler. this cannot be done with @override_settings as
    permissions.perms is already imported at import point, instead we got to monkeypatch
    the modules (not really nice, but only an issue in tests)
    """
    pybb_views.perms = permissions.perms = util.resolve_class(class_name)


def _detach_perms_class():
    """
    reset permission handler (otherwise other tests may fail)
    """
    pybb_views.perms = permissions.perms = util.resolve_class('pybb.permissions.DefaultPermissionHandler')


class ControlsAndPermissionsTest(TestCase, SharedTestModule):

    def create_initial(self, on_moderation=False, closed=False, sticky=False, hidden=False):
        """
        * forum1: normal
            * topic1_1: normal
                * post1_1_1: alice
                * post1_1_2: bob
                * post1_1_3: alice + on_moderation
            * topic1_2: on_moderation
                * post1_2_1: alice + on_moderation
            * topic1_3: on_moderation (topic has been marked as waiting for a global moderation)
                * post1_3_1: alice
                * post1_3_2: bob + on_moderation
            * topic1_4: closed
                * post1_4_1: alice
                * post1_4_2: bob
            * topic1_5: sticky
                * post1_5_1: alice
                * post1_5_2: bob
        * forum2: hidden
            * topic2_1: normal
                * post2_1_1: alice
                * post2_1_2: bob
        """
        topics = []
        alice = User.objects.create_user('alice', 'alice@localhost', 'alice')
        bob = User.objects.create_user('bob', 'bob@localhost', 'bob')
        category = Category.objects.create(name='test')
        forum1 = Forum.objects.create(name='forum 1', description='bar 1', category=category)
        topic1_1 = Topic.objects.create(name='topic 1_1', forum=forum1, user=alice)
        topics.append(topic1_1)
        self.create_post(topic=topic1_1, user=alice, body='post 1_1 1')
        self.create_post(topic=topic1_1, user=bob, body='post 1_1_2')

        if on_moderation:
            self.create_post(topic=topic1_1, user=alice, body='post 1_1_3', on_moderation=True)
            topic1_2 = Topic.objects.create(name='topic 1_2', forum=forum1, user=alice,
                                            on_moderation=True)
            topics.append(topic1_2)
            self.create_post(topic=topic1_2, user=alice, body='post 1_2_1', on_moderation=True)
            topic1_3 = Topic.objects.create(name='topic 1_3', forum=forum1, user=alice, )
            topics.append(topic1_3)
            self.create_post(topic=topic1_3, user=alice, body='post 1_3_1')
            self.create_post(topic=topic1_3, user=bob, body='post 1_3_2', on_moderation=True)
            topic1_3.on_moderation = True
            topic1_3.save()

        if closed:
            topic1_4 = Topic.objects.create(name='topic 1_4', forum=forum1, user=alice, closed=True)
            topics.append(topic1_4)
            self.create_post(topic=topic1_4, user=alice, body='post 1_4_1')
            self.create_post(topic=topic1_4, user=bob, body='post 1_4_2')

        if sticky:
            topic1_5 = Topic.objects.create(name='topic 1_5', forum=forum1, user=alice, sticky=True)
            topics.append(topic1_5)
            self.create_post(topic=topic1_5, user=alice, body='post 1_5_1')
            self.create_post(topic=topic1_5, user=bob, body='post 1_5_2')

        if hidden:
            forum2 = Forum.objects.create(name='forum 2', description='bar 2', category=category,
                                          hidden=True)
            topic2_1 = Topic.objects.create(name='topic 2_1', forum=forum2, user=alice)
            topics.append(topic2_1)
            self.create_post(topic=topic2_1, user=alice, body='post 2_1_1')
            self.create_post(topic=topic2_1, user=bob, body='post 2_1_2')
        return topics

    @skip("Run this test manually")
    def test_permission_documentation(self):
        topics = self.create_initial(on_moderation=True, closed=True, sticky=True, hidden=True)
        forum = topics[0].forum
        hidden_forum = topics[-1].forum
        closed_topic = Topic.objects.get(name='topic 1_4')
        author_topic = topics[0]
        author_post = topics[0].head
        other_post = topics[0].posts.exclude(user=author_post.user).first()
        author = author_post.user
        other = other_post.user
        author_on_moderation_post = topics[0].last_post
        author_on_moderation_topic = topics[1]
        other_on_moderation_post = Post.objects.get(body='post 1_3_2')
        other_on_moderation_topic = Topic.objects.create(name='topic 1_6', forum=forum, user=other,
                                                         on_moderation=True)
        self.create_post(topic=other_on_moderation_topic, user=other, body='post 1_6_1',
                         on_moderation=True)
        other_topic = Topic.objects.create(name='topic 1_7', forum=forum, user=other, )
        self.create_post(topic=other_topic, user=other, body='post 1_7_1')

        def _view_normal_forum(user):
            return permissions.perms.may_view_forum(user, forum)

        def _view_hidden_forum(user):
            return permissions.perms.may_view_forum(user, hidden_forum)

        def _view_other_topic(user):
            return permissions.perms.may_view_topic(user, other_topic)

        def _view_other_post(user):
            return permissions.perms.may_view_post(user, other_post)

        def _view_own_on_moderation_topic(user):
            if not is_anonymous(user) and author_on_moderation_topic.user.pk == user.pk:
                return permissions.perms.may_view_topic(user, author_on_moderation_topic)

        def _view_own_on_moderation_post(user):
            if not is_anonymous(user) and author_on_moderation_post.user.pk == user.pk:
                return permissions.perms.may_view_post(user, author_on_moderation_post)

        def _view_other_on_moderation_topic(user):
            return permissions.perms.may_view_topic(user, other_on_moderation_topic)

        def _view_other_on_moderation_post(user):
            return permissions.perms.may_view_post(user, other_on_moderation_post)

        def _add_post_in_normal_topic(user):
            return permissions.perms.may_create_post(user, other_topic)

        def _add_post_in_on_moderation_topic(user):
            return permissions.perms.may_create_post(user, author_on_moderation_topic)

        def _add_post_in_closed_topic(user):
            return permissions.perms.may_create_post(user, closed_topic)

        def _edit_own_normal_post(user):
            if not is_anonymous(user) and author_on_moderation_post.user.pk == user.pk:
                return permissions.perms.may_edit_post(user, author_post)

        def _edit_own_on_moderation_post(user):
            if not is_anonymous(user) and author_on_moderation_post.user.pk == user.pk:
                return permissions.perms.may_edit_post(user, author_on_moderation_post)

        def _edit_other_post(user):
            return permissions.perms.may_edit_post(user, other_post)

        def _delete_own_normal_post(user):
            if not is_anonymous(user) and author_on_moderation_post.user.pk == user.pk:
                return permissions.perms.may_delete_post(user, author_post)

        def _delete_own_on_moderation_post(user):
            if not is_anonymous(user) and author_on_moderation_post.user.pk == user.pk:
                return permissions.perms.may_delete_post(user, author_on_moderation_post)

        def _delete_other_post(user):
            return permissions.perms.may_delete_post(user, other_post)

        def _moderate_topic(user):
            return permissions.perms.may_moderate_topic(user, author_topic)

        def _close_and_unclose_topic(user):
            return permissions.perms.may_close_topic(user, author_topic)

        def _stick_and_unstick_topic(user):
            return permissions.perms.may_stick_topic(user, author_topic)

        def _manage_moderators(user):
            return permissions.perms.may_manage_moderators(user)

        tests = [
            _view_normal_forum,
            _view_hidden_forum,
            _view_other_topic,
            _view_other_post,
            _view_own_on_moderation_topic,
            _view_own_on_moderation_post,
            _view_other_on_moderation_topic,
            _view_other_on_moderation_post,
            _add_post_in_normal_topic,
            _add_post_in_on_moderation_topic,
            _add_post_in_closed_topic,
            _edit_own_normal_post,
            _edit_own_on_moderation_post,
            _edit_other_post,
            _delete_own_normal_post,
            _delete_own_on_moderation_post,
            _delete_other_post,
            _close_and_unclose_topic,
            _stick_and_unstick_topic,
            _manage_moderators,
        ]

        # get permissions
        change_topic_perm = Permission.objects.get_by_natural_key('change_topic', 'pybb', 'topic')
        delete_topic_perm = Permission.objects.get_by_natural_key('delete_topic', 'pybb', 'topic')
        change_post_perm = Permission.objects.get_by_natural_key('change_post', 'pybb', 'post')
        delete_post_perm = Permission.objects.get_by_natural_key('delete_post', 'pybb', 'post')

        # init all users
        anonymous = AnonymousUser()
        redactor = User.objects.create_user('redactor', 'redactor', 'redactor@localhost')
        redactor.is_staff = True
        redactor.save()
        moderator = User.objects.create_user('moderator', 'moderator', 'moderator@localhost')
        moderator.save()
        forum.moderators.add(moderator)
        hidden_forum.moderators.add(moderator)
        manager = User.objects.create_user('manager', 'manager', 'manager@localhost')
        manager.is_staff = True
        manager.save()
        manager.user_permissions.add(change_topic_perm, change_post_perm,
                                     delete_topic_perm, delete_post_perm)
        superuser = User.objects.create_user('superuser', 'superuser', 'superuser@localhost')
        superuser.is_superuser = True
        superuser.save()

        users = [
            (anonymous, 'Permissions for anonymous'),
            (author, 'Permissions for an logged-in user'),
            (moderator, 'Permissions for a moderator of the current forum'),
            (redactor, 'Permissions for a "is_staff" user without pybb permissions'),
            (manager, 'Permissions for a "is_staff" user with pybb permissions'),
            (superuser, 'Permissions for superuser'),
        ]

        # get the current documentation for permissions
        path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'permissions.rst')
        permission_doc = open(path, 'r').read()
        wrong_parts = []
        sep = '+----------------------------------+---------------------+---------------------+'
        intro = [
            '%(title)s:', '',
            sep,
            '|              action              |     can do with     |     can do with     |',
            '|                                  | PREMODERATION False | PREMODERATION True  |',
            '+==================================+=====================+=====================+',]

        ORIG = defaults.PYBB_PREMODERATION
        def fake_premoderation(user, body):
            return True

        for user, title in users:
            lines = ['\n'.join(intro) % {'title': title}]
            for test in tests:
                name = test.__name__.replace('_', ' ').strip()
                name += ' ' * (32 - len(name))
                results = []
                for value in (None, fake_premoderation):
                    defaults.PYBB_PREMODERATION = value
                    result = test(user)
                    if result is None:
                        result = 'see logged-in user'
                    else:
                        result = 'yes' if result else 'no'
                    result += ' ' * (19 - len(result))
                    results.append(result)
                lines.append('| %s | %s | %s |' % (name, results[0], results[1]))
                lines.append(sep)

            permission_doc_part = '\n'.join(lines)
            # Check that documentation is correct with reality
            # (maybe reality is not good, but it's not the purpose of this test)
            if permission_doc_part not in permission_doc:
                wrong_parts.append(permission_doc_part)

        if wrong_parts:
            self.fail('Permission document does not reflect what default Permission handler do. '
                      'If other permission tests success, please update the documentation with '
                      'those parts:\n\n%s' % '\n\n\n'.join(wrong_parts))

        defaults.PYBB_PREMODERATION = ORIG


    def test_may_create_post(self):
        topics = self.create_initial(on_moderation=True, closed=True, sticky=True, hidden=True)
        anonymous = AnonymousUser()
        alice = topics[0].user
        other = User.objects.create_user('other', 'other@localhost', 'other',)
        redactor = User.objects.create_user('redactor', 'redactor', 'redactor@localhost')
        redactor.is_staff = True
        redactor.save()
        moderator = User.objects.create_user('moderator', 'moderator', 'moderator@localhost')
        moderator.save()
        topics[0].forum.moderators.add(moderator)
        manager = User.objects.create_user('manager', 'manager', 'manager@localhost')
        manager.is_staff = True
        manager.save()
        change_topic_perm = Permission.objects.get_by_natural_key('change_topic', 'pybb', 'topic')
        change_post_perm = Permission.objects.get_by_natural_key('change_post', 'pybb', 'post')
        manager.user_permissions.add(change_topic_perm, change_post_perm)
        superuser = User.objects.create_user('superuser', 'superuser', 'superuser@localhost')
        superuser.is_superuser = True
        superuser.save()

        forum1, forum2 = topics[0].forum,  topics[-1].forum
        normal_topics = Topic.objects.filter(forum__hidden=False, forum__category__hidden=False,
                                             on_moderation=False, closed=False)
        on_moderation_topics = Topic.objects.filter(on_moderation=True)
        closed_topics = Topic.objects.filter(closed=True)
        hidden_topics = Topic.objects.filter(forum__hidden=True, forum__category__hidden=True)

        for topic in topics:
            if not permissions.perms.may_create_post(superuser, topic):
                self.fail('%s may create post in topic %s' % (superuser, topic))
            if not permissions.perms.may_create_post(manager, topic):
                self.fail('%s may create post in topic %s' % (manager, topic))
            if permissions.perms.may_create_post(anonymous, topic):
                self.fail('%s may NOT create post in topic %s' % (anonymous, topic))
            if topic.forum.pk != forum1.pk:
                if permissions.perms.may_create_post(moderator, topic):
                    self.fail('%s may NOT create post in topic %s' % (moderator, topic))
            else:
                if not permissions.perms.may_create_post(moderator, topic):
                    self.fail('%s may create post in topic %s' % (moderator, topic))

        for topic in normal_topics:
            if not permissions.perms.may_create_post(redactor, topic):
                self.fail('%s may create post in topic %s' % (redactor, topic))
            if not permissions.perms.may_create_post(other, topic):
                self.fail('%s may create post in topic %s' % (other, topic))

        for topic in on_moderation_topics:
            if permissions.perms.may_create_post(other, topic):
                self.fail('%s may NOT create post in topic %s' % (other, topic))
            if permissions.perms.may_create_post(alice, topic):
                self.fail('%s may NOT create post in topic %s' % (alice, topic))
            if permissions.perms.may_create_post(redactor, topic):
                self.fail('%s may NOT create post in topic %s' % (redactor, topic))

        for topic in closed_topics:
            if permissions.perms.may_create_post(anonymous, topic):
                self.fail('%s may NOT create post in topic %s' % (anonymous, topic))
            if permissions.perms.may_create_post(alice, topic):
                self.fail('%s may NOT create post in topic %s' % (alice, topic))
            if permissions.perms.may_create_post(redactor, topic):
                self.fail('%s may NOT create post in topic %s' % (redactor, topic))

        for topic in hidden_topics:
            if topic.on_moderation or topic.closed:
                if permissions.perms.may_create_post(redactor, topic):
                    self.fail('%s may NOT create post in topic %s' % (redactor, topic))
            else:
                if not permissions.perms.may_create_post(redactor, topic):
                    self.fail('%s may create post in topic %s' % (redactor, topic))
            if permissions.perms.may_create_post(alice, topic):
                self.fail('%s may NOT create post in topic %s' % (alice, topic))


    def test_filter_topics_anonymous_and_other(self):
        self.create_initial(on_moderation=True, closed=True, sticky=True, hidden=True)
        topics = Topic.objects.values_list('name', flat=True)
        anonymous = AnonymousUser()
        other = User.objects.create_user('other', 'other@localhost', 'other',)

        # even without premoderation, on_moderation mark must be significative on topics
        ORIG = defaults.PYBB_PREMODERATION
        defaults.PYBB_PREMODERATION = None

        excluded_topics = ['topic 1_2', 'topic 1_3', 'topic 2_1']
        expected_topics = topics.exclude(name__in=excluded_topics)

        anonymous_filtered_topics = permissions.perms.filter_topics(anonymous, topics)
        self.assertEqual(set(expected_topics), set(anonymous_filtered_topics))

        other_filtered_topics = permissions.perms.filter_topics(other, topics)
        self.assertEqual(set(expected_topics), set(other_filtered_topics))

        for topic in Topic.objects.filter(name__in=expected_topics):
            if not permissions.perms.may_view_topic(anonymous, topic):
                self.fail('%s may view topic %s' % (anonymous, topic))
            if not permissions.perms.may_view_topic(other, topic):
                self.fail('%s may view topic %s' % (other, topic))

        for topic in Topic.objects.exclude(name__in=expected_topics):
            if permissions.perms.may_view_topic(anonymous, topic):
                self.fail('%s may NOT view topic %s' % (anonymous, topic))
            if permissions.perms.may_view_topic(other, topic):
                self.fail('%s may NOT view topic %s' % (other, topic))
        defaults.PYBB_PREMODERATION = ORIG

    def test_filter_posts_anonymous_and_other(self):
        self.create_initial(on_moderation=True, closed=True, sticky=True, hidden=True)
        posts = Post.objects.values_list('body', flat=True)
        anonymous = AnonymousUser()
        other = User.objects.create_user('other', 'other@localhost', 'other',)

        ORIG = defaults.PYBB_PREMODERATION
        defaults.PYBB_PREMODERATION = None
        # "post 1_1_3" is not excluded because PYBB_PREMODERATION is not set, so on_moderation on
        # posts are ignored
        # same reason for "post 1_2_1", 1_3_1 and 1_3_2
        excluded_posts = ['post 2_1_1', 'post 2_1_2']  # exclude hidden forum posts
        expected_posts = posts.exclude(body__in=excluded_posts)

        anonymous_filtered_posts = permissions.perms.filter_posts(anonymous, posts)
        self.assertEqual(set(expected_posts), set(anonymous_filtered_posts))

        other_filtered_posts = permissions.perms.filter_posts(other, posts)
        self.assertEqual(set(expected_posts), set(other_filtered_posts))

        for post in Post.objects.filter(body__in=expected_posts):
            if not permissions.perms.may_view_post(anonymous, post):
                self.fail('%s may view post %s' % (anonymous, post))
            if not permissions.perms.may_view_post(other, post):
                self.fail('%s may view post %s' % (other, post))

        for post in Post.objects.exclude(body__in=expected_posts):
            if permissions.perms.may_view_post(anonymous, post):
                self.fail('%s may NOT view post %s' % (anonymous, post))
            if permissions.perms.may_view_post(other, post):
                self.fail('%s may NOT view post %s' % (other, post))

        # now, test with PREMODERATION
        def fake_premoderation(user, body):
            return True
        defaults.PYBB_PREMODERATION = fake_premoderation

        # also exclude on_moderation posts or on_moderation topic
        excluded_posts += ['post 1_1_3', 'post 1_2_1', 'post 1_3_1', 'post 1_3_2']
        expected_posts = posts.exclude(body__in=excluded_posts)

        anonymous_filtered_posts = permissions.perms.filter_posts(anonymous, posts)
        self.assertEqual(set(expected_posts), set(anonymous_filtered_posts))

        other_filtered_posts = permissions.perms.filter_posts(other, posts)
        self.assertEqual(set(expected_posts), set(other_filtered_posts))

        for post in Post.objects.filter(body__in=expected_posts):
            if not permissions.perms.may_view_post(anonymous, post):
                self.fail('%s may view post %s' % (anonymous, post))
            if not permissions.perms.may_view_post(other, post):
                self.fail('%s may view post %s' % (other, post))

        for post in Post.objects.exclude(body__in=expected_posts):
            if permissions.perms.may_view_post(anonymous, post):
                self.fail('%s may NOT view post %s' % (anonymous, post))
            if permissions.perms.may_view_post(other, post):
                self.fail('%s may NOT view post %s' % (other, post))

        defaults.PYBB_PREMODERATION = ORIG

    def test_filter_topics_author(self):
        topics = self.create_initial(on_moderation=True, closed=True, sticky=True, hidden=True)
        alice = topics[0].user
        topics = Topic.objects.values_list('name', flat=True)
        # even without premoderation, on_moderation mark must be significative on topics
        ORIG = defaults.PYBB_PREMODERATION
        defaults.PYBB_PREMODERATION = None

        # "topic 1_2"is not excluded even if on_moderation because it's my own topic
        # topic 1_3 is excluded because it's a "general" moderation (ùy post is not on_moderation,
        # but the whole topic is)
        excluded_topics = ['topic 2_1', 'topic 1_3']
        expected_topics = topics.exclude(name__in=excluded_topics)

        filtered_topics = permissions.perms.filter_topics(alice, topics)
        self.assertEqual(set(expected_topics), set(filtered_topics))

        for topic in Topic.objects.filter(name__in=expected_topics):
            if not permissions.perms.may_view_topic(alice, topic):
                self.fail('%s may view topic %s' % (alice, topic))

        for topic in Topic.objects.exclude(name__in=expected_topics):
            if permissions.perms.may_view_topic(alice, topic):
                self.fail('%s may NOT view topic %s' % (alice, topic))

        defaults.PYBB_PREMODERATION = ORIG


    def test_filter_posts_author(self):
        topics = self.create_initial(on_moderation=True, closed=True, sticky=True, hidden=True)
        alice = topics[0].user
        posts = Post.objects.values_list('body', flat=True)

        ORIG = defaults.PYBB_PREMODERATION
        defaults.PYBB_PREMODERATION = None
        # "post 1_1_3" is not excluded because PYBB_PREMODERATION is not set, so on_moderation on
        # posts is ignored
        # same reason for "post 1_2_1", 1_3_1 and 1_3_2
        excluded_posts = ['post 2_1_2', ]  # exclude hidden forum posts I didn't create
        expected_posts = posts.exclude(body__in=excluded_posts)
        filtered_posts = permissions.perms.filter_posts(alice, posts)
        self.assertEqual(set(expected_posts), set(filtered_posts))

        # now, test with PREMODERATION
        def fake_premoderation(user, body):
            return True
        defaults.PYBB_PREMODERATION = fake_premoderation

        # on_moderation posts I created are not excluded ('1_1_3' and '1_2_1')
        # My posts must not be excluded even if those are in a topic which need moderation (1_3_1)
        # 1_3_2 is excluded because topic (I created) is now on_moderation. So I can't see others
        # post in this topic even if those posts are not on_moderation.
        excluded_posts += ['post 1_3_2', ]
        expected_posts = posts.exclude(body__in=excluded_posts)
        filtered_posts = permissions.perms.filter_posts(alice, posts)
        self.assertEqual(set(expected_posts), set(filtered_posts))

        for post in Post.objects.filter(body__in=expected_posts):
            if not permissions.perms.may_view_post(alice, post):
                self.fail('%s may view post %s' % (alice, post))

        for post in Post.objects.exclude(body__in=expected_posts):
            if permissions.perms.may_view_post(alice, post):
                self.fail('%s may NOT view post %s' % (alice, post))

        defaults.PYBB_PREMODERATION = ORIG


    def test_filter_topics_staff_without_perms(self):
        # redactor is a staff member (he can access to admin for SOME models, eg: News app models)
        # but he has NO rights on pybb models
        topics = self.create_initial(on_moderation=True, closed=True, sticky=True, hidden=True)
        redactor = User.objects.create_user('redactor', 'redactor', 'redactor@localhost')
        redactor.is_staff = True
        redactor.save()
        topics = Topic.objects.values_list('name', flat=True)
        # even without premoderation, on_moderation mark must be significative on topics
        ORIG = defaults.PYBB_PREMODERATION
        defaults.PYBB_PREMODERATION = None

        # same exclusions as if redactor was a "other" user except that  staff user may see
        # hidden forum/cats
        excluded_topics = ['topic 1_2', 'topic 1_3']
        expected_topics = topics.exclude(name__in=excluded_topics)

        filtered_topics = permissions.perms.filter_topics(redactor, topics)
        self.assertEqual(set(expected_topics), set(filtered_topics))

        for topic in Topic.objects.filter(name__in=expected_topics):
            if not permissions.perms.may_view_topic(redactor, topic):
                self.fail('%s may view topic %s' % (redactor, topic))

        for topic in Topic.objects.exclude(name__in=expected_topics):
            if permissions.perms.may_view_topic(redactor, topic):
                self.fail('%s may NOT view topic %s' % (redactor, topic))
        defaults.PYBB_PREMODERATION = ORIG


    def test_filter_posts_staff_without_perms(self):
        topics = self.create_initial(on_moderation=True, closed=True, sticky=True, hidden=True)
        redactor = User.objects.create_user('redactor', 'redactor', 'redactor@localhost')
        redactor.is_staff = True
        redactor.save()
        posts = Post.objects.values_list('body', flat=True)

        ORIG = defaults.PYBB_PREMODERATION
        defaults.PYBB_PREMODERATION = None
        # staff user may see hidden forum/cats
        excluded_posts = []
        expected_posts = posts.exclude(body__in=excluded_posts)
        filtered_posts = permissions.perms.filter_posts(redactor, posts)
        self.assertEqual(set(expected_posts), set(filtered_posts))

        for post in Post.objects.filter(body__in=expected_posts):
            if not permissions.perms.may_view_post(redactor, post):
                self.fail('%s may view post %s' % (redactor, post))

        for post in Post.objects.exclude(body__in=expected_posts):
            if permissions.perms.may_view_post(redactor, post):
                self.fail('%s may NOT view post %s' % (redactor, post))

        # now, test with PREMODERATION
        def fake_premoderation(user, body):
            return True
        defaults.PYBB_PREMODERATION = fake_premoderation

        # same exclusions as if redactor was a "other" user
        excluded_posts += ['post 1_1_3', 'post 1_2_1', 'post 1_3_1', 'post 1_3_2',]
        expected_posts = posts.exclude(body__in=excluded_posts)
        filtered_posts = permissions.perms.filter_posts(redactor, posts)
        self.assertEqual(set(expected_posts), set(filtered_posts))

        for post in Post.objects.filter(body__in=expected_posts):
            if not permissions.perms.may_view_post(redactor, post):
                self.fail('%s may view post %s' % (redactor, post))

        for post in Post.objects.exclude(body__in=expected_posts):
            if permissions.perms.may_view_post(redactor, post):
                self.fail('%s may NOT view post %s' % (redactor, post))

        defaults.PYBB_PREMODERATION = ORIG


    def test_filter_topics_staff_with_perms(self):
        # manager see everything
        topics = self.create_initial(on_moderation=True, closed=True, sticky=True, hidden=True)
        change_topic_perm = Permission.objects.get_by_natural_key('change_topic', 'pybb', 'topic')
        change_post_perm = Permission.objects.get_by_natural_key('change_post', 'pybb', 'post')
        manager = User.objects.create_user('manager', 'manager', 'manager@localhost')
        manager.is_staff = True
        manager.save()
        manager.user_permissions.add(change_topic_perm, change_post_perm)
        topics = Topic.objects.values_list('name', flat=True)

        expected_topics = topics
        filtered_topics = permissions.perms.filter_topics(manager, topics)
        self.assertEqual(set(expected_topics), set(filtered_topics))

        for topic in Topic.objects.filter(name__in=expected_topics):
            if not permissions.perms.may_view_topic(manager, topic):
                self.fail('%s may view topic %s' % (manager, topic))
        self.assertEqual(Topic.objects.exclude(name__in=expected_topics).count(), 0)


    def test_filter_posts_staff_with_perms(self):
        topics = self.create_initial(on_moderation=True, closed=True, sticky=True, hidden=True)
        change_topic_perm = Permission.objects.get_by_natural_key('change_topic', 'pybb', 'topic')
        change_post_perm = Permission.objects.get_by_natural_key('change_post', 'pybb', 'post')
        manager = User.objects.create_user('manager', 'manager', 'manager@localhost')
        manager.is_manager = True
        manager.save()
        manager.user_permissions.add(change_topic_perm, change_post_perm)
        posts = Post.objects.values_list('body', flat=True)

        ORIG = defaults.PYBB_PREMODERATION
        defaults.PYBB_PREMODERATION = None
        expected_posts = posts
        filtered_posts = permissions.perms.filter_posts(manager, posts)
        self.assertEqual(set(expected_posts), set(filtered_posts))

        # now, test with PREMODERATION
        def fake_premoderation(user, body):
            return True
        defaults.PYBB_PREMODERATION = fake_premoderation

        filtered_posts = permissions.perms.filter_posts(manager, posts)
        self.assertEqual(set(expected_posts), set(filtered_posts))

        for post in Post.objects.filter(body__in=expected_posts):
            if not permissions.perms.may_view_post(manager, post):
                self.fail('%s may view post %s' % (manager, post))
        self.assertEqual(Post.objects.exclude(body__in=expected_posts).count(), 0)

        defaults.PYBB_PREMODERATION = ORIG


    def test_filter_topics_superuser(self):
        # superuser see everything
        topics = self.create_initial(on_moderation=True, closed=True, sticky=True, hidden=True)
        superuser = User.objects.create_user('superuser', 'superuser', 'superuser@localhost')
        superuser.is_superuser = True
        superuser.save()
        topics = Topic.objects.values_list('name', flat=True)

        expected_topics = topics
        filtered_topics = permissions.perms.filter_topics(superuser, topics)
        self.assertEqual(set(expected_topics), set(filtered_topics))

        for topic in Topic.objects.filter(name__in=expected_topics):
            if not permissions.perms.may_view_topic(superuser, topic):
                self.fail('%s may view topic %s' % (superuser, topic))
        self.assertEqual(Topic.objects.exclude(name__in=expected_topics).count(), 0)


    def test_filter_posts_superuser(self):
        topics = self.create_initial(on_moderation=True, closed=True, sticky=True, hidden=True)
        superuser = User.objects.create_user('superuser', 'superuser', 'superuser@localhost')
        superuser.is_superuser = True
        superuser.save()
        posts = Post.objects.values_list('body', flat=True)

        ORIG = defaults.PYBB_PREMODERATION
        defaults.PYBB_PREMODERATION = None
        expected_posts = posts
        filtered_posts = permissions.perms.filter_posts(superuser, posts)
        self.assertEqual(set(expected_posts), set(filtered_posts))

        # now, test with PREMODERATION
        def fake_premoderation(user, body):
            return True
        defaults.PYBB_PREMODERATION = fake_premoderation

        filtered_posts = permissions.perms.filter_posts(superuser, posts)
        self.assertEqual(set(expected_posts), set(filtered_posts))

        for post in Post.objects.filter(body__in=expected_posts):
            if not permissions.perms.may_view_post(superuser, post):
                self.fail('%s may view post %s' % (superuser, post))
        self.assertEqual(Post.objects.exclude(body__in=expected_posts).count(), 0)

        defaults.PYBB_PREMODERATION = ORIG


    def test_post_actions_anonymous(self):
        topic1 = self.create_initial()[0]
        post1 = topic1.head
        response = self.client.get(topic1.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content)
        hrefs = tree.xpath(('//table[@id="post-%d"]'
                            '/descendant::div[@class="post-controls"]'
                            '/descendant::a/@href') % post1.pk)
        self.assertEqual(len(hrefs), 0)

    def test_post_actions_own_post(self):
        topic1, topic2 = self.create_initial(on_moderation=True)[0:2]
        post1_1 = topic1.head  # alice's post
        response = self.get_with_user(topic1.get_absolute_url(), 'alice', 'alice')
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content)
        hrefs = tree.xpath(('//table[@id="post-%d"]'
                            '/descendant::div[@class="post-controls"]'
                            '/descendant::a/@href') % post1_1.pk)
        edit_url = reverse('pybb:edit_post', kwargs={'pk': post1_1.pk})
        self.assertIn(edit_url, hrefs)
        if defaults.PYBB_ALLOW_DELETE_OWN_POST:
            delete_url = reverse('pybb:delete_post', kwargs={'pk': post1_1.pk})
            self.assertIn(delete_url, hrefs)
        self.assertTrue(len(hrefs), 1 + defaults.PYBB_ALLOW_DELETE_OWN_POST)

        # post on moderation should stay editable / deletable for it's author
        post2_1 = topic2.head  # alice's post
        response =self.get_with_user(topic2.get_absolute_url(), 'alice', 'alice')
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content)
        hrefs = tree.xpath(('//table[@id="post-%d"]'
                            '/descendant::div[@class="post-controls"]'
                            '/descendant::a/@href') % post2_1.pk)
        edit_url = reverse('pybb:edit_post', kwargs={'pk': post2_1.pk})
        self.assertIn(edit_url, hrefs)
        if defaults.PYBB_ALLOW_DELETE_OWN_POST:
            delete_url = reverse('pybb:delete_post', kwargs={'pk': post2_1.pk})
            self.assertIn(delete_url, hrefs)
        self.assertEqual(len(hrefs), 1 + defaults.PYBB_ALLOW_DELETE_OWN_POST)

    def test_post_actions_other_post(self):
        topic1 = self.create_initial()[0]
        post2 = topic1.last_post  # bob's post
        url = topic1.get_absolute_url()
        response = self.get_with_user(url, 'alice', 'alice')
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content)
        hrefs = tree.xpath(('//table[@id="post-%d"]'
                            '/descendant::div[@class="post-controls"]'
                            '/descendant::a/@href') % post2.pk)
        self.assertEqual(len(hrefs), 0)

    def test_post_actions_staff_no_perms(self):
        staff = User.objects.create_user('staff', 'staff@localhost', 'staff')
        staff.is_staff = True
        staff.save()
        topic1 = self.create_initial()[0]
        post1 = topic1.head
        response = self.get_with_user(topic1.get_absolute_url(), 'staff', 'staff')
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content)
        hrefs = tree.xpath(('//table[@id="post-%d"]'
                            '/descendant::div[@class="post-controls"]'
                            '/descendant::a/@href') % post1.pk)
        self.assertEqual(len(hrefs), 0)

    def test_post_actions_staff_with_perms(self):
        staff = User.objects.create_user('staff', 'staff@localhost', 'staff')
        staff.is_staff = True
        staff.save()
        change_topic_perm = Permission.objects.get_by_natural_key('change_topic', 'pybb', 'topic')
        delete_topic_perm = Permission.objects.get_by_natural_key('delete_topic', 'pybb', 'topic')
        change_post_perm = Permission.objects.get_by_natural_key('change_post', 'pybb', 'post')
        delete_post_perm = Permission.objects.get_by_natural_key('delete_post', 'pybb', 'post')

        staff.user_permissions.add(change_topic_perm)
        staff.user_permissions.add(change_post_perm)
        topic1, topic2 = self.create_initial(on_moderation=True)[0:2]
        post = topic2.head  # alice's post which need moderation

        topic_url = topic2.get_absolute_url()
        edit_url = reverse('pybb:edit_post', kwargs={'pk': post.pk})
        move_url = reverse('pybb:move_post', kwargs={'pk': post.pk})
        delete_url = reverse('pybb:delete_post', kwargs={'pk': post.pk})
        moderate_url = reverse('pybb:moderate_post', kwargs={'pk': post.pk})
        admin_url = reverse('admin:pybb_post_change', args=[post.pk, ])

        response = self.get_with_user(topic_url, 'staff', 'staff')
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content)
        hrefs = tree.xpath(('//table[@id="post-%d"]'
                            '/descendant::div[@class="post-controls"]'
                            '/descendant::a/@href') % post.pk)
        self.assertIn(edit_url, hrefs)
        self.assertIn(moderate_url, hrefs)
        self.assertIn(move_url, hrefs)
        self.assertIn(admin_url, hrefs)
        self.assertEqual(len(hrefs), 4)

        staff.user_permissions.add(delete_topic_perm)
        staff.user_permissions.add(delete_post_perm)
        response = self.get_with_user(topic_url, 'staff', 'staff')
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content)
        hrefs = tree.xpath(('//table[@id="post-%d"]'
                            '/descendant::div[@class="post-controls"]'
                            '/descendant::a/@href') % post.pk)
        self.assertIn(edit_url, hrefs)
        self.assertIn(moderate_url, hrefs)
        self.assertIn(admin_url, hrefs)
        self.assertIn(delete_url, hrefs)
        self.assertIn(move_url, hrefs)
        self.assertEqual(len(hrefs), 5)

    def test_post_actions_superuser(self):
        superuser = User.objects.create_user('superuser', 'superuser@localhost', 'superuser')
        superuser.is_superuser = True
        superuser.save()
        topic1, topic2 = self.create_initial(on_moderation=True)[0:2]
        post = topic2.head

        topic_url = topic2.get_absolute_url()
        edit_url = reverse('pybb:edit_post', kwargs={'pk': post.pk})
        delete_url = reverse('pybb:delete_post', kwargs={'pk': post.pk})
        move_url = reverse('pybb:move_post', kwargs={'pk': post.pk})
        moderate_url = reverse('pybb:moderate_post', kwargs={'pk': post.pk})
        admin_url = reverse('admin:pybb_post_change', args=[post.pk, ])

        response = self.get_with_user(topic2.get_absolute_url(), 'superuser', 'superuser')
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content)
        hrefs = tree.xpath(('//table[@id="post-%d"]'
                            '/descendant::div[@class="post-controls"]'
                            '/descendant::a/@href') % post.pk)
        self.assertIn(edit_url, hrefs)
        self.assertIn(moderate_url, hrefs)
        self.assertIn(admin_url, hrefs)
        self.assertIn(move_url, hrefs)
        self.assertIn(delete_url, hrefs)
        self.assertEqual(len(hrefs), 5)


    def test_post_actions_moderator(self):
        topic1, topic2 = self.create_initial(on_moderation=True)[0:2]
        forum1, post1_1_1, post1_2_1 = topic1.forum, topic1.head, topic2.head
        forum2 = Forum.objects.create(name='test 2', description='bar 2', category=forum1.category)

        moderator1 = User.objects.create_user('moderator1', 'moderator1@localhost', 'moderator1')
        moderator2 = User.objects.create_user('moderator2', 'moderator2@localhost', 'moderator2')
        forum1.moderators.add(moderator1)
        forum2.moderators.add(moderator2)

        # Alice's topic/post which does not need moderation
        topic_url = topic1.get_absolute_url()
        edit_url = reverse('pybb:edit_post', kwargs={'pk': post1_1_1.pk})
        delete_url = reverse('pybb:delete_post', kwargs={'pk': post1_1_1.pk})
        move_url = reverse('pybb:move_post', kwargs={'pk': post1_1_1.pk})
        moderate_url = reverse('pybb:moderate_post', kwargs={'pk': post1_1_1.pk})
        admin_url = reverse('admin:pybb_post_change', args=[post1_1_1.pk, ])

        # moderator1 can edit or delete alice's post which does not need moderation
        response = self.get_with_user(topic_url, 'moderator1', 'moderator1')
        tree = html.fromstring(response.content)
        self.assertEqual(response.status_code, 200)
        hrefs = tree.xpath(('//table[@id="post-%d"]'
                            '/descendant::div[@class="post-controls"]'
                            '/descendant::a/@href') % post1_1_1.pk)
        self.assertIn(edit_url, hrefs)
        self.assertIn(delete_url, hrefs)
        self.assertIn(move_url, hrefs)
        self.assertEqual(len(hrefs), 3)

        # moderator2 has not perms on alice's post because he is not moderator of this forum
        response = self.get_with_user(topic_url, 'moderator2', 'moderator2')
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content)
        hrefs = tree.xpath(('//table[@id="post-%d"]'
                            '/descendant::div[@class="post-controls"]'
                            '/descendant::a/@href') % post1_1_1.pk)
        self.assertEqual(len(hrefs), 0)


        # Alice's topic/post which need moderation
        topic_url = topic2.get_absolute_url()
        edit_url = reverse('pybb:edit_post', kwargs={'pk': post1_2_1.pk})
        delete_url = reverse('pybb:delete_post', kwargs={'pk': post1_2_1.pk})
        move_url = reverse('pybb:move_post', kwargs={'pk': post1_2_1.pk})
        moderate_url = reverse('pybb:moderate_post', kwargs={'pk': post1_2_1.pk})
        admin_url = reverse('admin:pybb_post_change', args=[post1_2_1.pk, ])

        # moderator1 can edit, approve or delete alice's post which need moderation
        response = self.get_with_user(topic_url, 'moderator1', 'moderator1')
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content)
        hrefs = tree.xpath(('//table[@id="post-%d"]'
                            '/descendant::div[@class="post-controls"]'
                            '/descendant::a/@href') % post1_2_1.pk)
        self.assertIn(edit_url, hrefs)
        self.assertIn(delete_url, hrefs)
        self.assertIn(move_url, hrefs)
        self.assertIn(moderate_url, hrefs)
        self.assertEqual(len(hrefs), 4)

        # moderator2 can not view this post because it require moderation and moderator2 is
        # not moderator of this forum
        response = self.get_with_user(topic_url, 'moderator2', 'moderator2')
        self.assertEqual(response.status_code, 403)


class CustomPermissionHandlerTest(TestCase, SharedTestModule):
    """ test custom permission handler """

    def setUp(self):
        self.create_user()
        # create public and hidden categories, forums, posts
        c_pub = Category(name='public')
        c_pub.save()
        c_hid = Category(name='private', hidden=True)
        c_hid.save()
        self.forum = Forum.objects.create(name='pub1', category=c_pub)
        Forum.objects.create(name='priv1', category=c_hid)
        Forum.objects.create(name='private_in_public_cat', hidden=True, category=c_pub)
        for f in Forum.objects.all():
            t = Topic.objects.create(name='a topic', forum=f, user=self.user)
            self.create_post(topic=t, user=self.user, body='test')
        # make some topics closed => hidden
        for t in Topic.objects.all()[0:2]:
            t.closed = True
            t.save()

        _attach_perms_class('pybb.tests.CustomPermissionHandler')

    def tearDown(self):
        _detach_perms_class()

    def test_category_permission(self):
        for c in Category.objects.all():
            # anon user may not see category
            r = self.get_with_user(c.get_absolute_url())
            if c.hidden:
                self.assertEqual(r.status_code, 302)
            else:
                self.assertEqual(r.status_code, 200)
                # logged on user may see all categories
            r = self.get_with_user(c.get_absolute_url(), 'zeus', 'zeus')
            self.assertEqual(r.status_code, 200)

    def test_forum_permission(self):
        for f in Forum.objects.all():
            r = self.get_with_user(f.get_absolute_url())
            self.assertEqual(r.status_code, 302 if f.hidden or f.category.hidden else 200)
            r = self.get_with_user(f.get_absolute_url(), 'zeus', 'zeus')
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.context['object_list'].count(), f.topics.filter(closed=False).count())

    def test_topic_permission(self):
        for t in Topic.objects.all():
            r = self.get_with_user(t.get_absolute_url())
            self.assertEqual(r.status_code, 302 if t.forum.hidden or t.forum.category.hidden else 200)
            r = self.get_with_user(t.get_absolute_url(), 'zeus', 'zeus')
            self.assertEqual(r.status_code, 200)

    def test_post_permission(self):
        for p in Post.objects.all():
            r = self.get_with_user(p.get_absolute_url())
            self.assertEqual(r.status_code, 302)
            r = self.get_with_user(p.get_absolute_url(), 'zeus', 'zeus')
            self.assertEqual(r.status_code, 302)

    def test_poll_add(self):
        self.login_client()
        values = {'body': 'test poll body',
                  'name': 'test poll name',
                  'poll_type': 1,  # poll_type: 1, create topic with poll
                  'poll_question': 'q1',
                  'poll_answers-0-text': 'answer1',
                  'poll_answers-1-text': 'answer2',
                  'poll_answers-TOTAL_FORMS': 2,}
        response = self.create_post_via_http(self.client, forum_id=self.forum.id, **values)
        self.assertEqual(response.status_code, 200)
        new_topic = Topic.objects.get(name='test poll name')
        self.assertIsNone(new_topic.poll_question)
        self.assertFalse(PollAnswer.objects.filter(topic=new_topic).exists()) # no answers here


class RestrictEditingHandler(permissions.DefaultPermissionHandler):
    def may_create_topic(self, user, forum):
        return False

    def may_create_post(self, user, topic):
        return False

    def may_edit_post(self, user, post):
        return False


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
        self.post = self.create_post(body='body post', topic=self.topic, user=staff, on_moderation=True)

    def test_redirect_category(self):
        # access without user should be redirected
        r = self.get_with_user(self.category.get_absolute_url())
        self.assertRedirects(r, settings.LOGIN_URL + '?next=%s' % self.category.get_absolute_url())
        # access with (unauthorized) user should get 403 (forbidden)
        r = self.get_with_user(self.category.get_absolute_url(), 'nostaff', 'nostaff')
        self.assertEquals(r.status_code, 403)
        # allowed user is allowed
        r = self.get_with_user(self.category.get_absolute_url(), 'staff', 'staff')
        self.assertEquals(r.status_code, 200)

    def test_redirect_forum(self):
        # access without user should be redirected
        r = self.get_with_user(self.forum.get_absolute_url())
        self.assertRedirects(r, settings.LOGIN_URL + '?next=%s' % self.forum.get_absolute_url())
        # access with (unauthorized) user should get 403 (forbidden)
        r = self.get_with_user(self.forum.get_absolute_url(), 'nostaff', 'nostaff')
        self.assertEquals(r.status_code, 403)
        # allowed user is allowed
        r = self.get_with_user(self.forum.get_absolute_url(), 'staff', 'staff')
        self.assertEquals(r.status_code, 200)

    def test_redirect_topic(self):
        # access without user should be redirected
        r = self.get_with_user(self.topic.get_absolute_url())
        self.assertRedirects(r, settings.LOGIN_URL + '?next=%s' % self.topic.get_absolute_url())
        # access with (unauthorized) user should get 403 (forbidden)
        r = self.get_with_user(self.topic.get_absolute_url(), 'nostaff', 'nostaff')
        self.assertEquals(r.status_code, 403)
        # allowed user is allowed
        r = self.get_with_user(self.topic.get_absolute_url(), 'staff', 'staff')
        self.assertEquals(r.status_code, 200)

    def test_redirect_post(self):
        # access without user should be redirected
        r = self.get_with_user(self.post.get_absolute_url())
        self.assertRedirects(r, settings.LOGIN_URL + '?next=%s' % self.post.get_absolute_url())
        # access with (unauthorized) user should get 403 (forbidden)
        r = self.get_with_user(self.post.get_absolute_url(), 'nostaff', 'nostaff')
        self.assertEquals(r.status_code, 403)
        # allowed user is allowed
        r = self.get_with_user(self.post.get_absolute_url(), 'staff', 'staff')
        self.assertEquals(r.status_code, 302)

    @override_settings(PYBB_ENABLE_ANONYMOUS_POST=False)
    def test_redirect_topic_add(self):
        _attach_perms_class('pybb.tests.RestrictEditingHandler')

        # access without user should be redirected
        add_topic_url = reverse('pybb:add_topic', kwargs={'forum_id': self.forum.id})
        r = self.get_with_user(add_topic_url)
        self.assertRedirects(r, settings.LOGIN_URL + '?next=%s' % add_topic_url)

        # access with (unauthorized) user should get 403 (forbidden)
        r = self.get_with_user(add_topic_url, 'staff', 'staff')
        self.assertEquals(r.status_code, 403)

        _detach_perms_class()

        # allowed user is allowed
        r = self.get_with_user(add_topic_url, 'staff', 'staff')
        self.assertEquals(r.status_code, 200)

    def test_redirect_post_edit(self):
        _attach_perms_class('pybb.tests.RestrictEditingHandler')

        # access without user should be redirected
        edit_post_url = reverse('pybb:edit_post', kwargs={'pk': self.post.id})
        r = self.get_with_user(edit_post_url)
        self.assertRedirects(r, settings.LOGIN_URL + '?next=%s' % edit_post_url)

        # access with (unauthorized) user should get 403 (forbidden)
        r = self.get_with_user(edit_post_url, 'staff', 'staff')
        self.assertEquals(r.status_code, 403)

        _detach_perms_class()

        # allowed user is allowed
        r = self.get_with_user(edit_post_url, 'staff', 'staff')
        self.assertEquals(r.status_code, 200)

    def test_profile_autocreation_signal_on(self):
        user = User.objects.create_user('cronos', 'cronos@localhost', 'cronos')
        profile = getattr(user, defaults.PYBB_PROFILE_RELATED_NAME, None)
        self.assertIsNotNone(profile)
        self.assertEqual(type(profile), util.get_pybb_profile_model())
        user.delete()

    def test_profile_autocreation_middleware(self):
        user = User.objects.create_user('cronos', 'cronos@localhost', 'cronos')
        getattr(user, defaults.PYBB_PROFILE_RELATED_NAME).delete()
        #just display a page : the middleware should create the profile
        self.get_with_user('/', 'cronos', 'cronos')
        user = User.objects.get(username='cronos')
        profile = getattr(user, defaults.PYBB_PROFILE_RELATED_NAME, None)
        self.assertIsNotNone(profile)
        self.assertEqual(type(profile), util.get_pybb_profile_model())
        user.delete()

    def test_user_delete_cascade(self):
        user = User.objects.create_user('cronos', 'cronos@localhost', 'cronos')
        profile = getattr(user, defaults.PYBB_PROFILE_RELATED_NAME, None)
        self.assertIsNotNone(profile)
        post = self.create_post(topic=self.topic, user=user, body='I \'ll be back')
        user_pk = user.pk
        profile_pk = profile.pk
        post_pk = post.pk

        user.delete()
        self.assertFalse(User.objects.filter(pk=user_pk).exists())
        self.assertFalse(Profile.objects.filter(pk=profile_pk).exists())
        self.assertFalse(Post.objects.filter(pk=post_pk).exists())


class NiceUrlsTest(TestCase, SharedTestModule):
    def __init__(self, *args, **kwargs):
        super(NiceUrlsTest, self).__init__(*args, **kwargs)
        self.ORIGINAL_PYBB_NICE_URL = defaults.PYBB_NICE_URL
        defaults.PYBB_NICE_URL = True
        self.urls = settings.ROOT_URLCONF

    def setUp(self):
        self.create_user()
        self.login_client()
        self.create_initial()
        self.ORIGINAL_PYBB_NICE_URL = defaults.PYBB_NICE_URL
        defaults.PYBB_NICE_URL = True

    def test_unicode_slugify(self):
        self.assertEqual(compat.slugify('北京 (China), Москва (Russia), é_è (a sad smiley !)'),
                         'bei-jing-china-moskva-russia-e_e-a-sad-smiley')

    def test_automatique_slug(self):
        self.assertEqual(compat.slugify(self.category.name), self.category.slug)
        self.assertEqual(compat.slugify(self.forum.name), self.forum.slug)
        self.assertEqual(compat.slugify(self.topic.name), self.topic.slug)

    def test_no_duplicate_slug(self):
        category_name = self.category.name
        forum_name = self.forum.name
        topic_name = self.topic.name

        # objects created without slug but the same name
        category = Category.objects.create(name=category_name)
        forum = Forum.objects.create(name=forum_name, description='bar', category=self.category)
        topic = Topic.objects.create(name=topic_name, forum=self.forum, user=self.user)

        slug_nb = len(Category.objects.filter(slug__startswith=category_name)) - 1
        self.assertEqual('%s-%d' % (compat.slugify(category_name), slug_nb), category.slug)
        slug_nb = len(Forum.objects.filter(slug__startswith=forum_name)) - 1
        self.assertEqual('%s-%d' % (compat.slugify(forum_name), slug_nb), forum.slug)
        slug_nb = len(Topic.objects.filter(slug__startswith=topic_name)) - 1
        self.assertEqual('%s-%d' % (compat.slugify(topic_name), slug_nb), topic.slug)

        # objects created with a duplicate slug but a different name
        category = Category.objects.create(name='test_slug_category', slug=compat.slugify(category_name))
        forum = Forum.objects.create(name='test_slug_forum', description='bar',
                                     category=self.category, slug=compat.slugify(forum_name))
        topic = Topic.objects.create(name='test_topic_slug', forum=self.forum,
                                     user=self.user, slug=compat.slugify(topic_name))
        slug_nb = len(Category.objects.filter(slug__startswith=category_name)) - 1
        self.assertEqual('%s-%d' % (compat.slugify(category_name), slug_nb), category.slug)
        slug_nb = len(Forum.objects.filter(slug__startswith=forum_name)) - 1
        self.assertEqual('%s-%d' % (compat.slugify(forum_name), slug_nb), forum.slug)
        slug_nb = len(Topic.objects.filter(slug__startswith=self.topic.name)) - 1
        self.assertEqual('%s-%d' % (compat.slugify(topic_name), slug_nb), topic.slug)

    def test_fail_on_too_many_duplicate_slug(self):

        original_duplicate_limit = defaults.PYBB_NICE_URL_SLUG_DUPLICATE_LIMIT

        defaults.PYBB_NICE_URL_SLUG_DUPLICATE_LIMIT = 200

        try:
            for _ in iter(range(200)):
                Topic.objects.create(name='dolly', forum=self.forum, user=self.user)
        except ValidationError as e:
            self.fail('Should be able to create "dolly", "dolly-1", ..., "dolly-199".\n')
        with self.assertRaises(ValidationError):
            Topic.objects.create(name='dolly', forum=self.forum, user=self.user)

        defaults.PYBB_NICE_URL_SLUG_DUPLICATE_LIMIT = original_duplicate_limit

    def test_long_duplicate_slug(self):
        long_name = 'abcde' * 51  # 255 symbols
        topic1 = Topic.objects.create(name=long_name, forum=self.forum, user=self.user)
        self.assertEqual(topic1.slug, long_name)
        topic2 = Topic.objects.create(name=long_name, forum=self.forum, user=self.user)
        self.assertEqual(topic2.slug, '%s-1' % long_name[:253])
        topic3 = Topic.objects.create(name=long_name, forum=self.forum, user=self.user)
        self.assertEqual(topic3.slug, '%s-2' % long_name[:253])

    def test_absolute_url(self):
        response = self.client.get(self.category.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['category'], self.category)
        self.assertEqual('/c/%s/' % (self.category.slug), self.category.get_absolute_url())
        response = self.client.get(self.forum.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['forum'], self.forum)
        self.assertEqual(
            '/c/%s/%s/' % (self.category.slug, self.forum.slug),
            self.forum.get_absolute_url()
            )
        response = self.client.get(self.topic.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['topic'], self.topic)
        self.assertEqual(
            '/c/%s/%s/%s/' % (self.category.slug, self.forum.slug, self.topic.slug),
            self.topic.get_absolute_url()
            )

    def test_add_topic(self):
        add_topic_url = reverse('pybb:add_topic', kwargs={'forum_id': self.forum.pk})
        response = self.client.get(add_topic_url)
        inputs = dict(html.fromstring(response.content).xpath('//form[@class="%s"]' % "post-form")[0].inputs)
        self.assertNotIn('slug', inputs)
        values = self.get_form_values(response)
        values.update({'name': self.topic.name, 'body': '[b]Test slug body[/b]', 'poll_type': 0})
        response = self.client.post(add_topic_url, data=values, follow=True)
        slug_nb = len(Topic.objects.filter(slug__startswith=compat.slugify(self.topic.name))) - 1
        self.assertIsNotNone = Topic.objects.get(slug='%s-%d' % (self.topic.name, slug_nb))

        _attach_perms_class('pybb.tests.CustomPermissionHandler')
        response = self.client.get(add_topic_url)
        inputs = dict(html.fromstring(response.content).xpath('//form[@class="%s"]' % "post-form")[0].inputs)
        self.assertIn('slug', inputs)
        values = self.get_form_values(response)
        values.update({'name': self.topic.name, 'body': '[b]Test slug body[/b]',
                       'poll_type': 0, 'slug': 'test_slug'})
        response = self.client.post(add_topic_url, data=values, follow=True)
        self.assertIsNotNone = Topic.objects.get(slug='test_slug')
        _detach_perms_class()

    def test_old_url_redirection(self):

        original_perm_redirect = defaults.PYBB_NICE_URL_PERMANENT_REDIRECT

        for redirect_status in [301, 302]:
            defaults.PYBB_NICE_URL_PERMANENT_REDIRECT = redirect_status == 301

            response = self.client.get(reverse("pybb:category", kwargs={"pk": self.category.pk}))
            self.assertRedirects(response, self.category.get_absolute_url(), status_code=redirect_status)

            response = self.client.get(reverse("pybb:forum", kwargs={"pk": self.forum.pk}))
            self.assertRedirects(response, self.forum.get_absolute_url(), status_code=redirect_status)

            response = self.client.get(reverse("pybb:topic", kwargs={"pk": self.topic.pk}))
            self.assertRedirects(response, self.topic.get_absolute_url(), status_code=redirect_status)

        defaults.PYBB_NICE_URL_PERMANENT_REDIRECT = original_perm_redirect

    def tearDown(self):
        defaults.PYBB_NICE_URL = self.ORIGINAL_PYBB_NICE_URL


class TestTemplateTags(TestCase, SharedTestModule):
    """Tests all templatetags and filter defined by pybb"""

    # def setUp(self):
        # self.create_user()
        # self.create_initial()

    def test_pybb_time_anonymous(self):
        template = Template('{% load pybb_tags %}{% pybb_time a_time %}')
        context = Context({'user': AnonymousUser()})

        context['a_time'] = timezone.now() - timezone.timedelta(days=2)
        output = template.render(context)
        self.assertEqual(output, dateformat.format(context['a_time'], 'd M, Y H:i'))

        context['a_time'] = timezone.now() - timezone.timedelta(days=1)
        output = template.render(context)
        self.assertEqual(output, 'yesterday, %s' % context['a_time'].strftime('%H:%M'))

        context['a_time'] = timezone.now() - timezone.timedelta(hours=1)
        output = template.render(context)
        self.assertEqual(output, 'today, %s' % context['a_time'].strftime('%H:%M'))

        context['a_time'] = timezone.now() - timezone.timedelta(minutes=30)
        output = template.render(context)
        self.assertEqual(output, '30 minutes ago')

        context['a_time'] = timezone.now() - timezone.timedelta(seconds=30)
        output = template.render(context)
        self.assertEqual(output, '30 seconds ago')

    def test_pybb_time_authenticated(self):
        self.create_user()
        template = Template('{% load pybb_tags %}{% pybb_time a_time %}')
        context = Context({'user': self.user})
        context['a_time'] = timezone.now() - timezone.timedelta(days=4)
        output = template.render(context)
        tz = util.get_pybb_profile(self.user).time_zone * 60 * 60
        tz += time.altzone if time.daylight else time.timezone
        user_datetime = context['a_time'] + timezone.timedelta(seconds=tz)
        self.assertEqual(output, dateformat.format(user_datetime, 'd M, Y H:i'))

        context['a_time'] = timezone.now() - timezone.timedelta(seconds=30)
        output = template.render(context)
        self.assertEqual(output, '30 seconds ago')

    def test_pybb_get_time(self):
        template = Template(('{% load pybb_tags %}{% pybb_get_time a_time as time_output %}'
                             '{{ time_output|upper }}'))
        context = Context({'user': AnonymousUser(),
                           'a_time': timezone.now() - timezone.timedelta(seconds=30)})
        output = template.render(context)
        self.assertEqual(output, '30 SECONDS AGO')

    def test_pybb_link(self):
        self.create_user()
        self.create_initial()
        template = Template(('{% load pybb_tags %}'
                             '{% pybb_link topic %}, '
                             '{% pybb_link forum %}, '
                             '{% pybb_link post "Hello <World>" %}'))
        context = Context({'user': AnonymousUser(),
                           'post': self.post,
                           'topic': self.topic,
                           'forum': self.forum})
        expected = ('<a href="%s">%s</a>' % (self.topic.get_absolute_url(), self.topic),
                    '<a href="%s">%s</a>' % (self.forum.get_absolute_url(), self.forum),
                    '<a href="%s">%s</a>' % (self.post.get_absolute_url(), 'Hello &lt;World&gt;'))
        expected = ', '.join(expected)
        output = template.render(context)
        self.assertEqual(output, expected)

    def test_pybb_posted_by(self):
        self.create_user()
        self.create_initial()
        template = Template(('{% load pybb_tags %}'
                             '{% if post|pybb_posted_by:user %}YES{% else %}NO{% endif %}:'
                             '{% if post|pybb_posted_by:anonymous %}YES{% else %}NO{% endif %}'))
        context = Context({'user': self.user,
                           'anonymous': AnonymousUser(),
                           'post': self.post})
        output = template.render(context)
        self.assertEqual(output, 'YES:NO')


    def test_pybb_is_topic_unread(self):
        self.create_user()
        self.create_initial()
        self.login_client()
        self.client.get(self.topic.get_absolute_url())
        template = Template(('{% load pybb_tags %}'
                             '{% if topic|pybb_is_topic_unread:user %}YES{% else %}NO{% endif %}:'
                             '{% if topic|pybb_is_topic_unread:anonymous %}YES{% else %}NO{% endif %}:'
                             '{% if topic|pybb_is_topic_unread:bob %}YES{% else %}NO{% endif %}'))
        context = Context({'user': self.user,
                           'anonymous': AnonymousUser(),
                           'bob': User.objects.create_user('bob', 'bob@localhost', 'bob'),
                           'topic': self.topic})
        output = template.render(context)
        self.assertEqual(output, 'NO:NO:YES')


    def test_pybb_topic_unread(self):
        self.create_user()
        self.login_client()
        bob = User.objects.create_user('bob', 'bob@localhost', 'bob')

        """
        creates a total of 6 topics in 3 forums.
            * Forum A
                * Topic A1
            * Forum B
                * Topic B1
                * Topic B2
            * Forum C
                * Topic C1
                * Topic C2
                * Topic C3
        """
        forums = []
        topics = []
        category = Category.objects.create(name='foo')
        for letter in 'ABC':
            forum = Forum.objects.create(name=letter, description=letter, category=category)
            forums.append(forum)
            topic = Topic.objects.create(name='%s1' % letter, forum=forum, user=bob)
            self.create_post(topic=topic, user=bob, body='test')
            topics.append(topic)
        topic = Topic.objects.create(name='B2', forum=forums[1], user=bob)
        self.create_post(topic=topic, user=bob, body='test')
        topics.append(topic)
        topic = Topic.objects.create(name='C2', forum=forums[2], user=bob)
        self.create_post(topic=topic, user=bob, body='test')
        topics.append(topic)
        topic = Topic.objects.create(name='C3', forum=forums[2], user=bob)
        self.create_post(topic=topic, user=bob, body='test')
        topics.append(topic)

        template = Template(('{% load pybb_tags %}'
                             '{% for topic in topics|pybb_topic_unread:user %}'
                             '{{ topic.name }}: {{ topic.unread }}\n'
                             '{% endfor %}'))

        # test with anonymous: unread should be empty (neither True, neither False)
        context = Context({'user': AnonymousUser(), 'topics': topics})
        output = template.render(context)
        expected = '\n'.join(('A1: ', 'B1: ', 'C1: ',
                              'B2: ', 'C2: ',
                              'C3: ', ''))
        self.assertEqual(output, expected)

        # User should have everything marked as unread
        context['user'] = self.user
        output = template.render(context)
        expected = '\n'.join(('A1: True', 'B1: True', 'C1: True',
                              'B2: True', 'C2: True',
                              'C3: True', ''))
        self.assertEqual(output, expected)

        # mark A1, B1 and C1 as read for user
        self.client.get(topics[0].get_absolute_url())
        self.client.get(topics[1].get_absolute_url())
        self.client.get(topics[2].get_absolute_url())
        output = template.render(context)
        expected = '\n'.join(('A1: False', 'B1: False', 'C1: False',
                              'B2: True', 'C2: True',
                              'C3: True', ''))
        self.assertEqual(output, expected)

        # mark all as read for user
        self.client.get(reverse('pybb:mark_all_as_read'))
        output = template.render(context)
        expected = '\n'.join(('A1: False', 'B1: False', 'C1: False',
                              'B2: False', 'C2: False',
                              'C3: False', ''))
        self.assertEqual(output, expected)


    def test_pybb_forum_unread(self):
        self.create_user()
        self.login_client()
        bob = User.objects.create_user('bob', 'bob@localhost', 'bob')

        """
        creates a total of 6 topics in 3 forums.
            * Forum A
                * Topic A1
            * Forum B
                * Topic B1
                * Topic B2
            * Forum C
                * Topic C1
                * Topic C2
                * Topic C3
        """
        forums = []
        topics = []
        category = Category.objects.create(name='foo')
        for letter in 'ABC':
            forum = Forum.objects.create(name=letter, description=letter, category=category)
            forums.append(forum)
            topic = Topic.objects.create(name='%s1' % letter, forum=forum, user=bob)
            self.create_post(topic=topic, user=bob, body='test')
            topics.append(topic)
        topic = Topic.objects.create(name='B2', forum=forums[1], user=bob)
        self.create_post(topic=topic, user=bob, body='test')
        topics.append(topic)
        topic = Topic.objects.create(name='C2', forum=forums[2], user=bob)
        self.create_post(topic=topic, user=bob, body='test')
        topics.append(topic)
        topic = Topic.objects.create(name='C3', forum=forums[2], user=bob)
        self.create_post(topic=topic, user=bob, body='test')
        topics.append(topic)

        template = Template(('{% load pybb_tags %}'
                             '{% for forum in forums|pybb_forum_unread:user %}'
                             '{{ forum.name }}: {{ forum.unread }}\n'
                             '{% endfor %}'))

        context = Context({'forums': forums})
        # test for anonymous user: unread is empty (neither True, neither False)
        context['user'] = AnonymousUser()
        output = template.render(context)
        expected = '\n'.join(('A: ', 'B: ', 'C: ', ''))
        self.assertEqual(output, expected)

        # User should have everything marked as unread
        context['user'] = self.user
        output = template.render(context)
        expected = '\n'.join(('A: True', 'B: True', 'C: True', ''))
        self.assertEqual(output, expected)

        # mark A1, B1 and C1 as read for user (so forum A is not unread now)
        self.client.get(topics[0].get_absolute_url())
        self.client.get(topics[1].get_absolute_url())
        self.client.get(topics[2].get_absolute_url())
        output = template.render(context)
        expected = '\n'.join(('A: False', 'B: True', 'C: True', ''))
        self.assertEqual(output, expected)

        # mark all as read for user
        self.client.get(reverse('pybb:mark_all_as_read'))
        output = template.render(context)
        expected = '\n'.join(('A: False', 'B: False', 'C: False', ''))
        self.assertEqual(output, expected)


    def test_pybb_topic_inline_pagination(self):
        self.create_user()
        self.create_initial()
        self.topic.post_count = defaults.PYBB_TOPIC_PAGE_SIZE * 13
        nb_pages = int(math.ceil(float(self.topic.post_count) / defaults.PYBB_TOPIC_PAGE_SIZE))

        template = Template(('{% load pybb_tags %}'
                             '{% for page in topic|pybb_topic_inline_pagination %}'
                             '{{ page }} '
                             '{% endfor %}'))
        context = Context({'user': AnonymousUser(), 'topic': self.topic})
        output = template.render(context)
        expected = '1 2 3 4 ... %d ' % nb_pages
        self.assertEqual(output, expected)

        self.topic.post_count = defaults.PYBB_TOPIC_PAGE_SIZE * 3
        output = template.render(context)
        expected = '1 2 3 '
        self.assertEqual(output, expected)


    def test_pybb_topic_poll_not_voted(self):
        self.create_user()
        self.create_initial()
        self.topic.poll_type = Topic.POLL_TYPE_SINGLE
        self.topic.poll_question = 'Where is Brian?'
        self.topic.save()
        kitchen = PollAnswer.objects.create(topic=self.topic, text='in the kitchen')
        bathroom = PollAnswer.objects.create(topic=self.topic, text='in the bathroom')

        template = Template((
            '{% load pybb_tags %}'
            '{% if topic|pybb_topic_poll_not_voted:user %}NOTVOTED{% else %}VOTED{% endif %}:'
            '{% if topic|pybb_topic_poll_not_voted:anonymous %}NOTVOTED{% else %}VOTED{% endif %}:'
            '{% if topic|pybb_topic_poll_not_voted:bob %}NOTVOTED{% else %}VOTED{% endif %}'))
        context = Context({'user': self.user,
                           'anonymous': AnonymousUser(),
                           'bob': User.objects.create_user('bob', 'bob@localhost', 'bob'),
                           'topic': self.topic})
        self.assertEqual(template.render(context), 'NOTVOTED:NOTVOTED:NOTVOTED')

        # bob answers
        PollAnswerUser.objects.create(poll_answer=kitchen, user=context['bob'])
        self.assertEqual(template.render(context), 'NOTVOTED:NOTVOTED:VOTED')

    def test_endswith(self):
        template = Template(('{% load pybb_tags %}'
                             '{{ test|endswith:"the end..." }}:'
                             '{{ test|endswith:"big bang" }}'))
        context = Context({'test': 'This is the end...'})
        self.assertEqual(template.render(context), 'True:False')


    def test_pybb_get_profile(self):
        template = Template(('{% load pybb_tags %}'
                             '{% pybb_get_profile bob as user_profile_via_args %}'
                             '{% pybb_get_profile user=bob as user_profile_via_kwargs %}'
                             '{% pybb_get_profile anonymous as no_profile %}'
                             '{{ user_profile_via_args.pk }}:'
                             '{{ user_profile_via_kwargs.pk }}:'
                             '{{ no_profile }}'))
        context = Context({'anonymous': AnonymousUser(),
                           'bob': User.objects.create_user('bob', 'bob@localhost', 'bob')})

        bob_profile_pk = util.get_pybb_profile(context['bob']).pk
        self.assertEqual(template.render(context), '%(pk)d:%(pk)d:None' % {'pk': bob_profile_pk})


    def test_pybb_get_latest_topics(self):
        self.create_user()
        self.create_initial()
        self.topic.name = '0'
        self.topic.save()
        for i in range(1, 10):
            topic = Topic.objects.create(name='%d' % i,
                                         user=self.user, forum=self.forum,
                                         on_moderation = bool(i % 2))
            self.create_post(topic=topic, user=self.user, body='foo', on_moderation=bool(i % 2))

        context = Context({'anonymous': AnonymousUser(), 'user': self.user})


        # user can view all it's 5 last topic (default slice is 5)
        template = Template(('{% load pybb_tags %}'
                             '{% pybb_get_latest_topics as topics %}'
                             '{% for topic in topics %}{{ topic.name }},{% endfor %}'))
        self.assertEqual(template.render(context), '9,8,7,6,5,')

        # user can view all it's topics
        template = Template(('{% load pybb_tags %}'
                             '{% pybb_get_latest_topics 20 as topics %}'
                             '{% for topic in topics %}{{ topic.name }},{% endfor %}'))
        self.assertEqual(template.render(context), '9,8,7,6,5,4,3,2,1,0,')

        # anonymous can view topics which do not require moderation (the odd ones)
        template = Template(('{% load pybb_tags %}'
                             '{% pybb_get_latest_topics 20 anonymous as topics %}'
                             '{% for topic in topics %}{{ topic.name }},{% endfor %}'))
        self.assertEqual(template.render(context), '8,6,4,2,0,')


    def test_pybb_get_latest_posts(self):
        self.create_user()
        self.create_initial()
        self.topic.name = '0'
        self.topic.save()
        self.post.body = 'A0'
        self.post.save()
        self.create_post(topic=self.topic, body='B0', user=self.user, on_moderation = True)
        for i in range(1, 10):
            topic = Topic.objects.create(name='%d' % i, user=self.user, forum=self.forum, )
            self.create_post(topic=topic, body='A%d' % i, user=self.user)
            self.create_post(topic=topic, body='B%d' % i, user=self.user, on_moderation = True)

        context = Context({'anonymous': AnonymousUser(), 'user': self.user})

        ORIG = defaults.PYBB_PREMODERATION
        # test without PREMODERATION
        defaults.PYBB_PREMODERATION = False
        # user can view all it's 5 last post (default slice is 5)
        template = Template(('{% load pybb_tags %}'
                             '{% pybb_get_latest_posts as posts %}'
                             '{% for post in posts %}{{ post.body }},{% endfor %}'))
        self.assertEqual(template.render(context), 'B9,A9,B8,A8,B7,')

        # user can view all it's posts
        template = Template(('{% load pybb_tags %}'
                             '{% pybb_get_latest_posts 20 as posts %}'
                             '{% for post in posts %}{{ post.body }},{% endfor %}'))
        self.assertEqual(template.render(context),
                         'B9,A9,B8,A8,B7,A7,B6,A6,B5,A5,B4,A4,B3,A3,B2,A2,B1,A1,B0,A0,')

        # anonymous can view all posts when PYBB_PREMODERATION is disabled
        template = Template(('{% load pybb_tags %}'
                             '{% pybb_get_latest_posts 20 anonymous as posts %}'
                             '{% for post in posts %}{{ post.body }},{% endfor %}'))
        self.assertEqual(template.render(context),
                         'B9,A9,B8,A8,B7,A7,B6,A6,B5,A5,B4,A4,B3,A3,B2,A2,B1,A1,B0,A0,')

        # now, test with PREMODERATION
        def fake_premoderation(user, body):
            return True
        defaults.PYBB_PREMODERATION = fake_premoderation
        # user can always view all it's posts even if those need moderation
        template = Template(('{% load pybb_tags %}'
                             '{% pybb_get_latest_posts 20 as posts %}'
                             '{% for post in posts %}{{ post.body }},{% endfor %}'))
        self.assertEqual(template.render(context),
                         'B9,A9,B8,A8,B7,A7,B6,A6,B5,A5,B4,A4,B3,A3,B2,A2,B1,A1,B0,A0,')

        # anonymous can view posts which do not require moderation (all "A" posts)
        template = Template(('{% load pybb_tags %}'
                             '{% pybb_get_latest_posts 20 anonymous as posts %}'
                             '{% for post in posts %}{{ post.body }},{% endfor %}'))
        self.assertEqual(template.render(context), 'A9,A8,A7,A6,A5,A4,A3,A2,A1,A0,')
        defaults.PYBB_PREMODERATION = ORIG


    def test_perms_check_app_installed(self):
        template = Template(('{% load pybb_tags %}'
                             '{{ "fairy"|check_app_installed }}:{{ "pybb"|check_app_installed }}'))
        self.assertEqual(template.render(Context()), 'False:True')


    def test_pybbm_calc_topic_views(self):
        self.create_user()
        self.create_initial()
        cache.delete(util.build_cache_key('anonymous_topic_views', topic_id=self.topic.id))
        context = Context({'topic': self.topic})
        template = Template(('{% load pybb_tags %}{{ topic|pybbm_calc_topic_views }}'))
        self.assertEqual(template.render(context), '0')

        self.client.get(self.topic.get_absolute_url())
        self.assertEqual(template.render(context), '1')

        bob = User.objects.create_user('bob', 'bob@localhost', 'bob')
        self.get_with_user(self.topic.get_absolute_url(), username='bob', password='bob')
        context['topic'] = Topic.objects.get(pk=self.topic.pk)
        self.assertEqual(template.render(context), '2')

        self.client.get(self.topic.get_absolute_url())
        self.assertEqual(template.render(context), '3')


def build_dynamic_test_for_templatetags_perms():
    """
    Dynamically creates test method for templatetags which are dynamically created via
    methods from PermissionHandler (pybb.permissions)
    """
    arg_mapping = {
        'categories': Category.objects.all(),
        'forums': Forum.objects.all(),
        'topics': Topic.objects.all(),
        'posts': Post.objects.all(),
        'category': Category.objects.first,
        'forum': Forum.objects.first,
        'topic': Topic.objects.first,
        'post': Post.objects.first,
        'user': User.objects.first,
    }

    def build_test_method(method_name, method, required_arg, templatetag_name):
        if method_name.startswith('filter') and len(method_args) == 3:
            # Method should have 2 args: user and queryset. else we can not test it
            def test(self):
                self.create_user()
                self.create_initial()
                context = Context({'user': self.user, 'qs': arg_mapping[required_arg]})
                template = Template(('{%% load pybb_tags %%}'
                                     '{%% for o in user|%s:qs %%}'
                                     '{{ o }}'
                                     '{%% endfor %%}') % templatetag_name)
                expected = ''.join(['%s' % obj for obj in method(self.user, context['qs'])])
                self.assertEqual(template.render(context), expected)
        elif method_name.startswith('may'):
            def test(self):
                self.create_user()
                self.create_initial()
                context = Context({'user': self.user})
                if required_arg:
                    context['obj'] = arg_mapping[required_arg]
                    if callable(context['obj']):
                        # because .first() is run when called, we need to call it now, not before
                        context['obj'] = context['obj']()
                    expected = '%s' % method(self.user, context['obj'])
                    tpl = '{%% load pybb_tags %%}{{ user|%s:obj }}' % templatetag_name
                else:
                    expected = '%s' % method(self.user)
                    tpl = '{%% load pybb_tags %%}{{ user|%s }}' % templatetag_name
                template = Template(tpl)
                self.assertEqual(template.render(context), expected)
        else:
            test = None
        return test

    for method_name, method in inspect.getmembers(permissions.perms):
        if not inspect.ismethod(method):
            continue  # only methods are used to dynamically build templatetags
        if not method_name.startswith('may') and not method_name.startswith('filter'):
            continue  # only (may|filter)* methods are used to dynamically build templatetags
        method_args = inspect.getargspec(method).args
        args_count = len(method_args)
        if args_count not in (2, 3):
            continue  # only methods with 2 or 3 params
        if method_args[0] != 'self' or method_args[1] != 'user':
            continue  # only methods with self and user as first args

        templatetag_name = 'pybb_%s' % method_name

        required_arg = None
        if len(method_args) == 3:
            # this is a filter which require a queryset or an obj
            required_arg = method_args[2]
            if required_arg not in arg_mapping:
                required_arg = method_name.split('_')[-1]
            if required_arg not in arg_mapping:
                # Method or its args are not well named. We can not dynamically test it
                continue
        test_method = build_test_method(method_name, method, required_arg, templatetag_name)
        if test_method:
            test_method.__name__ = str('test_%s' % templatetag_name)
            setattr(TestTemplateTags, test_method.__name__, test_method)
build_dynamic_test_for_templatetags_perms()


class MiscTest(TestCase, SharedTestModule):

    def test_profile_avatar_url_property(self):
        self.create_user()
        profile = util.get_pybb_profile(self.user)
        # test the default avatar
        self.assertEqual(profile.avatar_url, defaults.PYBB_DEFAULT_AVATAR_URL)

        # test if user has a valid avatar
        path = os.path.join(os.path.dirname(__file__), 'static', 'pybb', 'img', 'image.png')
        profile.avatar = SimpleUploadedFile(name='image.png',
                                            content=open(path, 'rb').read(),
                                            content_type='image/png')
        profile.save()
        self.assertNotEqual(profile.avatar_url, defaults.PYBB_DEFAULT_AVATAR_URL)
        self.assertTrue(profile.avatar_url.startswith(settings.MEDIA_URL + 'pybb/avatar/'))
        self.assertTrue(profile.avatar_url.endswith('.png'))


    def test_profile_get_display_name(self):
        self.create_user()
        profile = util.get_pybb_profile(self.user)
        self.assertEqual(profile.get_display_name(), self.user.get_username())
