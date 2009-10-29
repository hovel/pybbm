from urlparse import urljoin
from os.path import join

from django.conf import settings

def get(key, default):
    return getattr(settings, key, default)

UPLOAD_DIR = 'pybb_upload'

TOPIC_PAGE_SIZE = get('PYBB_TOPIC_PAGE_SIZE', 10)
FORUM_PAGE_SIZE = get('PYBB_FORUM_PAGE_SIZE', 20)
USERS_PAGE_SIZE = get('PYBB_USERS_PAGE_SIZE', 20)
HOST = get('PYBB_HOST', 'localhost:8000')

# Avatar settings
AVATARS_UPLOAD_TO = get('PYBB_AVATARS_UPLOAD_TO', join(UPLOAD_DIR, 'avatars'))
AVATAR_WIDTH = get('PYBB_AVATAR_WIDTH', 60)
AVATAR_HEIGHT = get('PYBB_AVATAR_HEIGHT', 60)
DEFAULT_AVATAR_URL = 'http://%s%s' % (HOST, get('PYBB_DEFAULT_AVATAR_URL', urljoin(settings.MEDIA_URL, 'pybb/img/default_avatar.jpg')))

DEFAULT_TIME_ZONE = get('PYBB_DEFAULT_TIME_ZONE', 3)
SIGNATURE_MAX_LENGTH = get('PYBB_SIGNATURE_MAX_LENGTH', 1024)
SIGNATURE_MAX_LINES = get('PYBB_SIGNATURE_MAX_LINES', 3)
QUICK_TOPICS_NUMBER = get('PYBB_QUICK_TOPICS_NUMBER', 10)
QUICK_POSTS_NUMBER = get('PYBB_QUICK_POSTS_NUMBER', 10)
READ_TIMEOUT = get('PYBB_READ_TIMEOUT', 3600 * 24 * 7)
POST_AUTOJOIN_TIMEOUT = get('PYBB_POST_TIMEOUT_AUTOJOIN', 60) # minutes
HEADER = get('PYBB_HEADER', 'PYBB')
TAGLINE = get('PYBB_TAGLINE', 'Django based forum engine')
DEFAULT_MARKUP = get('PYBB_DEFAULT_MARKUP', 'bbcode')
NOTICE = get('PYBB_NOTICE', '')
FREEZE_FIRST_POST = get('PYBB_FREEZE_FIRST_POST', True)
ADMIN_URL = get('PYBB_ADMIN_URL', '/admin/')
EMAIL_DEBUG = get('PYBB_EMAIL_DEBUG', False)
ATTACHMENT_UPLOAD_TO = get('PYBB_ATTACHMENT_UPLOAD_TO',
                           join(UPLOAD_DIR, 'attachments'))
ATTACHMENT_SIZE_LIMIT = get('PYBB_ATTACHMENT_SIZE_LIMIT', 1024 * 1024)
ATTACHMENT_ENABLE = get('PYBB_ATTACHMENT_ENABLE', True)

# That is used internally
DISABLE_NOTIFICATION = False
