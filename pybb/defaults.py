# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os.path

from django.conf import settings

PYBB_TOPIC_PAGE_SIZE = getattr(settings, 'PYBB_TOPIC_PAGE_SIZE', 10)
PYBB_FORUM_PAGE_SIZE = getattr(settings, 'PYBB_FORUM_PAGE_SIZE', 20)
PYBB_AVATAR_WIDTH = getattr(settings, 'PYBB_AVATAR_WIDTH', 80)
PYBB_AVATAR_HEIGHT = getattr(settings, 'PYBB_AVATAR_HEIGHT',80)
PYBB_MAX_AVATAR_SIZE = getattr(settings, 'PYBB_MAX_AVATAR_SIZE', 1024*50)
PYBB_DEFAULT_TIME_ZONE = getattr(settings, 'PYBB_DEFAULT_TIME_ZONE', 3)

PYBB_SIGNATURE_MAX_LENGTH = getattr(settings, 'PYBB_SIGNATURE_MAX_LENGTH', 1024)
PYBB_SIGNATURE_MAX_LINES = getattr(settings, 'PYBB_SIGNATURE_MAX_LINES', 3)

PYBB_DEFAULT_MARKUP = getattr(settings, 'PYBB_DEFAULT_MARKUP', 'bbcode')
PYBB_FREEZE_FIRST_POST = getattr(settings, 'PYBB_FREEZE_FIRST_POST', False)

PYBB_ATTACHMENT_SIZE_LIMIT = getattr(settings, 'PYBB_ATTACHMENT_SIZE_LIMIT', 1024 * 1024)
PYBB_ATTACHMENT_ENABLE = getattr(settings, 'PYBB_ATTACHMENT_ENABLE', False)
PYBB_ATTACHMENT_UPLOAD_TO = getattr(settings, 'PYBB_ATTACHMENT_UPLOAD_TO', os.path.join('pybb_upload', 'attachments'))

PYBB_DEFAULT_AVATAR_URL = getattr(settings,'PYBB_DEFAULT_AVATAR_URL',
    getattr(settings, 'STATIC_URL', '') + 'pybb/img/default_avatar.jpg')

PYBB_DEFAULT_TITLE = getattr(settings, 'PYBB_DEFAULT_TITLE', 'PYBB Powered Forum')

PYBB_SMILES_PREFIX = getattr(settings, 'PYBB_SMILES_PREFIX', 'pybb/emoticons/')

PYBB_SMILES = getattr(settings, 'PYBB_SMILES', {
    '&gt;_&lt;': 'angry.png',
    ':.(': 'cry.png',
    'o_O': 'eyes.png',
    '[]_[]': 'geek.png',
    '8)': 'glasses.png',
    ':D': 'lol.png',
    ':(': 'sad.png',
    ':O': 'shok.png',
    '-_-': 'shy.png',
    ':)': 'smile.png',
    ':P': 'tongue.png',
    ';)': 'wink.png'
})

#TODO In a near future, this code will be deleted when callable settings will not 
#supported anymore.
import warnings
from django.utils.six import string_types
from django.utils.translation import ugettext as _
warning = _('%(setting_name)s should not be a callabled anymore but a path to the callable.'\
    'ex : myproject.markup_engines.my_own_bbcode')


def deprecated_check(setting_name):
    setting = globals().get(setting_name)
    values = setting if type(setting) is not dict else setting.values()
    for value in values:
        if isinstance(value, string_types):
            continue
        warnings.warn(
            warning % {'setting_name':setting_name,}, 
            DeprecationWarning
        )

if not hasattr(settings, 'PYBB_MARKUP_ENGINES'):
    #TODO In a near future, thoses settings will be pathes to callable
    #We let it "as it" for now for backward compatibility
    from .markup_engines import init_bbcode_parser, init_markdown_parser, bbcode, markdown
    init_bbcode_parser()
    init_markdown_parser()
    PYBB_MARKUP_ENGINES = {'bbcode':bbcode, 'markdown': markdown,}
