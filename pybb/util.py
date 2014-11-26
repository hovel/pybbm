# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import re
import uuid

from django.utils.importlib import import_module
from django.utils.six import string_types
from django.utils.translation import ugettext as _

from pybb.compat import get_username_field, get_user_model

MARKUP_ENGINES = {}
QUOTE_ENGINES = {}
SMILES_DICT = None

def _init_smilies():
    """
    Initializes the smilies replacement only once
    This is in a function to avoid recursive import problems because we need
    some pybb.defaults and pybb.defaults, for backward compat reason, need smile_it
    
    """
    global SMILES_DICT
    if SMILES_DICT is not None:
        return
    from django.conf import settings
    from pybb.defaults import PYBB_SMILES, PYBB_SMILES_PREFIX
    if PYBB_SMILES:
        SMILES_DICT = {}
        for smile, url in PYBB_SMILES.items():
            SMILES_DICT[smile] = '<img src="%s%s%s" alt="smile" />' % (
                settings.STATIC_URL, 
                PYBB_SMILES_PREFIX, 
                url
            )
    else:
        SMILES_DICT = False


def smile_it(s):
    global SMILES_DICT
    if SMILES_DICT is None:
        _init_smilies()
    for k, v in SMILES_DICT.items():
        s = s.replace(k, v)
    return s

def _render_quote(name, value, options, parent, context):
    if options and 'quote' in options:
        origin_author_html = '<em>%s</em><br>' % options['quote']
    else:
        origin_author_html = ''
    return '<blockquote>%s%s</blockquote>' % (origin_author_html, value)


def import_from_path(path):
    if path :
        path = path.split('.')
        to_import = path.pop()
        module = import_module('.'.join(path))
        if module :
            return getattr(module, to_import)
    return None


def get_markup_engine(name=None):
    """
    Returns the named parse engine, or the default parser if name is not given.
    """
    if not name:
        from pybb.defaults import PYBB_MARKUP
        name = PYBB_MARKUP
    if name not in MARKUP_ENGINES:
        from pybb.defaults import PYBB_MARKUP_ENGINES
        if not name in PYBB_MARKUP_ENGINES:
            return
        engine = PYBB_MARKUP_ENGINES.get(name)
        if isinstance(engine, string_types):
            #This is a path, import it
            engine = import_from_path(engine)
        MARKUP_ENGINES[name] = engine
    return MARKUP_ENGINES.get(name, None)


def get_quote_engine(name=None):
    """
    Returns the named quote engine, or the default quoter if name is not given.
    """
    if not name:
        from pybb.defaults import PYBB_MARKUP
        name = PYBB_MARKUP
    if name not in QUOTE_ENGINES:
        from pybb.defaults import PYBB_QUOTE_ENGINES
        if not name in PYBB_QUOTE_ENGINES:
            return
        engine = PYBB_QUOTE_ENGINES.get(name)
        #TODO In a near future, we should stop to support callable :
        #settings files should be simplest as possible and not define or import things.
        if isinstance(engine, string_types):
            #This is a path, import it
            engine = import_from_path(engine)
        QUOTE_ENGINES[name] = engine
    return QUOTE_ENGINES.get(name, None)


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
