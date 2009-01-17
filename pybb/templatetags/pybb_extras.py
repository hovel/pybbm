from datetime import datetime, timedelta

from django import template
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.template import RequestContext
from django.utils.encoding import smart_unicode
from django.db import settings
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.utils import dateformat

from pybb.models import Forum, Topic, Read
from pybb.unread import cache_unreads
from pybb import settings as pybb_settings

register = template.Library()

@register.filter
def pybb_profile_link(user):
    data = u'<a href="%s">%s</a>' % (\
        reverse('pybb_profile', args=[user.username]), user.username)
    return mark_safe(data)


@register.tag
def pybb_time(parser, token):
    try:
        tag, time = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError('pybb_time requires single argument')
    else:
        return PybbTimeNode(time)


class PybbTimeNode(template.Node):
    def __init__(self, time):
        self.time = template.Variable(time)

    def render(self, context):
        time = self.time.resolve(context)

        delta = datetime.now() - time
        today = datetime.now().replace(hour=0, minute=0, second=0)
        yesterday = today - timedelta(days=1)

        if delta.days == 0:
            if delta.seconds < 60:
                if context['LANGUAGE_CODE'].startswith('ru'):
                    msg = _('seconds ago,seconds ago,seconds ago')
                    import pytils
                    msg = pytils.numeral.choose_plural(delta.seconds, msg)
                else:
                    msg = _('seconds ago')
                return u'%d %s' % (delta.seconds, msg)

            elif delta.seconds < 3600:
                minutes = int(delta.seconds / 60)
                if context['LANGUAGE_CODE'].startswith('ru'):
                    msg = _('minutes ago,minutes ago,minutes ago')
                    import pytils
                    msg = pytils.numeral.choose_plural(minutes, msg)
                else:
                    msg = _('minutes ago')
                return u'%d %s' % (minutes, msg)
        if time > today:
            return _('today, %s') % time.strftime('%H:%M')
        elif time > yesterday:
            return _('yesterday, %s') % time.strftime('%H:%M')
        else:
            return dateformat.format(time, 'd M, Y H:i')


# TODO: this old code requires refactoring
@register.inclusion_tag('pybb/pagination.html',takes_context=True)
def pybb_pagination(context, adjacent_pages=5):
    """
    Return the list of A tags with links to pages.
    """

    page_list = range(
        max(1,context['page'] - adjacent_pages),
        min(context['pages'],context['page'] + adjacent_pages) + 1)
    lower_page = None
    higher_page = None

    if not 1 == context['page']:
        lower_page = context['page'] - 1

    if not 1 in page_list:
        page_list.insert(0,1)
        if not 2 in page_list:
            page_list.insert(1,'.')

    if not context['pages'] == context['page']:
        higher_page = context['page'] + 1

    if not context['pages'] in page_list:
        if not context['pages'] - 1 in page_list:
            page_list.append('.')
        page_list.append(context['pages'])
    get_params = '&'.join(['%s=%s' % (x[0],','.join(x[1])) for x in
        context['request'].GET.iteritems() if (not x[0] == 'page' and not x[0] == 'per_page')])
    if get_params:
        get_params = '?%s&' % get_params
    else:
        get_params = '?'

    return {
        'get_params': get_params,
        'lower_page': lower_page,
        'higher_page': higher_page,
        'page': context['page'],
        'pages': context['pages'],
        'page_list': page_list,
        'per_page': context['per_page'],
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
            if (now - delta > topic.updated):
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
