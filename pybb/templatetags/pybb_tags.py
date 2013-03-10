# -*- coding: utf-8 -*-

import math
from string import strip
import time

from django import template
from django.utils.safestring import mark_safe
from django.utils.encoding import smart_unicode
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.utils import dateformat

try:
    from django.utils.timezone import timedelta
    from django.utils.timezone import now as tznow
except ImportError:
    import datetime
    from datetime import timedelta
    tznow = datetime.datetime.now

try:
    import pytils
    pytils_enabled = True
except ImportError:
    pytils_enabled = False

from pybb.models import TopicReadTracker, ForumReadTracker, PollAnswerUser
from pybb.permissions import perms
from pybb import defaults


register = template.Library()


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

        delta = tznow() - context_time
        today = tznow().replace(hour=0, minute=0, second=0)
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
            tz = tz1 + context['user'].get_profile().time_zone * 60 * 60
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

    return perms.may_moderate_topic(user, topic)

@register.filter
def pybb_editable_by(post, user):
    """
    Check if the post could be edited by the user.
    """
    return perms.may_edit_post(user, post)    


@register.filter
def pybb_posted_by(post, user):
    """
    Check if the post is writed by the user.
    """
    return post.user == user


@register.filter
def pybb_is_topic_unread(topic, user):
    if not user.is_authenticated():
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

    if user.is_authenticated():
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
    if user.is_authenticated():
        for forum in forum_list:
            forum.unread = forum.topic_count > 0
        forum_marks = ForumReadTracker.objects.filter(
                user=user,
                forum__in=forum_list
                ).select_related('forum')
        forum_dict = dict(((forum.id, forum) for forum in forum_list))
        for mark in forum_marks:
            if (forum_dict[mark.forum.id].updated is None) or\
               (forum_dict[mark.forum.id].updated <= mark.time_stamp):
                forum_dict[mark.forum.id].unread = False
    return forum_list


@register.filter
def pybb_topic_inline_pagination(topic):
    page_count = int(math.ceil(topic.post_count / float(defaults.PYBB_TOPIC_PAGE_SIZE)))
    if page_count <= 5:
        return range(1, page_count+1)
    return range(1, 5) + ['...', page_count]


@register.filter
def pybb_topic_poll_not_voted(topic, user):
    return not PollAnswerUser.objects.filter(poll_answer__topic=topic, user=user).exists()


@register.filter
def endswith(str, substr):
    return str.endswith(substr)