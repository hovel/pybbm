# coding=utf-8
from __future__ import unicode_literals
import django
from django.conf import settings


def get_image_field_class():
    try:
        from sorl.thumbnail import ImageField
    except ImportError:
        from django.db.models import ImageField
    return ImageField


def get_image_field_full_name():
    try:
        from sorl.thumbnail import ImageField
        name = 'sorl.thumbnail.fields.ImageField'
    except ImportError:
        from django.db.models import ImageField
        name = 'django.db.models.fields.files.ImageField'
    return name


def get_user_model():
    if django.VERSION[:2] >= (1, 5):
        from django.contrib.auth import get_user_model
        return get_user_model()
    else:
        from django.contrib.auth.models import User
        User.get_username = lambda u: u.username  # emulate new 1.5 method
        return User


def get_user_model_path():
    if django.VERSION[:2] >= (1, 5):
        return getattr(settings, 'AUTH_USER_MODEL', 'auth.User')
    else:
        return 'auth.User'


def get_username_field():
    if django.VERSION[:2] >= (1, 5):
        return get_user_model().USERNAME_FIELD
    else:
        return 'username'


def get_user_frozen_models(user_model):
    from south.creator.freezer import freeze_apps
    user_app, user_class = user_model.split('.')
    if user_model != 'auth.User':
        from south.migration.base import Migrations
        from south.exceptions import NoMigrations
        try:
            user_migrations = Migrations(user_app)
        except NoMigrations:
            extra_model = freeze_apps(user_app)
        else:
            from pybb import defaults
            migration_name = defaults.PYBB_INITIAL_CUSTOM_USER_MIGRATION or '0001_initial.py'
            initial_user_migration = user_migrations.migration(migration_name)
            extra_model = initial_user_migration.migration_class().models
    else:
        extra_model = freeze_apps(user_app)
    return extra_model


def get_atomic_func():
    try:
        from django.db.transaction import atomic as atomic_func
    except ImportError:
        from django.db.transaction import commit_on_success as atomic_func
    return atomic_func


def get_paginator_class():
    try:
        from pure_pagination import Paginator
        pure_pagination = True
    except ImportError:
        # the simplest emulation of django-pure-pagination behavior
        from django.core.paginator import Paginator, Page
        class PageRepr(int):
            def querystring(self):
                return 'page=%s' % self
        Page.pages = lambda self: [PageRepr(i) for i in range(1, self.paginator.num_pages + 1)]
        pure_pagination = False

    return Paginator, pure_pagination