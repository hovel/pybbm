#!/usr/bin/env python
# vim:fileencoding=utf-8

__author__ = 'zeus'

import defaults

def processor(request):
    context = {}
    for i in (
        'PYBB_TEMPLATE',
        'PYBB_BUTTONS',
        'PYBB_DEFAULT_AVATAR_URL',
        'PYBB_MARKUP',
        ):
        context[i] = getattr(defaults, i, None)
    return context
