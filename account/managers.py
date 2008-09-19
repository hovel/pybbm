import os
import sha
import time

from django.db.models import Manager

class OneTimeCodeManager(Manager):
    """
    Manager for onetimecode model.
    """

    def generate(self, user, action=None, data=None):
        """
        Create new onetimecode for user and save it.
        """

        rnd = '%s-%s' % (os.urandom(20), str(time.time()))
        code = sha.new(rnd).hexdigest()
        return self.create(code=code, user=user, action=action, data=data)


    def wrap_url(self, url, user, action=None, data=None):
        """
        Create new onetimecode and append it to the url.
        """

        otcode = self.generate(user, action=action, data=data)
        clue = '?' in url and '&' or '?'
        url = '%s%sotcode=%s' % (url, clue, otcode.code)
        return url
