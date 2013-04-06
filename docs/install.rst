Installation
============

Requirements
------------

PyBBM required next packages to be installed:

* django
* markdown
* postmarkup
* django-annoying
* django-pure-pagination


All packages can be installed as a dependency for PyBBM if you install it with pip or easy_install::

    pip install pybbm

* We strongly recommend you to use `south` application for building migration in your projects.
PyBBM forum supports `south`, but it should be installed separately.

* For better perfomance and easy using you can use any thumbnail django application. PyBBM by default use
`sorl.thumbnail` if it installed and included in your `INSTALLED_APPS` setting. It is used for defining
`avatar` field in `PybbProfile` model and for resizing avatar in `pybb/avatar.html` template.

* `PIL` (Python Imaging Library) or it fork `Pillow` is optional if you configure sorl.thumbnail to use
different backend, but remember, that using an ImageField in forms requires that the Python Imaging Library
is installed (e.g. you should install it if you use buildin profile).

* For better support ru language you can install `pytils` application.

Fresh project
-------------

If you start a new project based on pybbm, checkout pybbm.org website codebase from https://github.com/hovel/pybbm_org
and skip next steps )

Enable applications and edit settings
-------------------------------------

* Add following apps to your `INSTALLED_APPS` to enable pybbm and required applications.

    * pybb
    * pure_pagination

  ::

    INSTALLED_APPS = (
        ....
        'pybb',
        'pure_pagination',
        ...
    )

  It is highly recommended that you also enable `south` application for properly
  migrate future updates and `pytils` application for better support ru language

* Add `pybb.context_processors.processor` to your `settings.CONTEXT_PROCESSORS`::

    CONTEXT_PROCESSORS = (
        ...
        'pybb.context_processors.processor',
        ...
        )

* Add `pybb.middleware.PybbMiddleware` to your `settings.MIDDLEWARE_CLASSES`::

    MIDDLEWARE_CLASSES = (
        ...
        'pybb.middleware.PybbMiddleware',
        ...
    )

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

    AUTH_PROFILE_MODULE = 'pybb.Profile'

If you have custom site profile check that it inherits from `pybb.models.PybbProfile` or
contains all fields from this class.

Sync/Migrate database
---------------------

If you first time install pybbm and have south installed, run::

    python manage.py syncdb --all
    python manage.py migrate pybb --fake

or just::

    python manage.py syncdb

if south is not installed.

Run `migrate` command to update pybbm or if you migrate from pybb to pybbm::

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

* Basic template contains at least `content` block.

