# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.validators import validate_email
from django.template.loader import render_to_string
from django.utils import translation
from django.contrib.sites.models import Site

from pybb import defaults, util, compat

from pybb.compat import send_mass_html_mail


def notify_topic_subscribers(post):
    topic = post.topic
    if post != topic.head:
        old_lang = translation.get_language()

        # Define constants for templates rendering
        delete_url = reverse('pybb:delete_subscription', args=[post.topic.id])
        current_site = Site.objects.get_current()
        from_email = settings.DEFAULT_FROM_EMAIL
        context = {
            'post': post,
            'post_url': 'http://%s%s' % (current_site, post.get_absolute_url()),
            'topic_url': 'http://%s%s' % (current_site, post.topic.get_absolute_url()),
            'delete_url_full': 'http://%s%s' % (current_site, delete_url),

            #backward compat only. TODO Delete those vars in next major release
            #and rename delete_url_full with delete_url for consistency
            'site': current_site,
            'delete_url': delete_url,
        }
        base_tpl = 'pybb/mail_templates/subscription_email_'

        mails = []
        for user in topic.subscribers.exclude(pk=post.user.pk):
            try:
                validate_email(user.email)
            except:
                # Invalid email
                continue

            if user.email == '%s@example.com' % getattr(user, compat.get_username_field()):
                continue

            lang = util.get_pybb_profile(user).language or settings.LANGUAGE_CODE
            translation.activate(lang)
            subject = render_to_string('%ssubject.html' % base_tpl, context)
            # Email subject *must not* contain newlines
            subject = ''.join(subject.splitlines())
            context.update({
                'user': user,
                'subject': subject,
            })
            txt_message = render_to_string('%sbody.html' % base_tpl, context)
            html_message = render_to_string('%sbody-html.html' % base_tpl, context)
            mails.append((subject, txt_message, from_email, [user.email], html_message))

        # Send mails
        send_mass_html_mail(mails, fail_silently=True)

        # Reactivate previous language
        translation.activate(old_lang)
