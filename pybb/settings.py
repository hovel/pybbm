from os.path import join
from annoying.functions import get_config

PYBB_TOPIC_PAGE_SIZE = get_config('PYBB_TOPIC_PAGE_SIZE', 10)
PYBB_FORUM_PAGE_SIZE = get_config('PYBB_FORUM_PAGE_SIZE', 10)
PYBB_USERS_PAGE_SIZE = get_config('PYBB_USERS_PAGE_SZIE', 20)
PYBB_AVATAR_WIDTH = get_config('PYBB_AVATAR_WIDTH', 60)
PYBB_AVATAR_HEIGHT = get_config('PYBB_AVATAR_HEIGHT',60)
PYBB_MAX_AVATAR_SIZE = get_config('PYBB_MAX_AVATAR_SIZE', 1024*50)
PYBB_DEFAULT_TIME_ZONE = get_config('PYBB_DEFAULT_TIME_ZONE', 3)

PYBB_SIGNATURE_MAX_LENGTH = get_config('PYBB_SIGNATURE_MAX_LENGTH', 1024)
PYBB_SIGNATURE_MAX_LINES = get_config('PYBB_SIGNATURE_MAX_LINES', 3)

PYBB_READ_TIMEOUT = get_config('PYBB_READ_TIMEOUT', 3600 * 24 * 7) # seconds

PYBB_DEFAULT_MARKUP = get_config('PYBB_DEFAULT_MARKUP', 'bbcode')
PYBB_FREEZE_FIRST_POST = get_config('PYBB_FREEZE_FIRST_POST', False)

PYBB_ATTACHMENT_SIZE_LIMIT = get_config('PYBB_ATTACHMENT_SIZE_LIMIT', 1024 * 1024)
PYBB_ATTACHMENT_ENABLE = get_config('PYBB_ATTACHMENT_ENABLE', False)
PYBB_ATTACHMENT_UPLOAD_TO = get_config('PYBB_ATTACHMENT_UPLOAD_TO', join('pybb_upload', 'attachments'))

PYBB_DEFAULT_AVATAR_URL = get_config('MEDIA_URL', '') + 'pybb/img/default_avatar.jpg'

PYBB_DEFAULT_TITLE = get_config('PYBB_DEFAULT_TITLE', 'PYBB Powered Forum')

from postmarkup import render_bbcode
from markdown import Markdown
from django.utils.html import urlize

PYBB_SMILES_PREFIX = 'pybb/emoticons/'

PYBB_SMILES = get_config('PYBB_SMILES', {
    '&gt;_&lt;': 'angry.png',
    ':.(': 'cry.png',
    'o_O': 'eyes.png',
    '[]_[]': 'geek.png',
    '8)': 'glasses.png',
    ':D': 'lol.png',
    ':(': 'sad.png',
    ':O': 'shok.png',
    '-_-': 'shy.png',
    ':)': 'smile.png',
    ':P': 'tongue.png',
    ';)': 'wink.png'
})

MEDIA_URL = get_config('MEDIA_URL', '/media/')

def smile_it(str):
    s = str
    for smile, url in PYBB_SMILES.items():
        s = s.replace(smile, '<img src="%s%s%s">' % (MEDIA_URL, PYBB_SMILES_PREFIX, url))
    return s

PYBB_MARKUP_ENGINES = get_config('PYBB_MARKUP_ENGINES', {
    'bbcode': lambda str: urlize(smile_it(render_bbcode(str))),
    'markdown': lambda str: urlize(smile_it(Markdown(safe_mode='escape').convert(str)))
})

PYBB_QUOTE_ENGINES = get_config('PYBB_QUOTE_ENGINES', {
    'bbcode': lambda text, username="": '[quote="%s"]%s[/quote]\n' % (username, text),
    'markdown': lambda text, username="": '>'+text.replace('\n','\n>').replace('\r','\n>') + '\n'
})