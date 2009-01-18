from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from pybb.gravatar import check_gravatar

class Command(BaseCommand):
    help = 'Fetch avatars from gravatar.com service for those users which did not set avatar'

    def handle(self, *args, **kwargs):
        for user in User.objects.all():
            print user.username
            old_avatar = user.pybb_profile.avatar
            if check_gravatar(user, ignore_date_joined=True):
                print ' + Found gravatar'
