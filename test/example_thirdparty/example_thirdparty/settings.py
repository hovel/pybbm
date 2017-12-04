# -*- coding: utf-8 -*-
# Django settings for example project.
from __future__ import unicode_literals
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'testdb.sqlite'),
    }
}

TIME_ZONE = 'UTC'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1

USE_I18N = True
USE_L10N = True

USE_TZ = True

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

STATIC_ROOT = os.path.join(BASE_DIR, 'static_collected')
STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

SECRET_KEY = '0t!z!jzl#o%4=#!it5!4pgge_!9_$2v*l-(jdn++!_sxn)+$wl'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                # 'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'pybb.context_processors.processor',
            ],
        },
    },
]

MIDDLEWARE_CLASSES = MIDDLEWARE = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'account.middleware.LocaleMiddleware',
    'pybb.middleware.PybbMiddleware',
)

ROOT_URLCONF = 'example_thirdparty.urls'

WSGI_APPLICATION = 'example_thirdparty.wsgi.application'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'pybb.apps.PybbConfig',
    'sorl.thumbnail',
    'pure_pagination',
    'account',
    'pinax_theme_bootstrap',
    'bootstrapform',
    'captcha',
)

AUTH_PROFILE_MODULE = 'pybb.Profile'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Pybb
PYBB_TEMPLATE = "site_base.html"
PYBB_ATTACHMENT_ENABLE = True
