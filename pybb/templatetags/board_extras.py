from datetime import datetime, timedelta

from django import template
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.template import RequestContext
from django.utils.encoding import smart_unicode
from django.db import settings
from django.utils.html import escape

register = template.Library()

@register.filter
def profile_link(user):
    data = u'<a href="%s">%s</a>' % (\
        reverse('board_profile', args=[user.username]), user.username)
    return mark_safe(data)


@register.filter
def board_time(time):
    delta = datetime.now() - time
    today = datetime.now().replace(hour=0, minute=0, second=0)
    yesterday = today - timedelta(days=1)

    if delta.days == 0 and delta.seconds < 3600:
        minutes = int(delta.seconds / 60)
        return '%d minutes ago' % minutes
    else:
        if time > today:
            return 'today, %s' % time.strftime('%H:%M')
        elif time > yesterday:
            return 'yesterday, %s' % time.strftime('%H:%M')
        else:
            return time.strftime('%d %b, %Y %H:%M')


# TODO: this old code requires refactoring
@register.inclusion_tag('board/pagination.html',takes_context=True)
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
