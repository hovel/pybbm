Installation
============

Requirements
------------

PyBBM requires the following packages:

* django
* markdown
* postmarkup
* django-annoying


By installing PyBBM with ``pip`` or ``easy_install``, all the above dependencies will be installed automatically::

    pip install pybbm

* We strongly recommend you to use `south` application for building migration in your projects.
  PyBBM forum supports `south`, but it should be installed separately.

* For better perfomance and easy images thumbnailing you can use any thumbnail django application.
  PyBBM by default uses `sorl.thumbnail` if it installed and included in your `INSTALLED_APPS` setting.
  It is used for defining `avatar` field in `PybbProfile` model and for resizing avatar in `pybb/avatar.html`
  template.

* `PIL` (Python Imaging Library) or it fork `Pillow` is optional if you configure sorl.thumbnail to use
  different backend or don't use sorl.thumbnail in general, but remember, that using an ImageField in forms requires that the Python Imaging Library
  is installed (e.g. you should install it if you use buildin profile).

* PyBBM emulates behavior and functionality of `django-pure-pagination`, but we recommend to install it in your
  project, if you didn't did this yet

* For better support ru language you can install `pytils` application.

Fresh project
-------------

If you start a new project based on pybbm, checkout pybbm.org website codebase from https://github.com/hovel/pybbm_org
and skip next steps )

Enable applications and edit settings
-------------------------------------

* Add following apps to your `INSTALLED_APPS` to enable pybbm and required applications.

    * pybb

  ::

    INSTALLED_APPS = (
        ....
        'pybb',
        ...
    )

  It is highly recommended that you also enable `south` application for properly
  migrate future updates and `pytils` application for better support ru language

* Add `pybb.context_processors.processor` to your `settings.TEMPLATE_CONTEXT_PROCESSORS`::

    TEMPLATE_CONTEXT_PROCESSORS = (
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

Setup forum's profile model and PYBB_PROFILE_RELATED_NAME setting.

If you have no site profile, dafault settings will satisfy your needs.

If you have custom user model, which stores all profile fields itself, or
if you have custom site profile model, then check that it inherits from `pybb.profiles.PybbProfile` or
contains all fields and properties from this class.
Then set `PYBB_PROFILE_RELATED_NAME` to `None` for custom user model, or to related_name
from OneToOne field related to User from custom site profile model

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

