# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _

from pybb import defaults
from pybb.util import FilePathGenerator

from pybb.models.post import Post

class Attachment(models.Model):
    class Meta(object):
        verbose_name = _('Attachment')
        verbose_name_plural = _('Attachments')

    post = models.ForeignKey(Post, verbose_name=_('Post'), related_name='attachments')
    size = models.IntegerField(_('Size'))
    file = models.FileField(_('File'),
                            upload_to=FilePathGenerator(to=defaults.PYBB_ATTACHMENT_UPLOAD_TO))

    def save(self, *args, **kwargs):
        self.size = self.file.size
        super(Attachment, self).save(*args, **kwargs)

    def size_display(self):
        size = self.size
        if size < 1024:
            return '%db' % size
        elif size < 1024 * 1024:
            return '%dKb' % int(size / 1024)
        else:
            return '%.2fMb' % (size / float(1024 * 1024))
