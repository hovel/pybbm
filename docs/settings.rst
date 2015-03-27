Settings
========

Basic settings
--------------

.. _PYBB_TOPIC_PAGE_SIZE:

PYBB_TOPIC_PAGE_SIZE
....................

Number of posts in topic page

Default: 10

.. _PYBB_FORUM_PAGE_SIZE:

PYBB_FORUM_PAGE_SIZE
....................

Number of topics in forum page

Default: 10

.. _PYBB_FREEZE_FIRST_POST:

PYBB_FREEZE_FIRST_POST
......................

Freeze first post in topics (show on every page)

Default: False

.. _PYBB_DEFAULT_TITLE:

PYBB_DEFAULT_TITLE
..................

Default title for forum index page

Default: 'PYBB Powered Forum'

.. _PYBB_DEFAULT_AUTOSUBSCRIBE:

PYBB_DEFAULT_AUTOSUBSCRIBE
..........................

Users will be automatically subscribed to topic when create post in it.

Default: True

.. _PYBB_DISABLE_SUBSCRIPTIONS:

PYBB_DISABLE_SUBSCRIPTIONS
..........................

Users won't be able to subscribe to topic.
If you want to have a more advanced mode than enable / disable (for example, use model permissions),
you just have to overwrite the "may_subscribe_topic" method of the Permission handler.
If you disabled topic subscriptions, already subscribed users will still receive notifications:
see ``PYBB_DISABLE_NOTIFICATIONS`` to stop notifications sending.

Default: False

.. _PYBB_DISABLE_NOTIFICATIONS:

PYBB_DISABLE_NOTIFICATIONS
..........................

Users which have subscribed to a topic won't receive notifications but still be able to subscribe
to topics. See ``PYBB_DISABLE_NOTIFICATIONS`` to disable topic subscription too.
This is usefull if you want to to use your own notification system.

Default: False

.. _PYBB_USE_DJANGO_MAILER:

PYBB_USE_DJANGO_MAILER
......................

When True and django-mailer app installed, then for sending email pybbm will use this app. With django-mailer you can
manage emails from your site in queue. But in this case you have to periodically actually
send emails from queue. For more information see `app home page <https://github.com/pinax/django-mailer/>`_.

Default: False

.. _PYBB_INITIAL_CUSTOM_USER_MIGRATION:

PYBB_INITIAL_CUSTOM_USER_MIGRATION
..................................

Name of initial south migration in app where placed custom user model.
``None`` means that if app with custom user model has migrations, then '0001_initial.py' will be used by default.

Default: None


Emoticons
---------

.. _PYBB_SMILES_PREFIX:

PYBB_SMILES_PREFIX
..................

Prefix for emoticons images set, related to STATIC_URL.

Default: 'pybb/emoticons'

.. _PYBB_SMILES:

PYBB_SMILES
...........

Dict for emoticon replacement.
Key - text to be replaced, value - image name.

Default::

    {
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
    }

e.g. text  ";)" in post will be replaced to::

    <img src="{{ STATIC_URL }}{{ PYBB_SMILES_PREFIX }}wink.png">

with default setting.


User profile settings
---------------------

Next settings used only if you don't customize user profile model,
user profile creation form or templates.

.. _PYBB_PROFILE_RELATED_NAME:

PYBB_PROFILE_RELATED_NAME
.........................

Related name from profile's OneToOne relationship to User model. If profile model is User
model itselt then set it to `None`.

Default: 'pybb_profile'

For more information see :doc:`how to use custom user model with pybbm</customuser>`

.. _PYBB_AVATAR_WIDTH:

PYBB_AVATAR_WIDTH
.................

Avatar width to use in templates (avatars scaled using sorl.thumbnail
if it installed and included in project).

Default: 80

.. _PYBB_AVATAR_HEIGHT:

PYBB_AVATAR_HEIGHT
..................

Avatar height to use in templates (avatars scaled using sorl.thumbnail
if it installed and included in project)

Default: 80

.. _PYBB_MAX_AVATAR_SIZE:

PYBB_MAX_AVATAR_SIZE
....................

Maximum avatar size, in bytes

Default: 51200 (50 Kb)

.. _PYBB_DEFAULT_TIME_ZONE:

PYBB_DEFAULT_TIME_ZONE
......................

Default time zone for forum as integer. E.g. setting to 1 means GMT+1 zone.

Default: 3 (Moscow)

.. _PYBB_SIGNATURE_MAX_LENGTH:

PYBB_SIGNATURE_MAX_LENGTH
.........................

Limit of sybmols in user signature

Default: 1024

.. _PYBB_SIGNATURE_MAX_LINES:

PYBB_SIGNATURE_MAX_LINES
........................

Limit of lines in user signature

Default: 3

.. _PYBB_DEFAULT_AVATAR_URL:

PYBB_DEFAULT_AVATAR_URL
.......................

Will be used if user doesn't upload avatar

Default: settings.STATIC_URL + 'pybb/img/default_avatar.jpg'

Style
-----

You can use builtin templates with custom basic template.

.. _PYBB_TEMPLATE:

PYBB_TEMPLATE
.............

Builtin templates will inherit this template

Default: 'base.html


Markup engines
--------------

.. _PYBB_MARKUP:

PYBB_MARKUP
...........

Markup engine used in forum. Also see :ref:`PYBB_MARKUP_ENGINES` below

Default: 'bbcode`

.. _PYBB_MARKUP_ENGINES_PATHS:

PYBB_MARKUP_ENGINES_PATHS
.........................

