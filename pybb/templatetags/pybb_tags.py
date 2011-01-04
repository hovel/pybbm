# -*- coding: utf-8 -*-
import re
from datetime import datetime, timedelta
import time as time

try:
    import pytils

    pytils_enabled = True
except ImportError:
    pytils_enabled = False

from django import template
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.template import TextNode
from django.utils.encoding import smart_unicode
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.utils import dateformat
from django.utils.translation import ungettext

from pybb.models import Topic, TopicReadTracker, ForumReadTracker
from annoying.functions import get_config
MEDIA_URL = get_config('MEDIA_URL', None)

import pybb.settings as settings

MIDDLEWARE_CLASSES = get_config('MIDDLEWARE_CLASSES', None)
LANGUAGE_CODE = get_config('LANGUAGE_CODE', None)

register = template.Library()

#noinspection PyUnusedLocal
@register.tag
def pybb_csrf(parser, token):
    """
    This tag returns CsrfTokenNode if CsrfViewMiddleware is enabled, or empty string if not
    """

    if 'django.middleware.csrf.CsrfViewMiddleware' in MIDDLEWARE_CLASSES:
        from django.template.defaulttags import CsrfTokenNode

        return CsrfTokenNode()
    else:
        return TextNode('')


@register.filter
def pybb_profile_link(user):
    url = reverse('pybb_user', args=[user.username])
    return mark_safe(u'<a href="%s">%s</a>' % (url, user.username))


#noinspection PyUnusedLocal
@register.tag
def pybb_time(parser, token):
    try:
        tag, context_time = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError('pybb_time requires single argument')
    else:
        return PybbTimeNode(context_time)


class PybbTimeNode(template.Node):
    def __init__(self, time):
    #noinspection PyRedeclaration
        self.time = template.Variable(time)

    def render(self, context):
        context_time = self.time.resolve(context)

        delta = datetime.now() - context_time
        today = datetime.now().replace(hour=0, minute=0, second=0)
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        if delta.days == 0:
            if delta.seconds < 60:
                if context['LANGUAGE_CODE'].startswith('ru') and pytils_enabled:
                    msg = _('seconds ago,seconds ago,seconds ago')
                    msg = pytils.numeral.choose_plural(delta.seconds, msg)
                else:
                    msg = _('seconds ago')
                return u'%d %s' % (delta.seconds, msg)

            elif delta.seconds < 3600:
                minutes = int(delta.seconds / 60)
                if context['LANGUAGE_CODE'].startswith('ru') and pytils_enabled:
                    msg = _('minutes ago,minutes ago,minutes ago')
                    msg = pytils.numeral.choose_plural(minutes, msg)
                else:
                    msg = _('minutes ago')
                return u'%d %s' % (minutes, msg)
        if context['user'].is_authenticated():
            if time.daylight:
                tz1 = time.altzone
            else:
                tz1 = time.timezone
            tz = tz1 + context['user'].pybb_profile.time_zone * 60 * 60
            context_time = context_time + timedelta(seconds=tz)
        if today < context_time < tomorrow:
            return _('today, %s') % context_time.strftime('%H:%M')
        elif yesterday < context_time < today:
            return _('yesterday, %s') % context_time.strftime('%H:%M')
        else:
            return dateformat.format(context_time, 'd M, Y H:i')


@register.simple_tag
def pybb_link(object, anchor=u''):
    """
    Return A tag with link to object.
    """

    url = hasattr(object, 'get_absolute_url') and object.get_absolute_url() or None
    #noinspection PyRedeclaration
    anchor = anchor or smart_unicode(object)
    return mark_safe('<a href="%s">%s</a>' % (url, escape(anchor)))


@register.filter
def pybb_topic_moderated_by(topic, user):
    """
    Check if user is moderator of topic's forum.
    """

    return user.is_superuser or (user in topic.forum.moderators.all())

@register.filter
def pybb_editable_by(post, user):
    """
    Check if the post could be edited by the user.
    """

    if user.is_superuser:
        return True
    if post.user == user:
        return True
    if user in post.topic.forum.moderators.all():
        return True
    return False


@register.filter
def pybb_posted_by(post, user):
    """
    Check if the post is writed by the user.
    """

    return post.user == user


@register.filter
def pybb_equal_to(obj1, obj2):
    """
    Check if objects are equal.
    """

    return obj1 == obj2


@register.inclusion_tag('pybb/mini_pagination.html')
def pybb_topic_mini_pagination(topic):
    """
    Display links on topic pages.
    """
    is_paginated = topic.post_count > settings.PYBB_TOPIC_PAGE_SIZE
    if not is_paginated:
        pagination = None
    else:
        page_size = settings.PYBB_TOPIC_PAGE_SIZE
        a_template = u'<a href="%s?page=%%(p)s">%%(p)s</a>' % topic.get_absolute_url()
        page_count = ((topic.post_count - 1) / page_size ) + 1
        if page_count > 4:
            pages = [1, 2, page_count - 1, page_count]
            links = [a_template % {'p': page} for page in pages]
            pagination = u"%s, %s ... %s, %s" % tuple(links)
        else:
            pages = range(1, page_count + 1)
            links = [a_template % {'p': page} for page in pages]
            pagination = u", ".join(links)

    return {'pagination': pagination,
            'is_paginated': is_paginated,
    }


