# -*- coding: utf-8 -*-

from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse
from django.utils.feedgenerator import Atom1Feed
from django.utils.translation import ugettext_lazy as _

from pybb.models import Post, Topic


class PybbFeed(Feed):
    feed_type = Atom1Feed

    def link(self):
        return reverse('pybb:index')

    def item_guid(self, obj):
        return str(obj.id)

    def item_pubdate(self, obj):
        return obj.created


class LastPosts(PybbFeed):
    title = _('Latest posts on forum')
    description = _('Latest posts on forum')
    title_template = 'pybb/feeds/posts_title.html'
    description_template = 'pybb/feeds/posts_description.html'

    def items(self):
        return Post.objects.filter(topic__forum__hidden=False, topic__forum__category__hidden=False).order_by('-created')[:15]


class LastTopics(PybbFeed):
    title = _('Latest topics on forum')
    description = _('Latest topics on forum')
    title_template = 'pybb/feeds/topics_title.html'
    description_template = 'pybb/feeds/topics_description.html'

    def items(self):
        return Topic.objects.filter(forum__hidden=False, forum__category__hidden=False).order_by('-created')[:15]
