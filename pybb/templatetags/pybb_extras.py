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

from pybb.models import Forum, Topic, Read, PrivateMessage
from pybb.unread import cache_unreads
from pybb import settings as pybb_settings
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
    paginator = context['paginator']
    return {'page': page,
            'paginator': paginator,
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
    delta = timedelta(seconds=pybb_settings.READ_TIMEOUT)

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
    return mark_safe(getattr(pybb_settings, name, 'NOT DEFINED'))


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

    is_paginated = topic.post_count > pybb_settings.TOPIC_PAGE_SIZE
    if not is_paginated:
        pagination = None
    else:
        page_size = pybb_settings.TOPIC_PAGE_SIZE
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
