from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from pybb.models import Forum

class Command(BaseCommand):
    help = 'Set and remove moderator to all forums'
    args = '{add|del} username'

    def handle(self, *args, **kwargs):
        if len(args) != 2:
            raise CommandError("Enter action {add|del} and username")
        action, username = args
        assert action in ('add', 'del')
        user = User.objects.get(username=username)
        forums = Forum.objects.all()
        for forum in forums:
            forum.moderators.remove(user)
            if action == 'add':
                forum.moderators.add(user)
