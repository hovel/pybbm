#!/usr/bin/env python
# vim:fileencoding=utf-8
from time import sleep

__author__ = 'zeus'

from django.test import TestCase
from pybb.models import *
from django.contrib.auth.models import User
from django.test.client import Client
from django.core.urlresolvers import reverse
from pybb import defaults
from django.core import mail

try:
    from lxml import html
except:
    raise Exception('PyBB requires lxml for self testing')

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
        tree = html.fromstring(response.content)
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
        response = self.client.post(add_topic_url, data=values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'new topic test')

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
        sleep(1)
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
        self.assertEqual(client.get(category.get_absolute_url()).status_code, 404)
        self.assertEqual(client.get(forum_in_hidden.get_absolute_url()).status_code, 404)
        self.assertEqual(client.get(topic_in_hidden.get_absolute_url()).status_code, 404)

        self.assertNotContains(client.get(reverse('pybb:index')), forum_hidden.get_absolute_url())
        self.assertNotContains(client.get(reverse('pybb:feed', kwargs={'url': 'topics'})), topic_hidden.get_absolute_url())
        self.assertNotContains(client.get(reverse('pybb:feed', kwargs={'url': 'topics'})), topic_in_hidden.get_absolute_url())

        self.assertNotContains(client.get(reverse('pybb:feed', kwargs={'url': 'posts'})), post_hidden.get_absolute_url())
        self.assertNotContains(client.get(reverse('pybb:feed', kwargs={'url': 'posts'})), post_in_hidden.get_absolute_url())
        self.assertEqual(client.get(forum_hidden.get_absolute_url()).status_code, 404)
        self.assertEqual(client.get(topic_hidden.get_absolute_url()).status_code, 404)

        client.login(username='zeus', password='zeus')
        self.assertFalse(category.id in [c.id for c in client.get(reverse('pybb:index')).context['categories']])
        self.assertNotContains(client.get(reverse('pybb:index')), forum_hidden.get_absolute_url())
        self.assertEqual(client.get(category.get_absolute_url()).status_code, 404)
        self.assertEqual(client.get(forum_in_hidden.get_absolute_url()).status_code, 404)
        self.assertEqual(client.get(topic_in_hidden.get_absolute_url()).status_code, 404)
        self.assertEqual(client.get(forum_hidden.get_absolute_url()).status_code, 404)
        self.assertEqual(client.get(topic_hidden.get_absolute_url()).status_code, 404)
        self.user.is_staff = True
        self.user.save()
        self.assertTrue(category.id in [c.id for c in client.get(reverse('pybb:index')).context['categories']])
        self.assertContains(client.get(reverse('pybb:index')), forum_hidden.get_absolute_url())
        self.assertNotEqual(client.get(category.get_absolute_url()).status_code, 404)
        self.assertNotEqual(client.get(forum_in_hidden.get_absolute_url()).status_code, 404)
        self.assertNotEqual(client.get(topic_in_hidden.get_absolute_url()).status_code, 404)
        self.assertNotEqual(client.get(forum_hidden.get_absolute_url()).status_code, 404)
        self.assertNotEqual(client.get(topic_hidden.get_absolute_url()).status_code, 404)

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
        response = self.client.get(reverse('pybb:edit_post', kwargs={'pk': self.post.id}))
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content)
        values = dict(tree.xpath('//form[@method="post"]')[0].form_values())
        values['body'] = 'test edit'
        response = self.client.post(reverse('pybb:edit_post', kwargs={'pk': self.post.id}), data=values, follow=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.post.get_absolute_url(), follow=True)
        self.assertContains(response, 'test edit')
        # Check admin form
        self.user.is_staff = True
        self.user.save()
        response = self.client.get(reverse('pybb:edit_post', kwargs={'pk': self.post.id}))
        self.assertEqual(response.status_code, 200)
        tree = html.fromstring(response.content)
        values = dict(tree.xpath('//form[@method="post"]')[0].form_values())
        values['body'] = 'test edit'
        values['login'] = 'new_login'
        response = self.client.post(reverse('pybb:edit_post', kwargs={'pk': self.post.id}), data=values, follow=True)
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
        new_post = Post(topic=self.topic, user=self.user, body='test subscribtion юникод')
        new_post.save()
        self.assertTrue([msg for msg in mail.outbox if new_post.get_absolute_url() in msg.body])
        response = client.get(reverse('pybb:delete_subscription', args=[self.topic.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(user not in list(self.topic.subscribers.all()))

    def test_topic_updated(self):
        topic = Topic(name='etopic', forum=self.forum, user=self.user)
        topic.save()
        sleep(1)
        post = Post(topic=topic, user=self.user, body='bbcode [b]test[b]')
        post.save()
        client = Client()
        response = client.get(self.forum.get_absolute_url())
        self.assertEqual(response.context['topic_list'][0], topic)
        sleep(1)
        post = Post(topic=self.topic, user=self.user, body='bbcode [b]test[b]')
        post.save()
        client = Client()
        response = client.get(self.forum.get_absolute_url())
        self.assertEqual(response.context['topic_list'][0], self.topic)

    def test_user_view(self):
        resp = self.client.get(reverse('pybb:user', kwargs={'username': self.user.username}))
        self.assertEqual(resp.status_code, 200)

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
        self.category = Category(name='foo')
        self.category.save()
        self.forum = Forum(name='xfoo', description='bar', category=self.category)
        self.forum.save()
        self.topic = Topic(name='etopic', forum=self.forum, user=self.user)
        self.topic.save()

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

        # Post is not visible by others
        client = Client()
        response = client.get(post.get_absolute_url(), follow=True)
        self.assertEqual(response.status_code, 403)
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
        response = self.client.post(add_topic_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'new topic test')

        client = Client()
        response = client.get(self.forum.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'new topic name')
        response = client.get(Topic.objects.get(name='new topic name').get_absolute_url())
        self.assertEqual(response.status_code, 403)
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

    def test_attachment(self):
        add_post_url = reverse('pybb:add_post', kwargs={'topic_id': self.topic.id})
        self.login_client()
        response = self.client.get(add_post_url)
        values = self.get_form_values(response)
        values['body'] = 'test attachment'
        values['attachments-0-file'] = self.file
        response = self.client.post(add_post_url, values, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test attachment')

    def tearDown(self):
        defaults.PYBB_ATTACHMENT_ENABLE = self.PYBB_ATTACHMENT_ENABLE
        defaults.PYBB_PREMODERATION = self.ORIG_PYBB_PREMODERATION