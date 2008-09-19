# -*- coding: utf-8 -*-
import re
import htmlentitydefs

from django.utils.functional import Promise
from django.utils.translation import force_unicode
from django.utils.simplejson import JSONEncoder
from django.http import HttpResponse

class LazyJSONEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, Promise):
            return force_unicode(o)
        else:
            return super(LazyEncoder, self).default(o)

# see http://code.djangoproject.com/ticket/5868 for details about LazyJSONEncoder
class JsonResponse(HttpResponse):
    """Return http response with proper mime type and data in serialized format"""

    def __init__(self, data):
        json_data = LazyJSONEncoder().encode(data)
        super(JsonResponse, self).__init__(
            content=json_data, mimetype='application/json')


def decode_entities(data, encoding=None):
    """
    Decode HTML encoded entities to native unicode representation:
     * things like &nbps;, &raquo; etc
     * things like &#XXXX;
    Arguments:
     * data - encoded HTML data
     * encoding - optional encoding which result must be encoded to
    """

    def unicode_char_callback(match):
        code = match.group(1)
        try:
            return unichr(int(code))
        except ValueError:
            return code

    def entity_callback(match):
        entity = match.group(1)
        try:
            value = htmlentitydefs.name2codepoint[entity]
            try:
                data = unichr(value)
                if encoding:
                    data = data.encode(encoding)
                return data
            except UnicodeDecodeError:
                pass
        except KeyError:
            pass
        return u'&%s;' % entity

    if encoding is None and isinstance(data, str):
        try:
            data = data.decode('utf-8')
        except UnicodeDecodeError:
            print 'data encoding is not unicode neither utf-8'
            return ''
    data = re.sub(r'&([a-z]+);', entity_callback, data)
    data = re.sub(r'&#(\d+);', unicode_char_callback, data)
    return data
