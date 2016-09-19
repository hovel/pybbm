# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.validators import validate_email
from django.template.loader import render_to_string
from django.utils import translation
from django.contrib.sites.models import Site

from pybb import defaults, util, compat
from pybb.models import ForumSubscription

if defaults.PYBB_USE_DJANGO_MAILER:
    try:
        from mailer import send_mass_mail
    except ImportError:
        from django.core.mail import send_mass_mail
else:
    from django.core.mail import send_mass_mail


def notify_forum_subscribers(topic):
    forum = topic.forum
    qs = ForumSubscription.objects.exclude(user=topic.user).filter(forum=topic.forum)
    notifications = qs.filter(type=ForumSubscription.TYPE_NOTIFY)
    if notifications.count():
        users = (n.user for n in notifications.select_related('user'))
        context = {
            'manage_url': reverse('pybb:forum_subscription', kwargs={'pk': forum.id}),
            'topic': topic,
        }
        send_notification(users, 'forum_subscription_email', context)
    subscriptions = qs.filter(type=ForumSubscription.TYPE_SUBSCRIBE)
    if subscriptions.count():
        users = (s.user for s in subscriptions.select_related('user'))
        topic.subscribers.add(*users)


def notify_topic_subscribers(post):
    topic = post.topic
    users = topic.subscribers.exclude(pk=post.user.pk)
    if users.count():
        # Define constants for templates rendering
        context = {
            'delete_url': reverse('pybb:delete_subscription', args=[post.topic.id]),
            'post': post,
        }
        send_notification(users, 'subscription_email', context)


def send_notification(users, template, context={}):
    if not 'site' in context:
        context['site'] = Site.objects.get_current()
    old_lang = translation.get_language()
    from_email = settings.DEFAULT_FROM_EMAIL

    mails = tuple()
    for user in users:
        if not getattr(util.get_pybb_profile(user), 'receive_emails', True):
            continue

        try:
            validate_email(user.email)
        except:
            # Invalid email
            continue

        if user.email == '%s@example.com' % getattr(user, compat.get_username_field()):
            continue

        context['user'] = user

        lang = util.get_pybb_profile(user).language or settings.LANGUAGE_CODE
        translation.activate(lang)

        subject = render_to_string('pybb/mail_templates/%s_subject.html' % template, context)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())

        message = render_to_string('pybb/mail_templates/%s_body.html' % template, context)
        mails += ((subject, message, from_email, [user.email]),)

    # Send mails
    send_mass_mail(mails, fail_silently=True)

    # Reactivate previous language
    translation.activate(old_lang)
