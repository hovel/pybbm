# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import re
import uuid
import django
from django.utils.translation import ugettext as _


def unescape(text):
    """
    Do reverse escaping.
    """
    return text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', '\'')


def filter_blanks(user, str):
    """
    Replace more than 3 blank lines with only 1 blank line
    """
    if user.is_staff:
        return str
    return re.sub(r'\n{2}\n+', '\n', str)


def rstrip_str(user, str):
    """
    Replace strings with spaces (tabs, etc..) only with newlines
    Remove blank line at the end
    """
    if user.is_staff:
        return str
    return '\n'.join([s.rstrip() for s in str.splitlines()])


def get_user_model():
    if django.VERSION[:2] >= (1, 5):
        from django.contrib.auth import get_user_model
        return get_user_model()
    else:
        from django.contrib.auth.models import User
        User.get_username = lambda u: u.username  # emulate new 1.5 method
        return User


def get_user_model_path():
    User = get_user_model()
    return "%s.%s" % (User._meta.app_label, User._meta.object_name)


def get_username_field():
    if django.VERSION[:2] >= (1, 5):
        return get_user_model().USERNAME_FIELD
    else:
        return 'username'


def get_pybb_profile(user):
    from pybb import defaults

    if not user.is_authenticated():
        if defaults.PYBB_ENABLE_ANONYMOUS_POST:
            user = get_user_model().objects.get(**{get_username_field(): defaults.PYBB_ANONYMOUS_USERNAME})
        else:
            raise ValueError(_('Can\'t get profile for anonymous user'))

    if defaults.PYBB_PROFILE_RELATED_NAME:
        return getattr(user, defaults.PYBB_PROFILE_RELATED_NAME)
    else:
        return user


def get_pybb_profile_model():
    from pybb import defaults
    if defaults.PYBB_PROFILE_RELATED_NAME:
        return getattr(get_user_model(), defaults.PYBB_PROFILE_RELATED_NAME).related.model
    else:
        return get_user_model()


def build_cache_key(key_name, **kwargs):
    if key_name == 'anonymous_topic_views':
        return 'pybbm_anonymous_topic_%s_views' % kwargs['topic_id']
    else:
        raise ValueError('Wrong key_name parameter passed: %s' % key_name)


def get_file_path(instance, filename, to):
    """
    This function generate filename with uuid4
    it's useful if:
    - you don't want to allow others to see original uploaded filenames
    - users can upload images with unicode in filenames wich can confuse browsers and filesystem
    """
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join(to, filename)


def get_user_frozen_models(user_model):
    from south.creator.freezer import freeze_apps
    user_app, user_model = user_model.split('.')
    if user_model != 'auth.User':
        from south.migration.base import Migrations
        from south.exceptions import NoMigrations
        try:
            user_migrations = Migrations(user_app)
        except NoMigrations:
            extra_model = freeze_apps(user_app)
        else:
            from pybb import defaults
            migration_name = defaults.PYBB_INITIAL_CUSTOM_USER_MIGRATION
            initial_user_migration = user_migrations.migration(migration_name)
            extra_model = initial_user_migration.migration_class().models
    else:
        extra_model = freeze_apps(user_app)
    return extra_model
