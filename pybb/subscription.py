# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.core.validators import validate_email
from django.template.loader import render_to_string
from django.utils import translation

from pybb import defaults, util, compat

if defaults.PYBB_USE_DJANGO_MAILER:
    try:
        from mailer import send_mass_mail
    except ImportError as e:
        raise ImproperlyConfigured('settings.PYBB_USE_DJANGO_MAILER is {0} but mailer could not be imported.'
                                   ' Original exception: {1}'.format(defaults.PYBB_USE_DJANGO_MAILER, e.message))
else:
    from django.core.mail import send_mass_mail


def notify_topic_subscribers(post, request, *args, **kwargs):
    if defaults.PYBB_DISABLE_NOTIFICATIONS:
        return
    topic = post.topic
    if post != topic.head:
        old_lang = translation.get_language()

        # Define constants for templates rendering
        delete_url = reverse('pybb:delete_subscription', args=[post.topic.id])
        current_site = compat.get_current_site(request)
        from_email = settings.DEFAULT_FROM_EMAIL

        subject = render_to_string('pybb/mail_templates/subscription_email_subject.html',
                                   {'site': current_site,
                                    'post': post})
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())

        mails = tuple()
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

            message = render_to_string('pybb/mail_templates/subscription_email_body.html',
                                       {'site': current_site,
                                        'post': post,
                                        'delete_url': delete_url,
                                        'user': user})
            mails += ((subject, message, from_email, [user.email]),)

        # Send mails
        send_mass_mail(mails, fail_silently=True)

        # Reactivate previous language
        translation.activate(old_lang)
