from os.path import join
from annoying.functions import get_config

PYBB_TOPIC_PAGE_SIZE = get_config('PYBB_TOPIC_PAGE_SIZE', 10)
PYBB_FORUM_PAGE_SIZE = get_config('PYBB_FORUM_PAGE_SIZE', 20)
PYBB_USERS_PAGE_SIZE = get_config('PYBB_USERS_PAGE_SZIE', 20)
PYBB_AVATAR_WIDTH = get_config('PYBB_AVATAR_WIDTH', 60)
PYBB_AVATAR_HEIGHT = get_config('PYBB_AVATAR_HEIGHT',60)
PYBB_DEFAULT_TIME_ZONE = get_config('PYBB_DEFAULT_TIME_ZONE', 3)

PYBB_SIGNATURE_MAX_LENGTH = get_config('PYBB_SIGNATURE_MAX_LENGTH', 1024)
PYBB_SIGNATURE_MAX_LINES = get_config('PYBB_SIGNATURE_MAX_LINES', 3)

PYBB_READ_TIMEOUT = get_config('PYBB_READ_TIMEOUT', 3600 * 24 * 7) # seconds

PYBB_DEFAULT_MARKUP = get_config('PYBB_DEFAULT_MARKUP', 'bbcode')
PYBB_FREEZE_FIRST_POST = get_config('PYBB_FREEZE_FIRST_POST', False)

PYBB_ATTACHMENT_SIZE_LIMIT = get_config('PYBB_ATTACHMENT_SIZE_LIMIT', 1024 * 1024)
PYBB_ATTACHMENT_ENABLE = get_config('PYBB_ATTACHMENT_ENABLE', False)
PYBB_ATTACHMENT_UPLOAD_TO = get_config('PYBB_ATTACHMENT_UPLOAD_TO', join('pybb_upload', 'attachments'))

PYBB_DEFAULT_AVATAR_URL = get_config('PYBB_DEFAULT_AVATAR_URL', get_config('MEDIA_URL', '/media/') + 'pybb/img/default_avatar.jpg')

PYBB_DEFAULT_TITLE = get_config('PYBB_DEFAULT_TITLE', 'PYBB Powered Forum')

from bbmarkup import bbcode
from markdown import Markdown
from django.utils.html import urlize

PYBB_MARKUP_ENGINES = get_config('PYBB_MARKUP_ENGINES', {
    'bbcode': lambda str: urlize(bbcode(str)),
    'markdown': lambda str: urlize(Markdown(safe_mode='escape').convert(str))
})