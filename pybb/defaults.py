from os.path import join
from django.conf import settings

PYBB_TOPIC_PAGE_SIZE = getattr(settings, 'PYBB_TOPIC_PAGE_SIZE', 10)
PYBB_FORUM_PAGE_SIZE = getattr(settings, 'PYBB_FORUM_PAGE_SIZE', 20)
PYBB_AVATAR_WIDTH = getattr(settings, 'PYBB_AVATAR_WIDTH', 80)
PYBB_AVATAR_HEIGHT = getattr(settings, 'PYBB_AVATAR_HEIGHT',80)
PYBB_MAX_AVATAR_SIZE = getattr(settings, 'PYBB_MAX_AVATAR_SIZE', 1024*50)
PYBB_DEFAULT_TIME_ZONE = getattr(settings, 'PYBB_DEFAULT_TIME_ZONE', 3)

PYBB_SIGNATURE_MAX_LENGTH = getattr(settings, 'PYBB_SIGNATURE_MAX_LENGTH', 1024)
PYBB_SIGNATURE_MAX_LINES = getattr(settings, 'PYBB_SIGNATURE_MAX_LINES', 3)

PYBB_DEFAULT_MARKUP = getattr(settings, 'PYBB_DEFAULT_MARKUP', 'bbcode')
PYBB_FREEZE_FIRST_POST = getattr(settings, 'PYBB_FREEZE_FIRST_POST', False)

PYBB_ATTACHMENT_SIZE_LIMIT = getattr(settings, 'PYBB_ATTACHMENT_SIZE_LIMIT', 1024 * 1024)
PYBB_ATTACHMENT_ENABLE = getattr(settings, 'PYBB_ATTACHMENT_ENABLE', False)
PYBB_ATTACHMENT_UPLOAD_TO = getattr(settings, 'PYBB_ATTACHMENT_UPLOAD_TO', join('pybb_upload', 'attachments'))

PYBB_DEFAULT_AVATAR_URL = getattr(settings, 'STATIC_URL', '') + 'pybb/img/default_avatar.jpg'

PYBB_DEFAULT_TITLE = getattr(settings, 'PYBB_DEFAULT_TITLE', 'PYBB Powered Forum')

from postmarkup import render_bbcode
from markdown import Markdown
from django.utils.html import urlize

PYBB_SMILES_PREFIX = getattr(settings, 'PYBB_SMILES_PREFIX', 'pybb/emoticons/')

PYBB_SMILES = getattr(settings, 'PYBB_SMILES', {
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

#MEDIA_URL = getattr(settings, 'MEDIA_URL', '/media/')
#STATIC_URL = getattr(settings, 'STATIC_URL', '')

def smile_it(str):
    s = str
    for smile, url in PYBB_SMILES.items():
        s = s.replace(smile, '<img src="%s%s%s" alt="smile" />' % (settings.STATIC_URL, PYBB_SMILES_PREFIX, url))
    return s

PYBB_MARKUP_ENGINES = getattr(settings, 'PYBB_MARKUP_ENGINES', {
    'bbcode': lambda str: urlize(smile_it(render_bbcode(str, exclude_tags=['size', 'center']))),
    'markdown': lambda str: urlize(smile_it(Markdown(safe_mode='escape').convert(str)))
})

PYBB_QUOTE_ENGINES = getattr(settings, 'PYBB_QUOTE_ENGINES', {
    'bbcode': lambda text, username="": '[quote="%s"]%s[/quote]\n' % (username, text),
    'markdown': lambda text, username="": '>'+text.replace('\n','\n>').replace('\r','\n>') + '\n'
})

PYBB_MARKUP = getattr(settings, 'PYBB_MARKUP', 'bbcode')
PYBB_BUTTONS = getattr(settings, 'PYBB_BUTTONS', {})
#Dict of buttons that will be used, instead of text links if defined
#Currently supported buttons:
#  new_topic
#  submit
#  save

PYBB_TEMPLATE = getattr(settings, 'PYBB_TEMPLATE', "base.html")
PYBB_DEFAULT_AUTOSUBSCRIBE = getattr(settings, 'PYBB_DEFAULT_AUTOSUBSCRIBE', True)
PYBB_ENABLE_ANONYMOUS_POST = getattr(settings, 'PYBB_ENABLE_ANONYMOUS_POST', False)
PYBB_ANONYMOUS_USERNAME = getattr(settings, 'PYBB_ANONYMOUS_USERNAME', 'Anonymous')
PYBB_PREMODERATION = getattr(settings, 'PYBB_PREMODERATION', False)
PYBB_ENABLE_SELF_CSS = getattr(settings, 'PYBB_ENABLE_SELF_CSS', False)