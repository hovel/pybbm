# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import inspect

import math
import time
import warnings

import django
from django import template
from django.core.cache import cache
from django.utils.safestring import mark_safe
from django.utils.encoding import smart_text
from django.utils.html import escape
from django.utils.translation import ugettext as _, ungettext
from django.utils import dateformat
from django.utils.timezone import timedelta
from django.utils.timezone import now as tznow

from pybb.compat import is_authenticated, is_anonymous
from pybb.models import TopicReadTracker, ForumReadTracker, PollAnswerUser, Topic, Post
from pybb.permissions import perms
from pybb import defaults, util, compat


register = template.Library()
if django.VERSION >= (1, 9):
    register.assignment_tag = register.simple_tag


#noinspection PyUnusedLocal
@register.tag
def pybb_time(parser, token):
    try:
        tag, context_time = token.split_contents()
    except ValueError: # pragma: no cover
        raise template.TemplateSyntaxError('pybb_time requires single argument')
    else:
        return PybbTimeNode(context_time)


@register.assignment_tag(takes_context=True)
def pybb_get_time(context, context_time):
    return pybb_user_time(context_time, context['user'])


class PybbTimeNode(template.Node):
    def __init__(self, time):
    #noinspection PyRedeclaration
        self.time = template.Variable(time)

    def render(self, context):
        context_time = self.time.resolve(context)
        return pybb_user_time(context_time, context['user'])


def pybb_user_time(context_time, user):
    delta = tznow() - context_time
    today = tznow().replace(hour=0, minute=0, second=0)
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    if delta.days == 0:
        if delta.seconds < 60:
            msg = ungettext('%d second ago', '%d seconds ago', delta.seconds)
            return msg % delta.seconds
        elif delta.seconds < 3600:
            minutes = int(delta.seconds / 60)
            msg = ungettext('%d minute ago', '%d minutes ago', minutes)
            return msg % minutes
    if is_authenticated(user):
        if time.daylight: # pragma: no cover
            tz1 = time.altzone
        else: # pragma: no cover
            tz1 = time.timezone
        tz = tz1 + util.get_pybb_profile(user).time_zone * 60 * 60
        context_time = context_time + timedelta(seconds=tz)
    if today < context_time < tomorrow:
        return _('today, %s') % context_time.strftime('%H:%M')
    elif yesterday < context_time < today:
        return _('yesterday, %s') % context_time.strftime('%H:%M')
    else:
        return dateformat.format(context_time, 'd M, Y H:i')


@register.simple_tag
def pybb_link(object, anchor=''):
    """
    Return A tag with link to object.
    """

    url = hasattr(object, 'get_absolute_url') and object.get_absolute_url() or None
    #noinspection PyRedeclaration
    anchor = anchor or smart_text(object)
    return mark_safe('<a href="%s">%s</a>' % (url, escape(anchor)))


@register.filter
def pybb_topic_moderated_by(topic, user):  # pragma: no cover
    """
    Check if user is moderator of topic's forum.
    """
    warnings.warn("pybb_topic_moderated_by filter is deprecated and will be removed in later releases. "
                  "Use pybb_may_moderate_topic(user, topic) filter instead",
                  DeprecationWarning)
    return perms.may_moderate_topic(user, topic)

@register.filter
def pybb_editable_by(post, user):  # pragma: no cover
    """
    Check if the post could be edited by the user.
    """
    warnings.warn("pybb_editable_by filter is deprecated and will be removed in later releases. "
                  "Use pybb_may_edit_post(user, post) filter instead",
                  DeprecationWarning)
    return perms.may_edit_post(user, post)


@register.filter
def pybb_posted_by(post, user):
    """
    Check if the post is writed by the user.
    """
    return post.user == user


@register.filter
def pybb_is_topic_unread(topic, user):
    if not is_authenticated(user):
        return False

    last_topic_update = topic.updated or topic.created

    unread = not ForumReadTracker.objects.filter(
        forum=topic.forum,
        user=user.id,
        time_stamp__gte=last_topic_update).exists()
    unread &= not TopicReadTracker.objects.filter(
        topic=topic,
        user=user.id,
        time_stamp__gte=last_topic_update).exists()
    return unread


