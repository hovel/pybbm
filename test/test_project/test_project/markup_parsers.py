# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from pybb.markup.base import BaseParser
from pybb.markup.bbcode import BBCodeParser


class CustomBBCodeParser(BBCodeParser):
    def __init__(self):
        super(CustomBBCodeParser, self).__init__()
        self._parser.add_simple_formatter('ul', '<ul>%(value)s</ul>', transform_newlines=False, strip=True)
        self._parser.add_simple_formatter('li', '<li>%(value)s</li>', transform_newlines=False, strip=True)
        self._parser.add_simple_formatter('youtube',
                                          (
                                              '<iframe src="http://www.youtube.com/embed/%(value)s?wmode=opaque" '
                                              'data-youtube-id="%(value)s" allowfullscreen="" frameborder="0" '
                                              'height="315" width="560"></iframe>'
                                          ),
                                          replace_links=False)


class LiberatorParser(BaseParser):

    chains_to_freedom = (
        ('Windows', 'GNU Linux'),
        ('Mac OS', 'FreeBSD'),
        ('PHP', 'Python'),
    )

    def format(self, text):
        for r in self.chains_to_freedom:
            text = text.replace(*r)
        return text

    def quote(self, text, username=''):
        return 'posted by: %s\n%s' % (username, text) if username else text
