Pre-moderation
==============

PyBBM shipped with fully customizable pre-moderation system.

Because in different circumstances you may need different pre-moderation conditions,
pybbm gives you ability to create custom filter for messages that require pre-moderation.

All you need is to provide function from two arguments: `user` and `body`. This function
should return `True` if message pass filter and `False` if message require pre-moderation.

For example, next filter allow to post without pre-moderation only for superusers::

    def check_superuser(user, post):
        if user.is_superuser:
            return True
        return False

Told pybbm to use this function by setting `PYBB_PREMODERATION` in settings::

    PYBB_PREMODERATION = check_superuser

