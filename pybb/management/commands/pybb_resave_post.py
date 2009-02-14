from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from pybb.models import Post
from pybb import settings as app_settings

class Command(BaseCommand):
    help = 'Resave all posts.'

    def handle(self, *args, **kwargs):
        app_settings.DISABLE_NOTIFICATION = True

        for count, post in enumerate(Post.objects.all()):
            if count and not count % 1000:
                print count
            post.save()