else:
    PYBB_MARKUP_ENGINES = getattr(settings, 'PYBB_MARKUP_ENGINES')
    deprecated_check('PYBB_MARKUP_ENGINES')

if not hasattr(settings, 'PYBB_QUOTE_ENGINES'):
    #TODO In a near future, thoses settings will be pathes to callable
    #We let it "as it" for now for backward compatibility
    from .markup_engines import bbcode_quote, markdown_quote
    PYBB_QUOTE_ENGINES = {'bbcode': bbcode_quote, 'markdown': markdown_quote,}
else:
    PYBB_QUOTE_ENGINES = getattr(settings, 'PYBB_QUOTE_ENGINES')
    deprecated_check('PYBB_QUOTE_ENGINES')

PYBB_MARKUP = getattr(settings, 'PYBB_MARKUP', None)
if not PYBB_MARKUP or not PYBB_MARKUP in PYBB_MARKUP_ENGINES:
    if not PYBB_MARKUP_ENGINES:
        PYBB_MARKUP = None
    elif 'bbcode' in PYBB_MARKUP_ENGINES:
        #Backward compatibility. bbcode is the default markup
        PYBB_MARKUP = 'bbcode'
    else:
        #If a dev define his own markups, auto choose the first one to save a line in settings :)
        PYBB_MARKUP_ENGINES.keys()[0]

PYBB_TEMPLATE = getattr(settings, 'PYBB_TEMPLATE', "base.html")
PYBB_DEFAULT_AUTOSUBSCRIBE = getattr(settings, 'PYBB_DEFAULT_AUTOSUBSCRIBE', True)
PYBB_ENABLE_ANONYMOUS_POST = getattr(settings, 'PYBB_ENABLE_ANONYMOUS_POST', False)
PYBB_ANONYMOUS_USERNAME = getattr(settings, 'PYBB_ANONYMOUS_USERNAME', 'Anonymous')
PYBB_ANONYMOUS_VIEWS_CACHE_BUFFER = getattr(settings, 'PYBB_ANONYMOUS_VIEWS_CACHE_BUFFER', 100)

PYBB_PREMODERATION = getattr(settings, 'PYBB_PREMODERATION', False)

if not hasattr(settings, 'PYBB_BODY_CLEANERS'):
    #TODO In a near future, thoses settings will be pathes to callable
    #We let it "as it" for now for backward compatibility
    from pybb.util import filter_blanks, rstrip_str
    PYBB_BODY_CLEANERS = [rstrip_str, filter_blanks]
else:
    PYBB_BODY_CLEANERS = getattr(settings, 'PYBB_BODY_CLEANERS')
    deprecated_check('PYBB_BODY_CLEANERS')

PYBB_BODY_VALIDATOR = getattr(settings, 'PYBB_BODY_VALIDATOR', None)

PYBB_POLL_MAX_ANSWERS = getattr(settings, 'PYBB_POLL_MAX_ANSWERS', 10)

PYBB_AUTO_USER_PERMISSIONS = getattr(settings, 'PYBB_AUTO_USER_PERMISSIONS', True)

PYBB_USE_DJANGO_MAILER = getattr(settings, 'PYBB_USE_DJANGO_MAILER', False)

PYBB_PERMISSION_HANDLER = getattr(settings, 'PYBB_PERMISSION_HANDLER', 'pybb.permissions.DefaultPermissionHandler')

PYBB_PROFILE_RELATED_NAME = getattr(settings, 'PYBB_PROFILE_RELATED_NAME', 'pybb_profile')

PYBB_INITIAL_CUSTOM_USER_MIGRATION = getattr(settings, 'PYBB_INITIAL_CUSTOM_USER_MIGRATION', None)

#Backward compatibility : import old functions which was defined here if some devs did used it
#TODO in a near future : delete those imports
from .util import smile_it, _render_quote
from .markup_engines import bbcode, markdown
