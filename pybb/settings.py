from urlparse import urljoin
from os.path import join
import sys

from django.conf import settings

DEFAULTS = (
    ('TOPIC_PAGE_SIZE', 10),
    ('FORUM_PAGE_SIZE', 20),
    ('USERS_PAGE_SIZE', 20),
    ('HOST', 'hey.fix.your.settings'),
    ('AVATARS_UPLOAD_TO', join('pybb_upload', 'avatars')),
    ('AVATAR_WIDTH', 60),
    ('AVATAR_HEIGHT', 60),
    ('DEFAULT_AVATAR_URL', 'pybb/img/default_avatar.jpg'),
    ('DEFAULT_TIME_ZONE', 3),
    ('SIGNATURE_MAX_LENGTH', 1024),
    ('SIGNATURE_MAX_LINES', 3),
    ('QUICK_TOPICS_NUMBER', 10),
    ('QUICK_POSTS_NUMBER', 10),
    ('READ_TIMEOUT', 3600 * 24 * 7), # seconds
    ('POST_TIMEOUT_AUTOJOIN', 60), # minutes
    ('HEADER', 'PyBB'),
    ('TAGLINE', 'Yet another PyBB forum'),
    ('DEFAULT_MARKUP', 'bbcode'),
    ('NOTICE', ''),
    ('FREEZE_FIRST_POST', True),
    ('ADMIN_URL', '/admin/'),
    ('EMAIL_DEBUG', False),
    ('ATTACHMENT_UPLOAD_TO', join('pybb_upload', 'attachments')),
    ('ATTACHMENT_SIZE_LIMIT', 1024 * 1024),
    ('ATTACHMENT_ENABLE', True),
)

mod = sys.modules[__name__]

for key, default in DEFAULTS:
    setattr(mod, key, getattr(settings, 'PYBB_%s' % key, default))

mod.DEFAULT_AVATAR_URL = 'http://%s%s%s' % (mod.HOST, settings.MEDIA_URL,
                                            mod.DEFAULT_AVATAR_URL)


# Internal settings
DISABLE_NOTIFICATION = False
