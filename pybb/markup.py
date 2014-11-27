# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import bbcode
import re
from django.conf import settings
from django.utils.html import urlize
from markdown import Markdown
from pybb.defaults import PYBB_SMILES, PYBB_SMILES_PREFIX


def smile_it(s):
    for smile, url in PYBB_SMILES.items():
        s = s.replace(smile, '<img src="%s%s%s" alt="smile" />' % (settings.STATIC_URL, PYBB_SMILES_PREFIX, url))
    return s


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


class BaseParser(object):
    def format(self, text):
        return text

    def quote(self, text, username=''):
        return text


class BBCodeParser(BaseParser):
    def _render_quote(self, name, value, options, parent, context):
        if options and 'quote' in options:
            origin_author_html = '<em>%s</em><br>' % options['quote']
        else:
            origin_author_html = ''
        return '<blockquote>%s%s</blockquote>' % (origin_author_html, value)

    def __init__(self):
        self._parser = bbcode.Parser()
        self._parser.add_simple_formatter('img', '<img src="%(value)s">', replace_links=False)
        self._parser.add_simple_formatter('code', '<pre><code>%(value)s</code></pre>',
                                          render_embedded=False, transform_newlines=False,
                                          swallow_trailing_newline=True)
        self._parser.add_formatter('quote', self._render_quote, strip=True, swallow_trailing_newline=True)

    def format(self, text):
        return smile_it(self._parser.format(text))

    def quote(self, text, username=''):
        return '[quote="%s"]%s[/quote]\n' % (username, text)


class MarkdownParser(BaseParser):
    def __init__(self):
        self._parser = Markdown(safe_mode='escape')

    def format(self, text):
        return urlize(smile_it(self._parser.convert(text)))

    def quote(self, text, username=''):
        return '>' + text.replace('\n', '\n>').replace('\r', '\n>') + '\n'

