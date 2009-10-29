import re
#from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

import pybb
from pybb.models import Attachment, Profile

def build_new_path(path, dir):
    print path
    path = path.replace('pybb/' + dir, 'pybb_upload/' + dir)
    path = re.search('pybb_upload.*', path).group(0)
    return path


class Command(BaseCommand):
    help = 'Fix avatars paths'

    def handle(self, *args, **kwargs):

        for profile in Profile.objects.all():
            if profile.avatar:
                old_path = profile.avatar.path
                new_path = build_new_path(old_path, 'avatars')
                profile.avatar = new_path
                profile.save()
                print old_path, '-->', new_path
