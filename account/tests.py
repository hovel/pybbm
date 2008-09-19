from django.test import TestCase
from django.contrib.auth.models import User

from account.models import OneTimeCode

class OneTimeCodeTestCase(TestCase):
    user = None

    def setUp(self):
        if not self.user:
            self.user = User.objects.create_user('foo', 'foo', 'foo')
        OneTimeCode.objects.all().delete()

    def testGenerate(self):
        otcode = OneTimeCode.objects.generate(self.user, 'foobar')
        test_otcode = OneTimeCode.objects.get()
        self.assertEqual(test_otcode.code, otcode.code)

    def testWrap(self):
        url = 'http://ya.ru/foo'
        wrapped_url = OneTimeCode.objects.wrap_url(url, self.user)
        otcode = OneTimeCode.objects.get()
        self.assertEqual('%s?otcode=%s' % (url,otcode.code), wrapped_url)

        OneTimeCode.objects.all().delete()
        url = 'http://ya.ru/foo'
        wrapped_url = OneTimeCode.objects.wrap_url(url,self.user)
        otcode = OneTimeCode.objects.get()
        self.assertEqual('%s?otcode=%s' % (url,otcode.code), wrapped_url)