@register.filter
def pybb_topic_unread(topics, user):
    """
    Mark all topics in queryset/list with .unread for target user
    """
    topic_list = list(topics)

    if is_authenticated(user):
        for topic in topic_list:
            topic.unread = True

        forums_ids = [f.forum_id for f in topic_list]
        forum_marks = dict([(m.forum_id, m.time_stamp)
                            for m
                            in ForumReadTracker.objects.filter(user=user, forum__in=forums_ids)])
        if len(forum_marks):
            for topic in topic_list:
                topic_updated = topic.updated or topic.created
                if topic.forum.id in forum_marks and topic_updated <= forum_marks[topic.forum.id]:
                    topic.unread = False

        qs = TopicReadTracker.objects.filter(user=user, topic__in=topic_list).select_related('topic')
        topic_marks = list(qs)
        topic_dict = dict(((topic.id, topic) for topic in topic_list))
        for mark in topic_marks:
            if topic_dict[mark.topic.id].updated <= mark.time_stamp:
                topic_dict[mark.topic.id].unread = False
    return topic_list


@register.filter
def pybb_forum_unread(forums, user):
    """
    Check if forum has unread messages.
    """
    forum_list = list(forums)
    if is_authenticated(user):
        for forum in forum_list:
            forum.unread = forum.topic_count > 0
        forum_marks = ForumReadTracker.objects.filter(
            user=user,
            forum__in=forum_list
        ).select_related('forum')
        forum_dict = dict(((forum.id, forum) for forum in forum_list))
        for mark in forum_marks:
            curr_forum = forum_dict[mark.forum.id]
            if (curr_forum.updated is None) or (curr_forum.updated <= mark.time_stamp):
                if not any((f.unread for f in pybb_forum_unread(curr_forum.child_forums.all(), user))):
                    forum_dict[mark.forum.id].unread = False
    return forum_list


@register.filter
def pybb_topic_inline_pagination(topic):
    page_count = int(math.ceil(topic.post_count / float(defaults.PYBB_TOPIC_PAGE_SIZE)))
    if page_count <= 5:
        return range(1, page_count+1)
    return list(range(1, 5)) + ['...', page_count]


@register.filter
def pybb_topic_poll_not_voted(topic, user):
    if is_anonymous(user):
        return True
    return not PollAnswerUser.objects.filter(poll_answer__topic=topic, user=user).exists()


@register.filter
def endswith(str, substr):
    return str.endswith(substr)


@register.assignment_tag
def pybb_get_profile(*args, **kwargs):
    try:
        return util.get_pybb_profile(kwargs.get('user') or args[0])
    except:
        return None


@register.assignment_tag(takes_context=True)
def pybb_get_latest_topics(context, cnt=5, user=None):
    qs = Topic.objects.all().order_by('-updated', '-created', '-id')
    if not user:
        user = context['user']
    qs = perms.filter_topics(user, qs)
    return qs[:cnt]


@register.assignment_tag(takes_context=True)
def pybb_get_latest_posts(context, cnt=5, user=None):
    qs = Post.objects.all().order_by('-created', '-id')
    if not user:
        user = context['user']
    qs = perms.filter_posts(user, qs)
    return qs[:cnt]


def load_perms_filters():
    def partial(func_name, perms_obj):
        def newfunc(user, obj_or_qs):
            return getattr(perms_obj, func_name)(user, obj_or_qs)
        return newfunc

    def partial_no_param(func_name, perms_obj):
        def newfunc(user):
            return getattr(perms_obj, func_name)(user)
        return newfunc

    for method_name, method in inspect.getmembers(perms):
        if not inspect.ismethod(method):
            continue  # pragma: no cover - only methods are used to dynamically build templatetags
        if not method_name.startswith('may') and not method_name.startswith('filter'):
            continue  # pragma: no cover - only (may|filter)* methods are used to dynamically build templatetags
        method_args = inspect.getargspec(method).args
        args_count = len(method_args)
        if args_count not in (2, 3):
            continue  # pragma: no cover - only methods with 2 or 3 params
        if method_args[0] != 'self' or method_args[1] != 'user':
            continue  # pragma: no cover - only methods with self and user as first args
        if len(inspect.getargspec(method).args) == 3:
            register.filter('%s%s' % ('pybb_', method_name), partial(method_name, perms))
        elif len(inspect.getargspec(method).args) == 2:
            register.filter('%s%s' % ('pybb_', method_name), partial_no_param(method_name, perms))
load_perms_filters()


@register.filter
def check_app_installed(app_name):
    return compat.is_installed(app_name)


@register.filter
def pybbm_calc_topic_views(topic):
    cache_key = util.build_cache_key('anonymous_topic_views', topic_id=topic.id)
    return topic.views + cache.get(cache_key, 0)
