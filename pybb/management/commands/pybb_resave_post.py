from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.conf import settings

from pybb.models import Post


class Command(BaseCommand):
    help = 'Resave all posts.'

    def handle(self, *args, **kwargs):
        settings.PYBB_DISABLE_NOTIFICATION = True

        for count, post in enumerate(Post.objects.all()):
            if count and not count % 1000:
                print count
            post.save()
