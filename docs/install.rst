Installation
============

Mandatory dependencies
----------------------

PyBBM requires the following packages:

* django
* markdown
* bbcode
* django-annoying


By installing PyBBM with ``pip`` or ``easy_install``, all the above dependencies will be installed automatically::

    pip install pybbm

Optional dependencies
---------------------

The following dependencies are optional. You can install them with ``pip install``:

* We strongly recommend to use ``south`` (with django<1.7) and django migrations since 1.7 version
  to smoothly migrate database schema in your projects.

* For better perfomance and easy images thumbnailing you can use any thumbnail django application.
  PyBBM by default uses ``sorl.thumbnail`` if it is installed and included in your ``INSTALLED_APPS`` setting.
  It is used for defining the `avatar` field in the `PybbProfile` model and for resizing the avatar
  in the ``pybb/avatar.html`` template. If you decide to install ``sorl.thumbnail`` with django 1.7 you
  have to install at least 11.12.1b version with::

    pip install "sorl-thumbnail>=11.12.1b"

* ``PIL`` (Python Imaging Library) or its more up-to-date fork ``Pillow`` is optional if you configure ``sorl.thumbnail``
  to use different backend or don't use ``sorl.thumbnail`` in general, but remember that using an ImageField in forms
  requires the Python Imaging Library to be installed (i.e. you should install it if you use the built-in profile).

* PyBBM emulates the behavior and functionality of ``django-pure-pagination``, but we recommend to install it in your
  project.

* For better support of the Russian language ``ru``, install ``pytils``.

* Choose from ``bbcode`` and ``markdown`` libraries if you use one of the attached to pybbm markup engines.
  For more information see :doc:`markup`

Fresh project
-------------

If you start a new project based on pybbm, checkout pybbm.org website codebase from https://github.com/hovel/pybbm_org
and skip the next steps.

Enable applications and edit settings
-------------------------------------

* Add the following apps to your ``INSTALLED_APPS`` to enable pybbm and required applications:

  * pybb

  ::

    INSTALLED_APPS = (
        ....
        'pybb',
        ...
    )

* Add ``pybb.context_processors.processor`` to your ``settings.TEMPLATE_CONTEXT_PROCESSORS``::

    TEMPLATE_CONTEXT_PROCESSORS = (
        ...
        'pybb.context_processors.processor',
        ...
        )

* Add ``pybb.middleware.PybbMiddleware`` to your ``settings.MIDDLEWARE_CLASSES``::

    MIDDLEWARE_CLASSES = (
        ...
        'pybb.middleware.PybbMiddleware',
        ...
    )

Enable PyBBM urlconf
--------------------

Put ``include('pybb.urls', namespace='pybb'))`` into main project ``urls.py`` file::

    urlpatterns = patterns('',
        ....
        (r'^forum/', include('pybb.urls', namespace='pybb')),
        ....
    )

Enable your site profile
------------------------

Setup forum's profile model and ``PYBB_PROFILE_RELATED_NAME`` setting.

If you have no site profile, dafault settings will satisfy your needs.

If you have a custom user model, which stores all profile fields itself, or if you have custom site profile model, then check that it inherits from ``pybb.profiles.PybbProfile`` or contains all fields and properties from this class.

Then set ``PYBB_PROFILE_RELATED_NAME`` to ``None`` for custom user model, or to related_name
from OneToOne field related to User from custom site profile model.

For more information see :doc:`how to use custom user model with pybbm</customuser>`

Sync/Migrate database
---------------------

Since django 1.7 release you have several combinations of installed packages that affect database migrations:

* **django >= 1.7**
  Django since 1.7 version has it's own `migration engine <https://docs.djangoproject.com/en/1.7/topics/migrations/>`_.
  Pybbm fully supports django 1.7 migrations, so just run::

    python manage.py migrate pybb

* **django < 1.7, south >= 1.0**
  South since version 1.0 changed default migration directory to `south_migrations`.
  This give reusable apps ability to support django native migrations and south migrations in parallel.
  Migration commands that you need::

    python manage.py syncdb --all
    python manage.py migrate pybb --fake

* **django < 1.7, south < 1.0**
  Override `SOUTH_MIGRATION_MODULES` setting as::

    SOUTH_MIGRATION_MODULES = {
        'pybb': 'pybb.south_migrations',
    }

  then run commands to migrate from above

* **django <1.7, south not installed**
  just type::

    python manage.py syncdb

  to get actual database state for your pybbm release

WARNING
'''''''

* If you have south enabled and use profile class under south control (like 'pybb.Profile'),
the profile for superuser will not be created after syncdb/migrate. It will be created during
first login of this user to the site by `pybb.middleware.PybbMiddleware`.

* We recommend to use database engine that supports transaction management (all django backends except sqlite).
  Otherwise you have small chance to face some inconsistency in DB after failed post/topic creation.

Templates
---------

Check that:

* Your templates directory contains the "base.html" template. Otherwise, set a custom base template with :ref:`PYBB_TEMPLATE`.

* Basic template contains at least a ``content`` block.

