# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from pybb.compat import get_user_model_path


@python_2_unicode_compatible
class PollAnswer(models.Model):
    topic = models.ForeignKey('Topic', related_name='poll_answers', verbose_name=_('Topic'))
    text = models.CharField(max_length=255, verbose_name=_('Text'))

    class Meta:
        verbose_name = _('Poll answer')
        verbose_name_plural = _('Polls answers')
        app_label = 'pybb'

    def __str__(self):
        return self.text

    def votes(self):
        return self.users.count()

    def votes_percent(self):
        topic_votes = self.topic.poll_votes()
        if topic_votes > 0:
            return 1.0 * self.votes() / topic_votes * 100
        else:
            return 0


@python_2_unicode_compatible
class PollAnswerUser(models.Model):
    poll_answer = models.ForeignKey(PollAnswer, related_name='users', verbose_name=_('Poll answer'))
    user = models.ForeignKey(get_user_model_path(), related_name='poll_answers', verbose_name=_('User'))
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Poll answer user')
        verbose_name_plural = _('Polls answers users')
        unique_together = (('poll_answer', 'user', ), )
        app_label = 'pybb'

    def __str__(self):
        return '%s - %s' % (self.poll_answer.topic, self.user)
