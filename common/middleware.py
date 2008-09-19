# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import rfc822

from django.conf import settings
from django.http import HttpResponseRedirect

import flash

class LoginRequiredMiddleware(object):
    """
    This middleware restrict access to site for not authenticated users.

    It allows access to views from settings.PUBLIC_REFIXES list.
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        for public_prefix in settings.PUBLIC_PREFIXES:
            if request.path.startswith(public_prefix):
                return None
        if not request.user.is_authenticated():
            flash.notice_next(u'Пожалуйста, авторизуйтесь')
            return HttpResponseRedirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
        else:
            return None


class AntiCacheMiddleware(object):
    """
    This middleware genereate HTTP headers 
    that prevent browser caching.
    """

    def process_response(self, request, response):
        if request.path.startswith(settings.MEDIA_URL):
            return response
        # date in the past
        response['Expires'] = 'Sat, 26 Jul 1997 05:00:00 GMT'

        # always modified
        response['Last-Modified'] = response['Expires'] 

        # HTTP/1.0
        response['Pragma'] = 'no-cache'

        # HTTP/1.1 + IE-specific (pre|post)-check
        response['Cache-Control'] = 'private, no-cache, no-store, must-revalidate, max-age=0, pre-check=0, post-check=0'

        return response
