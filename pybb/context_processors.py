#!/usr/bin/env python
# vim:fileencoding=utf-8

__author__ = 'zeus'

from django.conf import settings

def processor(self):
    context = {}
    template = getattr(settings, 'PYBB_TEMPLATE', False)
    if template:
        context['PYBB_TEMPLATE'] = template
    return context
