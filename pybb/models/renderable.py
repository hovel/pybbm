# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _

from pybb.util import unescape, _get_markup_formatter


class RenderableItem(models.Model):
    """
    Base class for models that has markup, body, body_text and body_html fields.
    """

    class Meta(object):
        abstract = True

    body = models.TextField(_('Message'))
    body_html = models.TextField(_('HTML version'))
    body_text = models.TextField(_('Text version'))

    def render(self):
        self.body_html = _get_markup_formatter()(self.body)
        # Remove tags which was generated with the markup processor
        text = strip_tags(self.body_html)
        # Unescape entities which was generated with the markup processor
        self.body_text = unescape(text)
