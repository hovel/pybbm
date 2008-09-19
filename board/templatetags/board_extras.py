from datetime import datetime, timedelta

from django import template
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe

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


