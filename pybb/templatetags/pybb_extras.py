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
from django.template import RequestContext
from django.utils.encoding import smart_unicode
from django.db import settings
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.utils import dateformat
from django.conf import settings

from pybb.models import Forum, Topic, Read
from pybb.unread import cache_unreads
from pybb.util import gravatar_url


register = template.Library()

@register.filter
def pybb_profile_link(user):
    data = u'<a href="%s">%s</a>' % (\
        reverse('pybb_profile', args=[user.username]), user.username)
    return mark_safe(data)


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


@register.inclusion_tag('pybb/pagination.html',takes_context=True)
def pybb_pagination(context, label):
    page = context['page']
    return {'page': page,
            'label': label,
            }


@register.simple_tag
def pybb_link(object, anchor=u''):
    """
    Return A tag with link to object.
    """

    url = hasattr(object,'get_absolute_url') and object.get_absolute_url() or None
    anchor = anchor or smart_unicode(object)
    return mark_safe('<a href="%s">%s</a>' % (url, escape(anchor)))


@register.filter
def pybb_has_unreads(topic, user):
    """
    Check if topic has messages which user didn't read.
    """

    now = datetime.now()
    delta = timedelta(seconds=settings.PYBB_READ_TIMEOUT)

    if not user.is_authenticated():
        return False
    else:
        if isinstance(topic, Topic):
            if topic.updated and (now - delta > topic.updated):
                return False
            else:
                if hasattr(topic, '_read'):
                    read = topic._read
                else:
                    try:
                        read = Read.objects.get(user=user, topic=topic)
                    except Read.DoesNotExist:
                        read = None

                if read is None:
                    return True
                else:
                    return topic.updated > read.time
        else:
            raise Exception('Object should be a topic')


@register.filter
def pybb_setting(name):
    return mark_safe(getattr(settings, 'PYBB_%s' % name, 'NOT DEFINED'))


@register.filter
def pybb_moderated_by(topic, user):
    """
    Check if user is moderator of topic's forum.
    """

    return user.is_superuser or user in topic.forum.moderators.all()


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


@register.filter
def pybb_unreads(qs, user):
    return cache_unreads(qs, user)


@register.inclusion_tag('pybb/topic_mini_pagination.html')
def pybb_topic_mini_pagination(topic):
    """
    Display links on topic pages.
    """

    is_paginated = topic.post_count > settings.PYBB_TOPIC_PAGE_SIZE
    if not is_paginated:
        pagination = None
    else:
        page_size = settings.PYBB_TOPIC_PAGE_SIZE
        template =  u'<a href="%s?page=%%(p)s">%%(p)s</a>' % topic.get_absolute_url()
        page_count =  ((topic.post_count - 1) / page_size ) + 1
        if page_count > 4:
            pages = [1, 2, page_count - 1, page_count]
            links = [template % {'p': page} for page in pages]
            pagination = u"%s, %s ... %s, %s" % tuple(links)
        else:
            pages = range(1,page_count+1)
            links = [template % {'p': page} for page in pages]
            pagination = u", ".join(links)

    return {'pagination': pagination,
            'is_paginated': is_paginated,
            }


@register.filter
def pybb_avatar_url(user):
    if user.pybb_profile.avatar:
        return user.pybb_profile.avatar.url
    else:
        return gravatar_url(user.email)


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
    order_by='"created"'

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
