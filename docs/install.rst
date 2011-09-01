Installation
============

Requirements
------------

PyBBM required next packages to be installed:

* django
* markdown
* postmarkup
* south
* pytils
* django-annoying
* sorl-thumbnail

All packages can be installed as a dependency for PyBBM if you install it with pip or easy_install::

    pip install pybbm

* PIL (Python Imaging Library) is optional if you configure sorl.thumbnail to use different backend,
  but remmember, that using an ImageField in forms requires that the Python Imaging Library is
  installed (e.g. you should install it if you use buildin profile).

Enable applications and edit settings
-------------------------------------

* Add following apps to your `INSTALLED_APPS` to enable pybbm and required applications.

    * pybb
    * pytils
    * sorl.thumbnail

  ::

    INSTALLED_APPS = (
        ....
        'pybb',
        'pytils',
        'sorl.thumbnail',
        ...
    )

  It is highly recommended that you also enable `south` application for properly
  migrate future updates

* Add `pybb.context_processors.processor` to your `settings.CONTEXT_PROCESSORS`
* Add `pybb.middleware.PybbMiddleware` to your `settings.MIDDLEWARE_CLASSES`

Enable PyBBM urlconf
--------------------

Put `include('pybb.urls', namespace='pybb'))` into main project urls.py file::

    urlpatterns = patterns('',
        ....
        (r'^forum/', include('pybb.urls', namespace='pybb')),
        ....
    )

Enable your site profile
------------------------

If you have no site profile, add next line to your settings::

    AUTH_PROFILE = 'pybb.Profile'

If you have custom site profile check that it inherits from `pybb.models.PybbProfile` or
contains all field from this class.

Sync/Migrate database
---------------------

Run `syncdb` and `migrate` commands::

    python manage.py syncdb
    python manage.py migrate

WARNING
'''''''

If you have south enabled and use profile class under south control (like 'pybb.Profile')
profile for superuser will not be created after syncdb/migrate. It will be created during
first login of this user to site by `pybb.middleware.PybbMiddleware`.

Templates
---------

Check that:

* your templates directory contains "base.html" template or you
  set custom base template with `PYBB_TEMPLATE`

* Basic template contains at last `content` block.

