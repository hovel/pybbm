# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
from django.conf import settings
from django.utils.html import escape
from pybb.defaults import PYBB_SMILES, PYBB_SMILES_PREFIX
from django.forms import Textarea


def smile_it(s):
    for smile, url in PYBB_SMILES.items():
        s = s.replace(smile, '<img src="%s%s%s" alt="smile" />' % (settings.STATIC_URL, PYBB_SMILES_PREFIX, url))
    return s


def filter_blanks(user, str):
    """
    Replace more than 3 blank lines with only 1 blank line
    """
    return re.sub(r'\n{2}\n+', '\n', str)


def rstrip_str(user, str):
    """
    Replace strings with spaces (tabs, etc..) only with newlines
    Remove blank line at the end
    """
    return '\n'.join([s.rstrip() for s in str.splitlines()])


class BaseParser(object):
    widget_class = Textarea

    def format_attachments(self, text, attachments):
        """
        Replaces attachment's references ([file-\d+]) inside a text with their related (web) URL

        :param text: text which contains attachment's references
        :type text: str or unicode
        :param attachments: related attached files
        :type attachments: Quersyset from a model with a "file" attribute.
        :returns: str or unicode with [file-\d+] replaced by related file's (web) URL
        """

        refs = re.findall( '\[file-([1-9][0-9]*)\]', text)
        if not refs:
            return text
        refs = sorted(set(refs))

        max_ref = attachments.count()
        if not max_ref:
            return text
        refs = [int(ref) for ref in refs if int(ref) <= max_ref]
        attachments = [a for a  in attachments.order_by('pk')[0:max(refs)]]
        for ref in refs:
            text = text.replace('[file-%d]' % ref, attachments[ref-1].file.url)

        return text

    def format(self, text, instance=None):
        if instance and instance.pk:
            text = self.format_attachments(text, attachments=instance.attachments.all())
        return escape(text)

    def quote(self, text, username=''):
        return text

    @classmethod
    def get_widget_cls(cls, **kwargs):
        """
        Returns the form widget class to use with this parser
        It allows you to define your own widget with custom class Media to add your
        javascript and CSS and/or define your custom "render" function
        which will allow you to add specific markup or javascript.
        """
        return cls.widget_class
