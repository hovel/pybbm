"""
Backend which autenticates user with onetimecode.
"""

from django.contrib.auth.models import User

from account.models import OneTimeCode

class OneTimeCodeBackend(object):
    """
    Backend which authenticats user with onetimecode.
    """

    def authenticate(self, code):
        """
        Authenticate user with onetimecode.
        """

        if code:
            try:
                otcode = OneTimeCode.objects.get(pk=code)
            except OneTimeCode.DoesNotExist:
                return None
            else:
                user = otcode.user
                otcode.delete()
                return user


    def get_user(self, user_id):
        """
        Find user with given ID.
        """

        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
