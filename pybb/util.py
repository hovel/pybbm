try:
    from hashlib import md5
except ImportError:
    from md5 import md5
import urllib

from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.contrib.sites.models import Site
from annoying.functions import get_config

import defaults
MEDIA_URL = get_config('MEDIA_URL', None)

#def paginate(items, request, per_page, total_count=None):
#    try:
#        page_number = int(request.GET.get('page', 1))
#    except ValueError:
#        page_number = 1
#
#    paginator = Paginator(items, per_page)
#    if total_count:
#        paginator._count = total_count
#
#    try:
#        page = paginator.page(page_number)
#    except (EmptyPage, InvalidPage):
#        page = paginator.page(1)
#
#    # generate 1 ... 6 7 8 *9* 10 11 12 ... 16
#    #                ^    middle      ^
#    # maximum 4 items for left and right position,
#    # first and last show forever
#    # '...' show if (1, last) not in middle
#
#    page.middle_begin = page.number - 3
#    if  page.middle_begin < 1:
#        page.middle_begin = 1
#    page.middle_end = page.number + 3
#    if  page.middle_end > paginator.num_pages:
#        page.middle_end = paginator.num_pages
#
#    get = request.GET.copy()
#
#    def new_get(page):
#        get['page'] = page
#        return page, '?%s' % get.urlencode()
#
#    if  page.middle_begin == 2:
#        page.middle_begin = 1 # == add "<a>1</a>", not "..."
#    if  page.middle_begin > 2: # add "<a>1</a> ... "
#        page.first = new_get(1)[1]
#    else:
#        page.first = None
#
#    if  page.middle_end == paginator.num_pages - 1:
#        page.middle_end = paginator.num_pages # == add "<a>last</a>", not "..."
#    if  page.middle_end < paginator.num_pages - 1: # add " ... <a>last</a>"
#        page.last = new_get(paginator.num_pages)[1]
#    else:
#        page.last = None
#
#    middle = xrange(page.middle_begin, page.middle_end + 1)
#    page.middle = map(new_get, middle)
#
#    return page, paginator


def unescape(text):
    """
    Do reverse escaping.
    """
    return text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', '\'')


#def gravatar_url(email):
#    """
#    Return gravatar URL for given email.
#
#    Details: http://gravatar.com/site/implement/url
#    """
#
#    hash = md5(email).hexdigest()
#    size = max(defaults.PYBB_AVATAR_WIDTH, defaults.PYBB_AVATAR_HEIGHT)
#    url = defaults.PYBB_DEFAULT_AVATAR_URL
#    hostname = Site.objects.get_current().domain
#    if not url.startswith('http://'):
#        url = 'http://%s%s%s' % (hostname,
#                                 MEDIA_URL,
#                                 defaults.PYBB_DEFAULT_AVATAR_URL)
#    default = urllib.quote(url)
#    url = 'http://www.gravatar.com/avatar/%s?s=%d&d=%s' % (hash, size, default)
#    return url
