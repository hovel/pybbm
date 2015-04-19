# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, transaction, DatabaseError
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from pybb.compat import get_user_model_path, get_atomic_func


class TopicReadTrackerManager(models.Manager):
    def get_or_create_tracker(self, user, topic):
        """
        Correctly create tracker in mysql db on default REPEATABLE READ transaction mode

        It's known problem when standrard get_or_create method return can raise exception
        with correct data in mysql database.
        See http://stackoverflow.com/questions/2235318/how-do-i-deal-with-this-race-condition-in-django/2235624
        """
        is_new = True
        sid = transaction.savepoint(using=self.db)
        try:
            with get_atomic_func()():
                obj = TopicReadTracker.objects.create(user=user, topic=topic)
            transaction.savepoint_commit(sid)
        except DatabaseError:
            transaction.savepoint_rollback(sid)
            obj = TopicReadTracker.objects.get(user=user, topic=topic)
            is_new = False
        return obj, is_new


class TopicReadTracker(models.Model):
    """
    Save per user topic read tracking
    """
    user = models.ForeignKey(get_user_model_path(), blank=False, null=False)
    topic = models.ForeignKey('Topic', blank=True, null=True)
    time_stamp = models.DateTimeField(auto_now=True)

    objects = TopicReadTrackerManager()

    class Meta(object):
        verbose_name = _('Topic read tracker')
        verbose_name_plural = _('Topic read trackers')
        unique_together = ('user', 'topic')
        app_label = 'pybb'


class ForumReadTrackerManager(models.Manager):
    def get_or_create_tracker(self, user, forum):
        """
        Correctly create tracker in mysql db on default REPEATABLE READ transaction mode

        It's known problem when standrard get_or_create method return can raise exception
        with correct data in mysql database.
        See http://stackoverflow.com/questions/2235318/how-do-i-deal-with-this-race-condition-in-django/2235624
        """
        is_new = True
        sid = transaction.savepoint(using=self.db)
        try:
            with get_atomic_func()():
                obj = ForumReadTracker.objects.create(user=user, forum=forum)
            transaction.savepoint_commit(sid)
        except DatabaseError:
            transaction.savepoint_rollback(sid)
            is_new = False
            obj = ForumReadTracker.objects.get(user=user, forum=forum)
        return obj, is_new


class ForumReadTracker(models.Model):
    """
    Save per user forum read tracking
    """
    user = models.ForeignKey(get_user_model_path(), blank=False, null=False)
    forum = models.ForeignKey('Forum', blank=True, null=True)
    time_stamp = models.DateTimeField(auto_now=True)

    objects = ForumReadTrackerManager()

    class Meta(object):
        verbose_name = _('Forum read tracker')
        verbose_name_plural = _('Forum read trackers')
        unique_together = ('user', 'forum')
        app_label = 'pybb'
