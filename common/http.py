# -*- coding: utf-8 -*-
import simplejson

from django.template.loader import render_to_string
from django.http import HttpResponseRedirect, HttpResponse
from django.conf import settings

class HttpResponseJson(HttpResponse):
    def __init__(self, data):
        json_data = simplejson.dumps(data)
        super(HttpResponseJson, self).__init__(
            content=json_data)#, mimetype='application/json')
