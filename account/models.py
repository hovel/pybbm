# -*- coding: utf-8

from datetime import datetime

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from account.managers import OneTimeCodeManager

class OneTimeCode(models.Model):
    """
    Model which stores onetimecodes which are used for
    authentication with the URL.
    """

    code = models.CharField(_('Code'), max_length=40, primary_key=True)
    user = models.ForeignKey(User, verbose_name=_('User'))
    action = models.CharField(_('Action'), blank=True, null=True, max_length=20)
    data = models.TextField(_('Data'), blank=True, null=True)
    time = models.DateTimeField(_('Creation time'), blank=True)

    objects = OneTimeCodeManager()

    def save(self):
        if not self.time:
            self.time = datetime.now()
        super(OneTimeCode, self).save()


    def __unicode__(self):
        return self.code


    class Admin:
        list_display = ['code', 'user', 'action']


    class Meta:
        ordering = ['-time']
