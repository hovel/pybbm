# coding=utf-8
from __future__ import unicode_literals

import django
from django.conf import settings
from django.utils.encoding import force_text
from unidecode import unidecode
from pybb import defaults

if defaults.PYBB_USE_DJANGO_MAILER:
    from mailer import send_html_mail, send_mail
else:
    from django.core.mail import send_mail, get_connection
    from django.core.mail.message import EmailMultiAlternatives

    def send_html_mail(subject, text_msg, html_msg, sender, recipient, 
            fail_silently=False, auth_user=None, auth_password=None, connection=None):
        """Sends an email with HTML alternative."""
        connection = connection or get_connection(username=auth_user,
                                    password=auth_password,
                                    fail_silently=fail_silently)
        msg = EmailMultiAlternatives(subject, text_msg, sender, recipient, connection=connection)
        msg.attach_alternative(html_msg, "text/html")
        msg.send()


def send_mass_html_mail(emails, *args, **kwargs):
    """
    Sends emails with html alternative if email item has html content.
    Email item is a tuple with an optionnal html message version :
        (subject, text_msg, sender, recipient, [html_msg])
    """
    for email in emails:
        subject, text_msg, sender, recipient = email[0:4]
        html_msg = email[4] if len(email) > 4 else ''
        if html_msg:
            send_html_mail(subject, text_msg, html_msg, sender, recipient, *args, **kwargs)
        else:
            send_mail(subject, text_msg, sender, recipient, *args, **kwargs)

def get_image_field_class():
    try:
        from PIL import Image
    except ImportError:
        from django.db.models import FileField
        return FileField
    try:
        from sorl.thumbnail import ImageField
    except ImportError:
        from django.db.models import ImageField
    return ImageField


def get_image_field_full_name():
    try:
        from PIL import Image
    except ImportError:
        return 'django.db.models.fields.files.FileField'
    try:
        from sorl.thumbnail import ImageField
        name = 'sorl.thumbnail.fields.ImageField'
    except ImportError:
        from django.db.models import ImageField
        name = 'django.db.models.fields.files.ImageField'
    return name


def get_user_model():
    from django.contrib.auth import get_user_model
    return get_user_model()


def get_user_model_path():
    return getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


def get_username_field():
    return get_user_model().USERNAME_FIELD


def get_atomic_func():
    from django.db.transaction import atomic as atomic_func
    return atomic_func


def get_paginator_class():
    try:
        from pure_pagination import Paginator
        pure_pagination = True
    except ImportError:
        # the simplest emulation of django-pure-pagination behavior
        from django.core.paginator import Paginator, Page
        class PageRepr(int):
            def querystring(self):
                return 'page=%s' % self
        Page.pages = lambda self: [PageRepr(i) for i in range(1, self.paginator.num_pages + 1)]
        pure_pagination = False

    return Paginator, pure_pagination


def is_installed(app_name):
    from django.apps import apps
    return apps.is_installed(app_name)


def get_related_model_class(parent_model, field_name):
    return parent_model._meta.get_field(field_name).related_model


def slugify(text):
    """
    Slugify function that supports unicode symbols
    :param text: any unicode text
    :return: slugified version of passed text
    """
    from django.utils.text import slugify as django_slugify

    return django_slugify(force_text(unidecode(text)))


def is_authenticated(user):
    if django.VERSION > (1, 9):
        return user.is_authenticated

    return user.is_authenticated()


def is_anonymous(user):
    if django.VERSION > (1, 9):
        return user.is_anonymous

    return user.is_anonymous()
