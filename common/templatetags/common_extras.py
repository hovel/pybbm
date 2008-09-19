# -*- coding: utf-8
from django import template
from django.template import RequestContext
from django.utils.encoding import smart_unicode
from django.db import settings

register = template.Library()

# TODO: this old code requires refactoring
@register.inclusion_tag('common/pagination.html',takes_context=True)
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


@register.inclusion_tag('common/link.html')
def link(object, anchor=u''):
    """
    Return A tag with link to object.
    """

    user_id = None
    url = hasattr(object,'get_absolute_url') and object.get_absolute_url() or None   
    anchor = anchor or smart_unicode(object)
    return {'user_id': user_id,
            'url': url,
            'anchor': anchor}


@register.inclusion_tag('common/link.html')
def edit_link(object, anchor=None):
    """
    Return A tag with link to edit page of object.
    """

    url = hasattr(object,'get_edit_url') and object.get_edit_url() or ''
    if anchor is None:
        anchor = u'редактировать'
    return {'url': url,
            'anchor': anchor}


@register.inclusion_tag('common/messages.html', takes_context=True)
def messages(context):
    return {'errors': context['request'].session['messages']['errors'],
            'notices': context['request'].session['messages']['notices']} 


@register.inclusion_tag('common/field_as_p.html')
def field_as_p(form, field_name):
    return {
        'errors': form.errors.get(field_name,[]),
        'field': form[field_name]}