#noinspection PyUnusedLocal
@register.tag(name='pybb_load_last_topics')
def do_pybb_load_last_topics(parser, token):
    """
    Create new context variable pointed to the list of topics.
    
    Usage examples:
        
        {% pybb_load_last_topics as last_topics %}
        {% pybb_load_last_topics as last_topics with limit=10 %}
        {% pybb_load_last_topics as last_topics with limit=10, category=cat.pk %}
        {% pybb_load_last_topics as last_topics with forum=forum.pk,order_by="updated" %}

    Available arguments for with clause:
        limit: limitation of number of loaded items
        category: primary key of category to load topics from
        forum: primary key of forum to load topics from
        order_by: the Topic field name to order the topic selection with. Default is "created"
    """

    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires arguments" % token.contents.split()[0]

    match = re.search(r'as\s+(\w+)(?:\s+with\s+(.+))?', arg)
    if not match:
        raise template.TemplateSyntaxError, "%r tag had invalid arguments" % tag_name
    name = match.group(1)

    limit = '10'
    category = '0'
    order_by = '"created"'

    if match.group(2):
        args = dict([x.strip().split('=') for x in match.group(2).split(',')])
        if 'limit' in args:
            limit = args['limit']
        if 'category' in args:
            category = args['category']
        if 'order_by' in args:
            order_by = args['order_by']

    return PybbLoadLastTopicsNode(name, limit, category, order_by)


class PybbLoadLastTopicsNode(template.Node):
    def __init__(self, name, limit, category, order_by):
        self.name = name
        self.limit = template.Variable(limit)
        self.category = template.Variable(category)
        self.order_by = template.Variable(order_by)

    def render(self, context):
        limit = self.limit.resolve(context)
        category = self.category.resolve(context)
        order_by = self.order_by.resolve(context)
        topics = Topic.objects.all().select_related().order_by('-' + order_by)
        if category:
            topics = topics.filter(forum__category__pk=category)
        context[self.name] = topics[:limit]
        return ''

@register.filter
def pybb_topic_unread(topics, user):
    """
    Mark all topics in queryset/list with .unread for target user
    """
    topic_list = list(topics)
    for topic in topic_list:
        topic.unread = True
    if user.is_authenticated():
        try:
            forum_mark = ForumReadTracker.objects.get(user=user, forum=topic_list[0].forum)
        except:
            forum_mark = None
        qs = TopicReadTracker.objects.filter(
                user=user,
                topic__in=topic_list
                ).select_related('topic')
        if forum_mark:
            qs.filter(topic__updated__gt=forum_mark.time_stamp)
        for topic in topic_list:
            if topic.updated < forum_mark.time_stamp:
                topic.unread = False
        topic_marks = list(qs)
        topic_dict = dict(((topic.id, topic) for topic in topic_list))
        for mark in topic_marks:
            if topic_dict[mark.topic.id].updated < mark.time_stamp:
                topic_dict[mark.topic.id].unread = False
    return topic_list


@register.filter
def pybb_forum_unread(forums, user):
    """
    Check if forum has unread messages.
    """
    forum_list = list(forums)
    for forum in forum_list:
        forum.unread = True
    if user.is_authenticated():
        forum_marks = ForumReadTracker.objects.filter(
                user=user,
                forum__in=forum_list
                ).select_related('forum')
        forum_dict = dict(((forum.id, forum) for forum in forum_list))
        for mark in forum_marks:
            if forum_dict[mark.forum.id].updated < mark.time_stamp:
                forum_dict[mark.forum.id].unread = False
    return forum_list

@register.simple_tag
def pybb_render_post(post, mode='html'):
    """
    Process post contents and replace special tags with human readeable messages.

    Arguments:
        post - the ``Post`` instance
        mode - "html" or "text". Control which field to use ``body_html`` or ``body_text``

    Currently following tags are supported:
    
        @@@AUTOJOIN-(SECONDS)@@@ - autojoin message

    """

    def render_autojoin_message(match):
        time_diff = int(match.group(1)) / 60

        if LANGUAGE_CODE.startswith('ru') and pytils_enabled:
            minutes = pytils.numeral.choose_plural(time_diff,
                                                   (u'минуту', u'минуты', u'минут'))
            join_message = u'Добавлено через %s %s' % (time_diff, minutes)
        else:
            join_message = ungettext(u"Added after %s minute",
                                     u"Added after %s minutes",
                                     time_diff)
            join_message %= time_diff

        if mode == 'html':
            return u'<div class="autojoin-message">%s</div>' % join_message
        else:
            return join_message


    body = getattr(post, 'body_%s' % mode)
    re_tag = re.compile(r'@@@AUTOJOIN-(\d+)@@@')
    return re_tag.sub(render_autojoin_message, body)
