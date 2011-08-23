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
        'PYBB_DEFAULT_TITLE'
        ):
        context[i] = getattr(defaults, i, None)
    context['PYBB_AVATAR_DIMENSIONS'] = '%sx%s' % (defaults.PYBB_AVATAR_WIDTH, defaults.PYBB_AVATAR_WIDTH)
    return context
