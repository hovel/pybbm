# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.html import urlize
from .util import smile_it

PARSERS = {}

def init_bbcode_parser():
    if 'bbcode' in PARSERS:
        return
    import bbcode
    from .util import _render_quote
    PARSERS['bbcode'] = bbcode.Parser()
    PARSERS['bbcode'].add_simple_formatter(
        'img', '<img src="%(value)s">', replace_links=False)
    PARSERS['bbcode'].add_simple_formatter(
        'code', '<pre><code>%(value)s</code></pre>', render_embedded=False, transform_newlines=False, swallow_trailing_newline=True)
    PARSERS['bbcode'].add_formatter(
        'quote', _render_quote, strip=True, swallow_trailing_newline=True)

def init_markdown_parser():
    from markdown import Markdown
    if 'markdown' in PARSERS:
        return
    PARSERS['markdown'] = Markdown(safe_mode='escape')


def bbcode(s):
    return smile_it(PARSERS['bbcode'].format(s))


def bbcode_quote(text, username=''):
    return '[quote="%s"]%s[/quote]\n' % (username, text)


def markdown(s):
    return urlize(smile_it(PARSERS['markdown'].convert(s)))


def markdown_quote(text, username=''):
    return '>'+text.replace('\n','\n>').replace('\r','\n>') + '\n'


