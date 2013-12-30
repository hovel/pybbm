# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings

from django.utils.importlib import import_module

def _resolve_class(name):
    """ resolves a class function given as string, returning the function """
    if not name: return False
    modname, funcname = name.rsplit('.', 1)
    return getattr(import_module(modname), funcname)


# Set forms to use, value should be in form <app>.<module>.<class_name>
# Specially useful when using third-party apps for forms, like crispy-forms
PYBB_POST_FORM = _resolve_class(getattr(settings, 'PYBB_POST_FORM', 'pybb.forms.PostForm'))
PYBB_ADMIN_POST_FORM = _resolve_class(getattr(settings, 'PYBB_ADMIN_POST_FORM', 'pybb.forms.AdminPostForm'))
PYBB_POLL_FORM = _resolve_class(getattr(settings, 'PYBB_POLL_FORM', 'pybb.forms.PollForm'))
PYBB_SEARCH_FORM = _resolve_class(getattr(settings, 'PYBB_SEARCH_FORM', 'pybb.forms.UserSearchForm'))
PYBB_PROFILE_FORM = _resolve_class(getattr(settings, 'PYBB_PROFILE_FORM', 'pybb.forms.EditProfileForm'))
