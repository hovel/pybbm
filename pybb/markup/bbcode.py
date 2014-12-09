# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from bbcode import Parser
from pybb.markup.base import smile_it, BaseParser


class BBCodeParser(BaseParser):
    def _render_quote(self, name, value, options, parent, context):
        if options and 'quote' in options:
            origin_author_html = '<em>%s</em><br>' % options['quote']
        else:
            origin_author_html = ''
        return '<blockquote>%s%s</blockquote>' % (origin_author_html, value)

    def __init__(self):
        self._parser = Parser()
        self._parser.add_simple_formatter('img', '<img src="%(value)s">', replace_links=False)
        self._parser.add_simple_formatter('code', '<pre><code>%(value)s</code></pre>',
                                          render_embedded=False, transform_newlines=False,
                                          swallow_trailing_newline=True)
        self._parser.add_formatter('quote', self._render_quote, strip=True, swallow_trailing_newline=True)

    def format(self, text):
        return smile_it(self._parser.format(text))

    def quote(self, text, username=''):
        return '[quote="%s"]%s[/quote]\n' % (username, text)
