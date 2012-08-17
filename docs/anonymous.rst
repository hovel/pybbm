Anonymous posting
=================

PyBBM allow you to enable anonymous posting on forum.

Be very carefull by enabling anonymous posting, it is better to enable
`BODY_CLEANER` setting to cleanup spam links from posts.

Enable `PYBB_ENABLE_ANONYMOUS_POST` and set `PYBB_ANONYMOUS_USERNAME` for enabling anonymous posting::

    PYBB_ENABLE_ANONYMOUS_POST = True
    PYBB_ANONYMOUS_USERNAME = 'Anonymous'

Carefully set `PYBB_ANONYMOUS_USERNAME`. It is better to create user with this username yourself rather than left
it to autoregister on first anonymous post, somemone may want to use this username and register before first
anonymous post will be posted, in that case anonymous post will share same account with this user.