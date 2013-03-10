#!/usr/bin/env python
import sys
import os
from os.path import dirname, abspath
from optparse import OptionParser

from django.conf import settings
import django

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.request',
    'pybb.context_processors.processor',
)

if django.get_version() >= (1, 4):
    TEMPLATE_CONTEXT_PROCESSORS += ['django.core.context_processors.tz',]

# For convenience configure settings if they are not pre-configured or if we
# haven't been provided settings to use by environment variable.
if not settings.configured and not os.environ.get('DJANGO_SETTINGS_MODULE'):
    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.admin',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.sites',
            'pytils',
            'sorl.thumbnail',
            'pure_pagination',
            'pybb',
        ],
        ROOT_URLCONF='test.test_project.test_urls',
        DEBUG=False,
        SITE_ID=1,
        STATIC_URL='/static/',
        AUTH_PROFILE_MODULE='pybb.Profile',
        TEMPLATE_DIRS=(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test/test_project/templates'), ),
        PYBB_ATTACHMENT_ENABLE=True,
        TEMPLATE_CONTEXT_PROCESSORS=TEMPLATE_CONTEXT_PROCESSORS,
    )

from django.test.simple import DjangoTestSuiteRunner


def runtests(*test_args, **kwargs):
    if 'south' in settings.INSTALLED_APPS:
        from south.management.commands import patch_for_test_db_setup
        patch_for_test_db_setup()

    if not test_args:
        test_args = ['pybb']
    parent = dirname(abspath(__file__))
    sys.path.insert(0, parent)
    test_runner = DjangoTestSuiteRunner(verbosity=kwargs.get('verbosity', 1), interactive=kwargs.get('interactive', False), failfast=kwargs.get('failfast'))
    failures = test_runner.run_tests(test_args)
    sys.exit(failures)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('--failfast', action='store_true', default=False, dest='failfast')

    (options, args) = parser.parse_args()

    runtests(failfast=options.failfast, *args)