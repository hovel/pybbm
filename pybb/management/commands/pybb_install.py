from optparse import make_option
import os
import shutil

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

import pybb

def copydir(src, dst):
    if not os.path.exists(dst):
        print 'Creating directory: %s' % dst
        os.mkdir(dst)
    else:
        print 'Directory already exists: %s' % dst

    for fname in os.listdir(src):
        src_path = os.path.join(src, fname)
        dst_path = os.path.join(dst, fname)
        if os.path.isdir(src_path):
            copydir(src_path, dst_path)
        else:
            print 'Creating file: %s' % dst_path
            shutil.copy(src_path, dst_path)


class Command(BaseCommand):
    help = 'Install pybb'

    def handle(self, *args, **kwargs):
        src_static = os.path.join(os.path.dirname(os.path.realpath(pybb.__file__)), 'static', 'pybb')
        dst_static = os.path.join(settings.MEDIA_ROOT, 'pybb') 

        print 'You media root is %s' % settings.MEDIA_ROOT
        print 'Pybb static files found in %s' % src_static
        print 'You can link or copy pybb static files to %s' % dst_static
        print 'Link/Copy/Skip: [L/c/s]'

        answer = raw_input().lower()
        if answer == 'l':
            os.symlink(src_static, dst_static)
        elif answer == 'c':
            copydir(src_static, dst_static)
        elif answer == 's':
            pass
        else:
            raise Exception('Unknown answer')

        avatar_dir = os.path.join(dst_static, 'avatars')
        if not os.path.exists(avatar_dir):
            print 'Avatar directory does not exist: %s' % avatar_dir
            print 'Create avatar directory: [Y/n]'
            
            answer = raw_input().lower()
            if answer == 'y':
                print 'Creating directory: %s' % avatar_dir
                os.mkdir(avatar_dir)
                print 'Changing access mode of avatar directory to 777'
                os.chmod(avatar_dir, 0777)

        attachments_dir = os.path.join(dst_static, 'attachments')
        if not os.path.exists(attachments_dir):
            print 'Attachments directory does not exist: %s' % attachments_dir
            print 'Create attachments directory: [Y/n]'
            
            answer = raw_input().lower()
            if answer == 'y':
                print 'Creating directory: %s' % attachments_dir
                os.mkdir(attachments_dir)
                print 'Changing access mode of attachments directory to 777'
                os.chmod(attachments_dir, 0777)
