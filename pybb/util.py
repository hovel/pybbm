# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import re
import uuid
from django.utils.translation import ugettext as _
from pybb.compat import get_username_field, get_user_model


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


class FilePathGenerator(object):
    """
    Special class for generating random filenames
    Can be deconstructed for correct migration
    """
    def __init__(self, to, *args, **kwargs):
        self.to = to

    def deconstruct(self, *args, **kwargs):
        return 'pybb.util.FilePathGenerator', [], {'to': self.to}

    def __call__(self, instance, filename):
        """
        This function generate filename with uuid4
        it's useful if:
        - you don't want to allow others to see original uploaded filenames
        - users can upload images with unicode in filenames wich can confuse browsers and filesystem
        """
        ext = filename.split('.')[-1]
        filename = "%s.%s" % (uuid.uuid4(), ext)
        return os.path.join(self.to, filename)
