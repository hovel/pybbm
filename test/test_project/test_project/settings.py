# coding=utf-8
from __future__ import unicode_literals
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'TEST_CHARSET': 'utf8',
    }
}
test_db = os.environ.get('DB', 'sqlite')
if test_db == 'mysql':
    DATABASES['default'].update({
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'pybbm',
        # 'USER': 'root',
        'TEST_COLLATION': 'utf8_general_ci',
    })
elif test_db == 'postgres':
    DATABASES['default'].update({
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        # 'USER': 'postgres',
        'NAME': 'pybbm',
        'OPTIONS': {}
    })

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'test_app',
    'pybb.apps.PybbConfig',
]

SECRET_KEY = 'some secret'

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
    'pybb.middleware.PybbMiddleware',
)

ROOT_URLCONF = 'test_project.urls'

SITE_ID = 1

STATIC_URL = '/static/'
MEDIA_ROOT = os.path.join(BASE_DIR, '..', '..', 'pybb_upload')
MEDIA_URL = '/media/'

AUTH_USER_MODEL = 'test_app.CustomUser'

LOGIN_URL = '/'
USE_TZ = True
PYBB_ATTACHMENT_ENABLE = True
PYBB_PROFILE_RELATED_NAME = 'pybb_customprofile'
