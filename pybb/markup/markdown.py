# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from markdown import Markdown
from django.utils.html import urlize
from pybb.markup.base import smile_it, BaseParser


class MarkdownParser(BaseParser):
    def __init__(self):
        self._parser = Markdown(safe_mode='escape')

    def format(self, text):
        return urlize(smile_it(self._parser.convert(text)))

    def quote(self, text, username=''):
        return '>' + text.replace('\n', '\n>').replace('\r', '\n>') + '\n'
