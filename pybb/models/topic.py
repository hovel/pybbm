# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.timezone import now as tznow
from django.utils.translation import ugettext_lazy as _

from pybb import defaults
from pybb.compat import get_user_model_path


@python_2_unicode_compatible
class Topic(models.Model):
    POLL_TYPE_NONE = 0
    POLL_TYPE_SINGLE = 1
    POLL_TYPE_MULTIPLE = 2

    POLL_TYPE_CHOICES = (
        (POLL_TYPE_NONE, _('None')),
        (POLL_TYPE_SINGLE, _('Single answer')),
        (POLL_TYPE_MULTIPLE, _('Multiple answers')),
    )

    forum = models.ForeignKey('pybb.Forum', related_name='topics', verbose_name=_('Forum'))
    name = models.CharField(_('Subject'), max_length=255)
    created = models.DateTimeField(_('Created'), null=True)
    updated = models.DateTimeField(_('Updated'), null=True)
    user = models.ForeignKey(get_user_model_path(), verbose_name=_('User'))
    views = models.IntegerField(_('Views count'), blank=True, default=0)
    sticky = models.BooleanField(_('Sticky'), blank=True, default=False)
    closed = models.BooleanField(_('Closed'), blank=True, default=False)
    subscribers = models.ManyToManyField(get_user_model_path(), related_name='subscriptions',
                                         verbose_name=_('Subscribers'), blank=True)
    post_count = models.IntegerField(_('Post count'), blank=True, default=0)
    readed_by = models.ManyToManyField(get_user_model_path(), through='TopicReadTracker', related_name='readed_topics')
    on_moderation = models.BooleanField(_('On moderation'), default=False)
    poll_type = models.IntegerField(_('Poll type'), choices=POLL_TYPE_CHOICES, default=POLL_TYPE_NONE)
    poll_question = models.TextField(_('Poll question'), blank=True, null=True)
    slug = models.SlugField(verbose_name=_("Slug"), max_length=255)

    class Meta(object):
        ordering = ['-created']
        verbose_name = _('Topic')
        verbose_name_plural = _('Topics')
        unique_together = ('forum', 'slug')

    def __str__(self):
        return self.name

    @cached_property
    def head(self):
        try:
            return self.posts.all().order_by('created', 'id')[0]
        except IndexError:
            return None

    @cached_property
    def last_post(self):
        try:
            return self.posts.order_by('-created', '-id').select_related('user')[0]
        except IndexError:
            return None

    def get_absolute_url(self):
        if defaults.PYBB_NICE_URL:
            return reverse('pybb:topic', kwargs={'slug': self.slug, 'forum_slug': self.forum.slug, 'category_slug': self.forum.category.slug})
        return reverse('pybb:topic', kwargs={'pk': self.id})

    def save(self, *args, **kwargs):
        if self.id is None:
            self.created = self.updated = tznow()

        forum_changed = False
        old_topic = None
        if self.id is not None:
            old_topic = Topic.objects.get(id=self.id)
            if self.forum != old_topic.forum:
                forum_changed = True

        super(Topic, self).save(*args, **kwargs)

        if forum_changed:
            old_topic.forum.update_counters()
            self.forum.update_counters()

    def delete(self, using=None):
        super(Topic, self).delete(using)
        self.forum.update_counters()

    def update_counters(self):
        self.post_count = self.posts.count()
        # force cache overwrite to get the real latest updated post
        if hasattr(self, 'last_post'):
            del self.last_post
        if self.last_post:
            self.updated = self.last_post.updated or self.last_post.created
        self.save()

    def get_parents(self):
        """
        Used in templates for breadcrumb building
        """
        parents = self.forum.get_parents()
        parents.append(self.forum)
        return parents

    def poll_votes(self):
        if self.poll_type != self.POLL_TYPE_NONE:
            return PollAnswerUser.objects.filter(poll_answer__topic=self).count()
        else:
            return None

@python_2_unicode_compatible
class PollAnswer(models.Model):
    topic = models.ForeignKey(Topic, related_name='poll_answers', verbose_name=_('Topic'))
    text = models.CharField(max_length=255, verbose_name=_('Text'))

    class Meta:
        verbose_name = _('Poll answer')
        verbose_name_plural = _('Polls answers')

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

    def __str__(self):
        return '%s - %s' % (self.poll_answer.topic, self.user)