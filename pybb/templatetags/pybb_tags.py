# -*- coding: utf-8 -*-
import inspect

import math
import time
import warnings

from django import template
from django.core.cache import cache
from django.template.base import get_library, InvalidTemplateLibrary, TemplateSyntaxError, TOKEN_BLOCK
from django.template.defaulttags import LoadNode, CommentNode, IfNode
from django.template.smartif import Literal
from django.utils.safestring import mark_safe
from django.utils.encoding import smart_unicode
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.utils import dateformat
from django.utils.timezone import timedelta
from django.utils.timezone import now as tznow
from pybb.util import build_cache_key

try:
    import pytils
    pytils_enabled = True
except ImportError:
    pytils_enabled = False

from pybb.models import TopicReadTracker, ForumReadTracker, PollAnswerUser, Topic, Post
from pybb.permissions import perms
from pybb import defaults, util


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
            tz = tz1 + util.get_pybb_profile(context['user']).time_zone * 60 * 60
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
    warnings.warn("pybb_topic_moderated_by filter is deprecated and will be removed in later releases. "
                  "Use pybb_may_moderate_topic(user, topic) filter instead",
                  DeprecationWarning)
    return perms.may_moderate_topic(user, topic)

@register.filter
def pybb_editable_by(post, user):
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


@register.assignment_tag
def pybb_get_profile(*args, **kwargs):
    try:
        return util.get_pybb_profile(kwargs.get('user') or args[0])
    except:
        return util.get_pybb_profile_model().objects.none()


@register.assignment_tag(takes_context=True)
def pybb_get_latest_topics(context, cnt=5, user=None):
    qs = Topic.objects.all().order_by('-updated', '-created')
    if not user:
        user = context['user']
    qs = perms.filter_topics(user, qs)
    return qs[:cnt]


@register.assignment_tag(takes_context=True)
def pybb_get_latest_posts(context, cnt=5, user=None):
    qs = Post.objects.all().order_by('-created')
    if not user:
        user = context['user']
    qs = perms.filter_posts(user, qs)
    return qs[:cnt]


def load_perms_filters():
    def partial(func_name, perms_obj):
        def newfunc(user, obj):
            return getattr(perms_obj, func_name)(user, obj)
        return newfunc

    for method in inspect.getmembers(perms):
        if inspect.ismethod(method[1]) and len(inspect.getargspec(method[1]).args) == 3 and\
                inspect.getargspec(method[1]).args[0] == 'self' and\
                (method[0].startswith('may') or method[0].startswith('filter')):
            register.filter('%s%s' % ('pybb_', method[0]), partial(method[0], perms))
load_perms_filters()

# next two tags copied from https://bitbucket.org/jaap3/django-friendly-tag-loader

@register.tag
def friendly_load(parser, token):
    """
    Tries to load a custom template tag set. Non existing tag libraries
    are ignored.

    This means that, if used in conjuction with ``if_has_tag``, you can try to
    load the comments template tag library to enable comments even if the
    comments framework is not installed.

    For example::

        {% load friendly_loader %}
        {% friendly_load comments webdesign %}

        {% if_has_tag render_comment_list %}
            {% render_comment_list for obj %}
        {% else %}
            {% if_has_tag lorem %}
                {% lorem %}
            {% endif_has_tag %}
        {% endif_has_tag %}
    """
    bits = token.contents.split()
    for taglib in bits[1:]:
        try:
            lib = get_library(taglib)
            parser.add_library(lib)
        except InvalidTemplateLibrary:
            pass
    return LoadNode()


@register.tag
def if_has_tag(parser, token):
    """
    The logic for both ``{% if_has_tag %}`` and ``{% if not_has_tag %}``.

    Checks if all the given tags exist (or not exist if ``negate`` is ``True``)
    and then only parses the branch that will not error due to non-existing
    tags.

    This means that the following is essentially the same as a
    ``{% comment %}`` tag::

      {% if_has_tag non_existing_tag %}
          {% non_existing_tag %}
      {% endif_has_tag %}

    Another example is checking a built-in tag. This will alway render the
    current year and never FAIL::

      {% if_has_tag now %}
          {% now \"Y\" %}
      {% else %}
          FAIL
      {% endif_has_tag %}
    """
    bits = list(token.split_contents())
    if len(bits) < 2:
        raise TemplateSyntaxError("%r takes at least one arguments" % bits[0])
    end_tag = 'end%s' % bits[0]
    has_tag = all([tag in parser.tags for tag in bits[1:]])
    nodelist_true = nodelist_false = CommentNode()
    if has_tag:
        nodelist_true = parser.parse(('else', end_tag))
        token = parser.next_token()
        if token.contents == 'else':
            parser.skip_past(end_tag)
    else:
        while parser.tokens:
            token = parser.next_token()
            if token.token_type == TOKEN_BLOCK and token.contents == end_tag:
                try:
                    return IfNode([(Literal(has_tag), nodelist_true),
                                   (None, nodelist_false)])
                except TypeError:  # < 1.4
                    return IfNode(Literal(has_tag), nodelist_true, nodelist_false)
            elif token.token_type == TOKEN_BLOCK and token.contents == 'else':
                break
        nodelist_false = parser.parse((end_tag,))
        token = parser.next_token()
    try:
        return IfNode([(Literal(has_tag), nodelist_true),
                       (None, nodelist_false)])
    except TypeError:  # < 1.4
        return IfNode(Literal(has_tag), nodelist_true, nodelist_false)


@register.filter
def pybbm_calc_topic_views(topic):
    cache_key = build_cache_key('anonymous_topic_views', topic_id=topic.id)
    return topic.views + cache.get(cache_key, 0)