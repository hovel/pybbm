#!/usr/bin/env python
# vim:fileencoding=utf-8

__author__ = 'zeus'

from django.test import TestCase
from pybb.models import *
from django.contrib.auth.models import User
from django.test.client import Client
from django.core.urlresolvers import reverse
from pybb import defaults

try:
    from lxml import html
except:
    raise Exception('PyBB requires lxml for self testing')

class BasicFeaturesTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('zeus', 'zeus@localhost', 'zeus')
        self.category = Category(name='foo')
        self.category.save()
        self.forum = Forum(name='xfoo', description='bar', category=self.category)
        self.forum.save()
        self.topic = Topic(name='etopic', forum=self.forum, user=self.user)
        self.topic.save()
        self.post = Post(topic=self.topic, user=self.user, body='bbcode [b]test[b]', markup='bbcode')
        self.post.save()

    def test_base(self):
        client = Client()
        # Check index page
        url = reverse('pybb_index')
        response = client.get(url)
        tree = html.fromstring(response.content)
        self.assertContains(response, u'foo')
        self.assertContains(response, self.forum.get_absolute_url())
        self.assertTrue(defaults.PYBB_DEFAULT_TITLE in tree.xpath('//title')[0].text_content())
        self.assertEqual(len(response.context['categories']), 1)

        # Check forum page
        url = reverse('pybb_forum', args=[self.forum.id])
        response = client.get(url)
        tree = html.fromstring(response.content)
        self.assertTrue(tree.xpath('//a[@href="%s"]' % self.topic.get_absolute_url()))
        self.assertTrue(tree.xpath('//title[contains(text(),"%s")]' % self.forum.name))
        self.assertFalse(tree.xpath('//a[contains(@href,"?page=")]'))
        self.assertFalse(response.context['is_paginated'])

    def test_pagination_and_topic_addition(self):
        client = Client()
        for i in range(0, defaults.PYBB_FORUM_PAGE_SIZE + 3):
            topic = Topic(name='topic_%s_' % i, forum=self.forum, user=self.user)
            topic.save()
        url = reverse('pybb_forum', args=[self.forum.id])
        response = client.get(url)
        self.assertEqual(len(response.context['topic_list']), defaults.PYBB_FORUM_PAGE_SIZE)
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(response.context['paginator'].num_pages,
                         ((defaults.PYBB_FORUM_PAGE_SIZE + 3) / defaults.PYBB_FORUM_PAGE_SIZE) + 1)

    def test_bbcode_and_topic_title(self):
        client = Client()
        url = reverse('pybb_topic', args=[self.topic.id])
        response = client.get(url)
        tree = html.fromstring(response.content)
        self.assertTrue(self.topic.name in tree.xpath('//title')[0].text_content())
        self.assertContains(response, self.post.body_html)
        self.assertContains(response, u'bbcode <strong>test</strong>')

    def test_post_deletion(self):
        post = Post(topic=self.topic, user=self.user, body='bbcode [b]test[b]', markup='bbcode')
        post.save()
        post.delete()
        Topic.objects.get(id=self.topic.id)
        Forum.objects.get(id=self.forum.id)

    def test_topic_deletion(self):
        topic = Topic(name='xtopic', forum=self.forum, user=self.user)
        topic.save()
        post = Post(topic=topic, user=self.user, body='one', markup='bbcode')
        post.save()
        post = Post(topic=topic, user=self.user, body='two', markup='bbcode')
        post.save()
        post.delete()
        Topic.objects.get(id=topic.id)
        Forum.objects.get(id=self.forum.id)
        topic.delete()
        Forum.objects.get(id=self.forum.id)

    def test_read_tracking(self):
        topic = Topic(name='xtopic', forum=self.forum, user=self.user)
        topic.save()
        post = Post(topic=topic, user=self.user, body='one', markup='bbcode')
        post.save()
        client = Client()
        client.login(username='zeus', password='zeus')
        # Topic status
        tree = html.fromstring(client.get(topic.forum.get_absolute_url()).content)
        self.assertTrue(tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % topic.get_absolute_url()))
        # Forum status
        tree = html.fromstring(client.get(reverse('pybb_index')).content)
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
        tree = html.fromstring(client.get(reverse('pybb_index')).content)
        self.assertFalse(tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % topic.forum.get_absolute_url()))
        # Post message
        response = client.post(reverse('pybb_add_post', args=[topic.id]), {'body': 'test tracking'}, follow=True)
        self.assertContains(response, 'test tracking')
        # Topic status - readed
        tree = html.fromstring(client.get(topic.forum.get_absolute_url()).content)
        self.assertFalse(tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % topic.get_absolute_url()))
        # Forum status - readed
        tree = html.fromstring(client.get(reverse('pybb_index')).content)
        self.assertFalse(tree.xpath('//a[@href="%s"]/parent::td[contains(@class,"unread")]' % topic.forum.get_absolute_url()))

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

        post_hidden = Post(topic=topic_hidden, user=self.user, body='hidden', markup='bbcode')
        post_hidden.save()

        post_in_hidden = Post(topic=topic_in_hidden, user=self.user, body='hidden', markup='bbcode')
        post_in_hidden.save()

        
        self.assertFalse(category.id in [c.id for c in client.get(reverse('pybb_index')).context['categories']])
        self.assertTrue(client.get(category.get_absolute_url()).status_code==404)
        self.assertTrue(client.get(forum_in_hidden.get_absolute_url()).status_code==404)
        self.assertTrue(client.get(topic_in_hidden.get_absolute_url()).status_code==404)

        self.assertNotContains(client.get(reverse('pybb_index')), forum_hidden.get_absolute_url())
        self.assertNotContains(client.get(reverse('pybb_feed', kwargs={'url': 'topics'})), topic_hidden.get_absolute_url())
        self.assertNotContains(client.get(reverse('pybb_feed', kwargs={'url': 'topics'})), topic_in_hidden.get_absolute_url())

        self.assertNotContains(client.get(reverse('pybb_feed', kwargs={'url': 'posts'})), post_hidden.get_absolute_url())
        self.assertNotContains(client.get(reverse('pybb_feed', kwargs={'url': 'posts'})), post_in_hidden.get_absolute_url())
        self.assertTrue(client.get(forum_hidden.get_absolute_url()).status_code==404)
        self.assertTrue(client.get(topic_hidden.get_absolute_url()).status_code==404)

        client.login(username='zeus', password='zeus')
        self.assertFalse(category.id in [c.id for c in client.get(reverse('pybb_index')).context['categories']])
        self.assertNotContains(client.get(reverse('pybb_index')), forum_hidden.get_absolute_url())
        self.assertTrue(client.get(category.get_absolute_url()).status_code==404)
        self.assertTrue(client.get(forum_in_hidden.get_absolute_url()).status_code==404)
        self.assertTrue(client.get(topic_in_hidden.get_absolute_url()).status_code==404)
        self.assertTrue(client.get(forum_hidden.get_absolute_url()).status_code==404)
        self.assertTrue(client.get(topic_hidden.get_absolute_url()).status_code==404)
        self.user.is_staff = True
        self.user.save()
        self.assertTrue(category.id in [c.id for c in client.get(reverse('pybb_index')).context['categories']])
        self.assertContains(client.get(reverse('pybb_index')), forum_hidden.get_absolute_url())
        self.assertFalse(client.get(category.get_absolute_url()).status_code==404)
        self.assertFalse(client.get(forum_in_hidden.get_absolute_url()).status_code==404)
        self.assertFalse(client.get(topic_in_hidden.get_absolute_url()).status_code==404)
        self.assertFalse(client.get(forum_hidden.get_absolute_url()).status_code==404)
        self.assertFalse(client.get(topic_hidden.get_absolute_url()).status_code==404)


        
