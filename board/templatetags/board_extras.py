from django import template
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def profile_link(user):
    data = u'<a href="%s">%s</a>' % (\
        reverse('board_profile', args=[user.username]), user.username)
    return mark_safe(data)
