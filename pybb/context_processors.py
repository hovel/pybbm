# -*- coding: utf-8 -*-

from pybb import defaults
from django.conf import settings

__author__ = 'zeus'

try:
    from sorl import thumbnail
    sorl_thumbnail_enabled = 'sorl.thumbnail' in settings.INSTALLED_APPS
except ImportError:
    sorl_thumbnail_enabled = True


def processor(request):
    context = {}
    for i in (
        'PYBB_TEMPLATE',
        'PYBB_DEFAULT_AVATAR_URL',
        'PYBB_MARKUP',
        'PYBB_DEFAULT_TITLE',
        'PYBB_ENABLE_ANONYMOUS_POST',
        'PYBB_ATTACHMENT_ENABLE',
        'PYBB_AVATAR_WIDTH',
        'PYBB_AVATAR_HEIGHT'
    ):
        context[i] = getattr(defaults, i, None)
    context['PYBB_USE_SORL_THUMBNAIL'] = sorl_thumbnail_enabled
    return context
