"""
This module contains middlewares for account application:
    * DebugLoginMiddleware
    * OneTimeCodeAuthMiddleware
    * TestCookieMiddleware
"""

from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.conf import settings                               #PC

from account.models import OneTimeCode
from account.util import email_template


class DebugLoginMiddleware(object):
    """
    This middleware can authenticate user with just an
    ID parameter in the URL.
    This is dangerous middleware, use it with caution.
    """

    def process_request(self, request):
        """
        Login user with ID from loginas param of the query GET data.

        Do it only then settings.ACCOUNT_LOGIN_DEBUG is True
        """

        if getattr(settings, 'ACCOUNT_LOGIN_DEBUG', False):
            try:
                id = int(request.GET.get('loginas', 0))
                user = User.objects.get(pk=id)
            except ValueError:
                return
            except User.DoesNotExist:
                return
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)    


class OneTimeCodeAuthMiddleware(object):
    """
    This middleware can authenticate user with onetimecode
    from otcode param of the query data.
    """

    def process_request(self, request):
        """
        Authenticate user with onetimecode from
        otcode param of the query data.
        """

        #Check that required middleware is enabled
        middleware = 'account.middleware.OneTimeCodeAuthMiddleware'
        if not middleware in settings.MIDDLEWARE_CLASSES:
            raise Exception('You should enable %s' % middleware)

        code = request.REQUEST.get('otcode', None)
        print code

        if not code:
            return


        try:
            otcode = OneTimeCode.objects.get(pk=code)
        except OneTimeCode.DoesNotExist:
            # TODO: may be need new setting
            # TODO: how we can calculate view which handles / url?
            return HttpResponseRedirect('/')

        user = authenticate(code=code)

        if user:
            if 'activation' == otcode.action:
                user.is_active = True
                user.save()
                email_template(user.email, 'account/mail/welcome.txt',
                               **{'login': user.username, 'domain': settings.DOMAIN})

            if 'new_password' == otcode.action:
                user.set_password(otcode.data)
                user.save()

            login(request, user)    
        otcode.delete()


class TestCookieMiddleware(object):
    """
    This middleware fixes error that appeares when user try to login
    not from page that was generated with django.contrib.auth.views.login view.
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Setup test cookie.
        """

        request.session.set_test_cookie()
