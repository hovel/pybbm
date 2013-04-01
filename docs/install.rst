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
* django-pure-pagination

* django-cbv (for django versions < 1.3)

All packages can be installed as a dependency for PyBBM if you install it with pip or easy_install::

    pip install pybbm

* PIL (Python Imaging Library) is optional if you configure sorl.thumbnail to use different backend,
  but remember, that using an ImageField in forms requires that the Python Imaging Library is
  installed (e.g. you should install it if you use buildin profile).

Fresh project
-------------

If you start a new project based on pybbm, checkout pybbm.org website codebase form https://github.com/hovel/pybbm_org
and skip next steps )

Enable applications and edit settings
-------------------------------------

* Add following apps to your `INSTALLED_APPS` to enable pybbm and required applications.

    * pybb
    * pytils
    * sorl.thumbnail
    * pure_pagination

  ::

    INSTALLED_APPS = (
        ....
        'pybb',
        'pytils',
        'sorl.thumbnail',
        'pure_pagination',
        ...
    )

  It is highly recommended that you also enable `south` application for properly
  migrate future updates

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

Set correct PYBB_PROFILE_RELATED_NAME setting.

If you have no site profile, dafault settings will satisfy your needs

If you have custom user model, which stores all profile fields itself or
if you have custom site profile model check that it inherits from `pybb.models.PybbProfileMixin` or
contains all fields and properties from this class.
Then set `PYBB_PROFILE_RELATED_NAME` to `None` for custom user model, or to related_name
from ForeignKey field related to User for custom site profile model

For more information see :doc:`how to use custom user model with pybbm</customuser>`

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

