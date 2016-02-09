#!/usr/bin/env python
import django
import sys
import os
from optparse import OptionParser
from django.conf import settings

project_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test/test_project')
sys.path.insert(0, project_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_project.settings')

try:
    from django.test.runner import DiscoverRunner as Runner
except ImportError:
    from django.test.simple import DjangoTestSuiteRunner as Runner


def runtests(*test_args, **kwargs):
    if django.VERSION[:2] >= (1, 7):
        django.setup()

    if not test_args:
        test_args = ['pybb']

    test_runner = Runner(verbosity=kwargs.get('verbosity', 1), interactive=kwargs.get('interactive', False),
                         failfast=kwargs.get('failfast'))
    failures = test_runner.run_tests(test_args)
    sys.exit(failures)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('--failfast', action='store_true', default=False, dest='failfast')

    (options, args) = parser.parse_args()

    runtests(failfast=options.failfast, *args)
