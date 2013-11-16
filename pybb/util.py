# -*- coding: utf-8 -*-

import re
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
            raise ValueError(_(u'Can\'t get profile for anonymous user'))

    if defaults.PYBB_PROFILE_RELATED_NAME:
        return getattr(user, defaults.PYBB_PROFILE_RELATED_NAME)
    else:
        return user


def get_pybb_profile_model():
    from pybb import defaults
    if defaults.PYBB_PROFILE_RELATED_NAME:
        return get_user_model()._meta.get_field_by_name(defaults.PYBB_PROFILE_RELATED_NAME)[0].model
    else:
        return get_user_model()


def build_cache_key(key_name, **kwargs):
    if key_name == 'anonymous_topic_views':
        return 'pybbm_anonymous_topic_%s_views' % kwargs['topic_id']
    else:
        raise ValueError('Wrong key_name parameter passed: %s' % key_name)