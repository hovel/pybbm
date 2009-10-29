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

from django.http import HttpResponse
from django.utils.functional import Promise
from django.utils.translation import force_unicode, check_for_language
from django.utils.simplejson import JSONEncoder
from django import forms
from django.template.defaultfilters import urlize as django_urlize
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.conf import settings

from pybb import settings as pybb_settings


def ajax(func):
    """
    Checks request.method is POST. Return error in JSON in other case.

    If view returned dict, returns JsonResponse with this dict as content.
    """
    def wrapper(request, *args, **kwargs):
        if request.method == 'POST':
            try:
                response = func(request, *args, **kwargs)
            except Exception, ex:
                response = {'error': traceback.format_exc()}
        else:
            response = {'error': {'type': 403, 'message': 'Accepts only POST request'}}
        if isinstance(response, dict):
            return JsonResponse(response)
        else:
            return response
    return wrapper


class LazyJSONEncoder(JSONEncoder):
    """
    This fing need to save django from crashing.
    """

    def default(self, o):
        if isinstance(o, Promise):
            return force_unicode(o)
        else:
            return super(LazyJSONEncoder, self).default(o)


class JsonResponse(HttpResponse):
    """
    HttpResponse subclass that serialize data into JSON format.
    """

    def __init__(self, data, mimetype='application/json'):
        json_data = LazyJSONEncoder().encode(data)
        super(JsonResponse, self).__init__(
            content=json_data, mimetype=mimetype)


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


def absolute_url(path):
    return 'http://%s%s' % (pybb_settings.HOST, path)


def memoize_method(func):
    """
    Cached result of function call.
    """

    def wrapper(self, *args, **kwargs):
        CACHE_NAME = '__memcache'
        try:
            cache = getattr(self, CACHE_NAME)
        except AttributeError:
            cache = {}
            setattr(self, CACHE_NAME, cache)
        key = (func, tuple(args), frozenset(kwargs.items()))
        if key not in cache:
            cache[key] = func(self, *args, **kwargs)
        return cache[key]
    return wrapper


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
    size = max(pybb_settings.AVATAR_WIDTH, pybb_settings.AVATAR_HEIGHT)
    default = urllib.quote(pybb_settings.DEFAULT_AVATAR_URL)
    url = 'http://www.gravatar.com/avatar/%s?s=%d&d=%s' % (hash, size, default)
    return url
