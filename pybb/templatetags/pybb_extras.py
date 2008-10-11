from datetime import datetime, timedelta

from django import template
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.template import RequestContext
from django.utils.encoding import smart_unicode
from django.db import settings
from django.utils.html import escape

from pybb.models import Forum, Topic, Read

register = template.Library()

# TODO:
# * rename all tags with pybb_ prefix

@register.filter
def profile_link(user):
    data = u'<a href="%s">%s</a>' % (\
        reverse('pybb_profile', args=[user.username]), user.username)
    return mark_safe(data)


@register.filter
def pybb_time(time):
    delta = datetime.now() - time
    today = datetime.now().replace(hour=0, minute=0, second=0)
    yesterday = today - timedelta(days=1)

    if delta.days == 0:
        if delta.seconds < 60:
            return '%s seconds ago' % delta.seconds
        elif delta.seconds < 3600:
            minutes = int(delta.seconds / 60)
            return '%d minutes ago' % minutes
    if time > today:
        return 'today, %s' % time.strftime('%H:%M')
    elif time > yesterday:
        return 'yesterday, %s' % time.strftime('%H:%M')
    else:
        return time.strftime('%d %b, %Y %H:%M')


# TODO: this old code requires refactoring
@register.inclusion_tag('pybb/pagination.html',takes_context=True)
def pagination(context, adjacent_pages=5):
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
def link(object, anchor=u''):
    """
    Return A tag with link to object.
    """

    url = hasattr(object,'get_absolute_url') and object.get_absolute_url() or None   
    anchor = anchor or smart_unicode(object)
    return mark_safe('<a href="%s">%s</a>' % (url, escape(anchor)))


@register.filter
def has_unreads(obj, user):
    """
    Check if obj topic has messages which user didn't read.
    """

    now = datetime.now()
    delta = timedelta(seconds=settings.PYBB_READ_TIMEOUT)

    if not user.is_authenticated():
        return False
    else:
        if isinstance(obj, Topic):
            if (now - delta > obj.updated):
                return False
            else:
                return obj.has_unreads(user)
        # Disabled because of big number of DB queries
        #elif isinstance(obj, Forum):
            #cnt1 = obj.topics.filter(updated__gt=(now - delta)).count()
            #cnt2 = Read.objects.filter(user=user, topic__forum=obj,\
                #time__gt=(now - delta)).count()
            #return not (cnt1 == cnt2)
        else:
            raise Exception('Object should be a topic')


@register.filter
def pybb_setting(name):
    return mark_safe(getattr(settings, name, 'NOT DEFINED'))


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
