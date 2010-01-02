from datetime import datetime
import os.path
import random
from BeautifulSoup import BeautifulSoup
import traceback
try:
	from hashlib import md5
except ImportError:
	from md5 import md5
import urllib

from django.utils.translation import check_for_language
from django import forms
from django.template.defaultfilters import urlize as django_urlize
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.conf import settings
from django.contrib.sites.models import Site


def urlize(data):
    """
    Urlize plain text links in the HTML contents.

    Do not urlize content of A and CODE tags.
    """

    soup = BeautifulSoup(data)
    for chunk in soup.findAll(text=True):
        islink = False
        ptr = chunk.parent
        while ptr.parent:
            if ptr.name == 'a' or ptr.name == 'code':
                islink = True
                break
            ptr = ptr.parent

        if not islink:
            chunk = chunk.replaceWith(django_urlize(unicode(chunk)))

    return unicode(soup)


def quote_text(text, markup, username=""):
    """
    Quote message using selected markup.
    """

    if markup == 'markdown':
        return '>'+text.replace('\n','\n>').replace('\r','\n>') + '\n'

    elif markup == 'bbcode':
        if username is not "":
            username = '="%s"' % username
        return '[quote%s]%s[/quote]\n' % (username, text)

    else:
        return text


def paginate(items, request, per_page, total_count=None):
    try:
        page_number = int(request.GET.get('page', 1))
    except ValueError:
        page_number = 1

    paginator = Paginator(items, per_page)
    if total_count:
        paginator._count = total_count

    try:
        page = paginator.page(page_number)
    except (EmptyPage, InvalidPage):
        page = paginator.page(1)

    # generate 1 ... 6 7 8 *9* 10 11 12 ... 16
    #                ^    middle      ^
    # maximum 4 items for left and right position,
    # first and last show forever
    # '...' show if (1, last) not in middle

    page.middle_begin = page.number - 3
    if  page.middle_begin < 1:
        page.middle_begin = 1
    page.middle_end = page.number + 3
    if  page.middle_end > paginator.num_pages:
        page.middle_end = paginator.num_pages

    get = request.GET.copy()

    def new_get(page):
        get['page'] = page
        return page, '?%s' % get.urlencode()

    if  page.middle_begin == 2:
        page.middle_begin = 1 # == add "<a>1</a>", not "..."
    if  page.middle_begin > 2: # add "<a>1</a> ... "
        page.first = new_get(1)[1]
    else:
        page.first = None

    if  page.middle_end == paginator.num_pages - 1:
        page.middle_end = paginator.num_pages # == add "<a>last</a>", not "..."
    if  page.middle_end < paginator.num_pages - 1: # add " ... <a>last</a>"
        page.last = new_get(paginator.num_pages)[1]
    else:
        page.last = None

    middle = xrange(page.middle_begin, page.middle_end + 1)
    page.middle = map(new_get, middle)

    return page, paginator


def set_language(request, language):
    """
    Change the language of session of authenticated user.
    """

    if language and check_for_language(language):
        if hasattr(request, 'session'):
            request.session['django_language'] = language
        else:
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language)


def unescape(text):
    """
    Do reverse escaping.
    """

    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', '\'')
    return text


def gravatar_url(email):
    """
    Return gravatar URL for given email.

    Details: http://gravatar.com/site/implement/url
    """

    hash = md5(email).hexdigest()
    size = max(settings.PYBB_AVATAR_WIDTH, settings.PYBB_AVATAR_HEIGHT)
    url = settings.PYBB_DEFAULT_AVATAR_URL
    hostname = Site.objects.get_current().domain
    if not url.startswith('http://'):
        url = 'http://%s%s%s' % (hostname,
                                 settings.MEDIA_URL,
                                 settings.PYBB_DEFAULT_AVATAR_URL)
    default = urllib.quote(url)
    url = 'http://www.gravatar.com/avatar/%s?s=%d&d=%s' % (hash, size, default)
    return url
