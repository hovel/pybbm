# -*- coding: utf-8 -*-
import traceback
from django.utils import simplejson

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.db import models
from django.core.serializers.json import DjangoJSONEncoder


class HttpResponseJson(HttpResponse):
    def __init__(self, data):
        json_data = simplejson.dumps(data)
        super(HttpResponseJson, self).__init__(
            content=json_data, mimetype='application/json')


def render_to(template):
    """
    Shortcut for rendering template with RequestContext.

    If decorated function returns non dict then just return that result
    else use RequestContext for rendering the template.
    """

    def decorator(func):
        def wrapper(request, *args, **kwargs):
            output = func(request, *args, **kwargs)
            if not isinstance(output, dict):
                return output
            else:
                ctx = RequestContext(request)
                return render_to_response(template, output, context_instance=ctx)
        return wrapper
    return decorator


def ajax(func):
    """
    Wrap response of view into JSON format.

    Checks request.method is POST. Return error in JSON in other case.
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
            return HttpResponseJson(response)
        else:
            return response
    return wrapper


class JSONField(models.TextField):
    """
    JSONField is a generic textfield that neatly serializes/unserializes
    JSON objects seamlessly.

    Origin: http://www.djangosnippets.org/snippets/1478/
    """

    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        if value == "":
            return None

        try:
            if isinstance(value, basestring):
                return simplejson.loads(value)
        except ValueError:
            pass
        return value

    def get_db_prep_save(self, value):
        if value == "":
            return None
        if isinstance(value, dict):
            value = simplejson.dumps(value, cls=DjangoJSONEncoder)
        return super(JSONField, self).get_db_prep_save(value)
