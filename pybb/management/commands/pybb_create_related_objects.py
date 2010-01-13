from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count
from django.contrib.auth.models import User

from pybb.models import Profile, ReadTracking

class Command(BaseCommand):
    help = 'Create Profile and ReadTracking objects for users which do not have them'

    def handle(self, *args, **kwargs):
        profile_count = 0
        readtracking_count = 0

        for user in User.objects.all():
            obj, new = Profile.objects.get_or_create(user=user)
            if new:
                profile_count += 1
            obj, new = ReadTracking.objects.get_or_create(user=user)
            if new:
                readtracking_count += 1

        print 'New profiles: %d' % profile_count
        print 'New ReadTracking objecgts: %d' % readtracking_count