Dict with avaiable markup engines path. One of them should be selected with PYBB_MARKUP

Markup engine should be a path to a class, that inherits from `pybb.markup.base.BaseParser`.
Markup engine should take care of replacing smiles in body with related emoticons.

by default PyBBM support `bbcode` and `markdown` markup::

    {
        'bbcode': 'pybb.markup.bbcode.BBCodeParser',
        'markdown': 'pybb.markup.markdown.MarkdownParser'
    }

Please note, that previous version of pybb used two different settings : 
`PYBB_MARKUP_ENGINES` and `PYBB_QUOTE_ENGINES` which were callables.
This is still supported, but is deprecated.

.. _PYBB_MARKUP_ENGINES:

PYBB_MARKUP_ENGINES (deprecated)
................................

Should be the same dict with paths to markup engine classes as `PYBB_MARKUP_ENGINES_PATH` setting

Default: `PYBB_MARKUP_ENGINES_PATHS`.

For more information see :doc:`markup`

.. _PYBB_QUOTE_ENGINES:

PYBB_QUOTE_ENGINES (deprecated)
...............................

**Deprecation note: Every markup class must inherit from  `pybb.markup.base.BaseParser`**

**For more information see :doc:`markup`**

Should be the same dict with paths to markup engine classes as `PYBB_MARKUP_ENGINES_PATH` setting

Default: `PYBB_MARKUP_ENGINES_PATHS`.


Post cleaning/validation
------------------------

.. _PYBB_BODY_CLEANERS:

PYBB_BODY_CLEANERS
..................

List of paths to 'cleaner' functions for body post to automatically remove undesirable content from posts.
Cleaners are user-aware, so you can disable them for some types of users.

Each function in list should accept `auth.User` instance as first argument and `string` instance as second, returned value will be sended to next function on list or saved and rendered as post body.

for example this is enabled by default `rstrip_str` cleaner::

    def rstrip_str(user, str):
        if user.is_staff:
            return str
        return '\n'.join([s.rstrip() for s in str.splitlines()])

Default::

    PYBB_BODY_CLEANERS = ['pybb.markup.base.rstrip_str', 'pybb.markup.base.filter_blanks']

.. _PYBB_BODY_VALIDATOR:

PYBB_BODY_VALIDATOR
...................

Extra form validation for body of post.

Called as::

    PYBB_BODY_VALIDATOR(user, body)

at `clean_body` method of `PostForm` Here you can do various checks based on user stats.
E.g. allow moderators to post links and don't allow others. By raising::

    forms.ValidationError('Here Error Message')

You can show user what is going wrong during validation.

You can use it for example for time limit between posts, preventing URLs, etc.

Default: None


Anonymous/guest posting
-----------------------

.. _PYBB_ENABLE_ANONYMOUS_POST:

PYBB_ENABLE_ANONYMOUS_POST
..........................

Allow post for not-authenticated users.

Default: False

See :doc:`anonymous posting</anonymous>` for details.

.. _PYBB_ANONYMOUS_USERNAME:

PYBB_ANONYMOUS_USERNAME
.......................

Username for anonymous posts. If no user with this username exists it will be created on first anonymous post.

Default: 'Anonymous'

.. _PYBB_ANONYMOUS_VIEWS_CACHE_BUFFER:

PYBB_ANONYMOUS_VIEWS_CACHE_BUFFER
.................................

Number of anonymous views for each topic, that will be cached. For disabling caching anonymous views
just set it to `None`.

Default: 100


Premoderation
-------------

.. _PYBB_PREMODERATION:

PYBB_PREMODERATION
..................

Filter for messages that require pre-moderation.

Default: False

See :doc:`Pre-moderation</premoderation>` for details.


Attachments
-----------

.. _PYBB_ATTACHMENT_ENABLE:

PYBB_ATTACHMENT_ENABLE
......................

Enable attahcments for all users.

Default: False

.. _PYBB_ATTACHMENT_SIZE_LIMIT:

PYBB_ATTACHMENT_SIZE_LIMIT
..........................

Maximum attachment limit (in bytes).

Default: 1048576 (1Mb)

.. _PYBB_ATTACHMENT_UPLOAD_TO:

PYBB_ATTACHMENT_UPLOAD_TO
.........................

Directory in your media path for uploaded attacments.

Default: 'pybb_upload/attachments'

Polls
-----

Note: For disabling polls on your forum, write custom permission handler and return from `may_create_poll` method `False`
See `PYBB_PERMISSION_HANDLER` setting.

.. _PYBB_POLL_MAX_ANSWERS:

PYBB_POLL_MAX_ANSWERS
.....................

Max count of answers, that user can add to topic.

Default: 10


Permissions
-----------

.. _PYBB_AUTO_USER_PERMISSIONS:

PYBB_AUTO_USER_PERMISSIONS
..........................

Automatically adds add post and add topic permissions to users on user.save().

Default: True

.. _PYBB_PERMISSION_HANDLER:

PYBB_PERMISSION_HANDLER
.......................

If you need custom permissions (for example, private forums based on application-specific 
user groups), you can set :ref:`PYBB_PERMISSION_HANDLER` to a class which inherits from
`pybb.permissions.DefaultPermissionHandler` (default), and override any of the `filter_*` and
`may_*` method. For details, look at the source of `pybb.permissions.DefaultPermissionHandler`.
All methods from permission handler (custom or default) can be used in templates as filters,
if loaded pybb_tags. In template will be loaded methods which start with 'may' or 'filter'
and with three or two arguments (include 'self' argument)

Default: 'pybb.permissions.DefaultPermissionHandler'
