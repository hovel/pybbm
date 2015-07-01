# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from pybb import defaults
from pybb.compat import get_user_model_path

from pybb.models.category import Category
from pybb.models.post import Post
from pybb.models.topic import Topic

@python_2_unicode_compatible
class Forum(models.Model):
    category = models.ForeignKey(Category, related_name='forums', verbose_name=_('Category'))
    parent = models.ForeignKey('self', related_name='child_forums', verbose_name=_('Parent forum'),
                               blank=True, null=True)
    name = models.CharField(_('Name'), max_length=80)
    position = models.IntegerField(_('Position'), blank=True, default=0)
    description = models.TextField(_('Description'), blank=True)
    moderators = models.ManyToManyField(get_user_model_path(), blank=True, null=True, verbose_name=_('Moderators'))
    updated = models.DateTimeField(_('Updated'), blank=True, null=True)
    post_count = models.IntegerField(_('Post count'), blank=True, default=0)
    topic_count = models.IntegerField(_('Topic count'), blank=True, default=0)
    hidden = models.BooleanField(_('Hidden'), blank=False, null=False, default=False)
    readed_by = models.ManyToManyField(get_user_model_path(), through='ForumReadTracker', related_name='readed_forums')
    headline = models.TextField(_('Headline'), blank=True, null=True)
    slug = models.SlugField(verbose_name=_("Slug"), max_length=255)

    class Meta(object):
        ordering = ['position']
        verbose_name = _('Forum')
        verbose_name_plural = _('Forums')
        unique_together = ('category', 'slug')

    def __str__(self):
        return self.name

    def update_counters(self):
        self.topic_count = Topic.objects.filter(forum=self).count()
        if self.topic_count:
            posts = Post.objects.filter(topic__forum_id=self.id)
            self.post_count = posts.count()
            if self.post_count:
                try:
                    last_post = posts.order_by('-created', '-id')[0]
                    self.updated = last_post.updated or last_post.created
                except IndexError:
                    pass
        else:
            self.post_count = 0
        self.save()

    def get_absolute_url(self):
        if defaults.PYBB_NICE_URL:
            return reverse('pybb:forum', kwargs={'slug': self.slug, 'category_slug': self.category.slug})
        return reverse('pybb:forum', kwargs={'pk': self.id})

    @property
    def posts(self):
        return Post.objects.filter(topic__forum=self).select_related()

    @cached_property
    def last_post(self):
        try:
            return self.posts.order_by('-created', '-id')[0]
        except IndexError:
            return None

    def get_parents(self):
        """
        Used in templates for breadcrumb building
        """
        parents = [self.category]
        parent = self.parent
        while parent is not None:
            parents.insert(1, parent)
            parent = parent.parent
        return parents
