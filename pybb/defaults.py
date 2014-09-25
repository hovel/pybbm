# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os.path

from django.conf import settings

from pybb.util import filter_blanks, rstrip_str


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
PYBB_POST_SORT_REVERSE = getattr(settings, 'PYBB_POST_SORT_REVERSE', False )


import bbcode
from markdown import Markdown
from django.utils.html import urlize
import pdb

import re


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

def smile_it(str):
    s = str
    for smile, url in PYBB_SMILES.items():
        s = s.replace(smile, '<img src="%s%s%s" alt="smile" />' % (settings.STATIC_URL, PYBB_SMILES_PREFIX, url))
    return s

bbcode_parser = bbcode.Parser()
#Removed in favorof enhanced parser
#bbcode_parser.add_simple_formatter('img', '<img src="%(value)s">', replace_links=False)
bbcode_parser.add_simple_formatter('img', '<img src="%(value)s"  class="img-responsive img-responsive-post"/>',  replace_links=False)
bbcode_parser.add_simple_formatter('code', '<pre><code>%(value)s</code></pre>', render_embedded=False, transform_newlines=False, swallow_trailing_newline=True)
def _render_quote(name, value, options, parent, context):
    if options and 'quote' in options:
        origin_author_html = '<em>%s</em><br>' % options['quote']
    else:
        origin_author_html = ''
    return '<blockquote>%s%s</blockquote>' % (origin_author_html, value)
bbcode_parser.add_formatter('quote', _render_quote, strip=True, swallow_trailing_newline=True)

def _render_size(name, value, options,parent, context):
    

    if options['size']=="50":
        return '<font size="2"> %s </font>' % (value)
    if options['size']=="100":
        return '<font size="4"> %s </font>' % (value)
    if options['size']=="200":
        return '<font size="6"> %s </font>' % (value)    

bbcode_parser.add_formatter('size', _render_size, swallow_trailing_newline=True)

def _render_youtube(name, value, options, parent, context):
    result = re.match('^[^v]+v=(.{11}).*', options['youtube'])
    return """<div class="embed-responsive embed-responsive-16by9"><object > <param name="movie" value="http://www.youtube.com/v/%s"></param>  
                <param name="allowFullScreen" value="true"></param><param name="allowscriptaccess" value="always"></param> 
                <embed src="http://www.youtube.com/v/%s" type="application/x-shockwave-flash" allowscriptaccess="always" 
                allowfullscreen="true" ></embed> </object></div> """ % (result.group(1) , result.group(1))
  
bbcode_parser.add_formatter('youtube', _render_youtube, swallow_trailing_newline=True)

PYBB_MARKUP_ENGINES = getattr(settings, 'PYBB_MARKUP_ENGINES', {
    'bbcode': lambda str: smile_it(bbcode_parser.format(str)),
    'markdown': lambda str: urlize(smile_it(Markdown(safe_mode='escape').convert(str)))
})

PYBB_QUOTE_ENGINES = getattr(settings, 'PYBB_QUOTE_ENGINES', {
    'bbcode': lambda text, username="": '[quote="%s"]%s[/quote]\n' % (username, text),
    'markdown': lambda text, username="": '>'+text.replace('\n','\n>').replace('\r','\n>') + '\n'
})

PYBB_MARKUP = getattr(settings, 'PYBB_MARKUP', 'bbcode')

PYBB_TEMPLATE = getattr(settings, 'PYBB_TEMPLATE', "base.html")
PYBB_DEFAULT_AUTOSUBSCRIBE = getattr(settings, 'PYBB_DEFAULT_AUTOSUBSCRIBE', True)
PYBB_ENABLE_ANONYMOUS_POST = getattr(settings, 'PYBB_ENABLE_ANONYMOUS_POST', False)
PYBB_ANONYMOUS_USERNAME = getattr(settings, 'PYBB_ANONYMOUS_USERNAME', 'Anonymous')
PYBB_ANONYMOUS_VIEWS_CACHE_BUFFER = getattr(settings, 'PYBB_ANONYMOUS_VIEWS_CACHE_BUFFER', 100)

PYBB_PREMODERATION = getattr(settings, 'PYBB_PREMODERATION', False)

PYBB_BODY_CLEANERS = getattr(settings, 'PYBB_BODY_CLEANERS', [rstrip_str, filter_blanks])

PYBB_BODY_VALIDATOR = getattr(settings, 'PYBB_BODY_VALIDATOR', None)

PYBB_POLL_MAX_ANSWERS = getattr(settings, 'PYBB_POLL_MAX_ANSWERS', 10)

PYBB_AUTO_USER_PERMISSIONS = getattr(settings, 'PYBB_AUTO_USER_PERMISSIONS', True)

PYBB_USE_DJANGO_MAILER = getattr(settings, 'PYBB_USE_DJANGO_MAILER', False)

PYBB_PERMISSION_HANDLER = getattr(settings, 'PYBB_PERMISSION_HANDLER', 'pybb.permissions.DefaultPermissionHandler')

PYBB_PROFILE_RELATED_NAME = getattr(settings, 'PYBB_PROFILE_RELATED_NAME', 'pybb_profile')

PYBB_INITIAL_CUSTOM_USER_MIGRATION = getattr(settings, 'PYBB_INITIAL_CUSTOM_USER_MIGRATION', None)
