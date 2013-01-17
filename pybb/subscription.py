# -*- coding: utf-8 -*-

from django.conf import settings
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.utils import translation
from django.contrib.sites.models import Site
from django import forms

from pybb import defaults

if defaults.PYBB_USE_DJANGO_MAILER:
    try:
        from mailer import send_mail
    except ImportError:
        from django.core.mail import send_mail
else:
    from django.core.mail import send_mail


email_validator = forms.EmailField()

def notify_topic_subscribers(post):
    topic = post.topic
    if post != topic.head:
        for user in topic.subscribers.all():
            if user != post.user:
                try:
                    email_validator.clean(user.email)
                except:
                    #invalid email
                    continue
                old_lang = translation.get_language()
                lang = user.get_profile().language or settings.LANGUAGE_CODE
                translation.activate(lang)
                delete_url = reverse('pybb:delete_subscription', args=[post.topic.id])
                current_site = Site.objects.get_current()
                subject = render_to_string('pybb/mail_templates/subscription_email_subject.html',
                                           { 'site': current_site,
                                             'post': post
                                           })
                # Email subject *must not* contain newlines
                subject = ''.join(subject.splitlines())
                message = render_to_string('pybb/mail_templates/subscription_email_body.html',
                                           { 'site': current_site,
                                             'post': post,
                                             'delete_url': delete_url,
                                             })
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
                translation.activate(old_lang)
