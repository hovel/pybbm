Anonymous posting
=================

PyBBM allow you to enable anonymous posting on forum.

Be very carefull by enabling anonymous posting, it is better to enable
`BODY_CLEANER` setting to cleanup spam links from posts.

Enable :ref:`PYBB_ENABLE_ANONYMOUS_POST` and set :ref:`PYBB_ANONYMOUS_USERNAME` for enabling anonymous posting::

    PYBB_ENABLE_ANONYMOUS_POST = True
    PYBB_ANONYMOUS_USERNAME = 'Anonymous'

Carefully set :ref:`PYBB_ANONYMOUS_USERNAME`. It is better to create user with this username yourself rather than left
it to autoregister on first anonymous post, somemone may want to use this username and register before first
anonymous post will be posted, in that case anonymous post will share same account with this user.

Anonymous topic views count cached for each topic. The reason to do this is not update database on each anonymous
request. Default value that will be cached is 100, this values controlled by :ref:`PYBB_ANONYMOUS_VIEWS_CACHE_BUFFER`
setting and can be disabled by this setting too.