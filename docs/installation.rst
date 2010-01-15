.. _installation:

Installation
============

If you like to use pybb as standalone application then may be you have to look on `other forum engines <http://code.djangoproject.com/wiki/ForumAppsComparison>`_. If you still want standalone pybb installation then setup django project with working signin/signup functions and then come back to this howto.
 

Integrating PyBB into existing django project
---------------------------------------------

* Install ``pybb dependencies``_ and pybb itself. You can ensure that all dependencies were installed by running ``manage.py shell`` and then ``import pybb.models``. If no exception was raised then you may proceed.
* Edit settings.py
  * Add ``pybb`` to ``INSTALLED_APPS``
  * Add ``from pybb.settings import *`` line
  * Add ``pybb.context_processors.pybb`` to ``TEMPLATE_CONTEXT_PROCESSORS``
  * Add ``pybb.middleware.PybbMiddleware`` to ``MIDDLEWARE_CLASSES``
* Add ``url('', include('pybb.urls'))`` to ``urls.py`` file
* Run command ``manage.py migrate`` if you installed `south <http://south.aeracode.org>`_ (recommended) or ``./manage.py syncdb`` (if south is not installed)
* Symlink or copy pybb static files to %MEDIA_ROOT%/pybb. You can use ``./manage.py pybb_install`` command.

.. _pybb dependencies: _dependencies
