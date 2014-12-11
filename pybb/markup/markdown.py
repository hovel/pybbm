# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from markdown import Markdown
from django.template import Context
from django.template.loader import get_template
from django.utils.html import urlize
from pybb.markup.base import smile_it, BaseParser


class MarkdownParser(BaseParser):

    class Widget(BaseParser.Widget):
        class Media:
            css = {
                'all':(
                    'markitup/skins/simple/style.css',
                    'markitup/sets/markdown/style.css',
                ),
            }
            js = (
                'markitup/ajax_csrf.js',
                'markitup/jquery.markitup.js',
                'markitup/sets/markdown/set.js',
                'pybb/js/markitup.js',
            )

        def render(self, *args, **kwargs):
            tpl = get_template('pybb/markup/markdown_widget.html')
            ctx = Context({'widget_output':super(MarkdownParser.Widget, self).render(*args, **kwargs)})
            return tpl.render(ctx)

    def __init__(self):
        self._parser = Markdown(safe_mode='escape')

    def format(self, text):
        return urlize(smile_it(self._parser.convert(text)))

    def quote(self, text, username=''):
        return '>' + text.replace('\n', '\n>').replace('\r', '\n>') + '\n'
